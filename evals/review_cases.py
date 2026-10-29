#!/usr/bin/env python3
"""Print event-time input and agent decisions for human case review."""

from __future__ import annotations

import argparse
import gzip
import json

from verify_trace import ROOT, agent_calls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id", nargs="?")
    args = parser.parse_args()
    actual = json.loads((ROOT / "actual.json").read_text(encoding="utf-8"))
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    gold = {case["id"]: case for case in expected["cases"]}
    for case in actual["cases"]:
        case_id = case["id"]
        if args.case_id and args.case_id != case_id:
            continue
        source = ROOT / "inputs" / f"{case_id}.json"
        if not source.exists():
            source = ROOT / "adversarial" / f"{case_id}.json"
        fixture = json.loads(source.read_text(encoding="utf-8"))
        log_path = ROOT / "logs" / f"{case_id}.txt"
        if log_path.exists():
            log = log_path.read_text(encoding="utf-8")
        else:
            with gzip.open(f"{log_path}.gz", "rt", encoding="utf-8") as stream:
                log = stream.read()
        decisions = [
            (item["tool"], item.get("arguments", {}))
            for item in agent_calls(log)
            if item.get("server") == "safeoutputs"
        ]
        print(
            f"\n=== {case_id} | {case['run_conclusion']} | {case['observed_action']} ==="
        )
        print(f"Title: {fixture['input']['title']}")
        print(f"Original body:\n{fixture['input']['body']}")
        print(
            f"Expected: {gold[case_id]['expected_action']} — {gold[case_id]['rationale']}"
        )
        for tool, arguments in decisions:
            print(f"Agent {tool}: {json.dumps(arguments, ensure_ascii=False)}")
        print(f"Run: {case['run_url']}")


if __name__ == "__main__":
    main()
