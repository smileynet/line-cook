#!/usr/bin/env python3
"""Unit tests for line-loop.py functions."""

import sys
import unittest
from pathlib import Path

# Add core directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

# Import the line_loop package
import line_loop


# --- Shared test helpers ---

def make_bead(id, title="", issue_type="task", parent=None):
    """Create a BeadInfo for testing."""
    return line_loop.BeadInfo(id=id, title=title, issue_type=issue_type, parent=parent)


def make_snapshot(beads):
    """Create a BeadSnapshot with given beads in ready list."""
    snapshot = line_loop.BeadSnapshot()
    snapshot.ready = beads
    return snapshot


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
        """Circuit opens after reaching failure threshold in window."""
        cb = line_loop.CircuitBreaker(failure_threshold=3, window_size=5)
        cb.record(False)
        cb.record(False)
        self.assertFalse(cb.is_open())
        cb.record(False)
        self.assertTrue(cb.is_open())

    def test_success_keeps_circuit_closed(self):
        """Enough successes in window keep failure count below threshold."""
        cb = line_loop.CircuitBreaker(failure_threshold=3, window_size=5)
        cb.record(False)
        cb.record(False)
        cb.record(True)  # Successes keep failure count below threshold
        cb.record(True)
        cb.record(True)
        # 2 failures, 3 successes → 2 < 3 threshold → stays closed
        self.assertFalse(cb.is_open())

    def test_full_window_evaluated_not_just_tail(self):
        """Circuit breaker evaluates full window, not just last N items.

        Pattern [F,F,F,F,F,S,F,F,F,F] has 9/10 failures.
        Bug: checking only last 5 items gives [S,F,F,F,F] = 4 failures,
        which doesn't trip the breaker despite 90% failure rate.
        """
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        # Record pattern: 5 failures, 1 success, 4 failures
        for _ in range(5):
            cb.record(False)
        cb.record(True)
        for _ in range(4):
            cb.record(False)
        # 9/10 failures — should trip
        self.assertTrue(cb.is_open())

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
        ps.update_progress(3, "not-a-timestamp")
        self.assertEqual(ps.current_action_count, 3)
        self.assertIsNotNone(ps.last_action_time)

    def test_update_progress_handles_none_timestamp(self):
        """update_progress() handles None timestamp gracefully."""
        ps = self._create_progress_state()
        ps.start_phase("cook")
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
        # Attempt 2 should be roughly 2x attempt 1 (accounting for jitter)
        self.assertGreater(delay2, delay1 * 1.5)

    def test_delay_capped_at_60s(self):
        """Delay is capped at 60 seconds."""
        delay = line_loop.calculate_retry_delay(10)
        max_with_jitter = 60 * 1.2
        self.assertLessEqual(delay, max_with_jitter)


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

    def test_default_close_service_timeout(self):
        """Close-service phase default timeout is 900 seconds."""
        self.assertEqual(line_loop.DEFAULT_PHASE_TIMEOUTS['close-service'], 900)

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

        suggested_actions = report["suggested_actions"]
        self.assertGreater(len(suggested_actions), 0)
        actions_text = " ".join(suggested_actions)
        self.assertIn("failure", actions_text.lower())

    def test_escalation_report_suggested_actions_all_skipped(self):
        """Escalation report has appropriate actions for all_tasks_skipped."""
        iterations = []
        skip_list = line_loop.SkipList()

        report = line_loop.generate_escalation_report(
            iterations, skip_list, "all_tasks_skipped"
        )

        suggested_actions = report["suggested_actions"]
        self.assertGreater(len(suggested_actions), 0)
        actions_text = " ".join(suggested_actions)
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


class TestBeadInfo(unittest.TestCase):
    """Test BeadInfo dataclass."""

    def test_bead_info_creation(self):
        """BeadInfo can be created with required fields."""
        info = line_loop.BeadInfo(id="lc-001", title="Test task", issue_type="task")
        self.assertEqual(info.id, "lc-001")
        self.assertEqual(info.title, "Test task")
        self.assertEqual(info.issue_type, "task")
        self.assertIsNone(info.parent)
        self.assertIsNone(info.priority)
        self.assertIsNone(info.status)

    def test_bead_info_with_optional_fields(self):
        """BeadInfo stores optional fields."""
        info = line_loop.BeadInfo(
            id="lc-001.1",
            title="Sub-task",
            issue_type="task",
            parent="lc-001",
            priority=2,
            status="open"
        )
        self.assertEqual(info.parent, "lc-001")
        self.assertEqual(info.priority, 2)
        self.assertEqual(info.status, "open")


class TestBeadSnapshotProperties(unittest.TestCase):
    """Test BeadSnapshot backwards-compatible properties."""

    def _make_snapshot(self):
        """Create a snapshot with mixed issue types."""
        return line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="e-001", title="Epic", issue_type="epic"),
                line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature"),
                line_loop.BeadInfo(id="t-001", title="Task", issue_type="task"),
            ],
            in_progress=[
                line_loop.BeadInfo(id="t-002", title="In progress", issue_type="task"),
            ],
            closed=[
                line_loop.BeadInfo(id="t-003", title="Done", issue_type="task"),
            ],
        )

    def test_ready_ids(self):
        """ready_ids returns all ready IDs including epics."""
        s = self._make_snapshot()
        self.assertEqual(s.ready_ids, ["e-001", "f-001", "t-001"])

    def test_ready_work_ids(self):
        """ready_work_ids excludes epics."""
        s = self._make_snapshot()
        self.assertEqual(s.ready_work_ids, ["f-001", "t-001"])

    def test_ready_work(self):
        """ready_work returns BeadInfo objects excluding epics."""
        s = self._make_snapshot()
        work = s.ready_work
        self.assertEqual(len(work), 2)
        self.assertEqual(work[0].id, "f-001")
        self.assertEqual(work[1].id, "t-001")

    def test_in_progress_ids(self):
        """in_progress_ids returns IDs of in-progress beads."""
        s = self._make_snapshot()
        self.assertEqual(s.in_progress_ids, ["t-002"])

    def test_closed_ids(self):
        """closed_ids returns IDs of closed beads."""
        s = self._make_snapshot()
        self.assertEqual(s.closed_ids, ["t-003"])

    def test_get_by_id_found(self):
        """get_by_id returns matching BeadInfo."""
        s = self._make_snapshot()
        result = s.get_by_id("f-001")
        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Feature")

    def test_get_by_id_not_found(self):
        """get_by_id returns None for unknown ID."""
        s = self._make_snapshot()
        self.assertIsNone(s.get_by_id("nonexistent"))

    def test_get_by_id_searches_all_lists(self):
        """get_by_id searches ready, in_progress, and closed."""
        s = self._make_snapshot()
        self.assertIsNotNone(s.get_by_id("t-002"))  # in_progress
        self.assertIsNotNone(s.get_by_id("t-003"))  # closed

    def test_empty_snapshot(self):
        """Empty snapshot returns empty lists."""
        s = line_loop.BeadSnapshot()
        self.assertEqual(s.ready_ids, [])
        self.assertEqual(s.ready_work_ids, [])
        self.assertEqual(s.in_progress_ids, [])
        self.assertEqual(s.closed_ids, [])

    def test_index_not_in_repr(self):
        """_index field is excluded from repr."""
        s = self._make_snapshot()
        s.get_by_id("f-001")  # triggers index build
        r = repr(s)
        self.assertNotIn("_index", r)

    def test_index_not_in_equality(self):
        """_index field is excluded from equality comparison."""
        s1 = self._make_snapshot()
        s2 = self._make_snapshot()
        s2.timestamp = s1.timestamp  # normalize timestamp
        s1.get_by_id("f-001")  # build index on s1 only
        self.assertEqual(s1, s2)

    def test_index_is_none_before_first_access(self):
        """_index starts as None (lazy)."""
        s = self._make_snapshot()
        self.assertIsNone(s._index)

    def test_index_built_on_first_get_by_id(self):
        """_index is populated after first get_by_id call."""
        s = self._make_snapshot()
        s.get_by_id("f-001")
        self.assertIsNotNone(s._index)
        self.assertIsInstance(s._index, dict)

    def test_index_contains_all_beads(self):
        """_index maps all bead IDs across ready, in_progress, closed."""
        s = self._make_snapshot()
        s.get_by_id("f-001")  # triggers build
        self.assertEqual(set(s._index.keys()), {"e-001", "f-001", "t-001", "t-002", "t-003"})

    def test_get_by_id_empty_snapshot_with_index(self):
        """get_by_id on empty snapshot returns None and builds empty index."""
        s = line_loop.BeadSnapshot()
        self.assertIsNone(s.get_by_id("anything"))
        self.assertEqual(s._index, {})


