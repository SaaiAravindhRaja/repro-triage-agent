#!/usr/bin/env python3
"""Copy frozen issue inputs into this project's sandbox for live evaluation.

The script refuses to create issues while the default-branch issue workflow is
active, avoiding accidental runs of an older configuration. Re-running skips
cases already recorded in the mapping file.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


REPO = "SaaiAravindhRaja/repro-triage-agent"
WORKFLOW_ID = 390537521
ROOT = Path(__file__).resolve().parent / "golden"
MAP = ROOT / "sandbox_issues.json"


def gh_api(endpoint: str, *args: str) -> dict:
    result = subprocess.run(
        ["gh", "api", endpoint, *args], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute", action="store_true", help="create missing sandbox issues"
    )
    parser.add_argument("--case", help="create or preview one case ID")
    args = parser.parse_args()

    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    mapping = json.loads(MAP.read_text(encoding="utf-8")) if MAP.exists() else {}
    known_ids = {case["id"] for case in expected["cases"]}
    if args.case and args.case not in known_ids:
        parser.error(f"unknown case ID: {args.case}")
    pending = [
        case["id"]
        for case in expected["cases"]
        if case["id"] not in mapping and (not args.case or case["id"] == args.case)
    ]
    print(f"{len(pending)} cases need sandbox issues: {', '.join(pending)}")
    if not args.execute or not pending:
        return

    workflow = gh_api(f"repos/{REPO}/actions/workflows/{WORKFLOW_ID}")
    if workflow["state"] != "disabled_manually":
        raise RuntimeError(
            f"Default-branch workflow is {workflow['state']}; disable it before creating cases"
        )
    for case_id in pending:
        historical_path = ROOT / "inputs" / f"{case_id}.json"
        adversarial_path = ROOT / "adversarial" / f"{case_id}.json"
        source_path = historical_path if historical_path.exists() else adversarial_path
        source = json.loads(source_path.read_text(encoding="utf-8"))
        issue = gh_api(
            f"repos/{REPO}/issues",
            "--method",
            "POST",
            "-f",
            f"title={source['input']['title']}",
            "-f",
            f"body={source['input']['body']}",
        )
        mapping[case_id] = {"number": issue["number"], "url": issue["html_url"]}
        MAP.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        print(f"{case_id}: {issue['html_url']}")


if __name__ == "__main__":
    main()
