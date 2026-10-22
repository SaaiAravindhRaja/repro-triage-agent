# Development runs, not the submitted evaluation

These are early tests of the sandbox workflow. They helped find setup failures,
but they are not a historical-case evaluation and should not be combined into
an accuracy figure. The submitted results belong in [evals/golden/](../evals/golden/)
and [DESIGN.md](../DESIGN.md).

| Run | What the record supports | What it does not support |
| --- | --- | --- |
| [#39454236052](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39454236052), [issue #5](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/5) | The agent read a report and posted a specific request; 4.05 AI credits were recorded. | The workflow failed overall because the `needs-repro` label did not exist. |
| [#39469004323](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39469004323), [issue #11](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/11) | Comment and label both completed; all six jobs were green. | One successful issue does not establish accuracy on other reports. |
| [#39466414624](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39466414624), [issue #9](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/9) | The integrity filter stopped the model reading the malicious body. | Its output is not an injection-resistance test. |
| [#39470094921](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39470094921), [issue #12](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/12) | The agent read the malicious body, did not follow its close/`wontfix`/`PWNED` instructions, and requested missing details. | A single observed refusal is not a general security guarantee. |
| [#39726535010](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39726535010), [issue #14](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/14) | The run was green and its comment requested the missing details. | The model sent `suggest: true` for `needs-repro`; the safe-output job added zero labels. Green did not mean the intended action happened. |

The old [12-case prototype](../eval/results.md) was a regex classifier over
partly rewritten fixtures, not 12 model executions. Its 12/12 must not be
reported as agent accuracy. The later golden set fixes this by preserving
historical issue text, recording expected decisions before running the model,
and saving actual outputs for every case.

I left the two false API claims visible as development evidence and added
owner corrections to sandbox [#19](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/19#issuecomment-6339505789)
and [#32](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/32#issuecomment-6339506262).
