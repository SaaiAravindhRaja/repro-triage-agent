# Repository instructions

This is a sandbox for an issue-triage workflow, not a pandas checkout. The
agent comments only on incomplete bug reports in this repository.

## Structure and commands

- `.github/workflows/smoke-triage.md` is the source workflow. Compile it with
  `gh aw compile smoke-triage`; commit the generated `.lock.yml` with changes.
- `.claude/skills/repro-triage/SKILL.md` is the triage procedure. It is read
  from the default branch on an admitted issue-open event.
- `scripts/preflight.py` rejects reruns, validates the target, limits the third
  issue-triggered start in an hour before inference, and writes a `noop` for closed
  or already-triaged issues. Handle a partial output manually; do not rerun the same issue.
  In gh-aw 0.92.0, a no-op written by a pre-agent
  step short-circuits inference. It has unit coverage and a live manual check on issue #54.
  Partial triage states fail closed. The script uses only the Python standard
  library.
- `evals/golden/` holds historical inputs, expected decisions, actual outputs,
  and run evidence. Do not use the older `eval/agent_eval.py` classifier as
  evidence of an LLM run.
- `evals/golden/inputs/` is a frozen evidence snapshot. Do not edit or
  autoformat it; `evals/reproduce.py` checks it against the preregistration
  commit.
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
`triage-output-approval` GitHub Environment job. Keep its required reviewer,
`main`-only policy, and disabled admin bypass. The enabled issue trigger is
restricted to repository admins. This is a sandbox, not an upstream pandas
deployment. Issue #54 exercised the approval gate after agent and detection;
issue #55 exercised Environment rejection with no public output.

## Forbidden changes

Do not close or delete issues, merge pull requests, force-push, or give the
agent direct write tools. Do not put secrets in source, logs, or issue bodies.
Do not broaden the GitHub repository allowlist or safe-output types without
reviewing the resulting permissions and threat model.
