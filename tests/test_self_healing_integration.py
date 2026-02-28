"""Cross-feature integration tests for Loop Self-Healing epic (lc-3nl).

Validates that the four self-healing features work together:
- T1: Feedback history accumulation (rolling window)
- T4: Circuit breaker warning threshold
- T5: Failure classification
- T9: Per-task retry budget (SkipList)

Also covers gaps identified during epic E2E review:
- _is_environmental_error() detection
- CircuitBreaker default warning_threshold auto-calculation
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.iteration import write_retry_context
from line_loop.loop import _is_environmental_error, classify_iteration_failure, calculate_retry_delay
from line_loop.models import (
    ActionRecord,
    CircuitBreaker,
    FailureCategory,
    IterationResult,
    ServeFeedback,
    ServeFeedbackIssue,
    SkipList,
)


def _make_iteration_result(tool_name="Bash", success=False, output=""):
    """Create an IterationResult with a single action for testing."""
    action = ActionRecord(
        tool_name=tool_name,
        tool_use_id="test-tool-001",
        input_summary="test command",
        output_summary=output,
        success=success,
        timestamp="2026-01-01T00:00:00",
    )
    return IterationResult(
        iteration=1,
        task_id="test-001",
        task_title="Test task",
        outcome="crashed",
        duration_seconds=1.0,
        serve_verdict=None,
        commit_hash=None,
        success=False,
        actions=[action],
    )


class TestSelfHealingIntegration(unittest.TestCase):
    """Cross-feature integration: warning → skip → feedback accumulation."""

    def test_warning_then_skip_then_feedback(self):
        """Simulate a task failing repeatedly across the self-healing pipeline.

        Journey: task fails → CB warns → more failures → skip list triggers →
        feedback accumulates in retry context throughout.
        """
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3)
        skip_list = SkipList(max_failures=3)
        cwd = Path(tempfile.mkdtemp())
        task_id = "test-integration-001"

        warned = False
        skipped = False
        for attempt in range(1, 6):
            # Record failure in circuit breaker
            cb.record(False)

            # Record failure in skip list
            now_skipped = skip_list.record_failure(task_id)
            if now_skipped:
                skipped = True

            # Check warning state
            if cb.should_warn() and not cb.is_open():
                warned = True

            # Accumulate feedback
            feedback = ServeFeedback(
                verdict="NEEDS_CHANGES",
                summary=f"Attempt {attempt} issues",
                issues=[
                    ServeFeedbackIssue(
                        severity="major",
                        location=f"foo.py:{attempt * 10}",
                        problem=f"Problem {attempt}",
                        suggestion=f"Fix {attempt}"
                    )
                ],
                task_id=task_id,
                task_title="Integration test task",
                attempt=attempt
            )
            write_retry_context(cwd, feedback)

        # Warning should have triggered before trip
        self.assertTrue(warned, "Circuit breaker should have warned before tripping")
        # Circuit breaker should be open after 5 failures
        self.assertTrue(cb.is_open(), "Circuit breaker should be open after 5 failures")
        # Skip list should have triggered at max_failures=3
        self.assertTrue(skipped, "Skip list should have skipped task after 3 failures")
        self.assertTrue(skip_list.is_skipped(task_id))

        # Feedback history should be capped at rolling window
        context_file = cwd / ".line-cook" / "retry-context.json"
        data = json.loads(context_file.read_text())
        self.assertEqual(len(data["history"]), 5)
        self.assertEqual(data["history"][0]["attempt"], 1)
        self.assertEqual(data["history"][-1]["attempt"], 5)

    def test_success_resets_skip_but_not_feedback_history(self):
        """Success resets skip list but feedback history persists."""
        skip_list = SkipList(max_failures=3)
        cwd = Path(tempfile.mkdtemp())
        task_id = "test-reset-001"

        # Accumulate 2 failures
        for attempt in range(1, 3):
            skip_list.record_failure(task_id)
            feedback = ServeFeedback(
                verdict="NEEDS_CHANGES",
                summary=f"Attempt {attempt}",
                issues=[],
                task_id=task_id,
                task_title="Reset test",
                attempt=attempt
            )
            write_retry_context(cwd, feedback)

        # Success resets skip list
        skip_list.record_success(task_id)
        self.assertFalse(skip_list.is_skipped(task_id))

        # But feedback history remains (for pattern detection)
        context_file = cwd / ".line-cook" / "retry-context.json"
        data = json.loads(context_file.read_text())
        self.assertEqual(len(data["history"]), 2)


class TestIsEnvironmentalError(unittest.TestCase):
    """Tests for _is_environmental_error() loop-level detection."""

    def test_detects_disk_full(self):
        result = _make_iteration_result(output="Error: No space left on device")
        self.assertTrue(_is_environmental_error(result))

    def test_detects_permission_denied(self):
        result = _make_iteration_result(output="Permission denied: /etc/config")
        self.assertTrue(_is_environmental_error(result))

    def test_detects_command_not_found(self):
        result = _make_iteration_result(output="bash: foobar: command not found")
        self.assertTrue(_is_environmental_error(result))

    def test_detects_out_of_memory(self):
        result = _make_iteration_result(output="Cannot allocate memory")
        self.assertTrue(_is_environmental_error(result))

    def test_ignores_normal_failures(self):
        result = _make_iteration_result(output="AssertionError: expected 1, got 2")
        self.assertFalse(_is_environmental_error(result))

    def test_ignores_successful_actions(self):
        result = _make_iteration_result(success=True, output="No space left on device")
        self.assertFalse(_is_environmental_error(result))

    def test_ignores_non_bash_actions(self):
        result = _make_iteration_result(tool_name="Read", output="Permission denied")
        self.assertFalse(_is_environmental_error(result))

    def test_empty_actions(self):
        result = IterationResult(
            iteration=1, task_id="test-001", task_title="Test task",
            outcome="crashed", duration_seconds=1.0, serve_verdict=None,
            commit_hash=None, success=False, actions=[]
        )
        self.assertFalse(_is_environmental_error(result))


class TestClassifyIterationFailure(unittest.TestCase):
    """Tests for classify_iteration_failure() — unified failure classification at iteration level."""

    def test_disk_full_is_environmental(self):
        result = _make_iteration_result(output="Error: No space left on device")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_permission_denied_is_environmental(self):
        result = _make_iteration_result(output="Permission denied: /etc/config")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_command_not_found_is_environmental(self):
        result = _make_iteration_result(output="bash: foobar: command not found")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_out_of_memory_is_environmental(self):
        result = _make_iteration_result(output="Cannot allocate memory")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_read_only_filesystem_is_environmental(self):
        result = _make_iteration_result(output="Error: read-only file system")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_too_many_open_files_is_environmental(self):
        result = _make_iteration_result(output="Error: too many open files")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)

    def test_connection_refused_is_transient(self):
        result = _make_iteration_result(output="curl: (7) Failed to connect: Connection refused")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_connection_reset_is_transient(self):
        result = _make_iteration_result(output="Connection reset by peer")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_rate_limit_is_transient(self):
        result = _make_iteration_result(output="Error: rate limit exceeded, retry after 60s")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_503_is_transient(self):
        result = _make_iteration_result(output="HTTP 503 Service Unavailable")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_502_is_transient(self):
        result = _make_iteration_result(output="HTTP 502 Bad Gateway")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_timeout_in_output_is_transient(self):
        result = _make_iteration_result(output="Error: connection timeout after 30s")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.TRANSIENT)

    def test_normal_failure_is_persistent(self):
        result = _make_iteration_result(output="AssertionError: expected 1, got 2")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.PERSISTENT)

    def test_empty_actions_is_persistent(self):
        result = IterationResult(
            iteration=1, task_id="test-001", task_title="Test task",
            outcome="crashed", duration_seconds=1.0, serve_verdict=None,
            commit_hash=None, success=False, actions=[]
        )
        self.assertEqual(classify_iteration_failure(result), FailureCategory.PERSISTENT)

    def test_ignores_successful_actions(self):
        """Successful actions should not influence classification."""
        result = _make_iteration_result(success=True, output="No space left on device")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.PERSISTENT)

    def test_ignores_non_bash_actions(self):
        """Non-Bash tool failures should not influence classification."""
        result = _make_iteration_result(tool_name="Read", output="Permission denied")
        self.assertEqual(classify_iteration_failure(result), FailureCategory.PERSISTENT)

    def test_environmental_takes_priority_over_transient(self):
        """If both environmental and transient signals present, environmental wins."""
        env_action = ActionRecord(
            tool_name="Bash", tool_use_id="t1", input_summary="cmd1",
            output_summary="No space left on device", success=False,
            timestamp="2026-01-01T00:00:00",
        )
        transient_action = ActionRecord(
            tool_name="Bash", tool_use_id="t2", input_summary="cmd2",
            output_summary="Connection refused", success=False,
            timestamp="2026-01-01T00:00:01",
        )
        result = IterationResult(
            iteration=1, task_id="test-001", task_title="Test task",
            outcome="crashed", duration_seconds=1.0, serve_verdict=None,
            commit_hash=None, success=False,
            actions=[env_action, transient_action],
        )
        self.assertEqual(classify_iteration_failure(result), FailureCategory.ENVIRONMENTAL)


class TestCircuitBreakerAutoWarningThreshold(unittest.TestCase):
    """Test default warning_threshold auto-calculation."""

    def test_default_threshold_is_sixty_percent(self):
        """Default warning_threshold should be 60% of failure_threshold."""
        cb = CircuitBreaker(failure_threshold=5)
        self.assertEqual(cb.warning_threshold, 3)  # int(5 * 0.6) = 3

    def test_default_threshold_minimum_is_one(self):
        """Warning threshold should never be less than 1."""
        cb = CircuitBreaker(failure_threshold=1)
        self.assertEqual(cb.warning_threshold, 1)  # max(1, int(1 * 0.6)) = 1

    def test_default_threshold_rounds_down(self):
        """Auto-calculation uses int() which truncates."""
        cb = CircuitBreaker(failure_threshold=7)
        self.assertEqual(cb.warning_threshold, 4)  # int(7 * 0.6) = 4

    def test_explicit_threshold_overrides_default(self):
        """Explicitly provided threshold should not be overridden."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=2)
        self.assertEqual(cb.warning_threshold, 2)

    def test_default_threshold_with_large_value(self):
        """Auto-calculation should work with large failure thresholds."""
        cb = CircuitBreaker(failure_threshold=100)
        self.assertEqual(cb.warning_threshold, 60)


class TestCalculateRetryDelayWithCategory(unittest.TestCase):
    """Test that calculate_retry_delay respects failure categories."""

    def test_transient_returns_zero(self):
        """Transient failures should retry immediately."""
        delay = calculate_retry_delay(3, category=FailureCategory.TRANSIENT)
        self.assertEqual(delay, 0.0)

    def test_environmental_returns_zero(self):
        """Environmental failures return 0 (caller should halt)."""
        delay = calculate_retry_delay(1, category=FailureCategory.ENVIRONMENTAL)
        self.assertEqual(delay, 0.0)

    def test_persistent_uses_backoff(self):
        """Persistent failures should use exponential backoff."""
        delay = calculate_retry_delay(2, category=FailureCategory.PERSISTENT)
        self.assertGreater(delay, 0.0)

    def test_none_category_uses_default_backoff(self):
        """No category should use default exponential backoff."""
        delay = calculate_retry_delay(2, category=None)
        self.assertGreater(delay, 0.0)


if __name__ == "__main__":
    unittest.main()
