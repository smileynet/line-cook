"""Test feedback history accumulation in retry context."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from core.line_loop.iteration import write_retry_context, clear_retry_context
from core.line_loop.models import ServeFeedback, ServeFeedbackIssue


def test_feedback_accumulates_across_retries():
    """Verify feedback history accumulates instead of replacing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        
        # First feedback (attempt 1)
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
        
        write_retry_context(cwd, feedback1)
        
        # Second feedback (attempt 2)
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
        
        write_retry_context(cwd, feedback2)
        
        # Read and verify history
        context_file = cwd / ".line-cook" / "retry-context.json"
        assert context_file.exists()
        
        data = json.loads(context_file.read_text())
        
        # Should have history array with both feedbacks
        assert "history" in data
        assert len(data["history"]) == 2
        
        # First entry should be attempt 1
        assert data["history"][0]["attempt"] == 1
        assert data["history"][0]["summary"] == "Missing error handling"
        
        # Second entry should be attempt 2
        assert data["history"][1]["attempt"] == 2
        assert data["history"][1]["summary"] == "Still missing edge case"
        
        # Current fields should match latest feedback
        assert data["attempt"] == 2
        assert data["verdict"] == "NEEDS_CHANGES"
        assert data["summary"] == "Still missing edge case"


def test_clear_retry_context_removes_file():
    """Verify clear removes the retry context file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = Path(tmpdir)
        
        feedback = ServeFeedback(
            verdict="NEEDS_CHANGES",
            summary="Test",
            task_id="test-001",
            attempt=1
        )
        
        write_retry_context(cwd, feedback)
        context_file = cwd / ".line-cook" / "retry-context.json"
        assert context_file.exists()
        
        clear_retry_context(cwd)
        assert not context_file.exists()
