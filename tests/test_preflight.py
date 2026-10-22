from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import preflight


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "not-created-yet" / "outputs.jsonl"
        self.environment = {
            "TRIAGE_ISSUE_NUMBER": "41",
            "TRIAGE_REPOSITORY": "SaaiAravindhRaja/repro-triage-agent",
            "GITHUB_EVENT_NAME": "issues",
            "GH_AW_SAFE_OUTPUTS": str(self.output),
        }

    def run_case(self, issue: dict, comments: list | None = None) -> None:
        responses = [{"name": "needs-repro"}, issue]
        if comments is not None:
            responses.append(comments)
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get", side_effect=responses):
                preflight.main()

    def test_fresh_issue_passes_to_agent_without_output(self) -> None:
        self.run_case({"number": 41, "state": "open", "labels": []}, [])
        self.assertFalse(self.output.exists())

    def test_label_without_bot_comment_fails_visibly(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "partial triage state"):
            self.run_case(
                {"number": 41, "state": "open", "labels": [{"name": "needs-repro"}]},
                [],
            )
        self.assertFalse(self.output.exists())

    def test_prior_comment_without_label_fails_visibly(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "partial triage state"):
            self.run_case(
                {"number": 41, "state": "open", "labels": []},
                [{"user": {"login": "github-actions[bot]"}, "body": preflight.WORKFLOW_MARKER}],
            )
        self.assertFalse(self.output.exists())

    def test_completed_prior_triage_short_circuits_agent(self) -> None:
        self.run_case(
            {"number": 41, "state": "open", "labels": [{"name": "needs-repro"}]},
            [{"user": {"login": "github-actions[bot]"}, "body": preflight.WORKFLOW_MARKER}],
        )
        self.assertEqual(json.loads(self.output.read_text())["type"], "noop")

    def test_reporter_cannot_spoof_a_prior_bot_comment(self) -> None:
        self.run_case(
            {"number": 41, "state": "open", "labels": []},
            [{"user": {"login": "reporter"}, "body": preflight.WORKFLOW_MARKER}],
        )
        self.assertFalse(self.output.exists())

    def test_pull_request_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "pull request"):
            self.run_case(
                {"number": 41, "state": "open", "labels": [], "pull_request": {}}
            )

    def test_manual_ref_mismatch_is_rejected(self) -> None:
        self.environment.update(
            {
                "GITHUB_EVENT_NAME": "workflow_dispatch",
                "TRIAGE_SOURCE_SHA": "a" * 40,
                "GITHUB_SHA": "b" * 40,
            }
        )
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight.subprocess, "check_output", return_value="b" * 40):
                with self.assertRaisesRegex(RuntimeError, "does not match"):
                    preflight.main()


if __name__ == "__main__":
    unittest.main()
