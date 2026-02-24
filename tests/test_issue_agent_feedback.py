#!/usr/bin/env python3
"""Test that issue-agent reads inspect feedback on re-trigger."""

import unittest
from pathlib import Path


class TestIssueAgentFeedback(unittest.TestCase):
    """Test issue-agent feedback reading from inspect results."""

    def setUp(self):
        self.template_path = Path("core/templates/agents/issue-agent.md.template")

    def test_issue_agent_reads_feedback(self):
        """Verify issue-agent template includes feedback reading step."""
        self.assertTrue(self.template_path.exists(), "issue-agent template not found")

        content = self.template_path.read_text()

        self.assertIn(".beads/inspect-feedback", content,
                       "Template should reference .beads/inspect-feedback directory")
        self.assertTrue(
            "issue-{{ISSUE_NUMBER}}.json" in content or "issue-$" in content,
            "Template should reference feedback file by issue number"
        )

        lines = content.split("\n")
        feedback_line = None
        classify_line = None

        for i, line in enumerate(lines):
            if "inspect-feedback" in line.lower():
                feedback_line = i
            if "### Step 2: Classify" in line:
                classify_line = i

        self.assertIsNotNone(feedback_line, "Feedback reading not found in template")
        self.assertIsNotNone(classify_line, "Classification step not found")
        self.assertLess(feedback_line, classify_line,
                        "Feedback reading should happen before classification")

    def test_feedback_file_format(self):
        """Verify feedback file format is referenced in issue-agent template."""
        content = self.template_path.read_text()

        self.assertIn("verdict", content.lower(), "Template should reference verdict")
        self.assertIn("dimensions", content.lower(), "Template should reference dimensions")
        self.assertIn("rationale", content.lower(), "Template should reference rationale")


if __name__ == "__main__":
    unittest.main()
