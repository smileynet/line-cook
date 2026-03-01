"""Test feedback broker functionality."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts dir for feedback_broker import
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "claude-code" / "scripts"))
from feedback_broker import (
    find_inspect_feedback_by_pr,
    read_inspect_feedback,
    read_issue_agent_feedback,
    read_loop_feedback,
    synthesize_feedback,
)


def make_broker_dir():
    """Create a temporary directory with .beads feedback subdirectories."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir)
    beads_dir = root / ".beads"
    beads_dir.mkdir()
    (beads_dir / "inspect-feedback").mkdir()
    (beads_dir / "loop-feedback").mkdir()
    (beads_dir / "issue-agent-feedback").mkdir()
    return root


def write_inspect_feedback(root, issue_number=42, verdict="POLISH", polish_attempts=1):
    """Write a sample inspect feedback file and return the data."""
    feedback = {
        "issue_number": issue_number,
        "pr_number": 7,
        "verdict": verdict,
        "polish_attempts": polish_attempts,
        "dimensions": {
            "what_changed": "Added null check",
            "project_value": "Prevents crash",
            "issue_validity": "Valid bug",
            "intent_alignment": "Matches issue",
            "scope": "Minimal change",
            "security": "No concerns",
            "code_quality": "Needs polish",
            "root_cause_depth": "Surface fix"
        },
        "rationale": "Code works but needs cleanup",
        "reviewed_at": "2026-02-23T21:00:00Z"
    }
    feedback_file = root / ".beads" / "inspect-feedback" / f"issue-{issue_number}.json"
    feedback_file.write_text(json.dumps(feedback, indent=2))
    return feedback


def write_issue_agent_feedback(root, issue_number=42):
    """Write a sample issue-agent feedback file and return the data."""
    feedback = {
        "issue_number": issue_number,
        "classification": "bug",
        "confidence": 0.85,
        "labels": ["bug", "needs-triage"],
        "analysis": "Null pointer in login handler",
        "proposed_fix": "Add null check before dereferencing",
        "reviewed_at": "2026-02-23T21:10:00Z"
    }
    feedback_file = root / ".beads" / "issue-agent-feedback" / f"issue-{issue_number}.json"
    feedback_file.write_text(json.dumps(feedback, indent=2))
    return feedback


def write_retry_context(root, task_id="lc-abc"):
    """Write a retry-context.json file (primary loop feedback path)."""
    data = {
        "task_id": task_id,
        "verdict": "NEEDS_CHANGES",
        "summary": "Variable naming needs improvement",
        "issues": [
            {"severity": "major", "location": "src/foo.py:10", "problem": "Unclear name"}
        ],
        "attempt": 2
    }
    line_cook_dir = root / ".line-cook"
    line_cook_dir.mkdir(exist_ok=True)
    (line_cook_dir / "retry-context.json").write_text(json.dumps(data, indent=2))
    return data


def write_loop_feedback(root, task_id="lc-abc"):
    """Write a sample loop feedback file and return the data."""
    feedback = {
        "task_id": task_id,
        "phase": "serve",
        "verdict": "NEEDS_CHANGES",
        "feedback": "Variable naming unclear, add comments",
        "iteration": 1,
        "reviewed_at": "2026-02-23T21:05:00Z"
    }
    feedback_file = root / ".beads" / "loop-feedback" / f"{task_id}.json"
    feedback_file.write_text(json.dumps(feedback, indent=2))
    return feedback