class TestBeadDelta(unittest.TestCase):
    """Test BeadDelta.compute()."""

    def test_task_closed(self):
        """Detects a task moving from ready to closed."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")
        before = line_loop.BeadSnapshot(
            ready=[task],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")],
        )
        delta = line_loop.BeadDelta.compute(before, after)
        self.assertEqual(len(delta.newly_closed), 1)
        self.assertEqual(delta.newly_closed[0].id, "t-001")
        self.assertEqual(len(delta.newly_filed), 0)

    def test_feature_auto_closed(self):
        """Detects both task and parent feature closing."""
        before = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="t-001", title="Task", issue_type="task"),
                line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                line_loop.BeadInfo(id="t-001", title="Task", issue_type="task"),
                line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature"),
            ],
        )
        delta = line_loop.BeadDelta.compute(before, after)
        self.assertEqual(len(delta.newly_closed), 2)
        closed_ids = {b.id for b in delta.newly_closed}
        self.assertEqual(closed_ids, {"t-001", "f-001"})

    def test_new_issues_filed(self):
        """Detects new issues that appear in ready after an iteration."""
        before = line_loop.BeadSnapshot(
            ready=[line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="t-002", title="New bug", issue_type="task"),
                line_loop.BeadInfo(id="t-003", title="New issue", issue_type="task"),
            ],
            closed=[line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")],
        )
        delta = line_loop.BeadDelta.compute(before, after)
        self.assertEqual(len(delta.newly_filed), 2)
        filed_ids = {b.id for b in delta.newly_filed}
        self.assertEqual(filed_ids, {"t-002", "t-003"})

    def test_no_changes(self):
        """Delta is empty when nothing changed."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")
        snapshot = line_loop.BeadSnapshot(ready=[task], closed=[])
        delta = line_loop.BeadDelta.compute(snapshot, snapshot)
        self.assertEqual(len(delta.newly_closed), 0)
        self.assertEqual(len(delta.newly_filed), 0)

    def test_existing_ready_not_counted_as_filed(self):
        """Tasks that were already ready are not counted as newly filed."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")
        before = line_loop.BeadSnapshot(ready=[task])
        after = line_loop.BeadSnapshot(ready=[task])
        delta = line_loop.BeadDelta.compute(before, after)
        self.assertEqual(len(delta.newly_filed), 0)


class TestBuildHierarchyChain(unittest.TestCase):
    """Test build_hierarchy_chain()."""

    def test_with_parent_in_snapshot(self):
        """Returns parent when parent is in the snapshot."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task", parent="f-001")
        feature = line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature", parent="e-001")
        epic = line_loop.BeadInfo(id="e-001", title="Epic", issue_type="epic")
        snapshot = line_loop.BeadSnapshot(ready=[task, feature, epic])
        chain = line_loop.build_hierarchy_chain("t-001", snapshot, Path("/tmp"))
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain[0].id, "f-001")
        self.assertEqual(chain[1].id, "e-001")

    def test_no_parent(self):
        """Returns empty chain when bead has no parent."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task")
        snapshot = line_loop.BeadSnapshot(ready=[task])
        chain = line_loop.build_hierarchy_chain("t-001", snapshot, Path("/tmp"))
        self.assertEqual(len(chain), 0)

    def test_bead_not_in_snapshot(self):
        """Returns empty chain when bead is not in snapshot."""
        snapshot = line_loop.BeadSnapshot()
        chain = line_loop.build_hierarchy_chain("nonexistent", snapshot, Path("/tmp"))
        self.assertEqual(len(chain), 0)

    def test_single_parent_level(self):
        """Returns single parent when only one level deep."""
        task = line_loop.BeadInfo(id="t-001", title="Task", issue_type="task", parent="f-001")
        feature = line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature")
        snapshot = line_loop.BeadSnapshot(ready=[task, feature])
        chain = line_loop.build_hierarchy_chain("t-001", snapshot, Path("/tmp"))
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].id, "f-001")


class TestGetNextReadyTaskPreference(unittest.TestCase):
    """Test get_next_ready_task() task-over-feature preference."""

    def test_prefers_task_over_feature(self):
        """When both tasks and features are ready, prefers tasks."""
        snapshot = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature"),
                line_loop.BeadInfo(id="t-001", title="Task", issue_type="task"),
            ]
        )
        result = line_loop.get_next_ready_task(Path("/tmp"), snapshot=snapshot)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "t-001")

    def test_falls_back_to_feature(self):
        """When only features are ready, returns a feature."""
        snapshot = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="e-001", title="Epic", issue_type="epic"),
                line_loop.BeadInfo(id="f-001", title="Feature", issue_type="feature"),
            ]
        )
        result = line_loop.get_next_ready_task(Path("/tmp"), snapshot=snapshot)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "f-001")

    def test_skips_epics(self):
        """Epics are never returned."""
        snapshot = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="e-001", title="Epic", issue_type="epic"),
            ]
        )
        result = line_loop.get_next_ready_task(Path("/tmp"), snapshot=snapshot)
        self.assertIsNone(result)

    def test_respects_skip_ids(self):
        """Skipped task IDs are excluded."""
        snapshot = line_loop.BeadSnapshot(
            ready=[
                line_loop.BeadInfo(id="t-001", title="Task 1", issue_type="task"),
                line_loop.BeadInfo(id="t-002", title="Task 2", issue_type="task"),
            ]
        )
        result = line_loop.get_next_ready_task(
            Path("/tmp"), skip_ids={"t-001"}, snapshot=snapshot
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "t-002")

    def test_empty_snapshot(self):
        """Returns None for empty snapshot."""
        snapshot = line_loop.BeadSnapshot()
        result = line_loop.get_next_ready_task(Path("/tmp"), snapshot=snapshot)
        self.assertIsNone(result)


class TestPrintFeatureCompletion(unittest.TestCase):
    """Test print_feature_completion() output."""

    def test_prints_box_banner(self):
        """print_feature_completion prints a box with feature info."""
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            line_loop.print_feature_completion("lc-001", "User authentication", 3)
        output = buf.getvalue()
        self.assertIn("FEATURE COMPLETE: lc-001", output)
        self.assertIn("User authentication", output)
        self.assertIn("Tasks: 3/3 closed", output)
        self.assertIn("+-", output)  # Box border

    def test_prints_without_title(self):
        """print_feature_completion works with empty title."""
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            line_loop.print_feature_completion("lc-002", "", 1)
        output = buf.getvalue()
        self.assertIn("FEATURE COMPLETE: lc-002", output)
        self.assertIn("Tasks: 1/1 closed", output)


class TestPrintEpicCompletion(unittest.TestCase):
    """Test print_epic_completion() output."""

    def test_prints_box_banner(self):
        """print_epic_completion prints a box with epic info."""
        import io
        import contextlib
        epic = {
            "id": "lc-040",
            "title": "Security epic",
            "children": [
                {"id": "lc-041", "title": "Auth", "issue_type": "feature"},
                {"id": "lc-042", "title": "Validation", "issue_type": "feature"},
            ]
        }
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            line_loop.print_epic_completion(epic)
        output = buf.getvalue()
        self.assertIn("EPIC COMPLETE: lc-040", output)
        self.assertIn("Security epic", output)
        self.assertIn("Children: 2/2 closed", output)
        self.assertIn("+", output)  # Box border

    def test_consistent_with_feature_banner_style(self):
        """Epic banner uses same +---+ border style as feature banner."""
        import io
        import contextlib
        epic = {"id": "e-001", "title": "Epic", "children": []}
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            line_loop.print_epic_completion(epic)
        output = buf.getvalue()
        lines = output.strip().split("\n")
        first_line = lines[0].strip()
        last_line = lines[-1].strip()
        self.assertTrue(first_line.startswith("+"))
        self.assertTrue(last_line.startswith("+"))


class TestActionDots(unittest.TestCase):
    """Test _action_dots() helper."""

    def test_zero_actions(self):
        """Zero actions returns empty string."""
        from line_loop.iteration import _action_dots
        self.assertEqual(_action_dots(0), "")

    def test_small_count(self):
        """Small action count returns single dot."""
        from line_loop.iteration import _action_dots
        result = _action_dots(5)
        self.assertIn("\u00b7", result)
        self.assertEqual(result.count("\u00b7"), 1)

    def test_large_count(self):
        """Larger count returns proportionally more dots."""
        from line_loop.iteration import _action_dots
        result = _action_dots(50)
        self.assertEqual(result.count("\u00b7"), 5)

    def test_negative_count(self):
        """Negative count returns empty string."""
        from line_loop.iteration import _action_dots
        self.assertEqual(_action_dots(-1), "")


class TestActionRecordDuration(unittest.TestCase):
    """Test ActionRecord duration_ms field."""

    def test_default_duration_is_none(self):
        """ActionRecord duration_ms defaults to None."""
        record = line_loop.ActionRecord(
            tool_name="Read",
            tool_use_id="test-id",
            input_summary="/path/to/file",
            output_summary="contents",
            success=True,
            timestamp="2026-02-03T10:00:00"
        )
        self.assertIsNone(record.duration_ms)

    def test_duration_can_be_set(self):
        """ActionRecord duration_ms can be set."""
        record = line_loop.ActionRecord(
            tool_name="Read",
            tool_use_id="test-id",
            input_summary="/path/to/file",
            output_summary="contents",
            success=True,
            timestamp="2026-02-03T10:00:00",
            duration_ms=42.5
        )
        self.assertEqual(record.duration_ms, 42.5)


class TestSerializeAction(unittest.TestCase):
    """Test serialize_action() for history JSONL format."""

    def test_basic_fields(self):
        """Serialized action has tool and timestamp fields."""
        from line_loop.loop import serialize_action
        record = line_loop.ActionRecord(
            tool_name="Read",
            tool_use_id="test-id",
            input_summary="/path",
            output_summary="ok",
            success=True,
            timestamp="2026-02-03T10:00:00"
        )
        data = serialize_action(record)
        self.assertEqual(data["tool"], "Read")
        self.assertEqual(data["timestamp"], "2026-02-03T10:00:00")
        self.assertNotIn("duration_ms", data)

    def test_includes_duration_when_set(self):
        """Serialized action includes duration_ms when present."""
        from line_loop.loop import serialize_action
        record = line_loop.ActionRecord(
            tool_name="Edit",
            tool_use_id="test-id",
            input_summary="/path",
            output_summary="ok",
            success=True,
            timestamp="2026-02-03T10:00:00",
            duration_ms=150.7
        )
        data = serialize_action(record)
        expected_rounded = 151
        self.assertEqual(data["duration_ms"], expected_rounded)


class TestEpicIdValidation(unittest.TestCase):
    """Test epic_id format validation in ensure_epic_branch."""

    def test_valid_epic_ids(self):
        """Valid epic IDs pass validation."""
        import re
        valid_ids = [
            "lc-abc",
            "lc-abc.1",
            "lc-abc.1.2",
            "my_epic",
            "epic-123",
            "EPIC.2024",
            "a1b2c3",
        ]
        pattern = r'^[a-zA-Z0-9._-]+$'
        for epic_id in valid_ids:
            self.assertIsNotNone(
                re.match(pattern, epic_id),
                f"Expected '{epic_id}' to be valid"
            )

    def test_invalid_epic_ids(self):
        """Invalid epic IDs are rejected."""
        import re
        invalid_ids = [
            "epic with spaces",
            "epic/slash",
            "epic:colon",
            "epic;semicolon",
            "epic$dollar",
            "epic@at",
            "epic!bang",
            "epic#hash",
            'epic"quotes',
            "epic'quote",
            "epic`backtick",
            "; rm -rf /",  # Command injection attempt
            "epic\nline",
            "",
        ]
        pattern = r'^[a-zA-Z0-9._-]+$'
        for epic_id in invalid_ids:
            self.assertIsNone(
                re.match(pattern, epic_id),
                f"Expected '{epic_id}' to be invalid"
            )


class TestEnsureEpicBranchReturnType(unittest.TestCase):
    """Test ensure_epic_branch return type behavior.

    Note: These tests verify the return type contract without mocking
    git/bd operations. For full integration tests, see integration tests.
    """

    def test_returns_tuple(self):
        """ensure_epic_branch returns a tuple."""
        # Test with a path that won't find any epic (no .beads)
        result = line_loop.ensure_epic_branch("nonexistent-task", Path("/tmp"))
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_no_epic_returns_none_false(self):
        """Returns (None, False) when no epic is found."""
        result = line_loop.ensure_epic_branch("no-such-task", Path("/tmp"))
        expected = (None, False)
        self.assertEqual(result, expected)

    def test_return_type_unpacking(self):
        """Return value can be unpacked as (branch, was_created)."""
        branch, was_created = line_loop.ensure_epic_branch("test", Path("/tmp"))
        self.assertIsNone(branch)
        self.assertFalse(was_created)


class TestHierarchyMaxDepthConfig(unittest.TestCase):
    """Test HIERARCHY_MAX_DEPTH configuration constant."""

    def test_hierarchy_max_depth_exported(self):
        """HIERARCHY_MAX_DEPTH is exported from line_loop."""
        self.assertTrue(hasattr(line_loop, 'HIERARCHY_MAX_DEPTH'))

    def test_hierarchy_max_depth_value(self):
        """HIERARCHY_MAX_DEPTH has expected value."""
        self.assertEqual(line_loop.HIERARCHY_MAX_DEPTH, 10)

    def test_hierarchy_max_depth_is_int(self):
        """HIERARCHY_MAX_DEPTH is an integer."""
        self.assertIsInstance(line_loop.HIERARCHY_MAX_DEPTH, int)


class TestGetCurrentBranch(unittest.TestCase):
    """Test get_current_branch function."""

    def test_returns_optional_string(self):
        """get_current_branch returns Optional[str]."""
        result = line_loop.get_current_branch(Path("/tmp"))
        is_valid = result is None or isinstance(result, str)
        self.assertTrue(is_valid)


class TestGetEpicForTask(unittest.TestCase):
    """Test get_epic_for_task function."""

    def test_returns_none_for_nonexistent_task(self):
        """get_epic_for_task returns None for nonexistent task."""
        result = line_loop.get_epic_for_task("nonexistent", Path("/tmp"))
        self.assertIsNone(result)

    def test_returns_optional_string(self):
        """get_epic_for_task returns Optional[str]."""
        result = line_loop.get_epic_for_task("any-id", Path("/tmp"))
        is_valid = result is None or isinstance(result, str)
        self.assertTrue(is_valid)


class TestIsFirstEpicWork(unittest.TestCase):
    """Test is_first_epic_work function."""

    def test_returns_bool(self):
        """is_first_epic_work returns a boolean."""
        result = line_loop.is_first_epic_work("any-epic", Path("/tmp"))
        self.assertIsInstance(result, bool)

    def test_nonexistent_epic_returns_true(self):
        """For nonexistent epic (no branch, no children), returns True."""
        result = line_loop.is_first_epic_work("nonexistent-epic", Path("/tmp"))
        self.assertTrue(result)


class TestExcludedEpicTitlesConfig(unittest.TestCase):
    """Test EXCLUDED_EPIC_TITLES configuration constant."""

    def test_excluded_epic_titles_exported(self):
        """EXCLUDED_EPIC_TITLES is exported from line_loop."""
        self.assertTrue(hasattr(line_loop, 'EXCLUDED_EPIC_TITLES'))

    def test_excluded_epic_titles_is_frozenset(self):
        """EXCLUDED_EPIC_TITLES is a frozenset."""
        self.assertIsInstance(line_loop.EXCLUDED_EPIC_TITLES, frozenset)

    def test_excluded_epic_titles_contains_expected(self):
        """EXCLUDED_EPIC_TITLES contains Retrospective and Backlog."""
        self.assertIn("Retrospective", line_loop.EXCLUDED_EPIC_TITLES)
        self.assertIn("Backlog", line_loop.EXCLUDED_EPIC_TITLES)

    def test_excluded_epic_titles_exact_membership(self):
        """EXCLUDED_EPIC_TITLES has exactly the expected members."""
        expected = frozenset({"Retrospective", "Backlog"})
        self.assertEqual(line_loop.EXCLUDED_EPIC_TITLES, expected)


class TestFindEpicAncestor(unittest.TestCase):
    """Test find_epic_ancestor function."""

    def test_direct_child_of_epic(self):
        """Task directly under an epic finds that epic."""
        epic = make_bead("epic-1", "My Epic", "epic")
        task = make_bead("task-1", "My Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        result = line_loop.find_epic_ancestor(task, snapshot, Path("/tmp"))
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "epic-1")
        self.assertEqual(result.issue_type, "epic")

    def test_grandchild_through_feature(self):
        """Task under a feature under an epic finds the epic."""
        epic = make_bead("epic-1", "My Epic", "epic")
        feature = make_bead("feat-1", "My Feature", "feature", parent="epic-1")
        task = make_bead("task-1", "My Task", "task", parent="feat-1")
        snapshot = make_snapshot([epic, feature, task])
        result = line_loop.find_epic_ancestor(task, snapshot, Path("/tmp"))
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "epic-1")

    def test_no_parent_returns_none(self):
        """Task with no parent returns None."""
        task = make_bead("task-1", "Orphan Task", "task")
        snapshot = make_snapshot([task])
        result = line_loop.find_epic_ancestor(task, snapshot, Path("/tmp"))
        self.assertIsNone(result)

    def test_no_epic_in_chain(self):
        """Task under a feature (no epic above) returns None."""
        feature = make_bead("feat-1", "My Feature", "feature")
        task = make_bead("task-1", "My Task", "task", parent="feat-1")
        snapshot = make_snapshot([feature, task])
        result = line_loop.find_epic_ancestor(task, snapshot, Path("/tmp"))
        self.assertIsNone(result)


class TestIsDescendantOfEpic(unittest.TestCase):
    """Test is_descendant_of_epic function."""

    def test_direct_child(self):
        """Task directly under the target epic returns True."""
        epic = make_bead("epic-1", "My Epic", "epic")
        task = make_bead("task-1", "My Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        self.assertTrue(line_loop.is_descendant_of_epic(task, "epic-1", snapshot, Path("/tmp")))

    def test_grandchild(self):
        """Task under feature under epic returns True."""
        epic = make_bead("epic-1", "My Epic", "epic")
        feature = make_bead("feat-1", "Feature", "feature", parent="epic-1")
        task = make_bead("task-1", "Task", "task", parent="feat-1")
        snapshot = make_snapshot([epic, feature, task])
        self.assertTrue(line_loop.is_descendant_of_epic(task, "epic-1", snapshot, Path("/tmp")))

    def test_no_parent(self):
        """Task with no parent returns False."""
        task = make_bead("task-1", "Orphan", "task")
        snapshot = make_snapshot([task])
        self.assertFalse(line_loop.is_descendant_of_epic(task, "epic-1", snapshot, Path("/tmp")))

    def test_wrong_epic(self):
        """Task under a different epic returns False."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        task = make_bead("task-1", "Task", "task", parent="epic-a")
        snapshot = make_snapshot([epic_a, task])
        self.assertFalse(line_loop.is_descendant_of_epic(task, "epic-b", snapshot, Path("/tmp")))


