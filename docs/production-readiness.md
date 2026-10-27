# Sandbox deployment record

This is the CS467 sandbox, not a pandas deployment. On 28 October 2026 the
workflow was enabled on `main` with `on.roles: [admin]`; ordinary public issue
authors cannot start model runs. No PR was opened against `pandas-dev/pandas`.
This is a bounded live demo, not production approval for upstream use.

## Controls configured on GitHub

- Required reviewer: the repository owner. Admin bypass is disabled; self-review
  is allowed because this is a single-owner sandbox.
- Deployment branch policy: `main` only.
- The approval gate is after model execution and threat detection. Both
  `safe_outputs` and `conclusion` require its success; it does not prevent
  inference cost. Inspect the issue, detector result, and `agent_output.json`
  artifact before approving; reject unsupported output or missing evidence.
- These settings are confirmed through GitHub's repository environment API.
  The gate has not yet been exercised in a workflow run. A no-action run may
  wait for review too.

## Remaining release blockers

- **Scope:** the admin-only trigger is intentionally not a public intake tool.
  Do not widen it to contributors or deploy to pandas without permission,
  reviewer capacity, and a new threat and cost review.
- **Input and integrity:** `min-integrity: none` lets admin-authored issues
  reach the model, including malicious text. Safe outputs constrain actions,
  but allowed comments can still be wrong.
- **Spend:** per-run and daily AI-credit settings are guardrails, not a hard
  provider billing cap. Manual runs bypass the daily guardrail, concurrent
  issue runs can overshoot it, and the per-user limit is experimental. Model
  cost is incurred before a reviewer approves or rejects output.
- **Model drift:** `gpt-5` and `gpt-5-mini` are aliases, not immutable pins.
  There is no scheduled golden-set drift check. A named owner must review
  output changes before each model/configuration change and on a regular
  schedule.
- **Unverified paths:** issue-open role enforcement, the rate limit, environment
  approval/rejection, and phone-based cancellation have not been tested
  end-to-end. The twelve scored runs predate these controls.
- **Residual permissions:** gh-aw 0.92.0's compiled safe-output and conclusion
  jobs include `pull-requests: write` even though the configured actions are
  issue-scoped. The agent itself remains read-only, but review the generated
  permissions on compiler upgrades and do not mistake fixed targets for a
  narrower token.

The historical 12-case evaluation remains useful for its stated scope: action
agreement on frozen inputs, with visible failures in comment quality. It does
not establish production safety, maintainer-time savings, live enforcement of
these new gates, or safe throughput under an issue burst.