class TestFeedbackBroker(unittest.TestCase):
    """Test feedback broker read and synthesis functions."""

    def setUp(self):
        self.mock_root = make_broker_dir()

    def test_reads_inspect_feedback(self):
        """Verify broker can read inspect feedback."""
        write_inspect_feedback(self.mock_root)
        feedback = read_inspect_feedback(self.mock_root, issue_number=42)

        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["verdict"], "POLISH")
        self.assertEqual(feedback["polish_attempts"], 1)
        self.assertEqual(feedback["issue_number"], 42)

    def test_reads_loop_feedback(self):
        """Verify broker can read loop feedback."""
        write_loop_feedback(self.mock_root)
        feedback = read_loop_feedback(self.mock_root, task_id="lc-abc")

        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["verdict"], "NEEDS_CHANGES")
        self.assertEqual(feedback["task_id"], "lc-abc")

    def test_synthesizes_unified_view(self):
        """Verify broker synthesizes feedback from multiple sources."""
        write_inspect_feedback(self.mock_root)
        write_loop_feedback(self.mock_root)

        unified = synthesize_feedback(self.mock_root, issue_number=42)

        self.assertEqual(unified["context_type"], "issue")
        self.assertEqual(unified["context_id"], "42")
        self.assertIn("inspect", unified["feedback_sources"])
        self.assertGreaterEqual(unified["summary"]["total_feedback_count"], 1)
        self.assertEqual(unified["summary"]["latest_verdict"], "POLISH")

    def test_handles_missing_feedback(self):
        """Verify broker handles missing feedback gracefully."""
        feedback = read_inspect_feedback(self.mock_root, issue_number=999)
        self.assertIsNone(feedback)

    def test_identifies_escalation_needed(self):
        """Verify broker identifies when escalation is needed."""
        write_inspect_feedback(self.mock_root, polish_attempts=3)

        unified = synthesize_feedback(self.mock_root, issue_number=42)
        self.assertTrue(unified["summary"]["escalation_needed"])

    def test_loop_feedback_synthesis(self):
        """Verify broker synthesizes loop feedback by task ID."""
        write_loop_feedback(self.mock_root)

        unified = synthesize_feedback(self.mock_root, task_id="lc-abc")

        self.assertEqual(unified["context_type"], "task")
        self.assertEqual(unified["context_id"], "lc-abc")
        self.assertIn("loop", unified["feedback_sources"])
        self.assertEqual(unified["summary"]["latest_verdict"], "NEEDS_CHANGES")

    def test_reads_issue_agent_feedback(self):
        """Verify broker can read issue-agent feedback."""
        write_issue_agent_feedback(self.mock_root)
        feedback = read_issue_agent_feedback(self.mock_root, issue_number=42)

        self.assertIsNotNone(feedback)
        self.assertEqual(feedback["classification"], "bug")
        self.assertAlmostEqual(feedback["confidence"], 0.85)

    def test_issue_agent_feedback_in_synthesis(self):
        """Verify issue-agent feedback appears in unified view."""
        write_issue_agent_feedback(self.mock_root)

        unified = synthesize_feedback(self.mock_root, issue_number=42)

        self.assertIn("issue_agent", unified["feedback_sources"])
        self.assertEqual(
            unified["feedback_sources"]["issue_agent"]["classification"], "bug"
        )

    def test_retry_context_primary_path(self):
        """Verify loop feedback reads retry-context.json first."""
        write_retry_context(self.mock_root, task_id="lc-xyz")
        # Also write legacy file with different data
        write_loop_feedback(self.mock_root, task_id="lc-xyz")

        feedback = read_loop_feedback(self.mock_root, task_id="lc-xyz")

        # Should get retry-context data (has "attempt" key), not legacy
        self.assertIsNotNone(feedback)
        self.assertIn("attempt", feedback)
        self.assertEqual(feedback["attempt"], 2)

    def test_retry_context_wrong_task_falls_through(self):
        """Verify retry-context.json is skipped when task_id doesn't match."""
        write_retry_context(self.mock_root, task_id="lc-other")
        write_loop_feedback(self.mock_root, task_id="lc-abc")

        feedback = read_loop_feedback(self.mock_root, task_id="lc-abc")

        # Should get legacy fallback (no "attempt" key)
        self.assertIsNotNone(feedback)
        self.assertNotIn("attempt", feedback)
        self.assertEqual(feedback["verdict"], "NEEDS_CHANGES")

    def test_pr_cross_reference(self):
        """Verify --pr finds inspect feedback by PR number."""
        write_inspect_feedback(self.mock_root, issue_number=42)
        # The inspect feedback for issue 42 has pr_number=7

        unified = synthesize_feedback(self.mock_root, pr_number=7)

        self.assertEqual(unified["context_type"], "pr")
        self.assertEqual(unified["context_id"], "7")
        self.assertIn("inspect", unified["feedback_sources"])
        self.assertEqual(unified["feedback_sources"]["inspect"]["pr_number"], 7)

    def test_pr_no_match(self):
        """Verify --pr returns empty when no feedback matches."""
        write_inspect_feedback(self.mock_root, issue_number=42)

        unified = synthesize_feedback(self.mock_root, pr_number=999)

        self.assertEqual(unified["context_type"], "pr")
        self.assertEqual(unified["feedback_sources"], {})

    def test_raises_without_query(self):
        """Verify synthesize_feedback raises when no query provided."""
        with self.assertRaises(ValueError):
            synthesize_feedback(self.mock_root)