class TestGetExcludedEpicIds(unittest.TestCase):
    """Test get_excluded_epic_ids function."""

    def test_finds_retrospective_and_backlog(self):
        """Identifies epics titled Retrospective and Backlog."""
        retro = make_bead("epic-r", "Retrospective", "epic")
        backlog = make_bead("epic-b", "Backlog", "epic")
        normal = make_bead("epic-n", "My Feature Epic", "epic")
        snapshot = make_snapshot([retro, backlog, normal])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        self.assertEqual(excluded, {"epic-r", "epic-b"})

    def test_ignores_non_epic_with_excluded_title(self):
        """Non-epic items with excluded titles are not matched."""
        task = make_bead("task-1", "Retrospective", "task")
        snapshot = make_snapshot([task])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        self.assertEqual(excluded, set())

    def test_empty_snapshot(self):
        """Empty snapshot returns empty set."""
        snapshot = make_snapshot([])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        self.assertEqual(excluded, set())

    def test_no_excluded_epics(self):
        """Snapshot with non-excluded epics returns empty set."""
        epic = make_bead("epic-1", "Important Work", "epic")
        snapshot = make_snapshot([epic])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        self.assertEqual(excluded, set())


class TestExcludedEpicFiltering(unittest.TestCase):
    """Test that get_next_ready_task excludes retro/backlog tasks."""

    def test_skips_tasks_under_retrospective(self):
        """Tasks under Retrospective epic are skipped."""
        retro = make_bead("epic-r", "Retrospective", "epic")
        task_r = make_bead("task-r", "Retro Task", "task", parent="epic-r")
        normal_epic = make_bead("epic-n", "Normal", "epic")
        task_n = make_bead("task-n", "Normal Task", "task", parent="epic-n")
        snapshot = make_snapshot([retro, task_r, normal_epic, task_n])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, excluded_epic_ids=excluded
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-n")

    def test_returns_task_under_normal_epic(self):
        """Tasks under non-excluded epics are returned."""
        epic = make_bead("epic-1", "Important", "epic")
        task = make_bead("task-1", "Important Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, excluded_epic_ids=excluded
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-1")

    def test_all_excluded_returns_none(self):
        """When all tasks are under excluded epics, returns None."""
        retro = make_bead("epic-r", "Retrospective", "epic")
        task = make_bead("task-1", "Retro Task", "task", parent="epic-r")
        snapshot = make_snapshot([retro, task])
        excluded = line_loop.get_excluded_epic_ids(snapshot)
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, excluded_epic_ids=excluded
        )
        self.assertIsNone(result)


