---
name: repro-triage
description: Judge whether a newly opened bug report contains an adequate, runnable reproduction, and name the specific missing pieces when it does not.
---

# repro-triage

When this skill is loaded and used, the FIRST line of the comment you post MUST be exactly:

    REPRO-TRIAGE-SKILL-LOADED

This marker proves to the run log that the skill was read and applied. Put it on its own line, then continue with the triage below it.

## What counts as an adequate reproduction

A bug report is adequately reproducible only when ALL of these hold. Judge them semantically — filled-in fields are not enough:

1. **Runnable minimal example** — a fenced code block that actually imports and exercises the library, not pseudo-code, not a screenshot, not a link with no inline code. A snippet that never imports the library under test is NOT a repro.
2. **Expected vs actual** — the report states what was expected and what actually happened (an error message, wrong value, or crash).
3. **Real version block** — concrete version information (library version, Python/runtime version, OS). Placeholders like `x.y.z`, `latest`, or `<paste here>` do NOT count.

## How to triage

- **Bug report, repro inadequate** → post ONE comment naming each missing item specifically ("no runnable example", "version shows a placeholder, not a real release", "snippet never imports the library"), and apply the `needs-repro` label.
- **Bug report, repro adequate** → post one short comment confirming the repro looks complete; apply NO label.
- **Feature request, question, or already-triaged** → no triage action; post one short comment saying so; apply NO label.

## Hard limits

You may ONLY post one comment and optionally apply the `needs-repro` label. You must never close, delete, edit, merge, or reassign — those capabilities are withheld at the permission layer, not by this text.
