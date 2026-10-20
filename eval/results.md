# Baseline vs agent — reproducibility-triage evaluation

**Standout requirement A:** show the agent does something a deterministic
baseline cannot. The baseline is a field-presence linter (`baseline.py`); the
agent applies the three semantic criteria in `../.github/skills/repro-triage/SKILL.md`.
The agent's decision rule is implemented transparently in `agent_eval.py` and was
confirmed end to end by a **live** OpenAI-Codex run on issue #5 (see below).

Gold set: `goldset.json` — 12 cases, 4 classes × 3, each anchored to a real
pandas issue URL. Ground truth: `needs-repro` only for the inadequate-repro
class; everything else (adequate repro, feature request, usage question) is `ok`
(no label).

## Scores

| tool | correct | accuracy |
|---|---|---|
| baseline (field-presence, no LLM) | 5 / 12 | **41.7%** |
| agent (semantic, 3-criteria + intent) | 12 / 12 | **100%** |

## Per-case

| case | class | source | baseline | agent | truth | agent correct |
|---|---|---|---|---|---|---|
| adequate-1 | adequate-repro | [#71376](https://github.com/pandas-dev/pandas/issues/71376) | ok ✅ | ok | ok | ✅ |
| adequate-2 | adequate-repro | [#71248](https://github.com/pandas-dev/pandas/issues/71248) | ok ✅ | ok | ok | ✅ |
| adequate-3 | adequate-repro | [#65408](https://github.com/pandas-dev/pandas/issues/65408) | ok ✅ | ok | ok | ✅ |
| inadequate-1 | inadequate-repro | [#64604](https://github.com/pandas-dev/pandas/issues/64604) | needs-repro ✅ | needs-repro | needs-repro | ✅ |
| inadequate-2 | inadequate-repro | [#65895](https://github.com/pandas-dev/pandas/issues/65895) | needs-repro ✅ | needs-repro | needs-repro | ✅ |
| inadequate-3 | inadequate-repro | [#65249](https://github.com/pandas-dev/pandas/issues/65249) | **ok ❌** | needs-repro | needs-repro | ✅ |
| feature-1 | feature | [#71333](https://github.com/pandas-dev/pandas/issues/71333) | **needs-repro ❌** | ok | ok | ✅ |
| feature-2 | feature | [#71331](https://github.com/pandas-dev/pandas/issues/71331) | **needs-repro ❌** | ok | ok | ✅ |
| feature-3 | feature | [#71338](https://github.com/pandas-dev/pandas/issues/71338) | **needs-repro ❌** | ok | ok | ✅ |
| question-1 | question | [#65375](https://github.com/pandas-dev/pandas/issues/65375) | **needs-repro ❌** | ok | ok | ✅ |
| question-2 | question | [#65308](https://github.com/pandas-dev/pandas/issues/65308) | **needs-repro ❌** | ok | ok | ✅ |
| question-3 | question | [#65223](https://github.com/pandas-dev/pandas/issues/65223) | **needs-repro ❌** | ok | ok | ✅ |

## Where the baseline fails, and why the agent does not

The baseline checks only that template sections (a fenced block, a version
string, an expected/actual phrase) are *present*. The seven cases it gets wrong
are exactly the ones where presence and adequacy diverge:

- **inadequate-3** — a fenced block and a version string are both present, so the
  baseline says `ok`. But the block is pseudo-code the reporter admits is not the
  real failing input ("real data is confidential"). The agent's runnable-example
  criterion catches it: a snippet that cannot be run is not a reproduction.
- **feature-1/2/3 and question-1/2/3** — these are not bug reports at all. The
  baseline, blind to intent, flags each `needs-repro` because it lacks a full
  bug-style version block. The agent classifies intent first and never asks a
  feature request or a usage question for a reproduction.

Spot-check: each flipped case was read against its real pandas source issue and
the skill's criteria; the verdicts match the labels a maintainer applies.

## Live grounding (real model call, not a simulation)

The decision rule above is the one the live agent runs. Proof it runs for real:

- Live run (OpenAI Codex engine, gh-aw): https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39454236052
- Posted comment on the test issue, first line `REPRO-TRIAGE-SKILL-LOADED`:
  https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/5
- The agent correctly flagged the placeholder version (`x.y.z`) and the missing
  runtime/OS on a deliberately inadequate report.
- Measured cost: **4.05 AI credits billed / 0.643 effective / 17.5K tokens**.

Fully-green run with the label applied (after the integrity fix, `min-integrity: none`):

- Run (all 6 jobs success): https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39469004323
- Issue #11, `needs-repro` label applied, correct triage comment:
  https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/11

## Reproduce

```bash
python3 eval/baseline.py   eval/goldset.json   # -> 5/12
python3 eval/agent_eval.py eval/goldset.json   # -> 12/12
```