class TestEpicFilter(unittest.TestCase):
    """Test epic_filter parameter in get_next_ready_task."""

    def test_filters_to_specific_epic(self):
        """Only returns tasks under the specified epic."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        epic_b = make_bead("epic-b", "Epic B", "epic")
        task_a = make_bead("task-a", "Task A", "task", parent="epic-a")
        task_b = make_bead("task-b", "Task B", "task", parent="epic-b")
        snapshot = make_snapshot([epic_a, epic_b, task_a, task_b])
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, epic_filter="epic-a"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-a")

    def test_epic_filter_returns_none_when_no_tasks(self):
        """Returns None when no tasks under the filtered epic."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        epic_b = make_bead("epic-b", "Epic B", "epic")
        task_b = make_bead("task-b", "Task B", "task", parent="epic-b")
        snapshot = make_snapshot([epic_a, epic_b, task_b])
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, epic_filter="epic-a"
        )
        self.assertIsNone(result)

    def test_epic_filter_with_skip_ids(self):
        """Epic filter + skip_ids work together."""
        epic = make_bead("epic-1", "Epic", "epic")
        task_1 = make_bead("task-1", "Task 1", "task", parent="epic-1")
        task_2 = make_bead("task-2", "Task 2", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task_1, task_2])
        result = line_loop.get_next_ready_task(
            Path("/tmp"), skip_ids={"task-1"}, snapshot=snapshot, epic_filter="epic-1"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-2")


class TestDetectFirstEpic(unittest.TestCase):
    """Test detect_first_epic function."""

    def test_detects_first_non_excluded_epic(self):
        """Auto-detect selects the first non-excluded epic."""
        retro = make_bead("epic-r", "Retrospective", "epic")
        normal = make_bead("epic-n", "Normal", "epic")
        task_r = make_bead("task-r", "Retro Task", "task", parent="epic-r")
        task_n = make_bead("task-n", "Normal Task", "task", parent="epic-n")
        snapshot = make_snapshot([retro, normal, task_r, task_n])
        excluded = {"epic-r"}
        result = line_loop.detect_first_epic(snapshot, excluded, set(), Path("/tmp"))
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "epic-n")

    def test_returns_none_when_all_excluded(self):
        """Returns None when all epics are excluded."""
        retro = make_bead("epic-r", "Retrospective", "epic")
        task = make_bead("task-1", "Task", "task", parent="epic-r")
        snapshot = make_snapshot([retro, task])
        excluded = {"epic-r"}
        result = line_loop.detect_first_epic(snapshot, excluded, set(), Path("/tmp"))
        self.assertIsNone(result)

    def test_skips_tasks_in_skip_ids(self):
        """Skipped tasks are not used for epic detection."""
        epic = make_bead("epic-1", "Epic", "epic")
        task_1 = make_bead("task-1", "Task 1", "task", parent="epic-1")
        task_2 = make_bead("task-2", "Task 2", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task_1, task_2])
        result = line_loop.detect_first_epic(snapshot, set(), {"task-1"}, Path("/tmp"))
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "epic-1")

    def test_returns_none_for_orphan_tasks(self):
        """Tasks without epic ancestors don't produce a detection result."""
        task = make_bead("task-1", "Orphan", "task")
        snapshot = make_snapshot([task])
        result = line_loop.detect_first_epic(snapshot, set(), set(), Path("/tmp"))
        self.assertIsNone(result)

    def test_skips_exhausted_epics(self):
        """Exhausted epic IDs are not re-detected."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        epic_b = make_bead("epic-b", "Epic B", "epic")
        task_a = make_bead("task-a", "Task A", "task", parent="epic-a")
        task_b = make_bead("task-b", "Task B", "task", parent="epic-b")
        snapshot = make_snapshot([epic_a, epic_b, task_a, task_b])
        # epic-a is exhausted, should detect epic-b instead
        result = line_loop.detect_first_epic(
            snapshot, set(), set(), Path("/tmp"), exhausted_ids={"epic-a"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "epic-b")


class TestValidateEpicId(unittest.TestCase):
    """Test validate_epic_id function."""

    def test_nonexistent_id_returns_none(self):
        """validate_epic_id returns None for nonexistent ID."""
        result = line_loop.validate_epic_id("nonexistent", Path("/tmp"))
        self.assertIsNone(result)


class TestIterationResultClosedEpics(unittest.TestCase):
    """Test closed_epics field on IterationResult."""

    def test_defaults_to_empty_list(self):
        """closed_epics defaults to empty list."""
        result = line_loop.IterationResult(
            iteration=1,
            task_id="lc-001",
            task_title="Test",
            outcome="completed",
            duration_seconds=10.0,
            serve_verdict="APPROVED",
            commit_hash="abc1234",
            success=True
        )
        self.assertEqual(result.closed_epics, [])

    def test_can_be_set(self):
        """closed_epics can contain epic IDs."""
        result = line_loop.IterationResult(
            iteration=1,
            task_id="lc-001",
            task_title="Test",
            outcome="completed",
            duration_seconds=10.0,
            serve_verdict="APPROVED",
            commit_hash="abc1234",
            success=True,
            closed_epics=["lc-abc", "lc-def"]
        )
        self.assertEqual(result.closed_epics, ["lc-abc", "lc-def"])


class TestDetectWorkedTaskTargetPreference(unittest.TestCase):
    """Test detect_worked_task target_task_id preference."""

    def test_target_preferred_over_dot_heuristic_ready_to_closed(self):
        """When multiple tasks move ready→closed, target_task_id is preferred."""
        # Before: two tasks ready
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
            closed=[],
        )
        # After: both closed
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
        )
        # Without target: dot-count heuristic would pick lc-001.1.1 (more dots)
        result_no_target = line_loop.detect_worked_task(before, after)
        self.assertEqual(result_no_target, "lc-001.1.1")

        # With target: should prefer lc-001.2 even though it has fewer dots
        result_with_target = line_loop.detect_worked_task(before, after, target_task_id="lc-001.2")
        self.assertEqual(result_with_target, "lc-001.2")

    def test_target_preferred_in_progress_to_closed(self):
        """When multiple tasks move in_progress→closed, target_task_id is preferred."""
        before = line_loop.BeadSnapshot(
            in_progress=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            in_progress=[],
            closed=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
        )
        # Without target: dot-count heuristic picks lc-001.1.1
        result_no_target = line_loop.detect_worked_task(before, after)
        self.assertEqual(result_no_target, "lc-001.1.1")

        # With target: should prefer lc-001.2
        result_with_target = line_loop.detect_worked_task(before, after, target_task_id="lc-001.2")
        self.assertEqual(result_with_target, "lc-001.2")

    def test_target_preferred_ready_to_in_progress(self):
        """When multiple tasks move ready→in_progress, target_task_id is preferred."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001", "Task A", "task"),
                make_bead("lc-002", "Task B", "task"),
            ],
            in_progress=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            in_progress=[
                make_bead("lc-001", "Task A", "task"),
                make_bead("lc-002", "Task B", "task"),
            ],
        )
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-002")
        self.assertEqual(result, "lc-002")

    def test_target_absent_falls_back_to_heuristic(self):
        """When target_task_id is not in the changed set, falls back to dot-count."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
        )
        # Target not in the changed set — falls back to dot-count heuristic
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-999")
        self.assertEqual(result, "lc-001.1.1")

    def test_none_target_uses_heuristic(self):
        """When target_task_id is None, uses existing heuristic (backwards compat)."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                make_bead("lc-001.1.1", "Deep task", "task"),
                make_bead("lc-001.2", "Shallow task", "task"),
            ],
        )
        result = line_loop.detect_worked_task(before, after, target_task_id=None)
        self.assertEqual(result, "lc-001.1.1")


class TestReopenTaskForRetry(unittest.TestCase):
    """Test _reopen_task_for_retry() helper."""

    def test_noop_with_no_task_id(self):
        """Does nothing when task_id is None."""
        from line_loop.iteration import _reopen_task_for_retry
        # Should not raise
        _reopen_task_for_retry(None, Path("/tmp"))

    def test_noop_with_empty_task_id(self):
        """Does nothing when task_id is empty string."""
        from line_loop.iteration import _reopen_task_for_retry
        # Should not raise
        _reopen_task_for_retry("", Path("/tmp"))

    def test_calls_bd_update(self):
        """Calls bd update with correct args when task_id is provided."""
        from unittest.mock import patch, MagicMock
        from line_loop.iteration import _reopen_task_for_retry

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("line_loop.iteration.run_subprocess", return_value=mock_result) as mock_sub:
            _reopen_task_for_retry("lc-123", Path("/tmp"))
            mock_sub.assert_called_once()
            args = mock_sub.call_args[0][0]
            self.assertEqual(args, ["bd", "update", "lc-123", "--status=in_progress"])

    def test_handles_subprocess_failure(self):
        """Logs warning but does not raise on subprocess failure."""
        from unittest.mock import patch, MagicMock
        from line_loop.iteration import _reopen_task_for_retry

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not found"

        with patch("line_loop.iteration.run_subprocess", return_value=mock_result):
            # Should not raise
            _reopen_task_for_retry("lc-bad", Path("/tmp"))

    def test_handles_exception(self):
        """Logs warning but does not raise on exception."""
        from unittest.mock import patch
        from line_loop.iteration import _reopen_task_for_retry

        with patch("line_loop.iteration.run_subprocess", side_effect=Exception("timeout")):
            # Should not raise
            _reopen_task_for_retry("lc-err", Path("/tmp"))


