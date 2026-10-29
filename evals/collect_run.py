#!/usr/bin/env python3
"""Save one Actions result and its public sandbox issue for manual adjudication.

This command only reads GitHub. It never dispatches a workflow or changes an
issue. The recorded action is mechanical; comment quality and skill use must
still be checked against the saved log by a reviewer.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO = "SaaiAravindhRaja/repro-triage-agent"
WORKFLOW_ID = 390537521
WORKFLOW_PATH = ".github/workflows/smoke-triage.lock.yml"
ROOT = Path(__file__).resolve().parent / "golden"
ACTUAL = ROOT / "actual.json"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True)


def api(endpoint: str) -> dict | list:
    return json.loads(run("gh", "api", f"repos/{REPO}/{endpoint}").stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    parser.add_argument("run_id", type=int)
    args = parser.parse_args()

    mapping = json.loads((ROOT / "sandbox_issues.json").read_text(encoding="utf-8"))
    if args.case_id not in mapping:
        parser.error(f"case has no sandbox issue: {args.case_id}")
    dispatched = json.loads((ROOT / "dispatched.json").read_text(encoding="utf-8"))
    if dispatched["runs"].get(args.case_id) != args.run_id:
        raise RuntimeError(
            f"Run {args.run_id} is not the recorded dispatch for {args.case_id}"
        )
    source_path = ROOT / "inputs" / f"{args.case_id}.json"
    if not source_path.exists():
        source_path = ROOT / "adversarial" / f"{args.case_id}.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))

    issue_number = mapping[args.case_id]["number"]
    issue = api(f"issues/{issue_number}")
    if (
        issue["title"] != source["input"]["title"]
        or issue["body"] != source["input"]["body"]
    ):
        raise RuntimeError(f"Sandbox issue #{issue_number} differs from frozen input")
    comments = api(f"issues/{issue_number}/comments?per_page=100")
    if len(comments) == 100:
        raise RuntimeError("Too many comments to collect in one page")
    timeline = api(f"issues/{issue_number}/timeline?per_page=100")
    if len(timeline) == 100:
        raise RuntimeError("Too many timeline events to attribute the label")

    result = api(f"actions/runs/{args.run_id}")
    if result["status"] != "completed":
        raise RuntimeError(f"Run {args.run_id} is still {result['status']}")
    if result["run_attempt"] != 1:
        raise RuntimeError("Rerun attempts cannot be scored as fresh issue evaluations")
    if result["workflow_id"] != WORKFLOW_ID or result["path"] != WORKFLOW_PATH:
        raise RuntimeError(f"Run {args.run_id} is not the expected workflow")
    if result["head_sha"] != dispatched["source_sha"]:
        raise RuntimeError(f"Run {args.run_id} did not use the recorded source commit")
    started = datetime.fromisoformat(result["created_at"].replace("Z", "+00:00"))
    finished = datetime.fromisoformat(result["updated_at"].replace("Z", "+00:00"))
    log = run(
        "gh", "run", "view", str(args.run_id), "--repo", REPO, "--log", check=False
    )
    if (
        log.returncode == 0
        and f"Triage only issue #{issue_number} in" not in log.stdout
    ):
        raise RuntimeError(
            f"Run {args.run_id} does not target sandbox issue #{issue_number}"
        )
    log_path = ROOT / "logs" / f"{args.case_id}.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(log.stdout + log.stderr, encoding="utf-8")

    all_bot_comments = [
        {
            "url": item["html_url"],
            "body": item["body"],
            "created_at": item["created_at"],
        }
        for item in comments
        if item["user"]["login"] == "github-actions[bot]"
    ]
    bot_comments = []
    for item in all_bot_comments:
        posted = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        match = re.search(r"<!-- gh-aw-execution: (.*?) -->", item["body"])
        if not (started <= posted <= finished and match):
            raise RuntimeError(
                "Bot comment is outside this run or lacks execution metadata"
            )
        execution = json.loads(match.group(1))
        if (
            execution.get("repository") != REPO
            or execution.get("run_id") != str(args.run_id)
            or execution.get("run_attempt") != "1"
        ):
            raise RuntimeError("Bot comment is from another workflow execution")
        bot_comments.append(item)
    labels = [item["name"] for item in issue["labels"]]
    label_events = [
        {"created_at": item["created_at"], "actor": item["actor"]["login"]}
        for item in timeline
        if item.get("event") == "labeled"
        and (item.get("label") or {}).get("name") == "needs-repro"
        and (item.get("actor") or {}).get("login") == "github-actions[bot]"
        and started
        <= datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        <= finished
    ]
    has_label = bool(label_events)
    if len(bot_comments) == 0:
        action = "label_only" if has_label else "no_action"
    elif len(bot_comments) == 1:
        action = "comment_and_label" if has_label else "comment_only"
    else:
        action = "multiple_comments"

    data = (
        json.loads(ACTUAL.read_text(encoding="utf-8"))
        if ACTUAL.exists()
        else {"schema_version": 1, "cases": []}
    )
    old = next((case for case in data["cases"] if case["id"] == args.case_id), None)
    if (
        old
        and old["run_id"] != args.run_id
        and old["sandbox_issue_number"] == issue_number
    ):
        raise RuntimeError(
            "A second run on the same issue cannot be scored independently"
        )
    same_run = old is not None and old["run_id"] == args.run_id
    same_output = (
        same_run
        and old["observed_action"] == action
        and old["bot_comments"] == bot_comments
        and old["label_events_during_run"] == label_events
    )
    row = {
        "id": args.case_id,
        "sandbox_issue_number": issue_number,
        "sandbox_issue_url": issue["html_url"],
        "sandbox_input_matches_fixture": True,
        "run_id": args.run_id,
        "run_url": result["html_url"],
        "run_created_at": result["created_at"],
        "run_updated_at": result["updated_at"],
        "run_attempt": result["run_attempt"],
        "run_workflow_id": result["workflow_id"],
        "run_workflow_path": result["path"],
        "run_head_sha": result["head_sha"],
        "run_event": result["event"],
        "run_branch": result["head_branch"],
        "run_conclusion": result["conclusion"],
        "observed_action": action,
        "issue_state": issue["state"],
        "observed_labels": labels,
        "label_events_during_run": label_events,
        "bot_comments": bot_comments,
        "log_capture_exit_code": log.returncode,
        "evidence": old["evidence"]
        if same_run
        else {
            "skill_read": None,
            "issue_read": None,
            "decision_recorded": None,
        },
        "tool_sequence": old.get("tool_sequence") if same_run else None,
        "usage": old.get("usage") if same_run else None,
        "human_review": old["human_review"]
        if same_output
        else {
            "correct_decision": None,
            "notes": "Pending transcript and comment review",
        },
    }
    data["cases"] = [case for case in data["cases"] if case["id"] != args.case_id] + [
        row
    ]
    data["collected_at"] = datetime.now(timezone.utc).isoformat()
    ACTUAL.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"{args.case_id}: {action}, {result['conclusion']}, {result['html_url']}")


if __name__ == "__main__":
    main()
