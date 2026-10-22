# Governance evidence and limits

[DESIGN.md](../DESIGN.md) is the submission's nine-control account. This file
records the corrections to an earlier draft, so the old claims do not survive
as a second version of the design.

- A source `permissions` block is not enough to describe the compiled workflow.
  gh-aw creates separate jobs for safe outputs; inspect the generated
  [lock file](../.github/workflows/smoke-triage.lock.yml) after compilation.
  In this version the output and conclusion jobs have `pull-requests: write`
  as well as `issues: write`, even though the enabled handlers are bound to
  an issue number. That is residual token scope, not a permission given to
  the model.
- The earlier draft said a separate fine-grained GitHub PAT handled writes.
  That was not established by the repository's secret inventory. A bot actor
  on comments does not itself prove a dedicated PAT or narrow PAT scope.
- `gpt-5` selected through a repository variable is a model name, not an
  immutable model-version pin. The detector now requests `gpt-5-mini`; that
  is also an alias, not an immutable snapshot. Future provider changes remain
  possible. A reproducer also needs the external repository variable
  `GH_AW_MODEL_AGENT_CODEX=gpt-5`. The first final
  [run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39731469850)
  logged a Codex CLI warning that `gpt-5` lacked local model metadata and
  fallback metadata was used; the run nevertheless completed. This is not a
  version pin or evidence that later model behavior is stable.
- A threat detector in warning mode is not a hard output gate. The new source
  and compiled lock set `continue-on-error: false`. An earlier
  [malicious-issue run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39470094921)
  showed one refusal; it does not establish broad injection resistance.
- [Run 39730488990](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39730488990)
  exposed a concrete detector failure: gh-aw's `detection` alias had no AI-credit
  price when model lookup timed out, so strict mode blocked the safe output.
  The [detector project's own notes](https://github.com/github/gh-aw-threat-detection/blob/main/README.md#ai-credits-and-token-usage)
  describe this failure mode. The workflow now requests `gpt-5-mini` explicitly;
  the first [run with that configuration](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39731469850)
  completed detection and the whole workflow. One pass does not prove that
  future provider or network failures cannot recur.
- The earlier 1000-credit per-run default was a generous failure ceiling, not
  a useful operating budget. The source now requests tighter per-run and daily
  limits; [DESIGN.md](../DESIGN.md) treats throughput under those caps as a
  limitation, not a promise. Manual dispatch bypasses the daily guardrail,
  and concurrent issue-open runs can pass before earlier ones are counted.
  It is an admission guardrail, not a hard spending cap.
- `min-integrity: none` lets this single-maintainer sandbox read its test
  issues, including malicious text. It removes the default author-trust
  filter, so bounded outputs and review remain important. It is not a
  recommended production default for pandas.
- `network: defaults` is the [AWF basic-infrastructure allowlist](https://github.github.com/gh-aw/reference/network/),
  not unrestricted web access. The compiled firewall also permits the needed
  GitHub and OpenAI endpoints. Hosted web search and shell tools are not
  exposed to the agent; the domain filter does not validate issue content.
- `on.roles: all` is necessary to accept issues from external reporters;
  omitting it caused gh-aw to compile a write-role gate in `pre_activation`.
  The compiled workflow no longer has that gate. Any public reporter can now
  trigger a paid run, so the daily admission limit is a cost guardrail, not
  protection against all spam or a fixed spending ceiling.
- The experimental user-rate-limit adds a two-runs-per-hour gate for external
  authors. The compiled pre-activation job now gates on that check, not the
  former write-role membership check. It is compile-checked, not live-tested
  with an external account; many accounts can still consume credits.

The configured model has only this repository in its GitHub-tool allowlist.
That limits where it reads, but the issue and tool responses remain untrusted.
No claim here treats prompt wording as a substitute for safe-output limits.