class TestFindInspectFeedbackByPr(unittest.TestCase):
    """Direct tests for find_inspect_feedback_by_pr."""

    def setUp(self):
        self.mock_root = make_broker_dir()

    def test_finds_feedback_matching_pr(self):
        """Happy path: returns feedback when PR number matches."""
        write_inspect_feedback(self.mock_root, issue_number=42)
        # write_inspect_feedback sets pr_number=7

        result = find_inspect_feedback_by_pr(self.mock_root, pr_number=7)

        self.assertIsNotNone(result)
        self.assertEqual(result["pr_number"], 7)
        self.assertEqual(result["issue_number"], 42)

    def test_returns_none_when_no_match(self):
        """Returns None when no file has the requested PR number."""
        write_inspect_feedback(self.mock_root, issue_number=42)

        result = find_inspect_feedback_by_pr(self.mock_root, pr_number=999)

        self.assertIsNone(result)

    def test_skips_malformed_json(self):
        """Skips corrupted files and continues scanning."""
        # Write a valid file
        write_inspect_feedback(self.mock_root, issue_number=42)
        # Write a corrupted file
        bad_file = self.mock_root / ".beads" / "inspect-feedback" / "issue-99.json"
        bad_file.write_text("{corrupt json!!!")

        result = find_inspect_feedback_by_pr(self.mock_root, pr_number=7)

        self.assertIsNotNone(result)
        self.assertEqual(result["pr_number"], 7)

    def test_returns_none_when_dir_missing(self):
        """Returns None when inspect-feedback directory doesn't exist."""
        empty_root = Path(tempfile.mkdtemp())

        result = find_inspect_feedback_by_pr(empty_root, pr_number=7)

        self.assertIsNone(result)


class TestMalformedJsonHandling(unittest.TestCase):
    """Verify all reader functions handle corrupted JSON gracefully."""

    def setUp(self):
        self.mock_root = make_broker_dir()

    def test_read_inspect_feedback_malformed(self):
        """read_inspect_feedback returns None on corrupted JSON."""
        bad_file = self.mock_root / ".beads" / "inspect-feedback" / "issue-42.json"
        bad_file.write_text("not valid json")

        result = read_inspect_feedback(self.mock_root, issue_number=42)

        self.assertIsNone(result)

    def test_read_loop_feedback_malformed_retry(self):
        """read_loop_feedback falls through when retry-context is corrupted."""
        line_cook_dir = self.mock_root / ".line-cook"
        line_cook_dir.mkdir(exist_ok=True)
        (line_cook_dir / "retry-context.json").write_text("{bad")
        # Write valid legacy fallback
        write_loop_feedback(self.mock_root, task_id="lc-abc")

        result = read_loop_feedback(self.mock_root, task_id="lc-abc")

        self.assertIsNotNone(result)
        self.assertEqual(result["task_id"], "lc-abc")

    def test_read_loop_feedback_malformed_legacy(self):
        """read_loop_feedback returns None when legacy file is corrupted."""
        bad_file = self.mock_root / ".beads" / "loop-feedback" / "lc-abc.json"
        bad_file.write_text("{{nope}}")

        result = read_loop_feedback(self.mock_root, task_id="lc-abc")

        self.assertIsNone(result)

    def test_read_issue_agent_feedback_malformed(self):
        """read_issue_agent_feedback returns None on corrupted JSON."""
        bad_file = self.mock_root / ".beads" / "issue-agent-feedback" / "issue-42.json"
        bad_file.write_text("[broken")

        result = read_issue_agent_feedback(self.mock_root, issue_number=42)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
