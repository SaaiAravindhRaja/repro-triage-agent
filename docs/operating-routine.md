# Sandbox operating routine

This is the current operating plan for the personal CS467 sandbox. It is not a
deployment plan for pandas and does not make the untested controls tested.

## Owner and separation of duties

Saai Aravindh Raja is the repository owner and workflow configuration owner.
He can change or disable the workflow, cancel a run, and rotate the repository
secret. He is also the current Environment reviewer, so he approves or rejects
the staged output. This is a real human check, but not independent separation
in a single-owner sandbox. A production deployment would name a maintainer who
does not control the workflow configuration.

## Before approving an output

The owner checks the issue, the agent artifact, the detector result, and the
proposed comment/label. Approve only a request that identifies missing details
from that issue and stays within the one-comment, one-`needs-repro` limit.
Reject a redundant, unsupported or misleading request. The Environment gate is
after inference, so rejection prevents publication but does not refund credits.

## Before a model or configuration change

The owner first disables the workflow, reviews the source and compiled lock,
and runs `gh aw compile smoke-triage --no-emit`, the unit suite, and the saved
evaluation replay. A new live comparison uses fresh sandbox issues and the
current `main` SHA; it is not a rerun of the historical score and incurs model
credits. Review every resulting action and comment against
[`comment-quality-review.md`](../evals/golden/comment-quality-review.md) before
re-enabling the workflow.

Do not use GitHub's **Re-run jobs** button after a failed attempt. Preflight
deliberately rejects any attempt after the first so that a replay cannot inherit
the original actor's admission. After checking the issue for partial output,
handle it manually; the deployed workflow accepts issue-open events only.

## Monthly check and incident response

The same fresh-copy comparison is the proposed monthly drift check. It is
manual and deliberately unscheduled because the current workflow is a bounded
course sandbox with paid inference. Record the model alias, commit SHA, action
result, credit cost, and any wording failure; pause the workflow if a decision,
tool sequence, or output quality changes materially.

For an incident, disable the workflow in GitHub Actions, cancel queued and
running jobs, inspect the affected issue and run artifacts, then rotate the
secret if account or token compromise is suspected. Cancellation of an
approval-queued run was exercised during the control check; the phone-only
version of this sequence remains documented rather than separately tested.
