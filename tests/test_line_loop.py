#!/usr/bin/env python3
"""Unit tests for line-loop.py functions."""

import sys
import unittest
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from importlib import import_module

# Import the module
line_loop = import_module("line-loop")


class TestParseServeResult(unittest.TestCase):
    """Test parse_serve_result() function."""

    def test_parse_approved_verdict(self):
        """APPROVED verdict is correctly parsed."""
        output = """
╔══════════════════════════════════════════════════════════════╗
║  SERVE: Dish Presented                                       ║
╚══════════════════════════════════════════════════════════════╝

REVIEW: lc-001 - Add feature
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Code looks good, well-tested.

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: APPROVED                       │
│ continue: true                          │
│ next_step: /line:tidy                   │
│ blocking_issues: 0                      │
└─────────────────────────────────────────┘
"""
        result = line_loop.parse_serve_result(output)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, "APPROVED")
        self.assertTrue(result.continue_)
        self.assertEqual(result.blocking_issues, 0)

    def test_parse_needs_changes_verdict(self):
        """NEEDS_CHANGES verdict is correctly parsed."""
        output = """
SERVE_RESULT
verdict: NEEDS_CHANGES
continue: false
next_step: /line:cook
blocking_issues: 2
"""
        result = line_loop.parse_serve_result(output)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, "NEEDS_CHANGES")
        self.assertFalse(result.continue_)
        self.assertEqual(result.blocking_issues, 2)

    def test_parse_blocked_verdict(self):
        """BLOCKED verdict is correctly parsed."""
        output = """
│ SERVE_RESULT                            │
│ verdict: BLOCKED                        │
│ continue: false                         │
│ blocking_issues: 1                      │
"""
        result = line_loop.parse_serve_result(output)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, "BLOCKED")
        self.assertFalse(result.continue_)

    def test_parse_skipped_verdict(self):
        """SKIPPED verdict is correctly parsed."""
        output = """
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: API timeout

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: SKIPPED                        │
│ continue: true                          │
│ blocking_issues: 0                      │
│ retry_recommended: true                 │
└─────────────────────────────────────────┘
"""
        result = line_loop.parse_serve_result(output)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, "SKIPPED")
        self.assertTrue(result.continue_)

    def test_parse_no_serve_result(self):
        """Returns None when no SERVE_RESULT block found."""
        output = "Some output without a SERVE_RESULT block"
        result = line_loop.parse_serve_result(output)
        self.assertIsNone(result)

    def test_parse_case_insensitive(self):
        """Verdict parsing is case-insensitive."""
        output = "verdict: approved\ncontinue: TRUE\nblocking_issues: 0"
        result = line_loop.parse_serve_result(output)
        self.assertIsNotNone(result)
        self.assertEqual(result.verdict, "APPROVED")

    def test_parse_malformed_output(self):
        """Handles malformed output gracefully."""
        output = "verdict: UNKNOWN_STATE\ncontinue: maybe"
        result = line_loop.parse_serve_result(output)
        # Should return None because UNKNOWN_STATE isn't a valid verdict
        self.assertIsNone(result)


class TestDetectKitchenComplete(unittest.TestCase):
    """Test detect_kitchen_complete() function."""

    def test_detects_kitchen_complete(self):
        """Detects KITCHEN_COMPLETE signal."""
        output = """
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN COMPLETE                                            ║
╚══════════════════════════════════════════════════════════════╝

Task: lc-001 - Add feature
Tests: ✓ All passing
Build: ✓ Successful

Signal: KITCHEN_COMPLETE
"""
        self.assertTrue(line_loop.detect_kitchen_complete(output))

    def test_detects_kitchen_complete_no_space(self):
        """Detects KITCHEN_COMPLETE without space."""
        output = "Signal: KITCHEN_COMPLETE"
        self.assertTrue(line_loop.detect_kitchen_complete(output))

    def test_no_kitchen_complete(self):
        """Returns False when no KITCHEN_COMPLETE signal."""
        output = "Some output without the signal"
        self.assertFalse(line_loop.detect_kitchen_complete(output))


