"""Test feedback history accumulation in retry context."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.iteration import write_retry_context, clear_retry_context
from line_loop.models import ServeFeedback, ServeFeedbackIssue


class TestFeedbackHistory(unittest.TestCase):
    """Test feedback history accumulation in retry context."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.cwd = Path(self._tmpdir)

    def test_feedback_accumulates_across_retries(self):
        """Verify feedback history accumulates instead of replacing."""
        feedback1 = ServeFeedback(
            verdict="NEEDS_CHANGES",
            summary="Missing error handling",
            issues=[
                ServeFeedbackIssue(
                    severity="critical",
                    location="foo.py:10",
                    problem="No error handling",
                    suggestion="Add try/except"
                )
            ],
            task_id="test-001",
            task_title="Test task",
            attempt=1
        )
        write_retry_context(self.cwd, feedback1)

        feedback2 = ServeFeedback(
            verdict="NEEDS_CHANGES",
            summary="Still missing edge case",
            issues=[
                ServeFeedbackIssue(
                    severity="major",
                    location="foo.py:15",
                    problem="Edge case not handled",
                    suggestion="Check for None"
                )
            ],
            task_id="test-001",
            task_title="Test task",
            attempt=2
        )
        write_retry_context(self.cwd, feedback2)

        context_file = self.cwd / ".line-cook" / "retry-context.json"
        self.assertTrue(context_file.exists())

        data = json.loads(context_file.read_text())

        self.assertIn("history", data)
        self.assertEqual(len(data["history"]), 2)
        self.assertEqual(data["history"][0]["attempt"], 1)
        self.assertEqual(data["history"][0]["summary"], "Missing error handling")
        self.assertEqual(data["history"][1]["attempt"], 2)
        self.assertEqual(data["history"][1]["summary"], "Still missing edge case")
        self.assertEqual(data["attempt"], 2)
        self.assertEqual(data["verdict"], "NEEDS_CHANGES")
        self.assertEqual(data["summary"], "Still missing edge case")

    def test_clear_retry_context_removes_file(self):
        """Verify clear removes the retry context file."""
        feedback = ServeFeedback(
            verdict="NEEDS_CHANGES",
            summary="Test",
            task_id="test-001",
            attempt=1
        )
        write_retry_context(self.cwd, feedback)

        context_file = self.cwd / ".line-cook" / "retry-context.json"
        self.assertTrue(context_file.exists())

        clear_retry_context(self.cwd)
        self.assertFalse(context_file.exists())


if __name__ == "__main__":
    unittest.main()
