"""Tests for per-task retry budget tracking across iterations."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.models import SkipList


class TestPerTaskRetryBudget(unittest.TestCase):
    """Test per-task retry budget tracking."""

    def test_tracks_individual_tasks(self):
        """Each task should have its own failure count."""
        skip_list = SkipList(max_failures=3)

        skip_list.record_failure("task-a")
        skip_list.record_failure("task-a")
        skip_list.record_failure("task-b")

        self.assertFalse(skip_list.is_skipped("task-a"))
        self.assertFalse(skip_list.is_skipped("task-b"))

        should_skip = skip_list.record_failure("task-a")
        self.assertTrue(should_skip)
        self.assertTrue(skip_list.is_skipped("task-a"))
        self.assertFalse(skip_list.is_skipped("task-b"))

    def test_persists_across_iterations(self):
        """Failure counts should accumulate across multiple iterations."""
        skip_list = SkipList(max_failures=2)

        skip_list.record_failure("task-x")
        self.assertFalse(skip_list.is_skipped("task-x"))

        should_skip = skip_list.record_failure("task-x")
        self.assertTrue(should_skip)
        self.assertTrue(skip_list.is_skipped("task-x"))

        # Still skipped in next iteration
        self.assertTrue(skip_list.is_skipped("task-x"))

    def test_resets_on_success(self):
        """Success should clear the failure count for that task."""
        skip_list = SkipList(max_failures=3)

        skip_list.record_failure("task-a")
        skip_list.record_failure("task-a")
        self.assertFalse(skip_list.is_skipped("task-a"))

        skip_list.record_success("task-a")

        skip_list.record_failure("task-a")
        self.assertFalse(skip_list.is_skipped("task-a"))

    def test_get_skipped_tasks_returns_budget_exceeded(self):
        """Should return list of tasks that exceeded their budget."""
        skip_list = SkipList(max_failures=2)

        skip_list.record_failure("task-a")
        skip_list.record_failure("task-a")
        skip_list.record_failure("task-b")
        skip_list.record_failure("task-b")
        skip_list.record_failure("task-c")

        skipped = skip_list.get_skipped_tasks()
        self.assertEqual(len(skipped), 2)
        self.assertIn({"id": "task-a", "failure_count": 2}, skipped)
        self.assertIn({"id": "task-b", "failure_count": 2}, skipped)

    def test_get_skipped_ids_returns_set(self):
        """Should return set of task IDs that are skipped."""
        skip_list = SkipList(max_failures=2)

        skip_list.record_failure("task-a")
        skip_list.record_failure("task-a")
        skip_list.record_failure("task-b")
        skip_list.record_failure("task-b")

        skipped_ids = skip_list.get_skipped_ids()
        self.assertEqual(skipped_ids, {"task-a", "task-b"})

    def test_multiple_tasks_independent_budgets(self):
        """Multiple tasks should have independent failure budgets."""
        skip_list = SkipList(max_failures=2)

        skip_list.record_failure("task-a")
        skip_list.record_failure("task-a")
        skip_list.record_failure("task-b")
        skip_list.record_failure("task-c")
        skip_list.record_failure("task-c")

        self.assertTrue(skip_list.is_skipped("task-a"))
        self.assertFalse(skip_list.is_skipped("task-b"))
        self.assertTrue(skip_list.is_skipped("task-c"))

        skip_list.record_success("task-b")
        skip_list.record_failure("task-b")
        self.assertFalse(skip_list.is_skipped("task-b"))

    def test_none_task_id_handled_gracefully(self):
        """None task_id should not cause errors."""
        skip_list = SkipList(max_failures=2)

        should_skip = skip_list.record_failure(None)
        self.assertFalse(should_skip)

        skip_list.record_success(None)
        self.assertFalse(skip_list.is_skipped(None))
        self.assertEqual(len(skip_list.get_skipped_ids()), 0)


if __name__ == "__main__":
    unittest.main()
