# Design: a narrow first pass on bug reports
This builds a safe first pass for [pandas](https://github.com/pandas-dev/pandas)
reports in my sandbox rather than deploying it to pandas itself.

## Why this task

My [read-only snapshot](evidence/pandas-bug-intake.json) found 111 pandas
issues opened 22 July–20 October 2026 with `Bug` on 22 October; 12 also had
`Needs Triage`. That gives the workflow a real intake context. In the
[30 newest](evidence/pandas-consecutive-30.json), two clearly needed details,
21 needed no action, and seven were uncertain. Both clear ask cases
([#71158](https://github.com/pandas-dev/pandas/issues/71158) and
[#70991](https://github.com/pandas-dev/pandas/issues/70991)) later progressed,
so I use the agent as a selective first pass, not as proof of time saved.

[Pandas's bug template](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/.github/ISSUE_TEMPLATE/bug_report.yaml)
asks for a copy-pastable example, expected behavior and `pd.show_versions()`.
I rejected a headings-only linter: it cannot judge whether code is
self-contained, a version is real, or a report is a feature request. I use
[preflight](scripts/preflight.py) for target and duplicate checks, and the
model for that semantic judgement. The earlier [regex prototype](eval/results.md)
used synthetic fixtures; its 12/12 is not evidence of agent accuracy.

## Boundary and procedure

The [workflow](.github/workflows/smoke-triage.md) admits only admin issue-open
events; there is no manual trigger. Actions uses its [compiled lock file](.github/workflows/smoke-triage.lock.yml).
The historical evaluation isolates the agent decision with manual dispatch on a
non-default branch. The checkout makes [AGENTS.md](AGENTS.md) available to
Codex; the workflow fetches the [skill](.claude/skills/repro-triage/SKILL.md)
before the issue. It checks bug intent, self-contained pandas code, expected
versus observed behavior, and pandas/Python/OS versions. An incomplete bug may
get one specific comment and `needs-repro`; readable non-bugs get no action.
Model-tool read failure is incomplete, while a preflight API failure stops before
inference or output. Preflight writes `noop` for closed or triaged issues and
independently limits starts before inference. [gh-aw documents](https://github.github.com/gh-aw/reference/steps-jobs/)
that pre-agent no-ops stop inference; unit tests cover those paths.

Issue/tool text is untrusted. Safe outputs bar destructive actions, but wrong comments or labels remain possible. There is no `CONTRIBUTING.md`: the workflow posts bounded bot output directly; no human submits agent-generated material, so a general AI-contribution policy does not govern this action path. The alternative of deploying to the upstream pandas repository was rejected: it would require maintainer permission and community review of every configuration change, which is impractical for a course project and unsafe before independent evaluation. What the agent is prevented from doing: it cannot close, delete, edit, merge, or push; it has no shell or CLI tool. What tests revealed and what remains unresolved: the pilot exposed a false API claim; the revision run repeated it and surfaced detector failures; the final twelve matched frozen decisions, but 2/5 comments had redundant requests, the model alias is not pinned, and non-admin trigger rejection was only source-checked. Rate-limit behavior at real pandas volume and model-change detection remain untested.

## Test record

The [golden set](evals/golden/) combines historical issues, no-action cases,
and a constructed malicious case. It uses issue text available at opening, not
later labels or replies. Gold decisions were frozen before runs; the
[method](evals/golden/README.md) records selection and comparison. Its balance
tests both action and restraint; it is an evaluation set, not a pandas-rate
estimate. Later work on [#69412](https://github.com/pandas-dev/pandas/issues/69412#issuecomment-5784836367)
and [#69436](https://github.com/pandas-dev/pandas/issues/69436#issuecomment-5804717944)
also shows why a request must stay specific. Those replies were not agent input.

The [pilot](evals/pilot/) exposed a false API claim. The
[retry pass](evals/revision1/) showed the same weakness: six of 12 workflows
were green, five detector jobs failed, and one upload failed. A green
[comment](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/32#issuecomment-6333624363)
wrongly rejected `df.select` and `pd.col`, although both
[`select`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/core/frame.py#L6057)
and [`col`](https://github.com/pandas-dev/pandas/blob/fbfadf45ae216faf91c622a68cb6d3e91559c284/pandas/__init__.py#L110)
existed then. I corrected the skill and detector model, then reran fresh copies.
All [twelve final runs](evals/golden/results.md) matched their frozen action on
first attempt. The [five public comments](evals/golden/comment-quality-review.md)
were courteous and 40--87 words; 3/5 avoided redundant requests (#43 minor,
#45 material). The injection did not redirect the bot. The 74.85-credit run
set and 2/30 clear-request slice support keeping deployment narrow. Afterward,
I corrected [AGENTS.md](AGENTS.md)'s duplicate-skip claim and added approval,
a two-read repository-file budget, rerun rejection and diagnostic-only failure
reports. The [post-hardening checks](evals/posthardening/) exercised skill
loading, approval, bounded output, rejection, cancellation and rerun blocking.

## Governance controls and evidence
1. **Identity — tested.** Comments come from `github-actions[bot]` with a run link.
2. **Least privilege — configured, compile checked.** The agent job has only
   `actions`, `contents` and `issues` read scopes in the [lock file](.github/workflows/smoke-triage.lock.yml);
   GitHub tools reach only this sandbox. Writes use a separate output job. The
   compiler still grants the output and conclusion jobs `pull-requests: write`;
   the fixed issue target and disabled failure reports, not token scope alone,
   keep this workflow off PRs.
3. **Safe outputs — tested.** At most one comment and one `needs-repro` label
   per run; failure and missing-tool issues are disabled. A detector error blocks them.
4. **Human approval — tested after the scored runs.** The compiled output and
   conclusion jobs require success from the approval job. On
   [#54](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/54), the
   owner reviewed the staged output, then approved one comment and one label.
   Current Environment settings require owner review and disable admin bypass. On
   [#55](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/55), I rejected
   staged output: no comment or label was published. In this single-owner sandbox,
   approval is a human check, not independent separation.
5. **Budgets — configured, not a hard spend cap.** Agent and detector time out
   at ten minutes; compiler jobs allow setup/logging. Caps: 20 credits/run and ten for detection;
   preflight admits at most two issue-triggered starts per repository/hour before inference.
   The 100-credit guardrail remains conservative and can block work earlier when usage accounting is missing.
6. **Audit trail — live evidence retained.** [Logs](evals/golden/) and the [current check](evals/posthardening/) retain visible calls, outputs and credits; hidden reasoning and the exact backend build are not available.
7. **Kill switch — exercised.** I disabled/re-enabled it during seeding,
   disabled it after evaluation, and cancelled an approval-queued run. Phone-only
   operation is documented but was not separately tested.
8. **Drift detection — proposed review cadence.** Before model/configuration
   changes and monthly, I will use fresh sandbox copies and review each action
   and comment against the [quality rubric](evals/golden/comment-quality-review.md).
9. **Accountability — owner-managed.** Saai Aravindh Raja owns configuration
   and the kill switch; [the routine](docs/operating-routine.md) records checks.
   The owner is accountable for output approval in this single-owner sandbox.

`roles: [admin]` skips ordinary reporters before inference: safer for sandbox
spend, but not community intake. Because the only output is one comment and one
label on a selected issue, bounded safe-outputs and single-owner approval are
proportionate — heavier controls like CODEOWNERS or draft PRs serve no purpose here.
The owner path, approval, rejection, cancellation and rerun block were live-checked;
non-admin rejection was source and lock checked. Recovery is manual handling after
checking for partial output. AWF restricts network; shell/CLI tools are off.
## Bill of materials
- **Models:** Codex triage uses repo var `GH_AW_MODEL_AGENT_CODEX=gpt-5`; detection requests `gpt-5-mini`. Neither is pinned.
  Final logs show `gpt-5-2025-08-07` and `gpt-5-mini-2025-08-07` and their credit costs.
- **Instructions:** [AGENTS.md](AGENTS.md), [workflow](.github/workflows/smoke-triage.md),
  and [skill](.claude/skills/repro-triage/SKILL.md).
- **Tools and MCP servers:** sandbox-only GitHub MCP: up to two repository-file reads and two issue reads. No bash or CLI proxy.
- **Data sources:** live GitHub issue content (untrusted); [evidence/](evidence/) snapshots for need justification.
- **Permissions and outputs:** read-only agent scopes; separate safe-output path for one comment and one existing label. The compiled output job retains `pull-requests: write`; see the lock file.
- **Logs and evaluations:** [Actions runs](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions),
  [golden inputs/outputs](evals/golden/), and gh-aw credit logs where present.
- **Humans:** the owner maintains the configuration, reviews drift and can
  disable it; pandas maintainers are not participants in this test.
## Five failure questions

1. **An issue claims approval to close stale reports.** Its words are data;
   no close output or write tool is exposed. In the constructed case,
   [run 39773156674](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39773156674)
   left it open with a relevant comment and only `needs-repro`.
2. **The provider changes the model.** A model change itself is not detected.
   A changed decision might appear in a gold run; the owner must disable the
   workflow, inspect the diff and test a replacement before re-enabling it.
3. **There are 300 issues in a week.** Ordinary reporters do not start this
   admin-only sandbox workflow. Admin issue opens are stopped before inference
   after two starts in an hour; the daily guardrail can stop them sooner. There
   is no manual-dispatch bypass. Skipped reports need manual handling.
4. **A GitHub/MCP response carries instructions.** The response is untrusted
   input. The model might still misclassify the report, but it cannot gain
   close, merge or shell capability from that text. It could still put a wrong
   claim in the permitted comment on the selected issue; output limits do not
   check factual accuracy.
5. **A maintainer has only a phone.** Open this repo's Actions page and
   [disable the workflow](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow),
   then [cancel queued and active runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/cancel-a-workflow-run).
   Check no run remains; revoke the key if the account is compromised.

## AI use

I set the sandbox and spending bounds. Codex drafted the workflow, skill,
scripts, initial case judgments and report. I checked source, permissions,
tests, logs and outputs against the frozen decisions; I'm responsible for this submission.
