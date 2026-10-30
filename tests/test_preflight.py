from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
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
            "TRIAGE_RUN_ID": "100",
            "TRIAGE_RUN_ATTEMPT": "1",
            "GITHUB_EVENT_NAME": "issues",
            "GH_AW_SAFE_OUTPUTS": str(self.output),
        }

    def run_case(self, issue: dict, comments: list | None = None) -> None:
        responses = [
            {
                "workflow_runs": [
                    {"id": 100, "created_at": "2026-10-30T08:00:00Z"}
                ]
            },
            {"name": "needs-repro"},
            issue,
        ]
        if comments is not None:
            responses.append(comments)
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get", side_effect=responses), patch.object(
                preflight,
                "now_utc",
                return_value=datetime(2026, 10, 30, 8, 30, tzinfo=timezone.utc),
            ):
                preflight.main()

    def test_fresh_issue_produces_no_preflight_output(self) -> None:
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
                [
                    {
                        "user": {"login": "github-actions[bot]"},
                        "body": preflight.WORKFLOW_MARKER,
                    }
                ],
            )
        self.assertFalse(self.output.exists())

    def test_completed_prior_triage_records_noop(self) -> None:
        self.run_case(
            {"number": 41, "state": "open", "labels": [{"name": "needs-repro"}]},
            [
                {
                    "user": {"login": "github-actions[bot]"},
                    "body": preflight.WORKFLOW_MARKER,
                }
            ],
        )
        self.assertEqual(
            json.loads(self.output.read_text()),
            {
                "type": "noop",
                "message": "No action: issue #41 already has a triage comment and label",
            },
        )

    def test_closed_issue_records_noop(self) -> None:
        self.run_case({"number": 41, "state": "closed", "labels": []})
        self.assertEqual(
            json.loads(self.output.read_text()),
            {"type": "noop", "message": "No action: issue #41 is not open"},
        )

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

    def test_rerun_attempt_is_rejected_before_any_api_call(self) -> None:
        self.environment["TRIAGE_RUN_ATTEMPT"] = "2"
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get") as api_get:
                with self.assertRaisesRegex(RuntimeError, "first workflow attempt"):
                    preflight.main()
        api_get.assert_not_called()

    def test_global_rate_limit_blocks_third_recent_issue_before_label_check(self) -> None:
        runs = {
            "workflow_runs": [
                {"id": 98, "created_at": "2026-10-30T08:25:00Z"},
                {"id": 99, "created_at": "2026-10-30T08:20:00Z"},
                {"id": 100, "created_at": "2026-10-30T08:30:00Z"},
            ]
        }
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get", return_value=runs) as api_get, patch.object(
                preflight,
                "now_utc",
                return_value=datetime(2026, 10, 30, 8, 30, tzinfo=timezone.utc),
            ):
                with self.assertRaisesRegex(RuntimeError, "global issue rate limit"):
                    preflight.main()
        api_get.assert_called_once_with(
            "actions/workflows/smoke-triage.lock.yml/runs?event=issues&per_page=100"
        )
        self.assertFalse(self.output.exists())

    def test_global_rate_limit_allows_second_recent_issue(self) -> None:
        responses = [
            {
                "workflow_runs": [
                    {"id": 99, "created_at": "2026-10-30T08:25:00Z"},
                    {"id": 100, "created_at": "2026-10-30T08:30:00Z"},
                ]
            },
            {"name": "needs-repro"},
            {"number": 41, "state": "open", "labels": []},
            [],
        ]
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get", side_effect=responses), patch.object(
                preflight,
                "now_utc",
                return_value=datetime(2026, 10, 30, 8, 30, tzinfo=timezone.utc),
            ):
                preflight.main()
        self.assertFalse(self.output.exists())

    def test_malformed_rate_listing_fails_closed_before_issue_read(self) -> None:
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(preflight, "api_get", return_value={"workflow_runs": [{}]}):
                with self.assertRaisesRegex(RuntimeError, "workflow run is missing an id"):
                    preflight.main()
        self.assertFalse(self.output.exists())

    def test_timezone_free_rate_timestamp_fails_closed(self) -> None:
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(
                preflight,
                "api_get",
                return_value={
                    "workflow_runs": [{"id": 99, "created_at": "2026-10-30T08:30:00"}]
                },
            ):
                with self.assertRaisesRegex(RuntimeError, "timezone-free"):
                    preflight.main()
        self.assertFalse(self.output.exists())

    def test_preflight_api_failure_has_no_public_output(self) -> None:
        with patch.dict(os.environ, self.environment, clear=True):
            with patch.object(
                preflight, "api_get", side_effect=RuntimeError("API unavailable")
            ):
                with self.assertRaisesRegex(RuntimeError, "API unavailable"):
                    preflight.main()
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
