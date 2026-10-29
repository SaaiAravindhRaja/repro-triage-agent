"""Regression checks for the two GitHub Actions log formats seen in this evaluation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))
from verify_trace import (  # noqa: E402
    SKILL,
    SKILL_DIRECTORY,
    agent_calls,
    credit,
    validate_file_reads,
)


class TraceParserTests(unittest.TestCase):
    def test_completed_call_survives_unknown_step_label(self) -> None:
        log = (
            "agent\tUNKNOWN STEP\t2026-10-22T06:09:13Z "
            '{"type":"item.completed","item":{"type":"mcp_tool_call",'
            '"server":"safeoutputs","tool":"noop"}}\n'
            "agent\tUNKNOWN STEP\t2026-10-22T06:09:14Z "
            '{"type":"other","unrelated":"truncated\n'
        )
        self.assertEqual([call["tool"] for call in agent_calls(log)], ["noop"])

    def test_credits_use_job_not_step_label(self) -> None:
        log = (
            "agent\tUNKNOWN STEP\t2026-10-22T06:09:30Z AI Credits: 4.4962\n"
            "detection\tUNKNOWN STEP\t2026-10-22T06:10:33Z AI Credits: 0.546725\n"
        )
        self.assertEqual(credit(log, "agent"), 4.4962)
        self.assertEqual(credit(log, "detection"), 0.546725)

    def test_fixture_read_is_rejected(self) -> None:
        calls = [
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": "evals/golden/expected.json"},
            }
        ]
        with self.assertRaisesRegex(ValueError, "Unexpected repository file read"):
            validate_file_reads(calls)

    def test_directory_then_skill_read_is_allowed(self) -> None:
        calls = [
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": SKILL_DIRECTORY},
            },
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": SKILL},
            },
        ]
        validate_file_reads(calls)

    def test_third_repository_file_read_is_rejected(self) -> None:
        calls = [
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": SKILL_DIRECTORY},
            },
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": SKILL},
            },
            {
                "server": "github",
                "tool": "get_file_contents",
                "arguments": {"path": SKILL},
            },
        ]
        with self.assertRaisesRegex(ValueError, "Too many repository file reads: 3"):
            validate_file_reads(calls)


if __name__ == "__main__":
    unittest.main()
