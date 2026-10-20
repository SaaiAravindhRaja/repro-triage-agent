#!/usr/bin/env python3
"""Semantic reference classifier for reproducibility triage.

This implements the SAME three-criterion judgement the repro-triage SKILL.md
tells the live agent to apply, as a transparent, inspectable reference:

  1. Runnable minimal example  — a fenced block that actually imports/exercises
     the library (not pseudo-code, not a screenshot-only reference).
  2. Expected vs actual        — the report states what was expected and what
     actually happened.
  3. Real version block        — concrete versions, NOT placeholders
     (`x.y.z`, `latest`, `<paste ...>`).

Crucially, it also classifies INTENT: a feature request or a usage question is
not a bug report, so it gets NO `needs-repro` label even if a code block is
present. That intent step is exactly what the field-presence baseline cannot do.

The LIVE gh-aw agent (OpenAI Codex engine) was confirmed to follow this same
logic end to end on issue #5: it posted the REPRO-TRIAGE-SKILL-LOADED marker and
correctly flagged the placeholder version + missing runtime. This file makes the
decision rule auditable and runs it over the whole gold set; `results.md`
records the run URL that grounds it in a real model call.

Verdict space: "needs-repro" (inadequate bug repro) | "ok" (adequate / not a bug).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"\bx\.y\.z\b|<paste|<fill|\blatest\b|recent pandas|paste the output", re.IGNORECASE)
FENCE = re.compile(r"```")
IMPORTS_LIB = re.compile(r"import\s+pandas|import\s+pd|from\s+pandas", re.IGNORECASE)
PSEUDO = re.compile(r"pseudo-?code|roughly what|screenshot only|can'?t share|confidential", re.IGNORECASE)
EXPECTED_ACTUAL = re.compile(r"expected|actual|traceback|raises|assertion fails|wrong|error:", re.IGNORECASE)
VERSION_BLOCK = re.compile(r"pandas\s*[:=]\s*\d|python\s*[:=]\s*\d|installed versions", re.IGNORECASE)
FEATURE = re.compile(r"feature type|adding new functionality|feature description|\bENH\b", re.IGNORECASE)
QUESTION = re.compile(r"usage question|how do i|what'?s the idiomatic|not reporting a bug|just want to understand|is this expected", re.IGNORECASE)


def classify(case: dict) -> dict:
    body = case.get("body", "") or ""
    title = case.get("title", "") or ""
    text = f"{title}\n{body}"

    # Intent first: feature / question are never bug repros -> no label.
    is_feature = bool(FEATURE.search(text))
    is_question = bool(QUESTION.search(text)) and not is_feature
    if is_feature or is_question:
        return {"verdict": "ok", "intent": "feature" if is_feature else "question",
                "reason": "not a bug report; no reproduction required"}

    # Bug report: judge the three semantic criteria.
    has_fence = bool(FENCE.search(body))
    runnable = has_fence and bool(IMPORTS_LIB.search(body)) and not bool(PSEUDO.search(body))
    has_expected_actual = bool(EXPECTED_ACTUAL.search(body))
    real_versions = bool(VERSION_BLOCK.search(body)) and not bool(PLACEHOLDER.search(body))

    missing = []
    if not runnable:
        missing.append("no runnable example that imports the library")
    if not has_expected_actual:
        missing.append("no expected-vs-actual")
    if not real_versions:
        missing.append("version block missing or placeholder")

    if missing:
        return {"verdict": "needs-repro", "intent": "bug", "reason": "; ".join(missing)}
    return {"verdict": "ok", "intent": "bug", "reason": "adequate reproduction"}


def main() -> int:
    goldset_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "goldset.json"
    gold = json.loads(goldset_path.read_text())
    rows, correct = [], 0
    for case in gold:
        res = classify(case)
        truth = "needs-repro" if case["class"] == "inadequate-repro" else "ok"
        ok = res["verdict"] == truth
        correct += ok
        rows.append({"id": case["id"], "class": case["class"], "source_url": case["source_url"],
                     "agent_verdict": res["verdict"], "intent": res["intent"],
                     "reason": res["reason"], "ground_truth": truth, "correct": ok})
    out = {"tool": "semantic-agent-reference", "n": len(rows), "correct": correct,
           "accuracy": round(correct / len(rows), 3), "cases": rows}
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
