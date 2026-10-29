# Reproducibility triage, in a sandbox

This is an Assignment 3 experiment, not a bot deployed to pandas. It tests
whether a GitHub Agentic Workflow can identify new pandas-style bug reports
that lack enough information to reproduce them. The workflow reads issues in
[this sandbox repository](https://github.com/SaaiAravindhRaja/repro-triage-agent)
only. It can request missing details with one comment and apply the existing
`needs-repro` label. It cannot close issues or act on the upstream tracker.
The twelve runs used [bdb0a6e](https://github.com/SaaiAravindhRaja/repro-triage-agent/commit/bdb0a6e4e0edc319e3596f4f7cc5652199e64e11)
on `assignment3-submission`, which was not the default branch at the time.
The complete submission is on `main`. The current workflow is enabled there,
but its issue trigger admits repository admins only. The issue-open event and
role rejection were not exercised in the scored evaluation, which used manual
dispatch. This remains a sandbox, not a deployment to pandas.

The submission is [DESIGN.md](DESIGN.md), the [workflow source](.github/workflows/smoke-triage.md)
and [compiled workflow](.github/workflows/smoke-triage.lock.yml), the
[repository instructions](AGENTS.md), the [triage skill](.claude/skills/repro-triage/SKILL.md),
and the [historical evaluation](evals/golden/results.md). The latter contains the original
inputs, expectations fixed before any run on this frozen set, observed outputs,
run links and reproduction instructions. `DESIGN.md` separates controls seen in
a live run from controls checked only in configuration and proposed follow-up.

The current workflow adds a post-agent approval job before safe outputs, and
the compiled output and conclusion jobs explicitly require approval success. Its
`triage-output-approval` GitHub Environment has a required reviewer, no admin
bypass, and a `main`-only branch policy. The setting is configured, but the
gate has not been exercised by a post-activation run. The historical twelve
runs predate it. Admin-triggered runs can still consume model credits before
approval. See the [deployment record](docs/production-readiness.md).

Why try this? A read-only [search snapshot](evidence/pandas-bug-intake.json)
found 111 pandas issues opened from 22 July to 20 October 2026 that carried a
`Bug` label when collected on 22 October. That is incoming volume, **not** a
measure of missing reproductions or time saved. The model's narrow task is to
read a report's code, expected and observed behavior, and environment details;
a [preflight script](scripts/preflight.py) handles mechanical checks. A useful
result is a specific request for missing information, not a decision about
whether the bug is real.

The preflight skips inference by writing gh-aw's supported `noop` record for a
closed or previously triaged issue. Unit tests check the output record; the
historical twelve cases did not exercise this path.

In a fixed [30-issue consecutive slice](evidence/pandas-consecutive-30.json),
only two were clear candidates for that request, 21 needed no action and seven
could not be judged confidently. This short retrospective sample does not
justify broad deployment or show maintainer time saved; it is a reason to keep
the experiment narrow.

In the [final comparison](evals/golden/results.md), all twelve first-attempt
runs matched the frozen action. A [manual quality audit](evals/golden/comment-quality-review.md)
found courteous comments ranging from 40--87 words, but two redundant requests:
one mild and one material. The runs used 74.85 AI credits, but did not show
maintainer-time savings. The evaluated `AGENTS.md` incorrectly said that the
preflight no-op did not skip inference; I corrected it after those runs. I also
added output approval, rate limiting that includes admins, a two-read repository-file
budget, and a rerun check after the evaluation. The run evidence remains pinned
to its original commit; the replay script checks the evaluated files at that
SHA instead of requiring the current working tree to stay frozen.

The older `eval/` directory is retained as a prototype. Its `agent_eval.py`
is a regex classifier, not an LLM run; its 12/12 result is **not** agent
accuracy. [Development notes](docs/report.md) record the early live runs and
their failures so that they are not mistaken for the submitted evaluation.
