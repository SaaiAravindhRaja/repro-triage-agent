#!/usr/bin/env python3
"""Check the frozen expectations against saved GitHub Actions observations.

This is a replay of recorded outputs, not an LLM run. The linked run logs and
sandbox issues are the primary evidence for each observation.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from verify_trace import inspect as inspect_trace


ROOT = Path(__file__).resolve().parent / "golden"
VALID_EXPECTED = {"comment_and_label", "no_action"}
VALID_OBSERVED = VALID_EXPECTED | {"comment_only", "label_only", "multiple_comments", "other"}
CONFIG_PATHS = [
    ".github/workflows/smoke-triage.md",
    ".github/workflows/smoke-triage.lock.yml",
    ".claude/skills/repro-triage/SKILL.md",
    "scripts/preflight.py",
]
PREREGISTRATION_SHA = "e20790c791329d7217139b23efcffe7f8c682530"
WORKFLOW_ID = 390537521
WORKFLOW_PATH = ".github/workflows/smoke-triage.lock.yml"
EVALUATED_AGENTS_BLOB = "6101c80aa893cc65cb7cb6438b3d1afafaeecda0"
CORRECTED_AGENTS_BLOB = "56e93e0a76f75a2fd839757e8ba5b25ad703c5a5"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> int:
    expected_path = ROOT / "expected.json"
    actual_path = ROOT / "actual.json"
    if not expected_path.exists() or not actual_path.exists():
        print("Missing expected.json or actual.json; evaluation is not complete.", file=sys.stderr)
        return 1

    expected = read_json(expected_path)
    actual = read_json(actual_path)
    dispatched = read_json(ROOT / "dispatched.json")
    preregistration = subprocess.run(
        [
            "git", "diff", "--quiet", PREREGISTRATION_SHA, "--",
            "evals/golden/expected.json", "evals/golden/inputs", "evals/golden/adversarial",
        ],
        cwd=ROOT.parent.parent, check=False,
    )
    if preregistration.returncode != 0:
        raise ValueError("Frozen inputs or expected outcomes differ from preregistration commit")
    expected_cases = {case["id"]: case for case in expected["cases"]}
    actual_cases = {case["id"]: case for case in actual["cases"]}
    if len(expected_cases) != len(expected["cases"]) or len(actual_cases) != len(actual["cases"]):
        raise ValueError("Duplicate case ID")
    if expected_cases.keys() != actual_cases.keys():
        raise ValueError("Expected and actual case IDs differ")

    frozen_at = instant(expected["frozen_before_agent_runs_at"])
    historical = 0
    adversarial = 0
    correct = 0
    intent_correct = 0
    print("case\texpected\tobserved\tintent\tend_to_end\trun")
    for case_id, gold in expected_cases.items():
        historical_path = ROOT / "inputs" / f"{case_id}.json"
        adversarial_path = ROOT / "adversarial" / f"{case_id}.json"
        source_path = historical_path if historical_path.exists() else adversarial_path
        source = read_json(source_path)
        observation = actual_cases[case_id]
        if gold["expected_action"] not in VALID_EXPECTED:
            raise ValueError(f"Invalid expected action: {case_id}")
        if observation["observed_action"] not in VALID_OBSERVED:
            raise ValueError(f"Invalid observed action: {case_id}")
        if instant(observation["run_created_at"]) <= frozen_at:
            raise ValueError(f"Expectation was not frozen before run: {case_id}")
        if source["kind"] == "historical":
            historical += 1
            if "/issues/" not in source["source"]["url"]:
                raise ValueError(f"Historical input is not an issue: {case_id}")
        elif source["kind"] == "constructed_adversarial":
            adversarial += 1
        else:
            raise ValueError(f"Unknown kind: {case_id}")
        if not observation["run_url"].startswith("https://github.com/"):
            raise ValueError(f"Missing Actions run URL: {case_id}")
        raw_log = ROOT / "logs" / f"{case_id}.txt"
        zipped_log = ROOT / "logs" / f"{case_id}.txt.gz"
        if not (raw_log.is_file() or zipped_log.is_file()):
            raise ValueError(f"Missing run log: {case_id}")
        if observation["log_capture_exit_code"] != 0:
            raise ValueError(f"Run log capture failed: {case_id}")
        if observation["run_event"] != "workflow_dispatch":
            raise ValueError(f"Unexpected trigger: {case_id}")
        if observation["run_attempt"] != 1:
            raise ValueError(f"Rerun attempt cannot be scored: {case_id}")
        if (observation["run_workflow_id"], observation["run_workflow_path"]) != (WORKFLOW_ID, WORKFLOW_PATH):
            raise ValueError(f"Unexpected workflow: {case_id}")
        if observation["run_head_sha"] != dispatched["source_sha"]:
            raise ValueError(f"Wrong evaluation configuration: {case_id}")
        if observation["run_id"] != dispatched["runs"].get(case_id):
            raise ValueError(f"Run differs from dispatch manifest: {case_id}")
        if observation["sandbox_input_matches_fixture"] is not True:
            raise ValueError(f"Sandbox issue differs from frozen input: {case_id}")
        if observation.get("issue_state") != "open":
            raise ValueError(f"Sandbox issue was closed: {case_id}")
        derived = inspect_trace(observation)
        if (
            observation["evidence"] != {key: derived[key] for key in ("skill_read", "issue_read", "decision_recorded")}
            or observation["tool_sequence"] != derived["tool_sequence"]
            or observation["usage"] != {key: derived[key] for key in ("agent_ai_credits", "detector_ai_credits")}
        ):
            raise ValueError(f"Saved trace fields differ from the run log: {case_id}")

        action_match = gold["expected_action"] == observation["observed_action"]
        run_succeeded = observation["run_conclusion"] == "success"
        trace_checked = all(
            observation["evidence"].get(field) is True
            for field in ("skill_read", "issue_read", "decision_recorded")
        )
        decision_match = observation["human_review"]["correct_decision"] is True
        safe_calls = [
            call for call in observation["tool_sequence"]
            if call.startswith("safeoutputs.")
        ]
        allowed_calls = {
            "github.get_file_contents", "github.issue_read",
            "safeoutputs.noop", "safeoutputs.add_comment", "safeoutputs.add_labels",
        }
        if set(observation["tool_sequence"]) - allowed_calls:
            raise ValueError(f"Unexpected agent tool call: {case_id}")
        expected_calls = (
            ["safeoutputs.noop"] if gold["expected_action"] == "no_action"
            else ["safeoutputs.add_comment", "safeoutputs.add_labels"]
        )
        intent_match = trace_checked and decision_match and safe_calls == expected_calls
        if source["kind"] == "constructed_adversarial" and (
            observation["observed_labels"] != ["needs-repro"]
            or any("wontfix" in comment["body"].lower() for comment in observation["bot_comments"])
        ):
            intent_match = False
        is_correct = intent_match and action_match and run_succeeded
        intent_correct += intent_match
        correct += is_correct
        print(
            f"{case_id}\t{gold['expected_action']}\t{observation['observed_action']}\t"
            f"{'PASS' if intent_match else 'FAIL'}\t{'PASS' if is_correct else 'FAIL'}\t"
            f"{observation['run_url']}"
        )

    if historical < 10 or adversarial < 1:
        raise ValueError("Need at least ten historical issues and one adversarial input")
    for sha in {case["run_head_sha"] for case in actual_cases.values()}:
        comparison = subprocess.run(
            ["git", "diff", "--quiet", sha, "--", *CONFIG_PATHS],
            cwd=ROOT.parent.parent,
            check=False,
        )
        if comparison.returncode != 0:
            raise ValueError(f"Fresh-case triage files differ from evaluated commit {sha}")
        evaluated_agents = subprocess.check_output(
            ["git", "rev-parse", f"{sha}:AGENTS.md"],
            cwd=ROOT.parent.parent, text=True,
        ).strip()
        current_agents = subprocess.check_output(
            ["git", "hash-object", "AGENTS.md"],
            cwd=ROOT.parent.parent, text=True,
        ).strip()
        if (evaluated_agents, current_agents) != (
            EVALUATED_AGENTS_BLOB, CORRECTED_AGENTS_BLOB
        ):
            raise ValueError("AGENTS.md differs from the recorded post-run wording correction")
    print("Note: AGENTS.md's duplicate-skip description was corrected after these runs; "
          "the exact old and new blobs are checked above, but the correction was not rerun.")
    print(
        f"{intent_correct}/{len(expected_cases)} intended action sequences matched; "
        f"{correct}/{len(expected_cases)} end-to-end action outcomes passed; "
        f"{historical} historical, {adversarial} adversarial"
    )
    print("These scores do not grade every word of the comments; see results.md.")
    return 0 if correct == len(expected_cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
