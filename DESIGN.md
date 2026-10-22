# Design: a narrow first pass on bug reports

This tests reports from [pandas](https://github.com/pandas-dev/pandas) in my
sandbox, not in pandas itself.

## Why this task

My [read-only snapshot](evidence/pandas-bug-intake.json) found 111 pandas
issues opened 22 July–20 October 2026 with `Bug` on 22 October; 12 also had
`Needs Triage`. In the [30 newest](evidence/pandas-consecutive-30.json), two
clearly needed details under my rule, 21 did not, and seven were uncertain.
The labels are retrospective. Both clear ask cases
([#71158](https://github.com/pandas-dev/pandas/issues/71158) and
[#70991](https://github.com/pandas-dev/pandas/issues/70991)) later progressed
without those details. I have not shown that asking saves maintainer time.

[Pandas's bug template](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/.github/ISSUE_TEMPLATE/bug_report.yaml)
asks for a copy-pastable example, expected behavior and `pd.show_versions()`.
I rejected a headings-only linter: it cannot judge if code is self-contained,
a version is real, or the issue is a feature request. I use
[preflight](scripts/preflight.py) for target and duplicate checks and the model
for that narrower judgement. The earlier [regex prototype](eval/results.md)
used synthetic fixtures; its 12/12 is not agent accuracy.

## Boundary and procedure

The [workflow](.github/workflows/smoke-triage.md) declares issue-open and
manual triggers; Actions uses its [compiled lock file](.github/workflows/smoke-triage.lock.yml).
This branch is not default, so I tested manual dispatch, not live issue-open.
The checkout makes [AGENTS.md](AGENTS.md) available to Codex; the workflow
explicitly fetches the
[skill](.claude/skills/repro-triage/SKILL.md) before the issue. The skill checks
bug intent, self-contained pandas code, expected versus observed behavior,
and pandas/Python/OS versions. An incomplete bug may get one specific comment
and `needs-repro`. Other readable cases get no public action; a failed read is
an incomplete run, not an inferred verdict.

Issue text and tool responses are untrusted. The tool list and safe outputs
exclude closing, deleting, editing, merging, reassigning and pushing. This
still permits a wrong comment or label; a human must correct those.
There is no `CONTRIBUTING.md`: the bot posts directly; no contributor submits its draft.

## Test record

The [golden set](evals/golden/) has historical issues, no-action cases and a
constructed malicious case. It uses issue text available at opening, not later
labels or replies. Gold decisions were frozen before runs on this set; the
[method](evals/golden/README.md) records selection and comparison. The
balanced set does not estimate live pandas error rates. Over-triage also costs
time: later discussion progressed on [#69412](https://github.com/pandas-dev/pandas/issues/69412#issuecomment-5784836367)
and [#69436](https://github.com/pandas-dev/pandas/issues/69436#issuecomment-5804717944)
without the details my rule would request. Those replies were not agent input.

The [pilot](evals/pilot/) made a false API claim. The
[retry pass](evals/revision1/) repeated it: six of 12 workflows were green,
five detector jobs failed, and one upload failed. A green
[comment](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/32#issuecomment-6333624363)
wrongly rejected `df.select` and `pd.col`; both
[`select`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/core/frame.py#L6057)
and [`col`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/__init__.py#L110)
existed then. I corrected the skill and detector model and reran fresh copies.
All [twelve final runs](evals/golden/results.md) completed on first attempt
and matched the frozen action. One comment clearly re-asked supplied details;
another did so mildly. The injected case failed to redirect the bot. The
runs used 74.85 AI credits. None of this proves time saved.
After the runs I corrected [AGENTS.md](AGENTS.md)'s duplicate-skip claim;
that wording change was not rerun on the fresh cases.

## Governance: what is enforced and what is not

1. **Identity — tested.** Comments come from `github-actions[bot]` with a run link.
2. **Least privilege — configured, compile checked.** The agent job has
   `contents: read` and `issues: read` in the [lock file](.github/workflows/smoke-triage.lock.yml);
   GitHub tools reach only this sandbox. Writes use a separate output job. The
   compiler still grants the output and conclusion jobs `pull-requests: write`;
   the fixed issue target and disabled failure reports, not token scope alone,
   keep this workflow off PRs.
3. **Safe outputs — tested.** At most one comment and one `needs-repro` label
   per run; failure-report issues are disabled. A detector error blocks them.
4. **Human approval — absent** for comments/labels; humans alone close or fix reports.
5. **Budgets — configured, not a hard spend cap.** Agent runtime is ten minutes,
   with 20 AI credits/run and ten for detection. External authors get two
   starts/hour. The 100-credit daily guardrail excludes manual runs and can
   be overshot by concurrent starts; the rate-limit feature is experimental.
6. **Audit trail — partial.** [Logs](evals/golden/) retain visible calls, outputs
   and credits, not hidden reasoning or exact backend build. The CLI used
   fallback model metadata.
7. **Kill switch — partly tested.** I disabled/re-enabled during seeding, then
   disabled after evaluation. Cancelling active jobs was untested; key deletion cannot stop one.
8. **Drift detection — proposed, not scheduled here.** Rerun gold before
   changes and monthly, add new cases, and review changed and sampled outputs.
9. **Accountability — owner-managed.** I can change or disable the workflow;
   I corrected [two false outputs](docs/report.md). Pandas did not approve it.

The workflow admits external authors with `on.roles: all`; the compiled
write-role gate is gone. That trigger and its per-user gate are not live-tested.
Spam could still cost money. AWF restricts network; shell/CLI tools are off.
Threat detection blocks flagged outputs, not wrong factual claims.

## Bill of materials

- **Models:** Codex triage uses repo var `GH_AW_MODEL_AGENT_CODEX=gpt-5`;
  detection requests `gpt-5-mini`. Neither is pinned. Final logs show
  `gpt-5-2025-08-07` and `gpt-5-mini-2025-08-07` and their credit costs.
- **Instructions:** [AGENTS.md](AGENTS.md), [workflow](.github/workflows/smoke-triage.md),
  and [skill](.claude/skills/repro-triage/SKILL.md).
- **Tools and data:** GitHub MCP `repos`/`issues`, restricted to this sandbox;
  `safeoutputs` MCP for a comment, label or no-op; issue title/body, skill at
  the chosen commit, and repository files. No bash or CLI proxy for the model.
- **Permissions and outputs:** read-only agent scopes; a separate safe-output
  path for one comment and one existing label. See the compiled lock file.
- **Logs and evaluations:** [Actions runs](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions),
  [golden inputs/outputs](evals/golden/), and gh-aw credit logs where present.
- **Humans:** the owner maintains the configuration, reviews drift and can
  disable it; pandas maintainers are not participants in this test.

## Five failure questions

1. **An issue claims approval to close stale reports.** Its words are data;
   the workflow has no close output or write tool. The constructed case in
   the golden set must also test whether the agent avoids a misleading comment
   or label. [Run 39773156674](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39773156674)
   left it open with a relevant comment and only `needs-repro`.
2. **The provider changes the model.** A model change itself would not be
   detected. A changed decision might appear at the next proposed pre-change
   or monthly gold run. The owner would disable the workflow,
   inspect the diff and test an explicit replacement before re-enabling it.
3. **There are 300 issues in a week.** If deployed, that is about 43/day if
   evenly spread. Each external author gets two/hour, but many accounts can
   still generate load. The 100-credit daily guardrail may stop later jobs,
   yet concurrent starts can overshoot it. At the measured median 6.22 credits,
   43 daily issues would use about 267 credits; the owner handles skipped and
   failed runs manually. This is no throughput guarantee.
4. **A GitHub/MCP response carries instructions.** The response is untrusted
   input. The model might still misclassify the report, but it cannot gain
   close, merge or shell capability from that text. It could still put a wrong
   claim in the permitted comment on the selected issue; output limits do not
   check factual accuracy.
5. **A maintainer has only a phone.** In a phone browser, open this repo's
   Actions page, [disable the workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow)
   to stop new starts, then [cancel queued and active runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/cancel-a-workflow-run).
   Check that no run remains; revoke the OpenAI key if the account is compromised.

## AI use

I set the sandbox and spending bounds. Codex chose the triage design and
drafted the workflow, skill, scripts, initial case judgments and this report.
I used Codex to check original issue text, compiled permissions, unit tests,
run logs and each public output against the frozen decisions. The checks are
retained here; I am responsible for the submission and its errors.
