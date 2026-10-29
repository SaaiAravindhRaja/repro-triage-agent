from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".github/workflows/smoke-triage.md"
LOCK = ROOT / ".github/workflows/smoke-triage.lock.yml"
APPROVAL_CONDITION = "needs.triage-output-approval.result == 'success'"
LOCK_CONDITIONS = {
    "safe_outputs": (
        "((!cancelled()) && needs.agent.result != 'skipped' && "
        "needs.detection.result == 'success') && "
        "(needs.triage-output-approval.result == 'success')"
    ),
    "conclusion": (
        "(always() && (needs.agent.result != 'skipped' || "
        "needs.activation.outputs.lockdown_check_failed == 'true' || "
        "needs.activation.outputs.oauth_token_check_failed == 'true' || "
        "needs.activation.outputs.stale_lock_file_failed == 'true' || "
        "needs.activation.outputs.secret_verification_result == 'failed' || "
        "needs.activation.outputs.daily_ai_credits_exceeded == 'true' || "
        "needs.activation.outputs.daily_ai_credits_guardrail_status == 'structural_error' || "
        "needs.activation.outputs.daily_ai_credits_guardrail_status == 'transient_error')) && "
        "(needs.triage-output-approval.result == 'success')"
    ),
}


class WorkflowGateTests(unittest.TestCase):
    @staticmethod
    def strip_comment(line: str) -> str:
        quote = None
        escaped = False
        for index, char in enumerate(line):
            if escaped:
                escaped = False
            elif char == "\\" and quote == '"':
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in ("'", '"'):
                quote = char
            elif char == "#" and (index == 0 or line[index - 1].isspace()):
                return line[:index].rstrip()
        return line

    @classmethod
    def active_lines(cls, text: str) -> str:
        return "\n".join(
            cleaned
            for line in text.splitlines()
            if (cleaned := cls.strip_comment(line)).strip()
        )

    def job_block(self, text: str, job: str) -> str:
        active = self.active_lines(text)
        match = re.search(
            rf"(?ms)^  {re.escape(job)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)",
            active,
        )
        self.assertIsNotNone(match, f"active {job} job is missing")
        assert match is not None
        return match.group(1)

    def test_source_and_lock_gate_every_writing_job_on_approval(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        lock = LOCK.read_text(encoding="utf-8")
        frontmatter = re.search(r"(?s)\A---\s*\n(.*?)\n---\s*", source)
        self.assertIsNotNone(frontmatter, "workflow frontmatter is missing")
        assert frontmatter is not None

        approval_source = self.job_block(frontmatter.group(1), "triage-output-approval")
        approval_lock = self.job_block(lock, "triage-output-approval")
        self.assertRegex(
            approval_source,
            r"(?m)^    environment: triage-output-approval$",
        )
        self.assertRegex(
            approval_lock,
            r"(?m)^    environment: triage-output-approval$",
        )

        for name in ("safe_outputs", "conclusion"):
            source_job = self.job_block(frontmatter.group(1), name)
            lock_job = self.job_block(lock, name)
            self.assertRegex(
                source_job,
                rf"(?m)^    if: {re.escape(APPROVAL_CONDITION)}$",
            )
            needs = re.search(
                r"(?ms)^    needs:\n(.*?)(?=^    [A-Za-z0-9_-]+:|\Z)", lock_job
            )
            condition = re.search(
                r"(?ms)^    if:\s*(.*?)(?=^    [A-Za-z0-9_-]+:|\Z)", lock_job
            )
            self.assertIsNotNone(needs, f"compiled {name} dependencies are missing")
            self.assertIsNotNone(condition, f"compiled {name} condition is missing")
            assert needs is not None and condition is not None
            self.assertIn("- triage-output-approval", needs.group(1))
            condition_value = condition.group(1).strip()
            if condition_value.startswith(">"):
                condition_value = condition_value[1:]
            self.assertEqual(" ".join(condition_value.split()), LOCK_CONDITIONS[name])

    def test_source_and_compiled_workflow_restrict_issue_trigger_to_admins(
        self,
    ) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        lock = LOCK.read_text(encoding="utf-8")
        frontmatter = re.search(r"(?s)\A---\s*\n(.*?)\n---\s*", source)
        self.assertIsNotNone(frontmatter, "workflow frontmatter is missing")
        assert frontmatter is not None

        self.assertRegex(frontmatter.group(1), r"(?m)^  roles: \[admin\]$")
        pre_activation = self.job_block(lock, "pre_activation")
        activation = self.job_block(lock, "activation")
        self.assertRegex(
            pre_activation,
            r'(?m)^          GH_AW_REQUIRED_ROLES: "admin"$',
        )
        self.assertIn(
            "activated: ${{ steps.check_membership.outputs.is_team_member == 'true' "
            "&& steps.check_rate_limit.outputs.rate_limit_ok == 'true' }}",
            pre_activation,
        )
        self.assertNotIn("GH_AW_RATE_LIMIT_IGNORED_ROLES", pre_activation)
        self.assertRegex(activation, r"(?m)^    needs: pre_activation$")
        self.assertRegex(
            activation,
            r"(?m)^    if: needs\.pre_activation\.outputs\.activated == 'true'$",
        )

    def test_source_limits_repository_file_reads_to_two(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        frontmatter = re.search(r"(?s)\A---\s*\n(.*?)\n---\s*", source)
        self.assertIsNotNone(frontmatter, "workflow frontmatter is missing")
        assert frontmatter is not None
        self.assertRegex(
            frontmatter.group(1),
            r"(?m)^      - name: get_file_contents\n        max-calls: 2$",
        )

    def test_source_and_lock_disable_diagnostic_issue_creation(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        lock = LOCK.read_text(encoding="utf-8")
        frontmatter = re.search(r"(?s)\A---\s*\n(.*?)\n---\s*", source)
        self.assertIsNotNone(frontmatter, "workflow frontmatter is missing")
        assert frontmatter is not None

        for key in ("missing-tool", "missing-data"):
            self.assertRegex(
                frontmatter.group(1),
                rf"(?m)^  {re.escape(key)}:\n    create-issue: false$",
            )
        conclusion = self.job_block(lock, "conclusion")
        self.assertRegex(
            conclusion, r'(?m)^          GH_AW_MISSING_TOOL_CREATE_ISSUE: "false"$'
        )
        self.assertRegex(
            conclusion, r'(?m)^          GH_AW_FAILURE_REPORT_AS_ISSUE: "false"$'
        )


if __name__ == "__main__":
    unittest.main()
