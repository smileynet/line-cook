"""Test feedback broker functionality."""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add scripts dir for feedback_broker import
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "claude-code" / "scripts"))
from feedback_broker import read_inspect_feedback, read_loop_feedback, synthesize_feedback


def make_broker_dir():
    """Create a temporary directory with .beads feedback subdirectories."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir)
    beads_dir = root / ".beads"
    beads_dir.mkdir()
    (beads_dir / "inspect-feedback").mkdir()
    (beads_dir / "loop-feedback").mkdir()
    (beads_dir / "issue-agent-feedback").mkdir()
    return root


def write_inspect_feedback(root, issue_number=42, verdict="POLISH", polish_attempts=1):
    """Write a sample inspect feedback file and return the data."""
    feedback = {
        "issue_number": issue_number,
        "pr_number": 7,
        "verdict": verdict,
        "polish_attempts": polish_attempts,
        "dimensions": {
            "what_changed": "Added null check",
            "project_value": "Prevents crash",
            "issue_validity": "Valid bug",
            "intent_alignment": "Matches issue",
            "scope": "Minimal change",
            "security": "No concerns",
            "code_quality": "Needs polish",
            "root_cause_depth": "Surface fix"
        },
        "rationale": "Code works but needs cleanup",
        "reviewed_at": "2026-02-23T21:00:00Z"
    }
    feedback_file = root / ".beads" / "inspect-feedback" / f"issue-{issue_number}.json"
    feedback_file.write_text(json.dumps(feedback, indent=2))
    return feedback


def write_loop_feedback(root, task_id="lc-abc"):
    """Write a sample loop feedback file and return the data."""
    feedback = {
        "task_id": task_id,
        "phase": "serve",
        "verdict": "NEEDS_CHANGES",
        "feedback": "Variable naming unclear, add comments",
        "iteration": 1,
        "reviewed_at": "2026-02-23T21:05:00Z"
    }
    feedback_file = root / ".beads" / "loop-feedback" / f"{task_id}.json"
    feedback_file.write_text(json.dumps(feedback, indent=2))
    return feedback


class TestFeedbackBroker(unittest.TestCase):
    """Test feedback broker read and synthesis functions."""

    def setUp(self):
        self.mock_root = make_broker_dir()

    def test_reads_inspect_feedback(self):
        """Verify broker can read inspect feedback."""
        write_inspect_feedback(self.mock_root)
        feedback = read_inspect_feedback(self.mock_root, issue_number=42)

        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["verdict"], "POLISH")
        self.assertEqual(feedback["polish_attempts"], 1)
        self.assertEqual(feedback["issue_number"], 42)

    def test_reads_loop_feedback(self):
        """Verify broker can read loop feedback."""
        write_loop_feedback(self.mock_root)
        feedback = read_loop_feedback(self.mock_root, task_id="lc-abc")

        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["verdict"], "NEEDS_CHANGES")
        self.assertEqual(feedback["task_id"], "lc-abc")

    def test_synthesizes_unified_view(self):
        """Verify broker synthesizes feedback from multiple sources."""
        write_inspect_feedback(self.mock_root)
        write_loop_feedback(self.mock_root)

        unified = synthesize_feedback(self.mock_root, issue_number=42)

        self.assertEqual(unified["context_type"], "issue")
        self.assertEqual(unified["context_id"], "42")
        self.assertIn("inspect", unified["feedback_sources"])
        self.assertGreaterEqual(unified["summary"]["total_feedback_count"], 1)
        self.assertEqual(unified["summary"]["latest_verdict"], "POLISH")

    def test_handles_missing_feedback(self):
        """Verify broker handles missing feedback gracefully."""
        feedback = read_inspect_feedback(self.mock_root, issue_number=999)
        self.assertIsNone(feedback)

    def test_identifies_escalation_needed(self):
        """Verify broker identifies when escalation is needed."""
        write_inspect_feedback(self.mock_root)

        # Modify feedback to have 3 polish attempts
        feedback_file = self.mock_root / ".beads" / "inspect-feedback" / "issue-42.json"
        feedback = json.loads(feedback_file.read_text())
        feedback["polish_attempts"] = 3
        feedback_file.write_text(json.dumps(feedback, indent=2))

        unified = synthesize_feedback(self.mock_root, issue_number=42)
        self.assertTrue(unified["summary"]["escalation_needed"])

    def test_loop_feedback_synthesis(self):
        """Verify broker synthesizes loop feedback by task ID."""
        write_loop_feedback(self.mock_root)

        unified = synthesize_feedback(self.mock_root, task_id="lc-abc")

        self.assertEqual(unified["context_type"], "task")
        self.assertEqual(unified["context_id"], "lc-abc")
        self.assertIn("loop", unified["feedback_sources"])
        self.assertEqual(unified["summary"]["latest_verdict"], "NEEDS_CHANGES")


if __name__ == "__main__":
    unittest.main()
