"""Tests for CircuitBreaker warning threshold."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.models import CircuitBreaker


class TestCircuitBreakerWarning(unittest.TestCase):
    """Test CircuitBreaker warning threshold."""

    def test_warning_threshold_not_reached(self):
        """Warning should not trigger when failures are below threshold."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3)
        cb.record(False)
        cb.record(False)
        self.assertFalse(cb.should_warn())
        self.assertFalse(cb.is_open())

    def test_warning_threshold_reached(self):
        """Warning should trigger at threshold."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3)
        cb.record(False)
        cb.record(False)
        cb.record(False)
        self.assertTrue(cb.should_warn())
        self.assertFalse(cb.is_open())

    def test_warning_before_trip(self):
        """Warning should trigger before circuit trips."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3)
        for _ in range(3):
            cb.record(False)
        self.assertTrue(cb.should_warn())
        self.assertFalse(cb.is_open())

        for _ in range(2):
            cb.record(False)
        self.assertTrue(cb.is_open())

    def test_warning_resets_on_success(self):
        """Warning should clear when circuit breaker is reset."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3)
        for _ in range(3):
            cb.record(False)
        self.assertTrue(cb.should_warn())

        cb.reset()
        self.assertFalse(cb.should_warn())
        self.assertFalse(cb.is_open())

    def test_warning_with_sliding_window(self):
        """Warning should respect sliding window."""
        cb = CircuitBreaker(failure_threshold=5, warning_threshold=3, window_size=10)
        for _ in range(7):
            cb.record(True)
        for _ in range(3):
            cb.record(False)
        self.assertTrue(cb.should_warn())
        self.assertFalse(cb.is_open())


if __name__ == "__main__":
    unittest.main()
