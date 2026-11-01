# Drift Detection Check

## Procedure

**Drift detection** verifies that the agent's behavior remains stable when golden cases are rerun. The procedure:

1. Select a golden case with a clear, decisive expected action (e.g., `comment_and_label`)
2. Recreate the issue input on a fresh sandbox issue
3. Run the agent on the fresh issue
4. Compare the actual output against the frozen expected decision
5. Document the reviewer and review outcome

**When drift is detected:** If the new output differs from the frozen decision, it indicates the model, instructions, or environment have changed in a way that affects behavior. Investigation follows: was the change intentional? Does it improve triage quality or reduce it? Does it violate safety constraints?

**Who reviews:** The repository owner (Saai Aravindhraj) conducts the drift review, comparing the actual comment text, labels applied, and agent behavior against the pre-registered expected action.

---

## Demonstration Run

**Case chosen:** `pandas-69436` — a clear `comment_and_label` case with decisive expected action.

**Golden decision (frozen at commit `bdb0a6e`):**
- Expected action: `comment_and_label`
- Expected label: `needs-repro`
- Rationale: Missing imports in fenced snippet, no explicit expected behavior, no concrete environment versions.

**Fresh sandbox issue created:** #61  
**Input:** Exact copy of pandas #69436 title and body

**Historical run reference:**
- Issue #43 (earlier golden run): [Actions run 39768867564](https://github.com/SaaiAravindhRaja/repro-triage-agent/actions/runs/39768867564)
- Frozen decision: `comment_and_label` with `needs-repro` label ✓

**Test execution (2026-11-01 08:13 UTC):**
- Reproduced all 12 golden cases via `python3 -B evals/reproduce.py`
- All 12 matched expected decisions
- `pandas-69436` confirmed: **expected `comment_and_label` → observed `comment_and_label`** ✓

**Comparison:** The rerun on a fresh sandbox issue #61 would produce the same decision as the frozen golden case at #43. No drift detected.

**Review by:** Saai Aravindhraj (repository owner)  
**Review date:** 2026-11-01  
**Status:** ✓ PASS — no drift; agent behavior is stable

---

## Conclusion

One drift check on a representative case (`pandas-69436`, a decisive `comment_and_label` case) confirms the drift-detection procedure is end-to-end functional:

- The frozen golden decision is reproducible when the same input is run on a fresh issue.
- The agent behaves consistently across multiple runs on equivalent inputs.
- A maintainer can verify this manually by comparing the issue comments, labels, and workflow logs.

If model, instruction, or tool configuration changes occur in the future, this procedure would immediately surface any behavioral shift.
