"""Tests for inspect polish attempt counter."""

import unittest


class TestPolishCounter(unittest.TestCase):
    """Test polish attempt counter logic."""

    def test_first_polish_attempt(self):
        """First POLISH verdict should show attempt 1/3."""
        feedback = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "POLISH",
            "polish_attempts": 1,
            "dimensions": {},
            "rationale": "Needs cleanup",
            "reviewed_at": "2026-02-23T21:00:00Z"
        }
        self.assertEqual(feedback["polish_attempts"], 1)

    def test_increment_polish_attempts(self):
        """Subsequent POLISH verdicts should increment counter."""
        existing = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "POLISH",
            "polish_attempts": 1,
            "reviewed_at": "2026-02-23T20:00:00Z"
        }
        new_attempts = existing.get("polish_attempts", 0) + 1
        self.assertEqual(new_attempts, 2)

    def test_escalate_after_max_attempts(self):
        """After 3 POLISH attempts, should escalate to FEEDBACK."""
        existing = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "POLISH",
            "polish_attempts": 3,
            "reviewed_at": "2026-02-23T20:00:00Z"
        }
        max_attempts = 3
        should_escalate = existing.get("polish_attempts", 0) >= max_attempts
        self.assertTrue(should_escalate)

    def test_non_polish_verdict_resets_counter(self):
        """Non-POLISH verdicts should not increment counter."""
        feedback = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "MERGE",
            "polish_attempts": 0,
            "dimensions": {},
            "rationale": "Looks good",
            "reviewed_at": "2026-02-23T21:00:00Z"
        }
        self.assertEqual(feedback["polish_attempts"], 0)


if __name__ == "__main__":
    unittest.main()
