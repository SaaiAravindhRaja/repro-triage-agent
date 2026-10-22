# Detector alias probes

These were sequential, first-attempt runs at
[`4453905`](https://github.com/SaaiAravindhRaja/repro-triage-agent/commit/4453905fb15b4e4f830536a7cf6ebb9e48bb3c7c)
on fresh sandbox issues. They are development evidence, not the final score.

- [Run 39730488990](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39730488990)
  read [issue #51](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/51)
  and correctly chose no action. Detection then failed with
  `unknown_model_ai_credits` for the default `detection` model alias; the
  workflow failed closed.
- [Run 39730920772](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39730920772)
  read [issue #40](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/40)
  and finished green with no action. The alias failure was intermittent even
  without concurrent evaluations.

`actual.json`, `dispatched.json`, and compressed logs retain the observations.
The [detector project's documentation](https://github.com/github/gh-aw-threat-detection/blob/main/README.md#ai-credits-and-token-usage)
describes this Codex alias failure. The next configuration uses explicit
`gpt-5-mini` in the compiled detector job and is evaluated on fresh issues.
