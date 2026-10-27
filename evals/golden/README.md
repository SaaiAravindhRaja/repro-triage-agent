# Golden evaluation

This is an issue-triggered workflow, so the historical set contains **issues**, not
pull requests. I selected 11 pandas issues to exercise four adequately documented
bugs, four incomplete bug reports, and three non-bugs that require no action.
This is a deliberately balanced test set, not a random sample or an estimate of
how often pandas reports need clarification. The twelfth case is a **constructed**
prompt injection, kept separate from historical inputs.

## Event-time inputs and pre-registered outcomes

Each `inputs/pandas-*.json` records the upstream issue URL, creation time,
exact title and body, and capture time. The read-only
`python3 evals/golden/inputs/_capture_historical.py --verify` check compares
these with GitHub and checks `userContentEdits` and title-rename events. All 11
had zero edits or renames at capture, making their opening text verifiable.
Later comments and labels were **not** fed to the agent. The constructed case
is in `adversarial/` and is not passed off as a real pandas report.

The action expectations and short reasons are in `expected.json`. They were
committed and pushed in [e20790c](https://github.com/SaaiAravindhRaja/repro-triage-agent/commit/e20790c791329d7217139b23efcffe7f8c682530)
before any run on this set. The original smoke runs in this repository predate
this evaluation and are not part of its score. A later event-time snapshot
would require new cases and a new pre-run gold commit.

`development_runs.json` keeps an earlier run on a copy of one frozen case.
That run finished green and posted a useful comment, but only suggested the
label, so it failed the intended action. The corrected workflow was tried on
12 copies in [`../pilot/`](../pilot/). Review of an earlier comment-only
[run on #14](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/14)
then exposed a retry edge case. The pilot also made a false API claim in a
bot comment. A later [12-run pass](../revision1/) tested the retry fix but
found infrastructure failures and repeated that false claim.
[Two serial probes](../detector-probes/) then showed the default detector
alias could fail even without concurrent runs; it was replaced with an
explicit model. These runs are development evidence, not the final score. The final
configuration uses fresh copies and a later commit. Because the same frozen
cases were reused after a general skill fix, this is a regression check, not
an independent holdout or an estimate of production accuracy.

## Sandbox execution and comparison

The inputs are copied without added instructions into fresh issues in
`SaaiAravindhRaja/repro-triage-agent`. `sandbox_issues.json` maps final case
IDs to those issue URLs. The default-branch issue workflow was disabled while
copies were created to avoid firing an older configuration, then re-enabled.
The configured branch workflow was manually dispatched with each issue number
and the full source commit SHA, recorded in `dispatched.json`; the preflight
checks that the SHA matches the checkout. The workflow's comment and label
targets are the selected issue. At evaluation time `assignment3-submission`
was not the default branch, so these runs do not test automatic issue-open
activation or role enforcement. The workflow was disabled after the last
scored run. It was later re-enabled on `main` with `roles: [admin]` and a
main-only approval environment; that deployment is not part of the score, and
neither control has been exercised by a new live run.

`actual.json` records each run URL/SHA/attempt/conclusion, output comment and
label, and a separate judgment of whether a request asked for the right
details. `logs/<case-id>.txt.gz` holds each complete Actions log; the linked
public run is the primary record. `python3 -B evals/verify_trace.py` checks
the tool transcript against the skill at that commit and the frozen issue
body. `python3 -B evals/reproduce.py` checks the pre-registration commit,
configuration SHA, saved observations and manual judgments. Neither command
calls a model, and a correct score here means agreement with this test rule,
not proven benefit in upstream pandas.

To check the original text, run
`python3 -B evals/golden/inputs/_capture_historical.py --verify`. To inspect a
stored log, use `gzip -cd evals/golden/logs/<case-id>.txt.gz`, or open its
public Actions run. A failed replay exits non-zero and prints each mismatch.

The recorded live runs cannot be repeated from their evaluated commit under
the current `main`-only approval-environment policy. Use
`python3 -B evals/reproduce.py` to check the saved comparison without model
usage. A new live check must dispatch the current `main` workflow with its
current full SHA against a fresh sandbox issue; it tests the current config,
not the historical one, and can incur new charges.

The run-time preflight writes gh-aw's `noop` record for a closed or previously
triaged issue. The current gh-aw documentation says a no-op from a custom
pre-agent step exits before inference ([steps and jobs](https://github.github.com/gh-aw/reference/steps-jobs/)).
Unit tests verify the record; the twelve live runs did not exercise that path.
The evaluated `AGENTS.md` described the no-op incorrectly; I corrected it
after the runs.

After the evaluation, I added a human-approval job and updated the compiled
lock. GitHub now has a required reviewer, admin bypass disabled, and a `main`-
only policy for that Environment; self-review is allowed. The setting is
configured but the gate has not been exercised by a workflow run. The
historical runs did not use it. `reproduce.py` checks each recorded run SHA
contains the evaluated files, rather than requiring the current working tree
to remain byte-identical to a historical configuration.
