# Development pass on the frozen cases

These 12 runs used configuration `adfd985e66514da54677ba4ce7e987f377d115ed`.
All completed and their observed output types matched `../golden/expected.json`.
That is not a comment-quality result: the [#19 comment](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/19#issuecomment-6333490832)
incorrectly said `DataFrame.select` and `pd.col` were not pandas APIs.
They are **not** the final score: the preflight at that commit treated a
comment-only or label-only partial write as already triaged. Issue
[#14](https://github.com/SaaiAravindhRaja/repro-triage-agent/issues/14)
demonstrated the comment-only state in an earlier run. I changed preflight to
fail visibly on either partial state, then ran the final evaluation on fresh
issues at the revised commit. The public run URLs and issue IDs are in
`dispatched.json` and `sandbox_issues.json`; `actual.json` records what each
pilot run did. The logs are kept for diagnosis, not mixed into the final score.
