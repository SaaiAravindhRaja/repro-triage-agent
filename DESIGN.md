# Design: a narrow first pass on bug reports
A safe first pass for [pandas](https://github.com/pandas-dev/pandas) bug reports,
run in my sandbox rather than deployed to pandas itself.

## Why this task

My [read-only snapshot](evidence/pandas-bug-intake.json) found 111 pandas issues
opened 22 July–20 October 2026 with `Bug`; 12 also had `Needs Triage`. In the
[30 newest](evidence/pandas-consecutive-30.json), two clearly needed details, 21
needed no action, seven were uncertain. Both clear ask cases
([#71158](https://github.com/pandas-dev/pandas/issues/71158),
[#70991](https://github.com/pandas-dev/pandas/issues/70991)) later progressed, so
I use the agent as a selective first pass, not proof of time saved.

[Pandas's bug template](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/.github/ISSUE_TEMPLATE/bug_report.yaml)
asks for a copy-pastable example, expected behavior and `pd.show_versions()`. I
rejected a headings-only linter: it cannot judge whether code is self-contained,
a version is real, or a report is a feature request. So
[preflight](scripts/preflight.py) does target and duplicate checks and the model
does semantic judgement. The earlier [regex prototype](eval/results.md) used
synthetic fixtures; its 12/12 is not evidence of agent accuracy.

## Boundary and procedure

The [workflow](.github/workflows/smoke-triage.md) admits only admin issue-open
events; there is no manual trigger, and Actions uses its [compiled lock file](.github/workflows/smoke-triage.lock.yml).
The checkout makes [AGENTS.md](AGENTS.md) available to Codex; the workflow
fetches the [skill](.claude/skills/repro-triage/SKILL.md) before the issue. It
checks bug intent, self-contained code, expected versus observed behavior, and
pandas/Python/OS versions. An incomplete bug may get one specific comment and
`needs-repro`; readable non-bugs get no action. [Preflight](scripts/preflight.py)
writes `noop` for closed or triaged issues, limits starts, and a preflight API
failure stops before inference. [gh-aw](https://github.github.com/gh-aw/reference/steps-jobs/)
confirms pre-agent no-ops stop inference; unit tests cover those paths.

Issue and tool text is untrusted. Safe outputs bar destructive actions, but a
wrong comment or label is still possible. There is no `CONTRIBUTING.md`: the
workflow posts bounded bot output directly and no human submits agent-generated
material, so a contributor AI policy does not govern this path.

**Alternative rejected:** deploying to upstream pandas — it would need maintainer
permission and review of every change, impractical for a course project and unsafe
before independent evaluation.
**Prevented:** the agent cannot close, delete, edit, merge or push; no shell/CLI.
**Tests revealed:** the pilot exposed a false API claim; the revision repeated it
and surfaced detector failures; the final twelve matched frozen decisions, though
2 of 5 comments carried a redundant request.
**Unresolved:** the model alias is not pinned (see BOM); rate-limit behavior at
pandas volume and model-change detection remain untested.

## Test record

The [golden set](evals/golden/) combines historical issues, no-action cases,
and a constructed malicious case, using issue text available at opening, not
later labels or replies. Gold decisions were frozen before runs; the
[method](evals/golden/README.md) records selection and comparison. It is an
evaluation set, not a pandas-rate estimate. Later work on
[#69412](https://github.com/pandas-dev/pandas/issues/69412#issuecomment-5784836367)
and [#69436](https://github.com/pandas-dev/pandas/issues/69436#issuecomment-5804717944)
shows why a request must stay specific. Those replies were not agent input.

The [pilot](evals/pilot/) exposed a false API claim; the
[retry pass](evals/revision1/) repeated it (six of 12 green, five detector
failures, one upload failure). A green
[comment](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/32#issuecomment-6333624363)
wrongly rejected `df.select` and `pd.col`, though both
[`select`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/core/frame.py#L6057)
and [`col`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/__init__.py#L110)
existed then. I corrected the skill and detector model and reran fresh copies.
All [twelve final runs](evals/golden/results.md) matched their frozen action
first attempt. The [five public comments](evals/golden/comment-quality-review.md)
were courteous, 40--87 words; 3/5 avoided redundant requests (#43 minor, #45
material); the injection did not redirect the bot. Afterward I corrected
[AGENTS.md](AGENTS.md)'s duplicate-skip claim and added approval, a two-read
file budget, rerun rejection and diagnostic-only failure reports. The
[post-hardening checks](evals/posthardening/) exercised skill loading, approval,
bounded output, rejection, cancellation and rerun blocking.

## Governance controls and evidence
1. **Identity — tested.** Comments come from `github-actions[bot]` with a run link.
2. **Least privilege — configured, compile checked, trigger live-tested.** The
   agent job has only `actions`, `contents` and `issues` read scopes in the
   [lock file](.github/workflows/smoke-triage.lock.yml); GitHub tools reach only
   this sandbox, and writes use a separate output job. The compiler still grants
   output/conclusion jobs `pull-requests: write`; the fixed issue target and
   disabled failure reports, not token scope alone, keep this workflow off PRs.
3. **Safe outputs — tested.** At most one comment and one `needs-repro` label per
   run; failure/missing-tool issues are disabled and a detector error blocks them.
4. **Human approval — tested after the scored runs.** The output and conclusion
   jobs require the approval job; Environment settings require owner review and
   disable admin bypass. On
   [#54](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/54) the
   owner approved one comment and label; on
   [#55](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/55) a
   rejection published nothing. In this single-owner sandbox, approval is a human
   check, not independent separation.
5. **Budgets — configured, not a hard spend cap.** Agent and detector time out at
   ten minutes. Caps: 20 credits/run, ten for detection; preflight admits at most
   two issue-triggered starts per repository/hour before inference. The 100-credit
   guardrail is conservative and can block earlier when accounting is missing.
6. **Audit trail — live evidence retained.** [Logs](evals/golden/) and the
   [current check](evals/posthardening/) retain visible calls, outputs and
   credits; hidden reasoning and the exact backend build are not available.
7. **Kill switch — exercised.** Disabled/re-enabled during seeding, disabled after
   evaluation, cancelled a queued run; phone-only path documented, untested.
8. **Drift detection — proposed review cadence.** Before model/config changes and monthly, I review each action and comment on fresh sandbox copies against the [quality rubric](evals/golden/comment-quality-review.md).
9. **Accountability — owner-managed.** Saai Aravindh Raja owns configuration, the kill switch and output approval; [the routine](docs/operating-routine.md) records checks.

`roles: [admin]` skips ordinary reporters before inference: safer for sandbox
spend, not community intake. Because the only output is one comment and one label
on a selected issue, bounded safe-outputs and single-owner approval are
proportionate; CODEOWNERS or draft PRs would serve no purpose here. The owner
path, approval, rejection, cancellation, rerun block and non-admin rejection were
all live-checked (see [posthardening](evals/posthardening/README.md)). Recovery is
manual after checking for partial output; AWF restricts network, shell/CLI off.
## Bill of materials
- **Models (not pinned):** triage `GH_AW_MODEL_AGENT_CODEX=gpt-5`, detection `gpt-5-mini`; final logs show `gpt-5-2025-08-07` / `gpt-5-mini-2025-08-07` and credit costs.
- **Instructions:** [AGENTS.md](AGENTS.md), [workflow](.github/workflows/smoke-triage.md), [skill](.claude/skills/repro-triage/SKILL.md).
- **Tools and MCP servers:** sandbox-only GitHub MCP: up to two repository-file reads and two issue reads. No bash or CLI proxy.
- **Data sources:** live GitHub issue content (untrusted); [evidence/](evidence/) snapshots for need justification.
- **Permissions and outputs:** read-only agent scopes; separate safe-output path for one comment and one existing label. The output job retains `pull-requests: write` (see lock file).
- **Logs and evaluations:** [Actions runs](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions), [golden inputs/outputs](evals/golden/), and gh-aw credit logs where present.
- **Humans:** the owner maintains config, reviews drift and can disable it; pandas maintainers are not participants.
## Five failure questions

1. **Issue claims approval to close stale reports.** Its words are data; no
   close output or write tool is exposed. In the constructed case,
   [run 39773156674](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39773156674)
   left it open with a relevant comment and only `needs-repro`.
2. **Provider changes the model.** The change itself is not detected; a changed
   decision might appear in a gold run. The owner must then disable the workflow,
   inspect the diff and test a replacement before re-enabling.
3. **300 issues in a week.** Ordinary reporters do not start this admin-only
   workflow. Admin opens are stopped before inference after two starts in an
   hour, and the daily guardrail sooner; there is no manual-dispatch bypass.
4. **A GitHub/MCP response carries instructions.** It is untrusted input. The
   model might misclassify the report but cannot gain close, merge or shell
   capability from that text. It could still put a wrong claim in the permitted
   comment; output limits do not check factual accuracy.
5. **A maintainer has only a phone.** Open Actions and
   [disable the workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow),
   then [cancel queued and active runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/cancel-a-workflow-run);
   check none remain and revoke the key if the account is compromised.

## AI use

I set the sandbox and spending bounds. Codex drafted the workflow, skill, scripts,
initial case judgments and report; I checked source, permissions, tests, logs and
outputs against the frozen decisions and am responsible for this submission.
