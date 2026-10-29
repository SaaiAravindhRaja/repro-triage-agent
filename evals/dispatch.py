#!/usr/bin/env python3
"""Dispatch missing golden cases, recording each run before starting the next."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "golden"
MANIFEST = ROOT / "dispatched.json"
BRANCH = "assignment3-submission"
REPO = "SaaiAravindhRaja/repro-triage-agent"


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def wait_for_completion(run_id: int) -> None:
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        response = command("gh", "api", f"repos/{REPO}/actions/runs/{run_id}")
        run = json.loads(response)
        if run["status"] == "completed":
            print(f"Run {run_id} finished: {run['conclusion']}", flush=True)
            return
        time.sleep(15)
    raise TimeoutError(f"Run {run_id} did not finish within 15 minutes")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--serial",
        action="store_true",
        help="wait for each run before starting the next",
    )
    parser.add_argument("--case", help="dispatch or preview one case ID")
    args = parser.parse_args()

    source_sha = command("git", "rev-parse", "HEAD").strip()
    expected = json.loads((ROOT / "expected.json").read_text(encoding="utf-8"))
    known_ids = {case["id"] for case in expected["cases"]}
    if args.case and args.case not in known_ids:
        parser.error(f"unknown case ID: {args.case}")
    issues = json.loads((ROOT / "sandbox_issues.json").read_text(encoding="utf-8"))
    manifest = (
        json.loads(MANIFEST.read_text(encoding="utf-8"))
        if MANIFEST.exists()
        else {"source_sha": source_sha, "runs": {}}
    )
    if manifest["source_sha"] != source_sha:
        raise RuntimeError("Dispatch manifest belongs to another configuration commit")
    for case in expected["cases"]:
        case_id = case["id"]
        if args.case and case_id != args.case:
            continue
        if case_id in manifest["runs"]:
            if args.serial and args.execute:
                wait_for_completion(manifest["runs"][case_id])
            continue
        number = issues[case_id]["number"]
        if not args.execute:
            print(f"Would dispatch {case_id} on issue #{number}")
            continue
        result = subprocess.run(
            [
                "gh",
                "aw",
                "run",
                "smoke-triage",
                "--ref",
                BRANCH,
                "--raw-field",
                f"issue_number={number}",
                "--raw-field",
                f"source_sha={source_sha}",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        run_ids = set(re.findall(r"/actions/runs/(\d+)", output))
        if len(run_ids) != 1:
            raise RuntimeError(
                f"Could not uniquely identify run for {case_id}: {output}"
            )
        run_id = int(run_ids.pop())
        manifest["runs"][case_id] = run_id
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"{case_id}: https://github.com/{REPO}/actions/runs/{run_id}", flush=True)
        if args.serial:
            wait_for_completion(run_id)


if __name__ == "__main__":
    main()
