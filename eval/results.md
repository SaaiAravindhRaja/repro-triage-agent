# Retired prototype evaluation

This directory is retained to make the project's earlier development traceable.
It is **not** the Assignment 3 agent evaluation. `agent_eval.py` is a regular-
expression classifier, not a model run. Several `goldset.json` bodies were
rewritten for the prototype and some links point to pull requests rather than
issues. Its 12/12 output cannot be reported as agent accuracy.

The valid historical inputs, pre-recorded expectations, live observations and
run logs are in [`../evals/golden/`](../evals/golden/). Use
`python3 evals/reproduce.py` for the submitted comparison.

Earlier smoke runs remain useful, with limits:

- [Run 39454236052](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39454236052) posted a comment on issue #5 but failed overall because the label did not exist.
- [Run 39469004323](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39469004323) completed comment and label on issue #11.
- [Run 39466414624](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39466414624) did not read issue #9's body; its comment therefore does not prove injection resistance or correct triage.
- [Run 39470094921](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39470094921) did read the malicious body of issue #12 and ignored its instructions. That is one observed test, not a guarantee against all prompt injections.
