"""Capture exact, unedited pandas issue inputs for the frozen evaluation set.

Run once with GitHub CLI authentication to create missing JSON fixtures, or run
with --verify to compare saved title/body and edit history with the live source.
The gold decisions are maintained separately in ../expected.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ISSUES = (71034, 71173, 69462, 70256, 69436, 69412, 68009, 69014, 71142, 70876, 71163)
REPOSITORY = "pandas-dev/pandas"
GRAPHQL = """query($number:Int!) {
  repository(owner:"pandas-dev", name:"pandas") {
    issue(number:$number) {
      number createdAt lastEditedAt
      userContentEdits(first:1) { totalCount }
      timelineItems(first:1, itemTypes:[RENAMED_TITLE_EVENT]) { totalCount }
    }
  }
}"""


def github_json(*args: str) -> dict:
    command = subprocess.run(
        ("gh", "api", *args), check=True, capture_output=True, text=True
    )
    return json.loads(command.stdout)


def issue_fixture(number: int) -> dict:
    issue = github_json(f"repos/{REPOSITORY}/issues/{number}")
    history = github_json("graphql", "-F", f"number={number}", "-f", f"query={GRAPHQL}")
    history_issue = history["data"]["repository"]["issue"]
    assert "pull_request" not in issue, f"#{number} is a PR, not an issue"
    assert issue["number"] == history_issue["number"] == number
    assert issue["created_at"] == history_issue["createdAt"]
    assert history_issue["lastEditedAt"] is None, f"#{number} has a body edit"
    assert history_issue["userContentEdits"]["totalCount"] == 0
    assert history_issue["timelineItems"]["totalCount"] == 0, f"#{number} has a title rename"
    assert isinstance(issue["body"], str) and issue["body"], f"#{number} has no body"

    return {
        "id": f"pandas-{number}",
        "kind": "historical",
        "source": {
            "repository": REPOSITORY,
            "issue_number": number,
            "url": issue["html_url"],
            "api_url": issue["url"],
            "created_at": issue["created_at"],
            "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "last_edited_at": history_issue["lastEditedAt"],
            "content_edit_count": history_issue["userContentEdits"]["totalCount"],
            "title_rename_count": history_issue["timelineItems"]["totalCount"],
            "provenance": "GitHub REST issue title/body; GraphQL confirmed zero content edits and title renames. Later labels and comments excluded.",
        },
        "input": {"title": issue["title"], "body": issue["body"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="check frozen inputs without writing")
    args = parser.parse_args()

    expected_path = Path(__file__).resolve().parents[1] / "expected.json"
    expected = json.loads(expected_path.read_text())
    expected_ids = {item["id"] for item in expected["cases"] if item["id"].startswith("pandas-")}
    assert expected_ids == {f"pandas-{number}" for number in ISSUES}

    destination = Path(__file__).resolve().parent
    fixtures = [issue_fixture(number) for number in ISSUES]
    for fixture in fixtures:
        path = destination / f"{fixture['id']}.json"
        if args.verify:
            saved = json.loads(path.read_text())
            assert saved["input"] == fixture["input"], f"{path.name} source text changed"
            assert saved["source"]["created_at"] == fixture["source"]["created_at"]
        else:
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite frozen input: {path}")
            path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n")
        print(f"{'verified' if args.verify else 'captured'} {fixture['id']}")


if __name__ == "__main__":
    main()