class TestParseIntentBlock(unittest.TestCase):
    """Test parse_intent_block() function."""

    def test_parse_intent_and_before_after(self):
        """Parses both INTENT and BEFORE → AFTER blocks."""
        output = """
INTENT:
  Add user authentication
  Goal: Secure API endpoints

BEFORE → AFTER:
  No auth → JWT-based auth
"""
        intent, before, after = line_loop.parse_intent_block(output)
        self.assertIsNotNone(intent)
        self.assertIn("authentication", intent.lower())
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)

    def test_parse_no_intent(self):
        """Returns None when no INTENT block found."""
        output = "Some output without intent"
        intent, before, after = line_loop.parse_intent_block(output)
        self.assertIsNone(intent)
        self.assertIsNone(before)
        self.assertIsNone(after)


class TestPhaseResult(unittest.TestCase):
    """Test PhaseResult dataclass."""

    def test_phase_result_creation(self):
        """PhaseResult can be created with required fields."""
        result = line_loop.PhaseResult(
            phase="cook",
            success=True,
            output="Test output",
            exit_code=0,
            duration_seconds=10.5
        )
        self.assertEqual(result.phase, "cook")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Test output")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.duration_seconds, 10.5)
        self.assertEqual(result.signals, [])
        self.assertEqual(result.actions, [])
        self.assertIsNone(result.error)

    def test_phase_result_with_error(self):
        """PhaseResult can be created with error."""
        result = line_loop.PhaseResult(
            phase="serve",
            success=False,
            output="",
            exit_code=-1,
            duration_seconds=5.0,
            error="Timeout after 300s"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Timeout after 300s")


class TestCircuitBreaker(unittest.TestCase):
    """Test CircuitBreaker class."""

    def test_circuit_starts_closed(self):
        """Circuit breaker starts in closed state."""
        cb = line_loop.CircuitBreaker()
        self.assertFalse(cb.is_open())

    def test_circuit_opens_after_failures(self):
        """Circuit opens after threshold consecutive failures."""
        cb = line_loop.CircuitBreaker(failure_threshold=3, window_size=5)
        cb.record(False)
        cb.record(False)
        self.assertFalse(cb.is_open())  # Not yet at threshold
        cb.record(False)
        self.assertTrue(cb.is_open())  # Now at threshold

    def test_success_keeps_circuit_closed(self):
        """Successes keep the circuit closed."""
        cb = line_loop.CircuitBreaker(failure_threshold=3, window_size=5)
        cb.record(False)
        cb.record(False)
        cb.record(True)  # Success interrupts failures
        cb.record(False)
        self.assertFalse(cb.is_open())

    def test_reset_clears_state(self):
        """Reset clears all recorded results."""
        cb = line_loop.CircuitBreaker(failure_threshold=2)
        cb.record(False)
        cb.record(False)
        self.assertTrue(cb.is_open())
        cb.reset()
        self.assertFalse(cb.is_open())


class TestProgressState(unittest.TestCase):
    """Test ProgressState class for intra-iteration progress tracking."""

    def _create_progress_state(self, status_file=None):
        """Helper to create a ProgressState with minimal required fields."""
        from datetime import datetime
        return line_loop.ProgressState(
            status_file=status_file,
            iteration=1,
            max_iterations=10,
            current_task="lc-001",
            current_task_title="Test task",
            tasks_completed=0,
            tasks_remaining=5,
            started_at=datetime.now(),
            iterations=[]
        )

    def test_start_phase_sets_fields(self):
        """start_phase() sets phase name and start time."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
        self.assertEqual(ps.current_phase, "cook")
        self.assertIsNotNone(ps.phase_start_time)
        self.assertEqual(ps.current_action_count, 0)

    def test_update_progress_sets_action_count(self):
        """update_progress() sets action count and last action time."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
        ps.update_progress(5, "2026-02-01T10:15:00")
        self.assertEqual(ps.current_action_count, 5)
        self.assertIsNotNone(ps.last_action_time)

    def test_update_progress_handles_malformed_timestamp(self):
        """update_progress() handles malformed timestamp gracefully."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
        # Should not raise - falls back to datetime.now()
        ps.update_progress(3, "not-a-timestamp")
        self.assertEqual(ps.current_action_count, 3)
        self.assertIsNotNone(ps.last_action_time)

    def test_update_progress_handles_none_timestamp(self):
        """update_progress() handles None timestamp gracefully."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
        # Should not raise - falls back to datetime.now()
        ps.update_progress(2, None)
        self.assertEqual(ps.current_action_count, 2)
        self.assertIsNotNone(ps.last_action_time)

    def test_throttle_initial_state(self):
        """_last_write starts at 0 before any writes."""
        ps = self._create_progress_state()
        self.assertEqual(ps._last_write, 0.0)

    def test_start_phase_resets_action_count(self):
        """start_phase() resets action count to 0."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
        ps.current_action_count = 10
        ps.start_phase("serve")
        self.assertEqual(ps.current_action_count, 0)
        self.assertEqual(ps.current_phase, "serve")


class TestCalculateRetryDelay(unittest.TestCase):
    """Test calculate_retry_delay() function."""

    def test_first_retry_delay(self):
        """First retry has base delay with jitter."""
        delay = line_loop.calculate_retry_delay(1)
        # Should be around 4s (2 * 2^1) with ±20% jitter
        self.assertGreater(delay, 3.0)
        self.assertLess(delay, 5.0)

    def test_exponential_growth(self):
        """Delay grows exponentially."""
        delay1 = line_loop.calculate_retry_delay(1, base=2.0)
        delay2 = line_loop.calculate_retry_delay(2, base=2.0)
        # Remove jitter by checking bounds
        # attempt 2 should be roughly 2x attempt 1
        self.assertGreater(delay2, delay1 * 1.5)

    def test_delay_capped_at_60s(self):
        """Delay is capped at 60 seconds."""
        delay = line_loop.calculate_retry_delay(10)  # Would be 2^10 = 1024 without cap
        self.assertLessEqual(delay, 60 * 1.2)  # Max 72s with jitter


class TestSkipList(unittest.TestCase):
    """Test SkipList class for tracking failing tasks."""

    def test_skip_list_starts_empty(self):
        """Skip list starts with no skipped tasks."""
        sl = line_loop.SkipList()
        self.assertEqual(sl.get_skipped_ids(), set())
        self.assertEqual(sl.get_skipped_tasks(), [])

    def test_record_failure_counts(self):
        """record_failure() increments failure count."""
        sl = line_loop.SkipList(max_failures=3)
        self.assertFalse(sl.record_failure("lc-001"))
        self.assertFalse(sl.record_failure("lc-001"))
        self.assertTrue(sl.record_failure("lc-001"))  # Third failure triggers skip
        self.assertEqual(sl.failed_tasks["lc-001"], 3)

    def test_record_failure_returns_true_when_skipped(self):
        """record_failure() returns True when task hits skip threshold."""
        sl = line_loop.SkipList(max_failures=2)
        self.assertFalse(sl.record_failure("lc-001"))
        self.assertTrue(sl.record_failure("lc-001"))

    def test_record_failure_empty_task_id(self):
        """record_failure() handles empty task ID gracefully."""
        sl = line_loop.SkipList()
        self.assertFalse(sl.record_failure(""))
        self.assertFalse(sl.record_failure(None))
        self.assertEqual(sl.failed_tasks, {})

    def test_record_success_clears_failures(self):
        """record_success() clears failure count for a task."""
        sl = line_loop.SkipList(max_failures=3)
        sl.record_failure("lc-001")
        sl.record_failure("lc-001")
        self.assertEqual(sl.failed_tasks["lc-001"], 2)
        sl.record_success("lc-001")
        self.assertNotIn("lc-001", sl.failed_tasks)

    def test_record_success_empty_task_id(self):
        """record_success() handles empty task ID gracefully."""
        sl = line_loop.SkipList()
        sl.record_failure("lc-001")
        sl.record_success("")  # Should not crash
        sl.record_success(None)  # Should not crash
        self.assertIn("lc-001", sl.failed_tasks)

    def test_is_skipped(self):
        """is_skipped() correctly identifies skipped tasks."""
        sl = line_loop.SkipList(max_failures=2)
        self.assertFalse(sl.is_skipped("lc-001"))
        sl.record_failure("lc-001")
        self.assertFalse(sl.is_skipped("lc-001"))
        sl.record_failure("lc-001")
        self.assertTrue(sl.is_skipped("lc-001"))

    def test_is_skipped_empty_task_id(self):
        """is_skipped() handles empty task ID gracefully."""
        sl = line_loop.SkipList()
        self.assertFalse(sl.is_skipped(""))
        self.assertFalse(sl.is_skipped(None))

    def test_get_skipped_ids(self):
        """get_skipped_ids() returns set of skipped task IDs."""
        sl = line_loop.SkipList(max_failures=2)
        sl.record_failure("lc-001")
        sl.record_failure("lc-001")  # Now skipped
        sl.record_failure("lc-002")  # Not yet skipped
        sl.record_failure("lc-003")
        sl.record_failure("lc-003")  # Now skipped
        skipped = sl.get_skipped_ids()
        self.assertEqual(skipped, {"lc-001", "lc-003"})

    def test_get_skipped_tasks(self):
        """get_skipped_tasks() returns list with failure counts."""
        sl = line_loop.SkipList(max_failures=2)
        sl.record_failure("lc-001")
        sl.record_failure("lc-001")
        sl.record_failure("lc-002")
        skipped = sl.get_skipped_tasks()
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["id"], "lc-001")
        self.assertEqual(skipped[0]["failure_count"], 2)

    def test_multiple_tasks_tracked_independently(self):
        """Different tasks are tracked independently."""
        sl = line_loop.SkipList(max_failures=3)
        sl.record_failure("lc-001")
        sl.record_failure("lc-002")
        sl.record_failure("lc-001")
        sl.record_failure("lc-002")
        sl.record_failure("lc-001")  # lc-001 now skipped
        self.assertTrue(sl.is_skipped("lc-001"))
        self.assertFalse(sl.is_skipped("lc-002"))


class TestDefaultPhaseTimeouts(unittest.TestCase):
    """Test that default phase timeouts are set correctly."""

    def test_default_cook_timeout(self):
        """Cook phase default timeout is 1200 seconds."""
        self.assertEqual(line_loop.DEFAULT_PHASE_TIMEOUTS['cook'], 1200)

    def test_default_serve_timeout(self):
        """Serve phase default timeout is 600 seconds."""
        self.assertEqual(line_loop.DEFAULT_PHASE_TIMEOUTS['serve'], 600)

    def test_default_tidy_timeout(self):
        """Tidy phase default timeout is 240 seconds."""
        self.assertEqual(line_loop.DEFAULT_PHASE_TIMEOUTS['tidy'], 240)

    def test_default_plate_timeout(self):
        """Plate phase default timeout is 600 seconds."""
        self.assertEqual(line_loop.DEFAULT_PHASE_TIMEOUTS['plate'], 600)

    def test_default_max_task_failures(self):
        """Default max task failures is 3."""
        self.assertEqual(line_loop.DEFAULT_MAX_TASK_FAILURES, 3)

    def test_skip_list_uses_default_max_failures(self):
        """SkipList uses DEFAULT_MAX_TASK_FAILURES by default."""
        sl = line_loop.SkipList()
        self.assertEqual(sl.max_failures, line_loop.DEFAULT_MAX_TASK_FAILURES)


class TestGenerateEscalationReport(unittest.TestCase):
    """Test generate_escalation_report function."""

    def _create_mock_iteration(self, iteration, task_id, outcome, success):
        """Create a mock IterationResult-like object."""
        return line_loop.IterationResult(
            iteration=iteration,
            task_id=task_id,
            task_title=f"Task {task_id}",
            outcome=outcome,
            duration_seconds=60.0,
            serve_verdict="NEEDS_CHANGES" if not success else "APPROVED",
            commit_hash=None,
            success=success
        )

    def test_escalation_report_has_required_fields(self):
        """Escalation report contains required fields."""
        iterations = [
            self._create_mock_iteration(1, "lc-001", "needs_retry", False),
            self._create_mock_iteration(2, "lc-001", "needs_retry", False),
        ]
        skip_list = line_loop.SkipList(max_failures=2)
        skip_list.record_failure("lc-001")
        skip_list.record_failure("lc-001")

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "all_tasks_skipped"
        )

        self.assertIn("stop_reason", report)
        self.assertIn("recent_failures", report)
        self.assertIn("skipped_tasks", report)
        self.assertIn("suggested_actions", report)
        self.assertIn("generated_at", report)

    def test_escalation_report_stop_reason(self):
        """Escalation report includes correct stop reason."""
        iterations = []
        skip_list = line_loop.SkipList()

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "circuit_breaker"
        )

        self.assertEqual(report["stop_reason"], "circuit_breaker")

    def test_escalation_report_includes_skipped_tasks(self):
        """Escalation report includes skipped tasks from skip list."""
        iterations = []
        skip_list = line_loop.SkipList(max_failures=2)
        skip_list.record_failure("lc-001")
        skip_list.record_failure("lc-001")
        skip_list.record_failure("lc-002")
        skip_list.record_failure("lc-002")

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "all_tasks_skipped"
        )

        self.assertEqual(len(report["skipped_tasks"]), 2)
        skipped_ids = {t["id"] for t in report["skipped_tasks"]}
        self.assertEqual(skipped_ids, {"lc-001", "lc-002"})

    def test_escalation_report_suggested_actions_circuit_breaker(self):
        """Escalation report has appropriate actions for circuit breaker."""
        iterations = []
        skip_list = line_loop.SkipList()

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "circuit_breaker"
        )

        self.assertGreater(len(report["suggested_actions"]), 0)
        # Should mention checking failures
        actions_text = " ".join(report["suggested_actions"])
        self.assertIn("failure", actions_text.lower())

    def test_escalation_report_suggested_actions_all_skipped(self):
        """Escalation report has appropriate actions for all_tasks_skipped."""
        iterations = []
        skip_list = line_loop.SkipList()

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "all_tasks_skipped"
        )

        self.assertGreater(len(report["suggested_actions"]), 0)
        # Should mention reviewing skipped tasks
        actions_text = " ".join(report["suggested_actions"])
        self.assertIn("skipped", actions_text.lower())


class TestFormatEscalationReport(unittest.TestCase):
    """Test format_escalation_report function."""

    def test_format_escalation_report_output(self):
        """format_escalation_report produces readable output."""
        escalation = {
            "stop_reason": "all_tasks_skipped",
            "skipped_tasks": [{"id": "lc-001", "failure_count": 3}],
            "recent_failures": [],
            "suggested_actions": ["Review the skipped tasks"]
        }
        result = line_loop.format_escalation_report(escalation)
        self.assertIn("ESCALATION REPORT", result)
        self.assertIn("lc-001", result)
        self.assertIn("all_tasks_skipped", result)

    def test_format_escalation_report_includes_recent_failures(self):
        """format_escalation_report includes recent failures."""
        escalation = {
            "stop_reason": "circuit_breaker",
            "skipped_tasks": [],
            "recent_failures": [
                {"iteration": 5, "task_id": "lc-123", "outcome": "needs_retry"}
            ],
            "suggested_actions": []
        }
        result = line_loop.format_escalation_report(escalation)
        self.assertIn("lc-123", result)
        self.assertIn("needs_retry", result)

    def test_format_escalation_report_includes_suggested_actions(self):
        """format_escalation_report includes suggested actions."""
        escalation = {
            "stop_reason": "circuit_breaker",
            "skipped_tasks": [],
            "recent_failures": [],
            "suggested_actions": ["Check logs", "Review tasks"]
        }
        result = line_loop.format_escalation_report(escalation)
        self.assertIn("Check logs", result)
        self.assertIn("Review tasks", result)


if __name__ == "__main__":
    unittest.main()
