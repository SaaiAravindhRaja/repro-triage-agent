#!/usr/bin/env python3
"""Check saved agent tool calls against each frozen input and recorded action."""

from __future__ import annotations

import gzip
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "golden"
FIXTURES = Path(__file__).resolve().parent / "golden"
ACTUAL = ROOT / "actual.json"
SKILL = ".claude/skills/repro-triage/SKILL.md"
SKILL_DIRECTORY = ".claude/skills/repro-triage"
ALLOWED_FILE_READ_PATHS = {SKILL_DIRECTORY, SKILL}


def result_text(item: dict) -> str:
    return item["result"]["content"][0]["text"]


def agent_calls(log: str) -> list[dict]:
    calls = []
    for line in log.splitlines():
        if not line.startswith("agent\t"):
            continue
        payload = line.partition("Z ")[2]
        if not payload.startswith('{"type":"item.completed"'):
            continue
        event = json.loads(payload)
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "mcp_tool_call":
            calls.append(item)
    return calls


def credit(log: str, job: str) -> float | None:
    values = [
        float(match.group(1))
        for line in log.splitlines()
        if line.startswith(f"{job}\t")
        for match in [re.search(r"AI Credits: ([0-9]+(?:\.[0-9]+)?)", line)]
        if match
    ]
    return values[-1] if values else None


def validate_file_reads(calls: list[dict]) -> None:
    for item in calls:
        if item.get("server") != "github" or item.get("tool") != "get_file_contents":
            continue
        path = (item.get("arguments") or {}).get("path")
        if path not in ALLOWED_FILE_READ_PATHS:
            raise ValueError(f"Unexpected repository file read: {path!r}")


def inspect(case: dict) -> dict:
    case_id = case["id"]
    raw_path = ROOT / "logs" / f"{case_id}.txt"
    zipped_path = ROOT / "logs" / f"{case_id}.txt.gz"
    if raw_path.is_file():
        log = raw_path.read_text(encoding="utf-8")
    else:
        with gzip.open(zipped_path, "rt", encoding="utf-8") as stream:
            log = stream.read()
    fixture_path = FIXTURES / "inputs" / f"{case_id}.json"
    if not fixture_path.exists():
        fixture_path = FIXTURES / "adversarial" / f"{case_id}.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    expected_skill = subprocess.run(
        ["git", "show", f"{case['run_head_sha']}:{SKILL}"],
        check=True, capture_output=True, text=True,
    ).stdout
    calls = agent_calls(log)
    validate_file_reads(calls)
    skill_position = issue_position = None
    skill_read = issue_read = False
    safe_calls = []
    for position, item in enumerate(calls):
        args = item.get("arguments") or {}
        complete = item.get("status") == "completed" and item.get("error") is None
        if item.get("server") == "github" and item.get("tool") == "get_file_contents":
            if args.get("path") == SKILL and args.get("sha") == case["run_head_sha"] and complete:
                document = json.loads(result_text(item))[0]
                resources = [entry["resource"] for entry in document["content"] if entry.get("type") == "resource"]
                if not skill_read and any(resource.get("text") == expected_skill for resource in resources):
                    skill_read = True
                    skill_position = position
        if item.get("server") == "github" and item.get("tool") == "issue_read":
            if args.get("issue_number") == case["sandbox_issue_number"] and complete:
                response = json.loads(result_text(item))[0]["issue"]
                matches_fixture = (
                    response.get("number") == case["sandbox_issue_number"]
                    and response.get("title") == fixture["input"]["title"]
                    and response.get("body") == fixture["input"]["body"]
                )
                if not issue_read and matches_fixture:
                    issue_read = True
                    issue_position = position
        if item.get("server") == "safeoutputs":
            safe_calls.append((position, item))

    names = [item["tool"] for _, item in safe_calls]
    if names == ["noop"]:
        decision_recorded = True
    elif names == ["add_comment", "add_labels"]:
        decision_recorded = (
            safe_calls[1][1].get("arguments", {}).get("labels")
            == [{"name": "needs-repro", "suggest": False}]
        )
    else:
        decision_recorded = False
    decision_recorded = bool(
        decision_recorded
        and all(item.get("status") == "completed" and item.get("error") is None for _, item in safe_calls)
        and skill_position is not None
        and issue_position is not None
        and skill_position < issue_position
        and all(issue_position < position for position, _ in safe_calls)
    )
    return {
        "skill_read": skill_read,
        "issue_read": issue_read,
        "decision_recorded": decision_recorded,
        "tool_sequence": [f"{item['server']}.{item['tool']}" for item in calls],
        "agent_ai_credits": credit(log, "agent"),
        "detector_ai_credits": credit(log, "detection"),
    }


def main() -> None:
    data = json.loads(ACTUAL.read_text(encoding="utf-8"))
    for case in data["cases"]:
        details = inspect(case)
        case["evidence"] = {key: details[key] for key in ("skill_read", "issue_read", "decision_recorded")}
        case["tool_sequence"] = details["tool_sequence"]
        case["usage"] = {key: details[key] for key in ("agent_ai_credits", "detector_ai_credits")}
        print(case["id"], case["evidence"], case["usage"])
    ACTUAL.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