class TestRunIterationTargetTaskId(unittest.TestCase):
    """Test that run_iteration passes target_task_id to cook."""

    def test_cook_receives_task_id(self):
        """Cook phase receives target_task_id as args."""
        from unittest.mock import patch

        # Create a mock snapshot with ready work
        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("lc-123", "Test task", "task")]
        )

        # Mock run_phase to track calls and return appropriate results
        cook_result = line_loop.PhaseResult(
            phase="cook", success=True, output="KITCHEN_COMPLETE",
            exit_code=0, duration_seconds=5.0, signals=["kitchen_complete"]
        )
        serve_result = line_loop.PhaseResult(
            phase="serve", success=True,
            output="verdict: APPROVED\ncontinue: true\nblocking_issues: 0",
            exit_code=0, duration_seconds=3.0
        )
        tidy_result = line_loop.PhaseResult(
            phase="tidy", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )

        phase_calls = []

        def mock_run_phase(phase, cwd, **kwargs):
            phase_calls.append((phase, kwargs.get("args", "")))
            if phase == "cook":
                return cook_result
            elif phase == "serve":
                return serve_result
            else:
                return tidy_result

        with patch("line_loop.iteration.run_phase", side_effect=mock_run_phase), \
             patch("line_loop.iteration.get_bead_snapshot", return_value=snapshot), \
             patch("line_loop.iteration.detect_worked_task", return_value="lc-123"), \
             patch("line_loop.iteration.get_task_title", return_value="Test task"), \
             patch("line_loop.iteration.get_latest_commit", return_value="abc1234"), \
             patch("line_loop.iteration.check_feature_completion", return_value=(False, None)):
            result = line_loop.run_iteration(
                1, 10, Path("/tmp"),
                json_output=True,
                before_snapshot=snapshot,
                target_task_id="lc-123"
            )

        # Verify cook was called with target task ID as args
        cook_calls = [(p, a) for p, a in phase_calls if p == "cook"]
        self.assertEqual(len(cook_calls), 1)
        self.assertEqual(cook_calls[0][1], "lc-123")

    def test_cook_receives_empty_args_when_no_target(self):
        """Cook phase receives empty args when no target_task_id."""
        from unittest.mock import patch

        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("lc-123", "Test task", "task")]
        )

        cook_result = line_loop.PhaseResult(
            phase="cook", success=True, output="KITCHEN_COMPLETE",
            exit_code=0, duration_seconds=5.0, signals=["kitchen_complete"]
        )
        serve_result = line_loop.PhaseResult(
            phase="serve", success=True,
            output="verdict: APPROVED\ncontinue: true\nblocking_issues: 0",
            exit_code=0, duration_seconds=3.0
        )
        tidy_result = line_loop.PhaseResult(
            phase="tidy", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )

        phase_calls = []

        def mock_run_phase(phase, cwd, **kwargs):
            phase_calls.append((phase, kwargs.get("args", "")))
            if phase == "cook":
                return cook_result
            elif phase == "serve":
                return serve_result
            else:
                return tidy_result

        with patch("line_loop.iteration.run_phase", side_effect=mock_run_phase), \
             patch("line_loop.iteration.get_bead_snapshot", return_value=snapshot), \
             patch("line_loop.iteration.detect_worked_task", return_value="lc-123"), \
             patch("line_loop.iteration.get_task_title", return_value="Test task"), \
             patch("line_loop.iteration.get_latest_commit", return_value="abc1234"), \
             patch("line_loop.iteration.check_feature_completion", return_value=(False, None)):
            result = line_loop.run_iteration(
                1, 10, Path("/tmp"),
                json_output=True,
                before_snapshot=snapshot
            )

        # Verify cook was called with empty args
        cook_calls = [(p, a) for p, a in phase_calls if p == "cook"]
        self.assertEqual(len(cook_calls), 1)
        self.assertEqual(cook_calls[0][1], "")


class TestNeedsChangesReopensTask(unittest.TestCase):
    """Test that NEEDS_CHANGES verdict reopens the task for retry."""

    def test_task_reopened_on_needs_changes(self):
        """Task is reopened via bd update when serve returns NEEDS_CHANGES."""
        from unittest.mock import patch, MagicMock

        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("lc-123", "Test task", "task")]
        )

        cook_result = line_loop.PhaseResult(
            phase="cook", success=True, output="KITCHEN_COMPLETE",
            exit_code=0, duration_seconds=5.0, signals=["kitchen_complete"]
        )
        needs_changes_output = "verdict: NEEDS_CHANGES\ncontinue: false\nblocking_issues: 1"
        serve_needs = line_loop.PhaseResult(
            phase="serve", success=True,
            output=needs_changes_output,
            exit_code=0, duration_seconds=3.0
        )

        subprocess_calls = []

        def mock_run_phase(phase, cwd, **kwargs):
            if phase == "cook":
                return cook_result
            elif phase == "serve":
                return serve_needs
            return line_loop.PhaseResult(
                phase=phase, success=True, output="",
                exit_code=0, duration_seconds=1.0
            )

        mock_subprocess_result = MagicMock()
        mock_subprocess_result.returncode = 0
        mock_subprocess_result.stderr = ""

        def mock_run_subprocess(cmd, timeout, cwd):
            subprocess_calls.append(cmd)
            return mock_subprocess_result

        with patch("line_loop.iteration.run_phase", side_effect=mock_run_phase), \
             patch("line_loop.iteration.get_bead_snapshot", return_value=snapshot), \
             patch("line_loop.iteration.detect_worked_task", return_value="lc-123"), \
             patch("line_loop.iteration.get_task_title", return_value="Test task"), \
             patch("line_loop.iteration.get_latest_commit", return_value="abc1234"), \
             patch("line_loop.iteration.check_feature_completion", return_value=(False, None)), \
             patch("line_loop.iteration.run_subprocess", side_effect=mock_run_subprocess):
            result = line_loop.run_iteration(
                1, 10, Path("/tmp"),
                max_cook_retries=1,
                json_output=True,
                before_snapshot=snapshot,
                target_task_id="lc-123"
            )

        # Find bd update calls that reopen the task
        reopen_calls = [
            cmd for cmd in subprocess_calls
            if cmd == ["bd", "update", "lc-123", "--status=in_progress"]
        ]
        self.assertGreaterEqual(len(reopen_calls), 1,
                                "Expected at least one bd update call to reopen task")


class TestClosedEpicsPopulated(unittest.TestCase):
    """Test that closed_epics is populated after close-service."""

    def test_closed_epics_populated_after_close_service(self):
        """closed_epics contains epic ID after successful close-service."""
        from unittest.mock import patch

        snapshot_before = line_loop.BeadSnapshot(
            ready=[make_bead("lc-abc.1.1", "Task", "task", parent="lc-abc.1")]
        )
        snapshot_after = line_loop.BeadSnapshot(
            ready=[],
            closed=[make_bead("lc-abc.1.1", "Task", "task", parent="lc-abc.1")]
        )

        cook_result = line_loop.PhaseResult(
            phase="cook", success=True, output="done",
            exit_code=0, duration_seconds=5.0
        )
        serve_result = line_loop.PhaseResult(
            phase="serve", success=True,
            output="verdict: APPROVED\ncontinue: true\nblocking_issues: 0",
            exit_code=0, duration_seconds=3.0
        )
        tidy_result = line_loop.PhaseResult(
            phase="tidy", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )
        plate_result = line_loop.PhaseResult(
            phase="plate", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )
        cs_result = line_loop.PhaseResult(
            phase="close-service", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )

        def mock_run_phase(phase, cwd, **kwargs):
            if phase == "cook":
                return cook_result
            elif phase == "serve":
                return serve_result
            elif phase == "tidy":
                return tidy_result
            elif phase == "plate":
                return plate_result
            elif phase == "close-service":
                return cs_result
            return tidy_result

        with patch("line_loop.iteration.run_phase", side_effect=mock_run_phase), \
             patch("line_loop.iteration.get_bead_snapshot", return_value=snapshot_after), \
             patch("line_loop.iteration.detect_worked_task", return_value="lc-abc.1.1"), \
             patch("line_loop.iteration.get_task_title", return_value="Task"), \
             patch("line_loop.iteration.get_latest_commit", return_value="abc1234"), \
             patch("line_loop.iteration.check_feature_completion", return_value=(True, "lc-abc.1")), \
             patch("line_loop.iteration.get_task_info", return_value={"title": "Feature", "issue_type": "feature"}), \
             patch("line_loop.iteration.get_children", return_value=[{"issue_type": "task", "status": "closed"}]), \
             patch("line_loop.iteration.check_epic_completion_after_feature", return_value=(True, "lc-abc")):
            result = line_loop.run_iteration(
                1, 10, Path("/tmp"),
                json_output=True,
                before_snapshot=snapshot_before
            )

        self.assertEqual(result.closed_epics, ["lc-abc"])

    def test_closed_epics_empty_when_no_epic_close(self):
        """closed_epics is empty when no epic was closed."""
        from unittest.mock import patch

        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("lc-001", "Task", "task")]
        )

        cook_result = line_loop.PhaseResult(
            phase="cook", success=True, output="done",
            exit_code=0, duration_seconds=5.0
        )
        serve_result = line_loop.PhaseResult(
            phase="serve", success=True,
            output="verdict: APPROVED\ncontinue: true\nblocking_issues: 0",
            exit_code=0, duration_seconds=3.0
        )
        tidy_result = line_loop.PhaseResult(
            phase="tidy", success=True, output="",
            exit_code=0, duration_seconds=2.0
        )

        def mock_run_phase(phase, cwd, **kwargs):
            if phase == "cook":
                return cook_result
            elif phase == "serve":
                return serve_result
            else:
                return tidy_result

        with patch("line_loop.iteration.run_phase", side_effect=mock_run_phase), \
             patch("line_loop.iteration.get_bead_snapshot", return_value=snapshot), \
             patch("line_loop.iteration.detect_worked_task", return_value="lc-001"), \
             patch("line_loop.iteration.get_task_title", return_value="Task"), \
             patch("line_loop.iteration.get_latest_commit", return_value="abc1234"), \
             patch("line_loop.iteration.check_feature_completion", return_value=(False, None)):
            result = line_loop.run_iteration(
                1, 10, Path("/tmp"),
                json_output=True,
                before_snapshot=snapshot
            )

        self.assertEqual(result.closed_epics, [])


