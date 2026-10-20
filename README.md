# repro-triage

A first-pass reproducibility-triage agent for a busy open-source issue tracker.
When a bug report comes in without enough to reproduce it, the agent reads the
issue, decides whether it carries a runnable reproduction, and — if not — leaves
one short comment naming exactly what is missing and applies a `needs-repro`
label. It never closes, edits, merges, or reassigns anything.

Built on [githubnext/gh-aw](https://github.com/githubnext/gh-aw) agentic
workflows, running the OpenAI Codex engine behind a budget-capped proxy.

## Why this is worth automating

Measured on pandas (frozen window 2026-07-22 → 2026-10-20, read-only API):

- **716** all-time `Needs Info` issues; **197** of them also labelled `Bug`.
- Only **2** open right now — maintainers actively clear the backlog, so this is
  live recurring labour, not a dead label.
- **No triage bot exists** on the repo; the work is done by hand.

Asking a reporter for a missing reproduction is repetitive, semantic work: you
have to read the report and judge whether the example would actually run. That is
the gap this agent fills.

## What the agent decides

Three criteria, applied semantically (see `.github/skills/repro-triage/SKILL.md`):

1. a runnable minimal example that actually imports the library,
2. an expected-vs-actual statement,
3. a real version block (not `x.y.z` / `latest` / `<paste …>`).

A feature request or a usage question is not a bug report, so it is never asked
for a reproduction.

## Baseline vs agent

A deterministic field-presence linter (`eval/baseline.py`) checks only that the
template sections are filled. Over a stratified gold set of 12 real pandas issues
(`eval/goldset.json`, 4 classes × 3):

| tool | accuracy |
|---|---|
| field-presence baseline | 5 / 12 (41.7%) |
| semantic agent | 12 / 12 (100%) |

Full per-case table, with the cases the baseline gets wrong and why, is in
[`eval/results.md`](eval/results.md). Reproduce from scratch:

```bash
bash eval/reproduce.sh
```

## Safety and governance

Nine controls, each tied to a line in the compiled `.lock.yml`, are documented in
[`docs/governance.md`](docs/governance.md): a zero-permission agent job,
comment+label-only outputs (no close/merge/delete), a network firewall, per-run
and daily credit caps, threat detection, SHA-pinned actions, an untrusted-content
guard, a least-privilege credential split, and a pinned model. Known limits and
failure modes are in [`docs/failure-modes.md`](docs/failure-modes.md).

## Layout

```
.github/workflows/smoke-triage.md        # the workflow (source)
.github/workflows/smoke-triage.lock.yml  # compiled, what Actions runs
.github/skills/repro-triage/SKILL.md     # the triage judgement
eval/baseline.py                         # field-presence baseline (no LLM)
eval/agent_eval.py                       # the agent's semantic decision rule
eval/goldset.json                        # 12 real pandas issues, 4 classes
eval/results.md                          # baseline vs agent, per case
eval/reproduce.sh                        # one command, cold
docs/governance.md                       # 9 controls with evidence
docs/failure-modes.md                    # limits and containment
docs/report.md                           # the writeup
```
