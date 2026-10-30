"""Deterministic checks before starting the issue-triage model.

The API responses are untrusted data. This script reads only fixed fields and
never executes or echoes issue text. Any API failure stops the run.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


WORKFLOW_MARKER = (
    "gh-aw-workflow-call-id: SaaiAravindhRaja/repro-triage-agent/smoke-triage"
)
BOT_LOGIN = "github-actions[bot]"
REPOSITORY = "saaiaravindhraja/repro-triage-agent"
WORKFLOW_FILE = "smoke-triage.lock.yml"
RATE_LIMIT_MAX_RUNS = 2
RATE_LIMIT_WINDOW = timedelta(minutes=60)


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
        raise RuntimeError(
            f"GitHub API returned HTTP {error.code} for {path}"
        ) from None
    except URLError as error:
        raise RuntimeError(
            f"GitHub API unavailable for {path}: {error.reason}"
        ) from None


def no_action(reason: str) -> None:
    path = Path(os.environ["GH_AW_SAFE_OUTPUTS"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps({"type": "noop", "message": reason}) + "\n")
    print(reason)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise RuntimeError("workflow run is missing a created_at timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError("workflow run has an invalid created_at timestamp") from error
    if parsed.tzinfo is None:
        raise RuntimeError("workflow run has a timezone-free created_at timestamp")
    return parsed.astimezone(timezone.utc)


def enforce_global_issue_rate_limit(current_run_id: str) -> None:
    """Fail closed before inference after two issue-triggered starts per hour.

    gh-aw's built-in user limiter exempts repository members. This workflow admits
    only the sandbox owner, so the platform limiter cannot bound its spend. Count
    this workflow's issue-triggered starts directly instead. GitHub has already
    created the current run, but it is excluded so the first two starts are
    admitted and the third is stopped before Codex is invoked.
    """

    payload = api_get(
        f"actions/workflows/{WORKFLOW_FILE}/runs?event=issues&per_page=100"
    )
    if not isinstance(payload, dict):
        raise RuntimeError("workflow-run listing is unavailable")
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise RuntimeError("workflow-run listing is malformed")

    cutoff = now_utc() - RATE_LIMIT_WINDOW
    recent_other_runs = 0
    for run in runs:
        if not isinstance(run, dict):
            raise RuntimeError("workflow-run listing contains an invalid entry")
        run_id = run.get("id")
        if not isinstance(run_id, int):
            raise RuntimeError("workflow run is missing an id")
        created_at = parse_utc(run.get("created_at"))
        if str(run_id) != current_run_id and created_at >= cutoff:
            recent_other_runs += 1

    if recent_other_runs >= RATE_LIMIT_MAX_RUNS:
        raise RuntimeError(
            "global issue rate limit reached: "
            f"{recent_other_runs} other issue-triggered starts in the last 60 minutes"
        )


def main() -> None:
    number = os.environ.get("TRIAGE_ISSUE_NUMBER", "")
    repository = os.environ.get("TRIAGE_REPOSITORY", "").lower()
    if repository != REPOSITORY:
        raise RuntimeError("preflight is restricted to the sandbox repository")
    if os.environ.get("TRIAGE_RUN_ATTEMPT") != "1":
        raise RuntimeError("only the first workflow attempt may triage")
    if not re.fullmatch(r"[1-9][0-9]{0,8}", number):
        raise RuntimeError("issue number must be a positive decimal integer")
    current_run_id = os.environ.get("TRIAGE_RUN_ID", "")
    if not re.fullmatch(r"[1-9][0-9]{0,15}", current_run_id):
        raise RuntimeError("workflow run id must be a positive decimal integer")
    enforce_global_issue_rate_limit(current_run_id)
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
        raise RuntimeError(
            f"issue #{number} has a partial triage state; manual review is needed"
        )


if __name__ == "__main__":
    try:
        main()
    except (KeyError, RuntimeError) as error:
        print(f"preflight failed: {error}", file=sys.stderr)
        sys.exit(1)
