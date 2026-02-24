"""Tests for failure classification and retry strategy."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
from line_loop.models import LoopError, FailureCategory
from line_loop.loop import calculate_retry_delay


class TestLoopErrorClassification(unittest.TestCase):
    """Test LoopError.classify_failure() method."""

    def test_timeout_is_persistent(self):
        """Timeout errors should be classified as PERSISTENT."""
        error = LoopError.from_timeout("test command", 30)
        self.assertEqual(error.classify_failure(), FailureCategory.PERSISTENT)

    def test_json_decode_is_persistent(self):
        """JSON decode errors should be classified as PERSISTENT."""
        try:
            json.loads("{invalid")
        except json.JSONDecodeError as e:
            error = LoopError.from_json_decode("test source", e)
            self.assertEqual(error.classify_failure(), FailureCategory.PERSISTENT)

    def test_io_is_environmental(self):
        """I/O errors should be classified as ENVIRONMENTAL."""
        error = LoopError.from_io("read", Path("/test/file"), IOError("test"))
        self.assertEqual(error.classify_failure(), FailureCategory.ENVIRONMENTAL)

    def test_subprocess_disk_full_is_environmental(self):
        """Subprocess errors with 'no space left' should be ENVIRONMENTAL."""
        error = LoopError.from_subprocess(
            "test command", 1, "Error: no space left on device"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.ENVIRONMENTAL)

    def test_subprocess_permission_denied_is_environmental(self):
        """Subprocess errors with 'permission denied' should be ENVIRONMENTAL."""
        error = LoopError.from_subprocess(
            "test command", 1, "Error: permission denied"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.ENVIRONMENTAL)

    def test_subprocess_out_of_memory_is_environmental(self):
        """Subprocess errors with 'cannot allocate memory' should be ENVIRONMENTAL."""
        error = LoopError.from_subprocess(
            "test command", 1, "Error: cannot allocate memory"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.ENVIRONMENTAL)

    def test_subprocess_command_not_found_is_environmental(self):
        """Subprocess errors with 'command not found' should be ENVIRONMENTAL."""
        error = LoopError.from_subprocess(
            "test command", 127, "bash: test: command not found"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.ENVIRONMENTAL)

    def test_subprocess_connection_refused_is_transient(self):
        """Subprocess errors with 'connection refused' should be TRANSIENT."""
        error = LoopError.from_subprocess(
            "curl http://api.example.com", 1,
            "curl: (7) Failed to connect: Connection refused"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.TRANSIENT)

    def test_subprocess_rate_limit_is_transient(self):
        """Subprocess errors with 'rate limit' should be TRANSIENT."""
        error = LoopError.from_subprocess(
            "api call", 1, "Error: rate limit exceeded, retry after 60s"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.TRANSIENT)

    def test_subprocess_503_is_transient(self):
        """Subprocess errors with '503' should be TRANSIENT."""
        error = LoopError.from_subprocess(
            "curl http://api.example.com", 1, "HTTP 503 Service Unavailable"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.TRANSIENT)

    def test_subprocess_generic_failure_is_persistent(self):
        """Generic subprocess failures should be PERSISTENT."""
        error = LoopError.from_subprocess(
            "pytest", 1, "FAILED tests/test_foo.py::test_bar - AssertionError"
        )
        self.assertEqual(error.classify_failure(), FailureCategory.PERSISTENT)

    def test_unknown_error_type_is_persistent(self):
        """Unknown error types should default to PERSISTENT."""
        error = LoopError(error_type="unknown", message="Something went wrong")
        self.assertEqual(error.classify_failure(), FailureCategory.PERSISTENT)


class TestRetryDelayCalculation(unittest.TestCase):
    """Test calculate_retry_delay() with failure categories."""

    def test_transient_immediate_retry(self):
        """TRANSIENT failures should retry immediately (0s delay)."""
        delay = calculate_retry_delay(0, FailureCategory.TRANSIENT)
        self.assertEqual(delay, 0.0)
        delay = calculate_retry_delay(5, FailureCategory.TRANSIENT)
        self.assertEqual(delay, 0.0)

    def test_environmental_no_retry(self):
        """ENVIRONMENTAL failures should return 0 (caller halts)."""
        delay = calculate_retry_delay(0, FailureCategory.ENVIRONMENTAL)
        self.assertEqual(delay, 0.0)
        delay = calculate_retry_delay(5, FailureCategory.ENVIRONMENTAL)
        self.assertEqual(delay, 0.0)

    def test_persistent_exponential_backoff(self):
        """PERSISTENT failures should use exponential backoff."""
        delay = calculate_retry_delay(0, FailureCategory.PERSISTENT)
        self.assertGreaterEqual(delay, 1.6)
        self.assertLessEqual(delay, 2.4)

        delay = calculate_retry_delay(1, FailureCategory.PERSISTENT)
        self.assertGreaterEqual(delay, 3.2)
        self.assertLessEqual(delay, 4.8)

        delay = calculate_retry_delay(2, FailureCategory.PERSISTENT)
        self.assertGreaterEqual(delay, 6.4)
        self.assertLessEqual(delay, 9.6)

    def test_unclassified_exponential_backoff(self):
        """Unclassified failures (None) should use exponential backoff."""
        delay = calculate_retry_delay(0, None)
        self.assertGreaterEqual(delay, 1.6)
        self.assertLessEqual(delay, 2.4)

        delay = calculate_retry_delay(1, None)
        self.assertGreaterEqual(delay, 3.2)
        self.assertLessEqual(delay, 4.8)

    def test_persistent_respects_max_delay(self):
        """PERSISTENT backoff should cap at MAX_RETRY_DELAY_SECONDS."""
        delay = calculate_retry_delay(20, FailureCategory.PERSISTENT)
        self.assertLessEqual(delay, 72.0)


if __name__ == "__main__":
    unittest.main()
