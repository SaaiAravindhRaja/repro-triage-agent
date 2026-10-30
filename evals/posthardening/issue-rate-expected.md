# Issue-trigger rate check: expected outcomes

This expectation was committed before opening the three sandbox issues below.
All are opened by the repository owner against the workflow at `72a389f`.

| Case | Title | Body | Expected result |
|---|---|---|---|
| one | `rate test one: export fails` | “A scheduled pandas export fails. Expected: a table. Observed: an error.” | Admission succeeds; one staged repro request and one staged `needs-repro` label, both rejected at Environment approval. |
| two | `rate test two: import fails` | “A pandas import fails in a job. Expected: import works. Observed: an error.” | Same as case one. |
| three | `rate test three: parse fails` | “A pandas parse fails. Expected: a DataFrame. Observed: an error.” | Pre-activation rejects the third owner issue-open start within one hour; no agent or detector job begins. |

All three issues remain open and receive no published comment or label. This is a
live control check outside the frozen 12-case score.
