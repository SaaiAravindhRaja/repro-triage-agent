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
- `on.roles: [admin]` is an exact allowlist. Only repository admins can start
  issue or manual runs; ordinary reporters are skipped before model execution.
  This limits sandbox spend but is not a usable pandas intake policy. The
  compiled role gate is not live-tested.
- The experimental user-rate-limit applies to every role and allows two starts
  per user per hour. It is compile-checked, not live-tested. An admin can still
  start paid runs, and the daily credit guardrail is not a hard provider billing cap.
- Preflight rejects reruns before inference. Missing-tool reports cannot create
  issues; missing-data reports flow only through the disabled failure-issue path.
  Those post-evaluation controls have unit and compiled-workflow coverage, not a live run.

The configured model has only this repository in its GitHub-tool allowlist.
That limits where it reads, but the issue and tool responses remain untrusted.
The one-file-read and two-issue-read budgets do not bind those reads to the
skill path/ref or selected issue number. The workflow prompt requests them and
the historical trace verifies them, but a future model could read another
sandbox file or issue. No claim here treats prompt wording as a substitute for
safe-output limits.

## Post-evaluation approval gate

After the twelve scored runs, the workflow gained a custom
`triage-output-approval` job. The compiled lock puts it after `agent` and
`detection`, gives it no token permissions, and makes both `safe_outputs` and
`conclusion` require its success. GitHub Settings
names the repository owner as reviewer, disables admin bypass, and limits the
environment to `main`; self-review is allowed. This is configured but not
exercised by a workflow run. Inspect the `agent` artifact, issue, and detector
result before approving. A no-action run may wait too.

The historical evaluation remains tied to its recorded commit and did not use
this gate. The current workflow is enabled on `main` for admins only; this is
not a deployment to pandas. See the [deployment record](production-readiness.md).
