# Failure modes and limits

- **Unreadable issue or skill:** A failed model-tool read should report an
  incomplete run, with no comment or label. [An early run](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39466414624)
  could not read an issue body. A preflight GitHub API failure instead exits
  before inference and produces no public output. Neither is a successful triage.
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
- **Approval configuration:** The current lock requires success from the
  `triage-output-approval` Environment job before safe outputs and conclusion.
  GitHub Settings has the repository owner as required reviewer, admin bypass disabled, and a
  `main`-only policy. Self-review is allowed. Issue #54 exercised approval;
  rejection remains untested, and a no-action run may wait for review too.
- **Trigger scope:** `on.roles: [admin]` blocks ordinary public reporters
  before inference. This limits public-trigger spend but means the sandbox
  does not triage community reports. The role check is not live-tested.
- **Preflight no-op:** Closed and already-triaged issues write a `noop` before
  the model step. gh-aw documents this as an inference short-circuit; unit tests
  and a later pre-removal manual run checked it. The historical live cases did not exercise
  it, so its effect on that scored set remains unmeasured.
- **Volume and drift:** The daily credit cap can leave work unfinished during
  a burst. The requested model name is mutable. Neither a 300-issue week nor
  provider updates can be handled by a 12-case test alone.

[DESIGN.md](../DESIGN.md) separates observed failures in the
[historical evaluation](../evals/golden/) from risks still untested.