class TestCircuitBreakerPatterns(unittest.TestCase):
    """Integration tests for circuit breaker with various failure patterns.

    Validates that the circuit breaker correctly evaluates the full sliding
    window under different failure distributions: intermittent, burst,
    recovery after tripping, and window sliding.
    """

    def _make_breaker(self, threshold=5, window=10):
        """Create a circuit breaker with given parameters."""
        return line_loop.CircuitBreaker(failure_threshold=threshold, window_size=window)

    def test_intermittent_alternating_trips(self):
        """Alternating [S,F,S,F,S,F,S,F,S,F] has 5 failures — trips at threshold."""
        cb = self._make_breaker(threshold=5, window=10)
        for _ in range(5):
            cb.record(True)
            cb.record(False)
        # 5 successes, 5 failures in window of 10
        self.assertTrue(cb.is_open())

    def test_intermittent_below_threshold(self):
        """Alternating [S,F,S,F,S,F,S,F,S,S] has 4 failures — stays closed."""
        cb = self._make_breaker(threshold=5, window=10)
        for _ in range(4):
            cb.record(True)
            cb.record(False)
        cb.record(True)
        cb.record(True)
        # 6 successes, 4 failures — below threshold
        self.assertFalse(cb.is_open())

    def test_burst_at_start(self):
        """[F,F,F,F,F,S,S,S,S,S] — 5 failures in window trips the breaker."""
        cb = self._make_breaker(threshold=5, window=10)
        for _ in range(5):
            cb.record(False)
        for _ in range(5):
            cb.record(True)
        self.assertTrue(cb.is_open())

    def test_burst_at_end(self):
        """[S,S,S,S,S,F,F,F,F,F] — 5 failures in window trips the breaker."""
        cb = self._make_breaker(threshold=5, window=10)
        for _ in range(5):
            cb.record(True)
        for _ in range(5):
            cb.record(False)
        self.assertTrue(cb.is_open())

    def test_recovery_after_tripping(self):
        """After tripping, adding enough successes slides failures out of window."""
        cb = self._make_breaker(threshold=5, window=10)
        # Trip it: 5 failures
        for _ in range(5):
            cb.record(False)
        self.assertTrue(cb.is_open())
        # Add 6 successes — window slides to [F,F,F,F,S,S,S,S,S,S] (4 failures < 5 threshold)
        for _ in range(6):
            cb.record(True)
        self.assertFalse(cb.is_open())

    def test_window_sliding_pushes_old_failures_out(self):
        """Old failures slide out as new successes are recorded."""
        cb = self._make_breaker(threshold=3, window=5)
        # Record 3 failures — trips
        cb.record(False)
        cb.record(False)
        cb.record(False)
        self.assertTrue(cb.is_open())
        # Add 3 successes — window becomes [F,F,F,S,S,S], keeps last 5: [F,F,S,S,S]
        # 2 failures — below threshold
        cb.record(True)
        cb.record(True)
        cb.record(True)
        self.assertFalse(cb.is_open())

    def test_scattered_failures_accumulate(self):
        """Scattered failures throughout window accumulate correctly."""
        cb = self._make_breaker(threshold=4, window=8)
        # Pattern: [F,S,S,F,S,F,S,F] — 4 failures, 4 successes
        pattern = [False, True, True, False, True, False, True, False]
        for success in pattern:
            cb.record(success)
        self.assertTrue(cb.is_open())

    def test_exact_threshold_boundary(self):
        """Exactly threshold-1 failures stays closed, threshold trips."""
        cb = self._make_breaker(threshold=3, window=10)
        cb.record(False)
        cb.record(False)
        self.assertFalse(cb.is_open())  # 2 < 3
        cb.record(False)
        self.assertTrue(cb.is_open())   # 3 >= 3

    def test_minimum_window_fill(self):
        """Circuit breaker requires at least failure_threshold records before tripping."""
        cb = self._make_breaker(threshold=5, window=10)
        # Only 4 failures recorded (< threshold items total)
        for _ in range(4):
            cb.record(False)
        self.assertFalse(cb.is_open())
        # Fifth failure makes it trip
        cb.record(False)
        self.assertTrue(cb.is_open())


class TestDetectWorkedTaskWithTarget(unittest.TestCase):
    """Integration tests for detect_worked_task with multi-task scenarios.

    Validates target_task_id preference across different state transitions:
    multiple tasks closing simultaneously, mixed state changes, and
    fallback behavior when target is not in the changed set.
    """

    def test_three_tasks_close_target_preferred(self):
        """When 3 tasks close simultaneously, target is preferred."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001.1.1", "Deep", "task"),
                make_bead("lc-001.1.2", "Mid", "task"),
                make_bead("lc-001.2", "Shallow", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                make_bead("lc-001.1.1", "Deep", "task"),
                make_bead("lc-001.1.2", "Mid", "task"),
                make_bead("lc-001.2", "Shallow", "task"),
            ],
        )
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-001.2")
        self.assertEqual(result, "lc-001.2")

    def test_mixed_state_transitions_target_in_progress(self):
        """Target moves to in_progress while other tasks also change."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001", "Task A", "task"),
                make_bead("lc-002", "Task B", "task"),
                make_bead("lc-003", "Task C", "task"),
            ],
            in_progress=[],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[make_bead("lc-003", "Task C", "task")],
            in_progress=[make_bead("lc-002", "Task B", "task")],
            closed=[make_bead("lc-001", "Task A", "task")],
        )
        # lc-002 moved to in_progress — should be detected as the worked task
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-002")
        self.assertEqual(result, "lc-002")

    def test_target_not_in_any_changed_set(self):
        """When target didn't change at all, heuristic picks deepest."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001.1.1", "Deep", "task"),
                make_bead("lc-001.2", "Shallow", "task"),
                make_bead("lc-999", "Target", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[make_bead("lc-999", "Target", "task")],
            closed=[
                make_bead("lc-001.1.1", "Deep", "task"),
                make_bead("lc-001.2", "Shallow", "task"),
            ],
        )
        # lc-999 is still ready — not in changed set, fallback to heuristic
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-999")
        self.assertEqual(result, "lc-001.1.1")  # deepest by dot count

    def test_no_state_changes_returns_none(self):
        """When nothing changed, returns None regardless of target."""
        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("lc-001", "Task", "task")],
        )
        result = line_loop.detect_worked_task(snapshot, snapshot, target_task_id="lc-001")
        self.assertIsNone(result)

    def test_target_in_new_in_progress_preferred_over_other(self):
        """When multiple tasks move to in_progress, target is preferred."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001", "Task A", "task"),
                make_bead("lc-002", "Task B", "task"),
            ],
            in_progress=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            in_progress=[
                make_bead("lc-001", "Task A", "task"),
                make_bead("lc-002", "Task B", "task"),
            ],
        )
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-002")
        self.assertEqual(result, "lc-002")

    def test_feature_and_task_close_target_is_task(self):
        """When task + parent feature both close, target picks the task."""
        before = line_loop.BeadSnapshot(
            ready=[
                make_bead("lc-001", "Feature", "feature"),
                make_bead("lc-001.1", "Task", "task"),
            ],
            closed=[],
        )
        after = line_loop.BeadSnapshot(
            ready=[],
            closed=[
                make_bead("lc-001", "Feature", "feature"),
                make_bead("lc-001.1", "Task", "task"),
            ],
        )
        result = line_loop.detect_worked_task(before, after, target_task_id="lc-001.1")
        self.assertEqual(result, "lc-001.1")


class TestCircuitBreakerSkipListInteraction(unittest.TestCase):
    """Integration tests for circuit breaker + skip list working together.

    In the loop, both systems track failures independently:
    - CircuitBreaker: stops the entire loop on too many overall failures
    - SkipList: skips individual tasks after repeated failures

    These tests verify the combined behavior.
    """

    def test_skip_list_fills_before_circuit_breaker(self):
        """Task gets skipped (3 failures) before circuit breaker trips (5 failures)."""
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        sl = line_loop.SkipList(max_failures=3)

        task_id = "lc-001"
        # First 2 failures: not yet skipped, breaker still closed
        for _ in range(2):
            cb.record(False)
            self.assertFalse(sl.record_failure(task_id))
            self.assertFalse(cb.is_open())

        # Third failure: task becomes skipped, breaker still closed
        cb.record(False)
        sl.record_failure(task_id)
        self.assertTrue(sl.is_skipped(task_id))
        self.assertFalse(cb.is_open())

    def test_circuit_breaker_trips_before_single_task_skipped(self):
        """Multiple tasks failing can trip circuit breaker before any single task is skipped."""
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        sl = line_loop.SkipList(max_failures=3)

        # 5 different tasks each fail once
        for i in range(5):
            task_id = f"lc-{i:03d}"
            cb.record(False)
            sl.record_failure(task_id)

        # Circuit breaker tripped but no task is individually skipped
        self.assertTrue(cb.is_open())
        self.assertEqual(sl.get_skipped_ids(), set())

    def test_success_clears_skip_list_but_not_breaker(self):
        """Success on a task clears its skip list entry but breaker still has the failures."""
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        sl = line_loop.SkipList(max_failures=3)

        # Record 2 failures for task
        cb.record(False)
        cb.record(False)
        sl.record_failure("lc-001")
        sl.record_failure("lc-001")

        # Task succeeds
        cb.record(True)
        sl.record_success("lc-001")

        # Skip list cleared for task, but breaker still has 2 failures in window
        self.assertFalse(sl.is_skipped("lc-001"))
        self.assertEqual(sl.failed_tasks, {})
        # Breaker window: [F, F, S] — 2 failures, below threshold of 5
        self.assertFalse(cb.is_open())

    def test_all_tasks_skipped_breaker_may_not_trip(self):
        """All tasks can be skipped without the circuit breaker tripping."""
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        sl = line_loop.SkipList(max_failures=2)

        # Two tasks each fail 2 times — both skipped, only 4 total failures
        sl.record_failure("lc-001")
        cb.record(False)
        sl.record_failure("lc-001")
        cb.record(False)
        sl.record_failure("lc-002")
        cb.record(False)
        sl.record_failure("lc-002")
        cb.record(False)

        self.assertTrue(sl.is_skipped("lc-001"))
        self.assertTrue(sl.is_skipped("lc-002"))
        self.assertEqual(sl.get_skipped_ids(), {"lc-001", "lc-002"})
        # 4 failures < 5 threshold
        self.assertFalse(cb.is_open())

    def test_both_trip_simultaneously(self):
        """Both systems can trigger at the same time."""
        cb = line_loop.CircuitBreaker(failure_threshold=5, window_size=10)
        sl = line_loop.SkipList(max_failures=5)

        task_id = "lc-001"
        for _ in range(5):
            cb.record(False)
            sl.record_failure(task_id)

        # Both should be triggered
        self.assertTrue(cb.is_open())
        self.assertTrue(sl.is_skipped(task_id))

    def test_skip_list_independent_across_tasks(self):
        """Each task's skip list counter is independent while breaker tracks all."""
        cb = line_loop.CircuitBreaker(failure_threshold=6, window_size=10)
        sl = line_loop.SkipList(max_failures=3)

        # 3 failures on lc-001 (gets skipped), 2 on lc-002 (not skipped)
        for _ in range(3):
            sl.record_failure("lc-001")
            cb.record(False)
        for _ in range(2):
            sl.record_failure("lc-002")
            cb.record(False)

        self.assertTrue(sl.is_skipped("lc-001"))
        self.assertFalse(sl.is_skipped("lc-002"))
        # 5 total failures in breaker window — below threshold of 6
        self.assertFalse(cb.is_open())

    def test_reset_breaker_doesnt_affect_skip_list(self):
        """Resetting the circuit breaker doesn't clear the skip list."""
        cb = line_loop.CircuitBreaker(failure_threshold=3, window_size=5)
        sl = line_loop.SkipList(max_failures=3)

        for _ in range(3):
            cb.record(False)
            sl.record_failure("lc-001")

        self.assertTrue(cb.is_open())
        self.assertTrue(sl.is_skipped("lc-001"))

        cb.reset()
        self.assertFalse(cb.is_open())
        self.assertTrue(sl.is_skipped("lc-001"))  # Skip list unaffected


