# Failure modes and limits

- **Unreadable issue or skill:** The agent should report an incomplete run,
  with no comment or label. [An early run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39466414624)
  could not read an issue body. That was not a successful triage.
- **False request for details:** A strict requirement for runnable code and
  full environment data may bother a reporter whose issue is already clear
  enough to investigate. Later work on [pandas #69412](https://github.com/pandas-dev/pandas/issues/69412#issuecomment-5784836367)
  and [#69436](https://github.com/pandas-dev/pandas/issues/69436#issuecomment-5804717944)
  illustrates the possible cost; those later replies must not be shown to the
  agent as event-time input.
- **Wrong public output:** The safe-output limit bounds quantity and type,
  not truth. One misplaced comment or label still consumes maintainer time.
  A green Actions run does not prove the decision was right.
- **Prompt injection or malicious tool text:** Closing issues and executing
  shell commands are outside the configured outputs and tools. A malicious
  input can still distort an allowed comment or label; the constructed case
  tests one route, not every attack.
- **Volume and drift:** The daily credit cap can leave work unfinished during
  a burst. The requested model name is mutable. Neither a 300-issue week nor
  provider updates can be handled by a 12-case test alone.

[DESIGN.md](../DESIGN.md) separates observed failures in the
[historical evaluation](../evals/golden/) from risks still untested.
