# Reproducibility triage, in a sandbox

This is a complete Assignment 3 implementation of safe, first-pass
reproducibility triage for pandas-style bug reports. The
[sandbox repository](https://github.com/SaaiAravindhRaja/repro-triage-agent)
contains 55 issues, a frozen 12-case evaluation, and live post-hardening
control checks. The workflow reads this sandbox only, requests missing details
with one comment, and applies the existing `needs-repro` label. It cannot close
issues or act on the upstream tracker.

The twelve scored runs used [bdb0a6e](https://github.com/SaaiAravindhRaja/repro-triage-agent/commit/bdb0a6e4e0edc319e3596f4f7cc5652199e64e11)
on `assignment3-submission`. The complete submission is on `main`, where the
current workflow is enabled for repository-admin issue opens. The scored runs
isolate the agent decision; later [post-hardening control checks](evals/posthardening/)
exercise the owner path, Environment approval and rejection, queued-run
cancellation, rerun blocking, and a manual no-op. This stays a sandbox rather
than an unapproved pandas deployment.

Start with [DESIGN.md](DESIGN.md), then inspect the [workflow source](.github/workflows/smoke-triage.md),
[compiled workflow](.github/workflows/smoke-triage.lock.yml),
[repository instructions](AGENTS.md), [triage skill](.claude/skills/repro-triage/SKILL.md),
and [historical evaluation](evals/golden/results.md). The evaluation keeps the
original inputs, preregistered expectations, observed outputs, run links and
reproduction commands together. `DESIGN.md` distinguishes live evidence,
configuration evidence, and proposed follow-up rather than blurring them.

The current workflow adds a post-agent approval job before safe outputs, and
the compiled output and conclusion jobs explicitly require approval success. Its
`triage-output-approval` GitHub Environment has a required reviewer, no admin
bypass, and a `main`-only branch policy. The
post-hardening checks exercised both approval and rejection; the historical
twelve runs predate the gate. Admin-triggered runs can still consume model
credits before approval. See the [deployment record](docs/production-readiness.md).

Why use an agent? A read-only [snapshot](evidence/pandas-bug-intake.json)
found 111 pandas issues opened from 22 July to 20 October 2026 with a `Bug`
label. A rule can check template fields, but it cannot reliably decide whether
code is self-contained, version details are real, or a report is actually a
bug. The agent makes that semantic first-pass judgement, while
[preflight](scripts/preflight.py) handles deterministic target and duplicate
checks. Its output is deliberately modest: one specific request for missing
information, not a decision about whether the bug is real.

The preflight skips inference by writing gh-aw's supported `noop` record for a
closed or previously triaged issue. Unit tests check the record; a later
manual check confirmed the runner skips inference. The historical twelve did not exercise it.

The [30-issue consecutive slice](evidence/pandas-consecutive-30.json) supports
that narrow design: two reports were clear candidates for a request, 21 needed
no action, and seven were uncertain. The workflow therefore demonstrates a
selective first pass rather than claiming broad deployment or unmeasured time
savings.

In the [final comparison](evals/golden/results.md), all twelve first-attempt
runs matched their frozen action. The [manual quality audit](evals/golden/comment-quality-review.md)
also checks the actual comments: all were courteous and 40--87 words; two
requests were redundant, one mildly and one materially. The runs consumed
74.85 AI credits. Iteration after the scored run added approval, rate limiting
that includes admins, a two-read repository-file budget, and rerun blocking.
The run evidence remains pinned to its original commit; the replay script checks
the evaluated files at that SHA instead of silently treating later hardening as
part of the score.

The older `eval/` directory is retained as a prototype. Its `agent_eval.py`
is a regex classifier, not an LLM run; its 12/12 result is **not** agent
accuracy. [Development notes](docs/report.md) record the early live runs and
their failures so that they are not mistaken for the submitted evaluation.