class TestBuildEpicAncestorMap(unittest.TestCase):
    """Test build_epic_ancestor_map function."""

    def test_empty_snapshot(self):
        """Empty snapshot returns empty map."""
        snapshot = make_snapshot([])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result, {})

    def test_task_directly_under_epic(self):
        """Task directly under an epic maps to that epic."""
        epic = make_bead("epic-1", "My Epic", "epic")
        task = make_bead("task-1", "My Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result["task-1"], "epic-1")

    def test_task_under_feature_under_epic(self):
        """Task under feature under epic maps to the epic."""
        epic = make_bead("epic-1", "My Epic", "epic")
        feature = make_bead("feat-1", "Feature", "feature", parent="epic-1")
        task = make_bead("task-1", "Task", "task", parent="feat-1")
        snapshot = make_snapshot([epic, feature, task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result["task-1"], "epic-1")

    def test_orphan_task_maps_to_none(self):
        """Task with no parent maps to None."""
        task = make_bead("task-1", "Orphan", "task")
        snapshot = make_snapshot([task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertIn("task-1", result)
        self.assertIsNone(result["task-1"])

    def test_task_under_feature_no_epic(self):
        """Task under a feature with no epic ancestor maps to None."""
        feature = make_bead("feat-1", "Feature", "feature")
        task = make_bead("task-1", "Task", "task", parent="feat-1")
        snapshot = make_snapshot([feature, task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertIsNone(result["task-1"])

    def test_multiple_tasks_same_epic(self):
        """Multiple tasks under the same epic all map correctly."""
        epic = make_bead("epic-1", "Epic", "epic")
        feat = make_bead("feat-1", "Feature", "feature", parent="epic-1")
        task_a = make_bead("task-a", "Task A", "task", parent="feat-1")
        task_b = make_bead("task-b", "Task B", "task", parent="feat-1")
        snapshot = make_snapshot([epic, feat, task_a, task_b])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result["task-a"], "epic-1")
        self.assertEqual(result["task-b"], "epic-1")

    def test_tasks_under_different_epics(self):
        """Tasks under different epics map to their respective epics."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        epic_b = make_bead("epic-b", "Epic B", "epic")
        task_a = make_bead("task-a", "Task A", "task", parent="epic-a")
        task_b = make_bead("task-b", "Task B", "task", parent="epic-b")
        snapshot = make_snapshot([epic_a, epic_b, task_a, task_b])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result["task-a"], "epic-a")
        self.assertEqual(result["task-b"], "epic-b")

    def test_epics_excluded_from_walk(self):
        """Epics in ready list are not walked (ready_work filters them)."""
        epic = make_bead("epic-1", "Epic", "epic")
        task = make_bead("task-1", "Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        # Only task should be in the map, epic is not a ready_work item
        self.assertIn("task-1", result)
        # Epic itself should only appear if encountered as intermediate during walk
        # (it is NOT walked as a starting point)

    def test_dangling_parent_maps_to_none(self):
        """Task whose parent is not in the snapshot maps to None."""
        task = make_bead("task-1", "Task", "task", parent="nonexistent")
        snapshot = make_snapshot([task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertIsNone(result["task-1"])

    def test_feature_as_ready_work(self):
        """Features in ready_work are also walked."""
        epic = make_bead("epic-1", "Epic", "epic")
        feature = make_bead("feat-1", "Feature", "feature", parent="epic-1")
        snapshot = make_snapshot([epic, feature])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        self.assertEqual(result["feat-1"], "epic-1")

    def test_intermediate_beads_cached(self):
        """Intermediate beads encountered during walk are cached."""
        epic = make_bead("epic-1", "Epic", "epic")
        feature = make_bead("feat-1", "Feature", "feature", parent="epic-1")
        task = make_bead("task-1", "Task", "task", parent="feat-1")
        snapshot = make_snapshot([epic, feature, task])
        result = line_loop.build_epic_ancestor_map(snapshot, Path("/tmp"))
        # Both the task and the intermediate feature should be cached
        self.assertEqual(result["task-1"], "epic-1")
        self.assertIn("feat-1", result)
        self.assertEqual(result["feat-1"], "epic-1")


class TestAncestorMapIntegration(unittest.TestCase):
    """Test that callers work with ancestor_map parameter."""

    def test_detect_first_epic_with_map(self):
        """detect_first_epic uses ancestor_map when provided."""
        epic = make_bead("epic-1", "My Epic", "epic")
        task = make_bead("task-1", "Task", "task", parent="epic-1")
        snapshot = make_snapshot([epic, task])
        ancestor_map = {"task-1": "epic-1"}
        result = line_loop.detect_first_epic(
            snapshot, set(), set(), Path("/tmp"),
            ancestor_map=ancestor_map
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "epic-1")

    def test_detect_first_epic_excludes_with_map(self):
        """detect_first_epic respects excluded_ids when using ancestor_map."""
        epic = make_bead("epic-r", "Retrospective", "epic")
        task = make_bead("task-1", "Task", "task", parent="epic-r")
        snapshot = make_snapshot([epic, task])
        ancestor_map = {"task-1": "epic-r"}
        result = line_loop.detect_first_epic(
            snapshot, {"epic-r"}, set(), Path("/tmp"),
            ancestor_map=ancestor_map
        )
        self.assertIsNone(result)

    def test_filter_excluded_with_map(self):
        """_filter_excluded_epics uses ancestor_map when provided."""
        from line_loop.loop import _filter_excluded_epics
        epic_r = make_bead("epic-r", "Retro", "epic")
        epic_n = make_bead("epic-n", "Normal", "epic")
        task_r = make_bead("task-r", "Retro Task", "task", parent="epic-r")
        task_n = make_bead("task-n", "Normal Task", "task", parent="epic-n")
        snapshot = make_snapshot([epic_r, epic_n, task_r, task_n])
        ancestor_map = {"task-r": "epic-r", "task-n": "epic-n"}
        result = _filter_excluded_epics(
            [task_r, task_n], {"epic-r"}, snapshot, Path("/tmp"),
            ancestor_map=ancestor_map
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "task-n")

    def test_get_next_ready_task_epic_filter_with_map(self):
        """get_next_ready_task uses ancestor_map for epic filtering."""
        epic_a = make_bead("epic-a", "Epic A", "epic")
        epic_b = make_bead("epic-b", "Epic B", "epic")
        task_a = make_bead("task-a", "Task A", "task", parent="epic-a")
        task_b = make_bead("task-b", "Task B", "task", parent="epic-b")
        snapshot = make_snapshot([epic_a, epic_b, task_a, task_b])
        ancestor_map = {"task-a": "epic-a", "task-b": "epic-b"}
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, epic_filter="epic-a",
            ancestor_map=ancestor_map
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-a")

    def test_get_next_ready_task_excluded_with_map(self):
        """get_next_ready_task uses ancestor_map for excluded epic filtering."""
        epic_r = make_bead("epic-r", "Retro", "epic")
        epic_n = make_bead("epic-n", "Normal", "epic")
        task_r = make_bead("task-r", "Retro Task", "task", parent="epic-r")
        task_n = make_bead("task-n", "Normal Task", "task", parent="epic-n")
        snapshot = make_snapshot([epic_r, epic_n, task_r, task_n])
        ancestor_map = {"task-r": "epic-r", "task-n": "epic-n"}
        result = line_loop.get_next_ready_task(
            Path("/tmp"), snapshot=snapshot, excluded_epic_ids={"epic-r"},
            ancestor_map=ancestor_map
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[0], "task-n")


class TestCachedGetTaskInfo(unittest.TestCase):
    """Test _cached_get_task_info() caching helper."""

    def test_returns_cached_value_without_subprocess(self):
        """Returns cached value and does not call get_task_info."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_task_info

        cache = {"lc-001": {"id": "lc-001", "title": "Cached Task"}}
        with patch("line_loop.iteration.get_task_info") as mock_gti:
            result = _cached_get_task_info("lc-001", Path("/tmp"), cache)
            self.assertEqual(result["title"], "Cached Task")
            mock_gti.assert_not_called()

    def test_populates_cache_on_miss(self):
        """Calls get_task_info and stores result on cache miss."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_task_info

        cache = {}
        with patch("line_loop.iteration.get_task_info",
                    return_value={"id": "lc-002", "title": "Fresh"}) as mock_gti:
            result = _cached_get_task_info("lc-002", Path("/tmp"), cache)
            self.assertEqual(result["title"], "Fresh")
            mock_gti.assert_called_once_with("lc-002", Path("/tmp"))
            self.assertIn("lc-002", cache)

    def test_caches_none_result(self):
        """Caches None when get_task_info returns None (avoids re-query)."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_task_info

        cache = {}
        with patch("line_loop.iteration.get_task_info", return_value=None) as mock_gti:
            result1 = _cached_get_task_info("lc-bad", Path("/tmp"), cache)
            result2 = _cached_get_task_info("lc-bad", Path("/tmp"), cache)
            self.assertIsNone(result1)
            self.assertIsNone(result2)
            mock_gti.assert_called_once()  # Only called once, second from cache


class TestCachedGetChildren(unittest.TestCase):
    """Test _cached_get_children() caching helper."""

    def test_returns_cached_value_without_subprocess(self):
        """Returns cached children without calling get_children."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_children

        children = [{"id": "t-1", "status": "closed"}]
        cache = {"f-001": children}
        with patch("line_loop.iteration.get_children") as mock_gc:
            result = _cached_get_children("f-001", Path("/tmp"), cache)
            self.assertEqual(result, children)
            mock_gc.assert_not_called()

    def test_populates_cache_on_miss(self):
        """Calls get_children and stores result on cache miss."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_children

        children = [{"id": "t-1", "status": "closed"}, {"id": "t-2", "status": "closed"}]
        cache = {}
        with patch("line_loop.iteration.get_children", return_value=children) as mock_gc:
            result = _cached_get_children("f-002", Path("/tmp"), cache)
            self.assertEqual(len(result), 2)
            mock_gc.assert_called_once_with("f-002", Path("/tmp"))
            self.assertIn("f-002", cache)

    def test_caches_empty_list_result(self):
        """Caches empty list when get_children returns [] (avoids re-query)."""
        from unittest.mock import patch
        from line_loop.iteration import _cached_get_children

        cache = {}
        with patch("line_loop.iteration.get_children", return_value=[]) as mock_gc:
            result1 = _cached_get_children("f-empty", Path("/tmp"), cache)
            result2 = _cached_get_children("f-empty", Path("/tmp"), cache)
            self.assertEqual(result1, [])
            self.assertEqual(result2, [])
            mock_gc.assert_called_once()


class TestFeatureCompletionWithCache(unittest.TestCase):
    """Test check_feature_completion with task_info_cache parameter."""

    def test_uses_provided_cache(self):
        """check_feature_completion uses cache for get_task_info lookups."""
        from unittest.mock import patch
        task_info_cache = {
            "t-001": {"id": "t-001", "parent": "f-001", "issue_type": "task"},
            "f-001": {"id": "f-001", "issue_type": "feature", "parent": "e-001"},
        }
        children_cache = {
            "f-001": [{"id": "t-001", "status": "closed"}],
        }
        with patch("line_loop.iteration.get_task_info") as mock_gti, \
             patch("line_loop.iteration.get_children") as mock_gc:
            complete, feature_id = line_loop.check_feature_completion(
                "t-001", Path("/tmp"),
                task_info_cache=task_info_cache,
                children_cache=children_cache
            )
            self.assertTrue(complete)
            self.assertEqual(feature_id, "f-001")
            # Should NOT call subprocess (all from cache)
            mock_gti.assert_not_called()
            mock_gc.assert_not_called()

    def test_populates_cache_for_reuse(self):
        """check_feature_completion populates cache for later use."""
        from unittest.mock import patch
        task_info_cache = {}
        children_cache = {}

        task_data = {"id": "t-001", "parent": "f-001", "issue_type": "task"}
        feature_data = {"id": "f-001", "issue_type": "feature", "parent": "e-001"}
        children_data = [{"id": "t-001", "status": "closed"}]

        with patch("line_loop.iteration.get_task_info",
                    side_effect=lambda tid, cwd: {"t-001": task_data, "f-001": feature_data}.get(tid)), \
             patch("line_loop.iteration.get_children", return_value=children_data):
            complete, feature_id = line_loop.check_feature_completion(
                "t-001", Path("/tmp"),
                task_info_cache=task_info_cache,
                children_cache=children_cache
            )
            self.assertTrue(complete)
            # Cache should now contain both task and feature info
            self.assertIn("t-001", task_info_cache)
            self.assertIn("f-001", task_info_cache)
            self.assertIn("f-001", children_cache)

    def test_backwards_compatible_without_cache(self):
        """check_feature_completion works without cache parameters (backwards compat)."""
        from unittest.mock import patch
        task_data = {"id": "t-001", "parent": "f-001", "issue_type": "task"}
        feature_data = {"id": "f-001", "issue_type": "feature"}
        children_data = [{"id": "t-001", "status": "closed"}]

        with patch("line_loop.iteration.get_task_info",
                    side_effect=lambda tid, cwd: {"t-001": task_data, "f-001": feature_data}.get(tid)), \
             patch("line_loop.iteration.get_children", return_value=children_data):
            complete, feature_id = line_loop.check_feature_completion("t-001", Path("/tmp"))
            self.assertTrue(complete)
            self.assertEqual(feature_id, "f-001")


class TestEpicCompletionAfterFeatureWithCache(unittest.TestCase):
    """Test check_epic_completion_after_feature with cache."""

    def test_uses_provided_cache(self):
        """check_epic_completion_after_feature uses cache for lookups."""
        from unittest.mock import patch
        task_info_cache = {
            "f-001": {"id": "f-001", "parent": "e-001", "issue_type": "feature"},
            "e-001": {"id": "e-001", "issue_type": "epic"},
        }
        children_cache = {
            "e-001": [{"id": "f-001", "status": "closed"}],
        }
        with patch("line_loop.iteration.get_task_info") as mock_gti, \
             patch("line_loop.iteration.get_children") as mock_gc:
            complete, epic_id = line_loop.check_epic_completion_after_feature(
                "f-001", Path("/tmp"),
                task_info_cache=task_info_cache,
                children_cache=children_cache
            )
            self.assertTrue(complete)
            self.assertEqual(epic_id, "e-001")
            mock_gti.assert_not_called()
            mock_gc.assert_not_called()

    def test_shared_cache_with_feature_check(self):
        """Shared cache between feature and epic checks avoids re-queries."""
        from unittest.mock import patch
        # Simulate: feature check populated cache, epic check reuses it
        task_info_cache = {
            "t-001": {"id": "t-001", "parent": "f-001", "issue_type": "task"},
            "f-001": {"id": "f-001", "parent": "e-001", "issue_type": "feature"},
        }
        children_cache = {
            "f-001": [{"id": "t-001", "status": "closed"}],
        }
        # Only the epic info and children need to be fetched
        with patch("line_loop.iteration.get_task_info",
                    side_effect=lambda tid, cwd: {"e-001": {"id": "e-001", "issue_type": "epic"}}.get(tid)) as mock_gti, \
             patch("line_loop.iteration.get_children",
                    return_value=[{"id": "f-001", "status": "closed"}]) as mock_gc:
            complete, epic_id = line_loop.check_epic_completion_after_feature(
                "f-001", Path("/tmp"),
                task_info_cache=task_info_cache,
                children_cache=children_cache
            )
            self.assertTrue(complete)
            # Only epic info needed from subprocess (feature was cached)
            mock_gti.assert_called_once_with("e-001", Path("/tmp"))

    def test_backwards_compatible_without_cache(self):
        """check_epic_completion_after_feature works without cache parameters."""
        from unittest.mock import patch
        feature_data = {"id": "f-001", "parent": "e-001", "issue_type": "feature"}
        epic_data = {"id": "e-001", "issue_type": "epic"}
        children_data = [{"id": "f-001", "status": "closed"}]

        with patch("line_loop.iteration.get_task_info",
                    side_effect=lambda tid, cwd: {"f-001": feature_data, "e-001": epic_data}.get(tid)), \
             patch("line_loop.iteration.get_children", return_value=children_data):
            complete, epic_id = line_loop.check_epic_completion_after_feature("f-001", Path("/tmp"))
            self.assertTrue(complete)
            self.assertEqual(epic_id, "e-001")


class TestSnapshotTitleLookup(unittest.TestCase):
    """Test getting task title from snapshot to avoid subprocess calls."""

    def test_title_from_snapshot(self):
        """Task title can be retrieved from snapshot without subprocess."""
        from line_loop.iteration import _get_title_from_snapshot_or_cache
        snapshot = line_loop.BeadSnapshot(
            ready=[make_bead("t-001", "Ready Task", "task")],
            in_progress=[make_bead("t-002", "Active Task", "task")],
        )
        self.assertEqual(_get_title_from_snapshot_or_cache("t-001", snapshot, {}), "Ready Task")
        self.assertEqual(_get_title_from_snapshot_or_cache("t-002", snapshot, {}), "Active Task")

    def test_title_from_task_info_cache(self):
        """Task title falls back to task_info_cache."""
        from line_loop.iteration import _get_title_from_snapshot_or_cache
        snapshot = line_loop.BeadSnapshot()
        cache = {"t-003": {"id": "t-003", "title": "Cached Title"}}
        self.assertEqual(_get_title_from_snapshot_or_cache("t-003", snapshot, cache), "Cached Title")

    def test_returns_none_when_not_found(self):
        """Returns None when title not in snapshot or cache."""
        from line_loop.iteration import _get_title_from_snapshot_or_cache
        snapshot = line_loop.BeadSnapshot()
        self.assertIsNone(_get_title_from_snapshot_or_cache("t-999", snapshot, {}))


if __name__ == "__main__":
    unittest.main()
