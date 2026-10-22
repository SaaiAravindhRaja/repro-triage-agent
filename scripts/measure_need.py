#!/usr/bin/env python3
"""Snapshot pandas issue volume for 22 July through 20 October 2026.

Uses GitHub's search API through an authenticated `gh` CLI. The Bug label is
the label at collection time, not necessarily the label at issue creation.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


QUERY = "repo:pandas-dev/pandas is:issue created:2026-07-22..2026-10-20 label:Bug"
OUTPUT = Path(__file__).resolve().parent.parent / "evidence" / "pandas-bug-intake.json"


def search(page: int) -> dict:
    endpoint = f"search/issues?q={quote(QUERY)}&per_page=100&page={page}"
    result = subprocess.run(
        ["gh", "api", endpoint], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def main() -> None:
    first = search(1)
    count = first["total_count"]
    issues = first["items"]
    for page in range(2, (count + 99) // 100 + 1):
        issues.extend(search(page)["items"])
    if len(issues) != count:
        raise RuntimeError(f"Search count changed during collection: {count} vs {len(issues)}")
    rows = [
        {
            "number": issue["number"],
            "url": issue["html_url"],
            "created_at": issue["created_at"],
            "labels_at_collection": [label["name"] for label in issue["labels"]],
        }
        for issue in issues
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "query": QUERY,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "total_count": count,
                "limitation": "Labels reflect collection time, not creation time; GitHub search is mutable.",
                "issues": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved {count} issues to {OUTPUT}")


if __name__ == "__main__":
    main()
