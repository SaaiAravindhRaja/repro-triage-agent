#!/usr/bin/env python3
"""Deterministic field-presence baseline for reproducibility triage.

This was the NON-LLM baseline in the retired prototype. It does exactly what
a naive template linter does: it checks whether the issue body contains the
expected template sections and whether they are non-empty. It does NOT reason
about whether the content is semantically an adequate reproduction. The saved
prototype score is not a comparison against live agent runs.

Verdict: "needs-repro" if any required field looks empty/missing, else "ok".
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Template fields a pandas-style bug report is expected to carry.
REQUIRED_SECTIONS = {
    "code": re.compile(r"```", re.IGNORECASE),  # a fenced block exists
    "versions": re.compile(
        r"version|pd\.__version__|INSTALLED VERSIONS", re.IGNORECASE
    ),
    "problem": re.compile(r"expected|actual|error|traceback|result", re.IGNORECASE),
}


def lint(body: str) -> dict:
    """Field-presence only. True = section appears non-empty."""
    body = body or ""
    present = {}
    for name, pat in REQUIRED_SECTIONS.items():
        present[name] = bool(pat.search(body))
    # Naive rule: all three template markers present -> considered fine.
    verdict = "ok" if all(present.values()) else "needs-repro"
    return {"verdict": verdict, "fields_present": present}


def main() -> int:
    goldset_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).parent / "goldset.json"
    )
    gold = json.loads(goldset_path.read_text())
    rows = []
    correct = 0
    for case in gold:
        res = lint(case["body"])
        # Ground truth: label is "needs-repro" only for the inadequate-repro class.
        truth = "needs-repro" if case["class"] == "inadequate-repro" else "ok"
        ok = res["verdict"] == truth
        correct += ok
        rows.append(
            {
                "id": case["id"],
                "class": case["class"],
                "source_url": case["source_url"],
                "baseline_verdict": res["verdict"],
                "ground_truth": truth,
                "correct": ok,
                "fields_present": res["fields_present"],
            }
        )
    out = {
        "tool": "baseline-field-presence",
        "n": len(rows),
        "correct": correct,
        "accuracy": round(correct / len(rows), 3),
        "cases": rows,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
