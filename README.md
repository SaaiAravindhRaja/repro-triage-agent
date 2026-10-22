# Reproducibility triage, in a sandbox

This is an Assignment 3 experiment, not a bot deployed to pandas. It tests
whether a GitHub Agentic Workflow can identify new pandas-style bug reports
that lack enough information to reproduce them. The workflow reads issues in
[this sandbox repository](https://github.com/SaaiAravindhRaja/repro-triage-agent)
only. It can request missing details with one comment and apply the existing
`needs-repro` label. It cannot close issues or act on the upstream tracker.
The tested revision is on `assignment3-submission`, not the default branch;
its issue-open trigger is configured but not deployed. Evaluation uses manual
dispatch at a recorded commit SHA.
The workflow was disabled after evaluation to prevent the older default-branch
configuration from starting new paid runs.

The submission is [DESIGN.md](DESIGN.md), the [workflow source](.github/workflows/smoke-triage.md)
and [compiled workflow](.github/workflows/smoke-triage.lock.yml), the
[repository instructions](AGENTS.md), the [triage skill](.claude/skills/repro-triage/SKILL.md),
and the [historical evaluation](evals/golden/results.md). The latter contains the original
inputs, expectations fixed before any run on this frozen set, observed outputs,
run links and reproduction instructions. `DESIGN.md` separates controls seen in
a live run from controls checked only in configuration and proposed follow-up.

Why try this? A read-only [search snapshot](evidence/pandas-bug-intake.json)
found 111 pandas issues opened from 22 July to 20 October 2026 that carried a
`Bug` label when collected on 22 October. That is incoming volume, **not** a
measure of missing reproductions or time saved. The model's narrow task is to
read a report's code, expected and observed behavior, and environment details;
a [preflight script](scripts/preflight.py) handles mechanical checks. A useful
result is a specific request for missing information, not a decision about
whether the bug is real.

In a fixed [30-issue consecutive slice](evidence/pandas-consecutive-30.json),
only two were clear candidates for that request, 21 needed no action and seven
could not be judged confidently. This short retrospective sample does not
justify broad deployment or show maintainer time saved; it is a reason to keep
the experiment narrow.

In the [final comparison](evals/golden/results.md), all twelve first-attempt
runs matched the frozen action. One comment clearly re-asked supplied details
and another did so mildly. The runs used 74.85 AI credits, but did not show
maintainer-time savings. A false duplicate-skip description in `AGENTS.md`
was corrected after these runs; the evaluated source workflow, compiled lock,
skill and preflight script are unchanged.

The older `eval/` directory is retained as a prototype. Its `agent_eval.py`
is a regex classifier, not an LLM run; its 12/12 result is **not** agent
accuracy. [Development notes](docs/report.md) record the early live runs and
their failures so that they are not mistaken for the submitted evaluation.
