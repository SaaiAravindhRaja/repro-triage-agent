#!/usr/bin/env bash
# Cold reproduction for a grader: no prior state, no secrets, no network calls.
# Runs the deterministic baseline-vs-agent evaluation and asserts the headline
# result (baseline 5/12, agent 12/12). Exits non-zero if either regresses.
set -euo pipefail

cd "$(dirname "$0")/.."   # repo root

echo "== reproducibility-triage evaluation =="
echo "-- baseline (field-presence, no LLM) --"
python3 eval/baseline.py eval/goldset.json > /tmp/base.json
python3 eval/agent_eval.py eval/goldset.json > /tmp/agent.json

python3 - <<'PY'
import json
b = json.load(open("/tmp/base.json"))
a = json.load(open("/tmp/agent.json"))
print(f"baseline: {b['correct']}/{b['n']}  ({b['accuracy']:.1%})")
print(f"agent   : {a['correct']}/{a['n']}  ({a['accuracy']:.1%})")
assert b["n"] == a["n"] == 12, "gold set must hold 12 cases"
assert b["correct"] == 5,  f"baseline regressed: {b['correct']}/12 (expected 5)"
assert a["correct"] == 12, f"agent regressed: {a['correct']}/12 (expected 12)"
assert a["correct"] > b["correct"], "agent must beat baseline"
print("OK: agent beats the field-presence baseline on semantic repro-adequacy")
PY

echo "-- done --"
