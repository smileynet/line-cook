"""Test feedback history accumulation in retry context."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.config import MAX_FEEDBACK_HISTORY
from line_loop.iteration import write_retry_context, clear_retry_context
from line_loop.models import ServeFeedback, ServeFeedbackIssue


class TestFeedbackHistory(unittest.TestCase):
    """Test feedback history accumulation in retry context."""

    def setUp(self):
        self.cwd = Path(tempfile.mkdtemp())

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

    def test_feedback_history_rolling_window(self):
        """Verify history is capped at MAX_FEEDBACK_HISTORY entries."""
        total_entries = MAX_FEEDBACK_HISTORY + 3

        for i in range(1, total_entries + 1):
            feedback = ServeFeedback(
                verdict="NEEDS_CHANGES",
                summary=f"Attempt {i} feedback",
                issues=[
                    ServeFeedbackIssue(
                        severity="major",
                        location=f"foo.py:{i * 10}",
                        problem=f"Problem {i}",
                        suggestion=f"Fix {i}"
                    )
                ],
                task_id="test-001",
                task_title="Test task",
                attempt=i
            )
            write_retry_context(self.cwd, feedback)

        context_file = self.cwd / ".line-cook" / "retry-context.json"
        data = json.loads(context_file.read_text())

        self.assertEqual(len(data["history"]), MAX_FEEDBACK_HISTORY)
        # Oldest entries (1..3) should be trimmed; first remaining is attempt 4
        first_kept = total_entries - MAX_FEEDBACK_HISTORY + 1
        self.assertEqual(data["history"][0]["attempt"], first_kept)
        self.assertEqual(data["history"][0]["summary"], f"Attempt {first_kept} feedback")
        # Last entry should be the most recent
        self.assertEqual(data["history"][-1]["attempt"], total_entries)
        self.assertEqual(data["history"][-1]["summary"], f"Attempt {total_entries} feedback")


if __name__ == "__main__":
    unittest.main()
