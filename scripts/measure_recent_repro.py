#!/usr/bin/env python3
"""Collect a fixed, consecutive pandas bug-intake slice without changing GitHub.

The frame is the 22 October 2026 search snapshot, not a fresh search. A later
run can yield different edit status because public issues remain mutable.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRAME = ROOT / "evidence" / "pandas-bug-intake.json"
ANNOTATIONS = ROOT / "evidence" / "pandas-consecutive-30-annotations.json"
DEFAULT_OUTPUT = ROOT / "evidence" / "pandas-consecutive-30-source.json"
ISSUE_FIELDS = """
  number url title body createdAt lastEditedAt author { login }
  userContentEdits(first: 1) { totalCount }
  timelineItems(first: 1, itemTypes: RENAMED_TITLE_EVENT) { totalCount }
"""


def frame_rows() -> list[dict]:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    issues = frame["issues"]
    if frame["total_count"] != len(issues):
        raise ValueError("The saved search frame is incomplete")
    ordered = sorted(issues, key=lambda row: (row["created_at"], row["number"]), reverse=True)
    if len({row["number"] for row in ordered}) != len(ordered):
        raise ValueError("The saved search frame contains duplicate issues")
    return ordered[:30]


def query_batch(batch: list[dict]) -> dict:
    fields = " ".join(
        f'i{row["number"]}: issue(number: {row["number"]}) {{{ISSUE_FIELDS}}}'
        for row in batch
    )
    query = f'query {{ repository(owner: "pandas-dev", name: "pandas") {{ {fields} }} }}'
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if payload.get("errors"):
        raise RuntimeError(f"GraphQL returned errors: {payload['errors']}")
    return payload["data"]["repository"]


def collect() -> dict:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    fixed = frame_rows()
    fetched = {}
    for start in range(0, len(fixed), 10):
        fetched.update(query_batch(fixed[start : start + 10]))
    rows = []
    for base in fixed:
        number = base["number"]
        issue = fetched.get(f"i{number}")
        if issue is None or issue["number"] != number:
            raise RuntimeError(f"Missing or mismatched issue #{number}")
        if issue["createdAt"] != base["created_at"]:
            raise RuntimeError(f"Creation time changed for #{number}")
        if issue["url"] != base["url"]:
            raise RuntimeError(f"URL changed for #{number}")
        edit_count = issue["userContentEdits"]["totalCount"]
        rename_count = issue["timelineItems"]["totalCount"]
        unchanged = issue["lastEditedAt"] is None and edit_count == 0 and rename_count == 0
        rows.append(
            {
                "number": number,
                "url": base["url"],
                "created_at": base["created_at"],
                "labels_at_frame_collection": base["labels_at_collection"],
                "author_login": issue["author"]["login"] if issue["author"] else None,
                "title_at_measurement": issue["title"],
                "body_at_measurement": issue["body"],
                "last_edited_at": issue["lastEditedAt"],
                "body_edit_count": edit_count,
                "title_rename_count": rename_count,
                "opening_text_status": "unchanged" if unchanged else "unknown",
            }
        )
    return {
        "frame": str(FRAME.relative_to(ROOT)),
        "frame_collected_at": frame["collected_at"],
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source_method": "GitHub GraphQL Issue.title/body/createdAt/lastEditedAt/userContentEdits and RENAMED_TITLE_EVENT count; frame is 30 newest by creation time from saved search",
        "caveat": "GitHub search labels were retrospective. Changed or renamed issues are not reconstructed; their opening text is unknown. Later API reads may differ.",
        "issues": rows,
    }


def checked_rows(source: dict, annotations: dict) -> tuple[list[dict], Counter]:
    rows = source["issues"]
    if len(rows) != 30 or [row["number"] for row in rows] != [row["number"] for row in frame_rows()]:
        raise ValueError("Source is not the fixed 30-issue consecutive slice")
    notes = annotations["issues"]
    if set(map(int, notes)) != {row["number"] for row in rows}:
        raise ValueError("Annotations must cover exactly the fixed 30 issues")
    counts: Counter = Counter()
    report_rows = []
    for row in rows:
        unchanged = (
            row["last_edited_at"] is None
            and row["body_edit_count"] == 0
            and row["title_rename_count"] == 0
        )
        if row["opening_text_status"] != ("unchanged" if unchanged else "unknown"):
            raise ValueError(f"Edit status disagrees with public history for #{row['number']}")
        note = notes[str(row["number"])]
        decision = note["decision"]
        if decision not in {"ask", "no_action", "unknown"}:
            raise ValueError(f"Invalid decision for #{row['number']}: {decision}")
        if row["opening_text_status"] != "unchanged" and decision != "unknown":
            raise ValueError(f"Edited or renamed issue #{row['number']} cannot be classified")
        if not note["reason"].strip():
            raise ValueError(f"Missing reason for #{row['number']}")
        counts[decision] += 1
        report_rows.append(
            {
                "number": row["number"],
                "url": row["url"],
                "created_at": row["created_at"],
                "author_login": row["author_login"],
                "opening_text_status": row["opening_text_status"],
                "body_edit_count": row["body_edit_count"],
                "title_rename_count": row["title_rename_count"],
                "decision": decision,
                "reason": note["reason"],
            }
        )
    return report_rows, counts


def summarize(source: dict, annotations: dict, output: Path | None) -> None:
    report_rows, counts = checked_rows(source, annotations)
    authors = Counter(row["author_login"] for row in report_rows)
    edited_or_renamed = sum(row["opening_text_status"] != "unchanged" for row in report_rows)
    print(f"Frame: {source['frame_collected_at']}; read: {source['collected_at']}")
    print(f"Consecutive 30: ask={counts['ask']}; no_action={counts['no_action']}; unknown={counts['unknown']}")
    print(f"Opening text unknown after edit/rename: {edited_or_renamed}; other uncertain judgments: {counts['unknown'] - edited_or_renamed}")
    print(f"Authors: {len(authors)}; largest author share: {authors.most_common(1)[0]}")
    print("Decisions apply the committed skill to recoverable opening text, not observed maintainer actions.")
    if output:
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite saved report: {output}")
        report = {
            "frame_collected_at": source["frame_collected_at"],
            "source_collected_at": source["collected_at"],
            "window_created_at": {
                "oldest": report_rows[-1]["created_at"],
                "newest": report_rows[0]["created_at"],
            },
            "frame": source["frame"],
            "source_file": str(DEFAULT_OUTPUT.relative_to(ROOT)),
            "annotations_file": str(ANNOTATIONS.relative_to(ROOT)),
            "source_method": source["source_method"],
            "review_method": annotations["review_method"],
            "skill_ref": annotations["skill_ref"],
            "skill_path": annotations["skill_path"],
            "counts": {
                "sample": len(report_rows),
                "ask": counts["ask"],
                "no_action": counts["no_action"],
                "unknown": counts["unknown"],
                "opening_text_unknown_after_edit_or_rename": edited_or_renamed,
                "ambiguous_rule_judgment": counts["unknown"] - edited_or_renamed,
                "distinct_authors": len(authors),
                "largest_author_share": authors.most_common(1)[0][1],
            },
            "limitations": [
                "The saved search selected issues with the Bug label at frame collection, not necessarily at creation; this is not all pandas bug intake.",
                "The newest 30 span a short, non-random period and include repeated authors. Do not extrapolate their missing-detail share to all pandas reports.",
                "A current GraphQL body/title was treated as opening text only with no visible body edit and no title rename. Deleted or inaccessible edit records cannot be ruled out.",
                "The decisions are a human application of the skill's completeness rule, not live agent outputs or maintainer decisions; no example was executed.",
                "Missing report details alone do not establish maintainer delay, cost savings, or that the proposed comment would help.",
            ],
            "issues": report_rows,
        }
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved report to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collect", type=Path, metavar="OUTPUT", help="read GitHub and write a source snapshot")
    parser.add_argument("--summarize", action="store_true", help="check saved source and manual annotations")
    parser.add_argument("--report", type=Path, metavar="OUTPUT", help="write a concise joined report (also summarizes)")
    args = parser.parse_args()
    if not args.collect and not args.summarize and not args.report:
        parser.error("choose --collect, --summarize, or --report")
    if args.collect:
        output = args.collect.resolve()
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite saved evidence: {output}")
        source = collect()
        output.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved {len(source['issues'])} issues to {output}")
    if args.summarize or args.report:
        source = json.loads(DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        annotations = json.loads(ANNOTATIONS.read_text(encoding="utf-8"))
        summarize(source, annotations, args.report.resolve() if args.report else None)


if __name__ == "__main__":
    main()
