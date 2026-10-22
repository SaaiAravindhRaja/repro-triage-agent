"""Deterministic checks before starting the issue-triage model.

The API responses are untrusted data. This script reads only fixed fields and
never executes or echoes issue text. Any API failure stops the run.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


WORKFLOW_MARKER = "gh-aw-workflow-call-id: SaaiAravindhRaja/repro-triage-agent/smoke-triage"
BOT_LOGIN = "github-actions[bot]"
REPOSITORY = "saaiaravindhraja/repro-triage-agent"


def api_get(path: str) -> object:
    token = os.environ["GH_TOKEN"]
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "repro-triage-preflight",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"GitHub API returned HTTP {error.code} for {path}") from None
    except URLError as error:
        raise RuntimeError(f"GitHub API unavailable for {path}: {error.reason}") from None


def no_action(reason: str) -> None:
    path = Path(os.environ["GH_AW_SAFE_OUTPUTS"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps({"type": "noop", "message": reason}) + "\n")
    print(reason)


def main() -> None:
    number = os.environ.get("TRIAGE_ISSUE_NUMBER", "")
    repository = os.environ.get("TRIAGE_REPOSITORY", "").lower()
    if repository != REPOSITORY:
        raise RuntimeError("preflight is restricted to the sandbox repository")
    if not re.fullmatch(r"[1-9][0-9]{0,8}", number):
        raise RuntimeError("issue number must be a positive decimal integer")
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        source_sha = os.environ.get("TRIAGE_SOURCE_SHA", "")
        if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
            raise RuntimeError("manual dispatch requires a full lowercase commit SHA")
        checkout_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if source_sha != checkout_sha or source_sha != os.environ.get("GITHUB_SHA"):
            raise RuntimeError("manual source SHA does not match the workflow checkout")

    label = api_get("labels/needs-repro")
    if not isinstance(label, dict) or label.get("name") != "needs-repro":
        raise RuntimeError("needs-repro label is unavailable")

    issue = api_get(f"issues/{number}")
    if not isinstance(issue, dict) or issue.get("number") != int(number):
        raise RuntimeError("issue response is missing or inconsistent")
    if "pull_request" in issue:
        raise RuntimeError("target is a pull request, not an issue")
    if issue.get("state") != "open":
        no_action(f"No action: issue #{number} is not open")
        return
    labels = issue.get("labels")
    if not isinstance(labels, list):
        raise RuntimeError("issue labels are unavailable")
    has_label = any(
        isinstance(item, dict) and item.get("name") == "needs-repro" for item in labels
    )

    prior_comment = False
    for page in range(1, 21):
        comments = api_get(f"issues/{number}/comments?per_page=100&page={page}")
        if not isinstance(comments, list):
            raise RuntimeError("issue comments are unavailable")
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            author = comment.get("user")
            body = comment.get("body")
            if (
                isinstance(author, dict)
                and author.get("login") == BOT_LOGIN
                and isinstance(body, str)
                and WORKFLOW_MARKER in body
            ):
                prior_comment = True
                break
        if prior_comment or len(comments) < 100:
            break
    else:
        raise RuntimeError("too many comments to rule out prior triage")

    if prior_comment and has_label:
        no_action(f"No action: issue #{number} already has a triage comment and label")
    elif prior_comment or has_label:
        raise RuntimeError(f"issue #{number} has a partial triage state; manual review is needed")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, RuntimeError) as error:
        print(f"preflight failed: {error}", file=sys.stderr)
        sys.exit(1)
