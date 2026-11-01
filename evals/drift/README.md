# Drift detection check

This is the first drift check run after the formal evaluation. It is not a
re-score of the golden set — it uses the same frozen inputs but fresh sandbox
issues at the current `main` configuration, to verify the agent's decisions
have not changed since the original evaluation.

## Pre-registered expectations (written before any run)

Two cases exercise both decision branches:

| Case | Expected action | Rationale |
| --- | --- | --- |
| pandas-71034 | `no_action` | Complete bug report: fenced example imports pandas, observed ParserError, expected C-engine behavior, and concrete pandas/Python/Linux versions. |
| pandas-69436 | `comment_and_label` | Incomplete bug report: fenced snippet uses pd/np/pa without importing them, no explicit expected behavior, and no concrete pandas/Python/OS version block. |

Expectations committed before issues were opened. The original golden-set
decisions for these cases were `no_action` and `comment_and_label` respectively.
A match on both confirms no detectable decision drift at this configuration.
A mismatch on either triggers a full 12-case re-evaluation before re-enabling
the workflow.

## Who reviews and what they check

The repository owner (Saai Aravindh Raja) reviews:
- The agent artifact (`agent_output.json`) for each run
- The detector result for each run
- The proposed comment and label (for the `comment_and_label` case) against the
  [quality rubric](../golden/comment-quality-review.md): specificity, no
  redundant requests, courteous tone
- The action type against the pre-registered expectation above

The owner approves or rejects the Environment gate after inspection. A rejected
run publishes no output and counts as a quality failure, not a workflow failure.

## Results

### First attempt — blocked by preflight rate limiter (expected behaviour)

Issues #58 (pandas-71034) and #59 (pandas-69436) were opened at 2026-11-01T07:13 UTC.
Both triggered runs immediately:
- [Run 41283887656](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/41283887656) — issue #58
- [Run 41283887357](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/41283887357) — issue #59

Both failed at the `Check label and prior triage` preflight step with:
`preflight failed: global issue rate limit reached: 2 other issue-triggered starts in the last 60 minutes`

The cause: a non-admin test run at 07:02 UTC (run 41283199069) was still within
the 60-minute window, and the two new runs started simultaneously — counting as
3 issue-triggered starts total. The preflight blocked both before any model work.
This is the rate limiter working as designed.

**No model was invoked and no output was produced on either issue.**

### Second attempt — pending

The rate limit window clears at 08:03 UTC. Fresh issues will be opened then.
Results will be recorded here after completion.

