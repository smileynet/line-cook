#!/usr/bin/env python3
"""Test that issue-agent surfaces confidence score in Path B."""

import unittest
from pathlib import Path


class TestIssueAgentConfidence(unittest.TestCase):
    """Test issue-agent confidence scoring in template."""

    def setUp(self):
        self.template_path = Path("core/templates/agents/issue-agent.md.template")

    def test_confidence_assessment_step_exists(self):
        """Verify issue-agent template includes confidence assessment."""
        self.assertTrue(self.template_path.exists(), "issue-agent template not found")

        content = self.template_path.read_text()
        self.assertIn("confidence", content.lower(),
                       "Template should include confidence assessment")

        lines = content.split("\n")
        step4_line = None
        step5_line = None
        confidence_line = None

        for i, line in enumerate(lines):
            if "### Step 4:" in line:
                step4_line = i
            if "### Step 5:" in line:
                step5_line = i
            if "confidence" in line.lower() and "###" in line:
                confidence_line = i

        self.assertIsNotNone(step4_line, "Step 4 not found")
        self.assertIsNotNone(step5_line, "Step 5 not found")
        self.assertIsNotNone(confidence_line, "Confidence assessment step not found")
        self.assertLess(step4_line, confidence_line,
                        "Confidence should be after Step 4")
        self.assertLess(confidence_line, step5_line,
                        "Confidence should be before Step 5")

    def test_path_b_includes_confidence(self):
        """Verify Path B comment template includes confidence indicator."""
        content = self.template_path.read_text()
        lines = content.split("\n")
        path_b_start = None

        for i, line in enumerate(lines):
            if "**Path B" in line and "no fix" in line.lower():
                path_b_start = i
                break

        self.assertIsNotNone(path_b_start, "Path B comment template not found")

        path_b_section = "\n".join(lines[path_b_start:path_b_start + 30])
        self.assertIn("confidence", path_b_section.lower(),
                       "Path B comment should include confidence indicator")
        self.assertIn("**", path_b_section,
                       "Path B comment should use markdown formatting for confidence")

    def test_confidence_levels_defined(self):
        """Verify confidence levels are clearly defined."""
        content = self.template_path.read_text()
        content_lower = content.lower()
        self.assertTrue(
            "high" in content_lower or "low" in content_lower,
            "Template should define confidence levels"
        )


if __name__ == "__main__":
    unittest.main()
