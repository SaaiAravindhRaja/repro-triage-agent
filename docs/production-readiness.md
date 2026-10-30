# Sandbox deployment record

This is the CS467 sandbox, not a pandas deployment. On 28 October 2026 the
workflow was enabled on `main` with `on.roles: [admin]`; ordinary public issue
authors cannot start model runs. No PR was opened against `pandas-dev/pandas`.
This is a bounded live demo, not production approval for upstream use.

## Controls configured on GitHub

- Required reviewer: the repository owner is currently named, admin bypass is
  disabled, and the owner approves or rejects staged output. This is a human
  gate, but not independent review in the single-owner sandbox.
- Deployment branch policy: `main` only.
- The approval gate is after model execution and threat detection. Both
  `safe_outputs` and `conclusion` require its success; it does not prevent
  inference cost. Inspect the issue, detector result, and `agent_output.json`
  artifact before approving; reject unsupported output or missing evidence.
- These settings are confirmed through GitHub's repository environment API,
  the approved [post-hardening run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/40834047322/attempts/1)
  on issue #54, and the rejected [issue-trigger run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/41026047026)
  on #55. A no-action run may wait for review too.

## Remaining release blockers

- **Scope:** the admin-only trigger is intentionally not a public intake tool.
  Do not widen it to contributors or deploy to pandas without permission,
  reviewer capacity, and a new threat and cost review.
- **Input and integrity:** `min-integrity: none` lets admin-authored issues
  reach the model, including malicious text. Safe outputs constrain actions,
  but allowed comments can still be wrong. The two-file-read cap does not
  restrict its path; the required skill path/ref is only prompt-enforced.
- **Spend:** per-run and daily AI-credit settings are guardrails, not a hard
  provider billing cap. The deployed workflow has no manual trigger. A preflight
  API check blocks the third issue-triggered start in an hour before inference;
  it fails closed on bad data. Model cost is still incurred before a reviewer
  approves or rejects output.
- **Model drift:** `gpt-5` and `gpt-5-mini` are aliases, not immutable pins.
  The owner has a documented manual [drift routine](operating-routine.md),
  but there is no scheduled golden-set run. A live check consumes credits and
  must use fresh issues under the current configuration.
- **Unverified paths:** non-admin role rejection and phone-based cancellation have not been tested
  end-to-end. The twelve scored runs predate these controls. The owner issue-open
  path, approval, rejection, queued-run cancellation and rerun rejection were
  tested separately. A rejected rerun is deliberate: the owner handles any
  partial output manually.
- **Residual permissions:** gh-aw 0.92.0's compiled safe-output and conclusion
  jobs include `pull-requests: write` even though the configured actions are
  issue-scoped. The agent itself remains read-only, but review the generated
  permissions on compiler upgrades and do not mistake fixed targets for a
  narrower token.

The historical 12-case evaluation remains useful for its stated scope: action
agreement on frozen inputs, with visible failures in comment quality. It does
not establish production safety, maintainer-time savings, safe throughput
under an issue burst, or live enforcement for non-admin reporters.
