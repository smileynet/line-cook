"""Test inspect feedback file persistence."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


def make_beads_dir():
    """Create a temporary directory with a .beads subdirectory."""
    tmpdir = tempfile.mkdtemp()
    beads_dir = Path(tmpdir) / ".beads"
    beads_dir.mkdir()
    return Path(tmpdir)


class TestInspectFeedback(unittest.TestCase):
    """Test inspect feedback file persistence."""

    def setUp(self):
        self.mock_root = make_beads_dir()

    def test_feedback_file_not_created_yet(self):
        """Verify feedback file doesn't exist before inspect runs."""
        feedback_dir = self.mock_root / ".beads" / "inspect-feedback"
        feedback_file = feedback_dir / "issue-42.json"
        self.assertFalse(feedback_file.exists())

    def test_feedback_can_be_written(self):
        """Verify feedback file can be written with correct structure."""
        feedback_dir = self.mock_root / ".beads" / "inspect-feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)

        feedback = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "MERGE",
            "dimensions": {
                "what_changed": "Added null check before array access",
                "project_value": "Prevents crash on empty input",
                "issue_validity": "Valid bug with clear reproduction",
                "intent_alignment": "Fix matches issue description",
                "scope": "Single file, minimal change",
                "security": "No security concerns",
                "code_quality": "Clean, follows conventions",
                "root_cause_depth": "Root cause fix"
            },
            "rationale": "Ready to merge - valid fix with no concerns",
            "reviewed_at": datetime.now().isoformat()
        }

        # Write atomically via temp file
        feedback_file = feedback_dir / "issue-42.json"
        temp_file = feedback_dir / "issue-42.json.tmp"
        temp_file.write_text(json.dumps(feedback, indent=2))
        temp_file.rename(feedback_file)

        # Verify file exists and is valid
        self.assertTrue(feedback_file.exists())
        loaded = json.loads(feedback_file.read_text())
        self.assertEqual(loaded["verdict"], "MERGE")
        self.assertEqual(loaded["issue_number"], 42)
        self.assertEqual(loaded["pr_number"], 7)
        self.assertEqual(len(loaded["dimensions"]), 8)

    def test_feedback_structure_requirements(self):
        """Document required feedback file structure."""
        required_schema = {
            "issue_number": "int - GitHub issue number",
            "pr_number": "int - GitHub PR number",
            "verdict": "str - MERGE|POLISH|FEEDBACK|REWORK|REJECT",
            "dimensions": {
                "what_changed": "str - 2-3 sentences",
                "project_value": "str - 2-3 sentences",
                "issue_validity": "str - 1-2 sentences",
                "intent_alignment": "str - 1-2 sentences",
                "scope": "str - 1-2 sentences",
                "security": "str - 1-2 sentences",
                "code_quality": "str - 1-2 sentences",
                "root_cause_depth": "str - 1-2 sentences"
            },
            "rationale": "str - 1 paragraph verdict explanation",
            "reviewed_at": "str - ISO 8601 timestamp"
        }

        self.assertIn("issue_number", required_schema)
        self.assertIn("verdict", required_schema)
        self.assertIn("dimensions", required_schema)
        self.assertEqual(len(required_schema["dimensions"]), 8)


if __name__ == "__main__":
    unittest.main()
