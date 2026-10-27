# Repository instructions

This is a sandbox for an issue-triage workflow, not a pandas checkout. The
agent comments only on incomplete bug reports in this repository.

## Structure and commands

- `.github/workflows/smoke-triage.md` is the source workflow. Compile it with
  `gh aw compile smoke-triage`; commit the generated `.lock.yml` with changes.
- `.claude/skills/repro-triage/SKILL.md` is the triage procedure. It is read at
  the explicit `source_sha` on manual runs, or from the default branch on issue
  events. Preflight checks that the manual SHA matches the checkout.
- `scripts/preflight.py` validates the target and writes a `noop` for closed
  or already-triaged issues. In gh-aw 0.92.0, a no-op written by a pre-agent
  step short-circuits inference. This path has unit coverage, not a live run.
  Partial triage states fail closed. The script uses only the Python standard
  library.
- `evals/golden/` holds historical inputs, expected decisions, actual outputs,
  and run evidence. Do not use the older `eval/agent_eval.py` classifier as
  evidence of an LLM run.
- Check source syntax with `gh aw compile smoke-triage --no-emit`. No package
  build or installation is needed for this repository.
- Run local tests with `python3 -B -m unittest discover -s tests -v`.
- Recheck the saved evaluation with `python3 -B evals/reproduce.py`.

## Conventions

Use a fresh sandbox issue for each independent evaluation run. Record expected
outcomes before running the agent. Cite the upstream issue as evidence, but
never write to it.
Keep source and compiled workflow in sync; inspect the compiled permissions
and safe-output targets after each compile.
The `safe_outputs` and `conclusion` jobs require success from the
`triage-output-approval` GitHub Environment job. Keep its required reviewer
and `main`-only policy; admin bypass is disabled. The enabled
issue trigger is restricted to repository admins. This is a sandbox, not an
upstream pandas deployment. The approval gate has not been exercised by a
post-activation workflow run.

## Forbidden changes

Do not close or delete issues, merge pull requests, force-push, or give the
agent direct write tools. Do not put secrets in source, logs, or issue bodies.
Do not broaden the GitHub repository allowlist or safe-output types without
reviewing the resulting permissions and threat model.
