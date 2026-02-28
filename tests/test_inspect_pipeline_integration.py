"""Integration test for inspect self-healing pipeline.

Tests the complete cross-feature flow:
  inspector JSON -> augment with polish_attempts -> write feedback file
  -> broker reads and synthesizes -> escalation at 3+ POLISH attempts

Replaces hollow tests:
  - test_inspect_polish_counter.py (asserted on hardcoded dicts)
  - test_inspector_json_output.py (tested json roundtrip, not production code)
  - test_inspect_feedback.py (tested Path.write_text, not inspect command)
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add scripts dir for feedback_broker import
sys.path.insert(
    0, str(Path(__file__).parent.parent / "plugins" / "claude-code" / "scripts")
)
from feedback_broker import (
    find_inspect_feedback_by_pr,
    read_inspect_feedback,
    synthesize_feedback,
)

VALID_VERDICTS = {"MERGE", "POLISH", "FEEDBACK", "REWORK", "REJECT"}
REQUIRED_DIMENSIONS = [
    "what_changed",
    "project_value",
    "issue_validity",
    "intent_alignment",
    "scope",
    "security",
    "code_quality",
    "root_cause_depth",
]
MAX_POLISH_ATTEMPTS = 3


# --- Pipeline simulation helpers ---


def make_inspector_output(issue_number, pr_number, verdict="MERGE"):
    """Create a valid inspector JSON output (stage 1 of pipeline)."""
    return {
        "issue_number": issue_number,
        "pr_number": pr_number,
        "verdict": verdict,
        "dimensions": {
            "what_changed": "Added null check before array access",
            "project_value": "Prevents crash on empty input",
            "issue_validity": "Valid bug with clear reproduction",
            "intent_alignment": "Fix matches issue description",
            "scope": "Single file, minimal change",
            "security": "No security concerns",
            "code_quality": (
                "Needs polish" if verdict == "POLISH" else "Clean, follows conventions"
            ),
            "root_cause_depth": "Root cause fix",
        },
        "rationale": "Needs cleanup" if verdict == "POLISH" else "Ready to merge",
    }


def augment_and_write(repo_root, inspector_output):
    """Simulate the inspect command's augmentation and atomic file write.

    Source of truth: .claude/commands/inspect.md (Step 3a: Write Feedback File).
    Replicates the logic from that command:
    1. Read existing feedback to get previous polish_attempts
    2. If POLISH: increment counter; else: reset to 0
    3. If counter >= MAX_POLISH_ATTEMPTS and POLISH: escalate to FEEDBACK
    4. Add reviewed_at timestamp
    5. Atomic write via temp file
    """
    issue_number = inspector_output["issue_number"]
    feedback_dir = repo_root / ".beads" / "inspect-feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / f"issue-{issue_number}.json"

    # Read existing feedback for previous attempts count
    previous_attempts = 0
    if feedback_file.exists():
        existing = json.loads(feedback_file.read_text())
        previous_attempts = existing.get("polish_attempts", 0)

    # Calculate new attempt count
    verdict = inspector_output["verdict"]
    if verdict == "POLISH":
        polish_attempts = previous_attempts + 1
    else:
        polish_attempts = 0

    # Escalation override
    if polish_attempts >= MAX_POLISH_ATTEMPTS and verdict == "POLISH":
        verdict = "FEEDBACK"
        rationale = (
            f"ESCALATED: {polish_attempts} consecutive POLISH attempts exceeded "
            f"threshold of {MAX_POLISH_ATTEMPTS}. {inspector_output['rationale']}"
        )
    else:
        rationale = inspector_output["rationale"]

    # Build augmented feedback
    augmented = {
        **inspector_output,
        "verdict": verdict,
        "rationale": rationale,
        "polish_attempts": polish_attempts,
        "reviewed_at": datetime.now().isoformat(),
    }

    # Atomic write via temp file
    temp_file = feedback_dir / f"issue-{issue_number}.json.tmp"
    temp_file.write_text(json.dumps(augmented, indent=2))
    temp_file.rename(feedback_file)

    return augmented


def make_repo_root():
    """Create a temporary repo root with .beads feedback directories."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir)
    (root / ".beads" / "inspect-feedback").mkdir(parents=True)
    return root


class TestInspectPipelineIntegration(unittest.TestCase):
    """Cross-feature integration test for the inspect self-healing pipeline.

    Tests the data contract: inspector output -> augmentation -> file write
    -> broker read -> synthesis -> escalation detection.
    """

    def setUp(self):
        self.repo_root = make_repo_root()
        self.addCleanup(shutil.rmtree, self.repo_root)

    def test_full_pipeline_single_review(self):
        """Inspector JSON -> augment -> write -> broker read -> verify roundtrip."""
        inspector_output = make_inspector_output(42, 7, verdict="MERGE")

        augment_and_write(self.repo_root, inspector_output)

        read_back = read_inspect_feedback(self.repo_root, issue_number=42)

        self.assertIsNotNone(read_back)
        self.assertEqual(read_back["verdict"], "MERGE")
        self.assertEqual(read_back["polish_attempts"], 0)
        self.assertEqual(read_back["issue_number"], 42)
        self.assertEqual(read_back["pr_number"], 7)
        self.assertIn("reviewed_at", read_back)
        self.assertEqual(len(read_back["dimensions"]), len(REQUIRED_DIMENSIONS))

    def test_escalation_after_three_polish_verdicts(self):
        """3 consecutive POLISH verdicts -> escalation to FEEDBACK."""
        for attempt in range(1, 4):
            inspector_output = make_inspector_output(42, 7, verdict="POLISH")
            written = augment_and_write(self.repo_root, inspector_output)
            if attempt < 3:
                # Before threshold: verdict stays POLISH
                self.assertEqual(written["verdict"], "POLISH")
                self.assertEqual(written["polish_attempts"], attempt)

        # 3rd attempt triggers escalation
        self.assertEqual(written["verdict"], "FEEDBACK")
        self.assertEqual(written["polish_attempts"], 3)
        self.assertIn("ESCALATED", written["rationale"])

        # Broker detects escalation
        unified = synthesize_feedback(self.repo_root, issue_number=42)
        self.assertTrue(unified["summary"]["escalation_needed"])
        self.assertEqual(unified["summary"]["latest_verdict"], "FEEDBACK")

    def test_polish_counter_increments(self):
        """Each POLISH verdict increments the counter by 1."""
        for expected in range(1, 3):
            inspector_output = make_inspector_output(42, 7, verdict="POLISH")
            written = augment_and_write(self.repo_root, inspector_output)
            self.assertEqual(written["polish_attempts"], expected)

    def test_non_polish_resets_counter(self):
        """Non-POLISH verdict resets counter to 0."""
        augment_and_write(
            self.repo_root, make_inspector_output(42, 7, verdict="POLISH")
        )

        written = augment_and_write(
            self.repo_root, make_inspector_output(42, 7, verdict="MERGE")
        )

        self.assertEqual(written["polish_attempts"], 0)
        self.assertEqual(written["verdict"], "MERGE")

    def test_pr_cross_reference_through_pipeline(self):
        """Written feedback can be found by PR number through broker."""
        augment_and_write(
            self.repo_root, make_inspector_output(42, 7, verdict="MERGE")
        )

        # find_inspect_feedback_by_pr scans all files for matching pr_number
        found = find_inspect_feedback_by_pr(self.repo_root, pr_number=7)
        self.assertIsNotNone(found)
        self.assertEqual(found["issue_number"], 42)

        # synthesize_feedback also works via PR query
        unified = synthesize_feedback(self.repo_root, pr_number=7)
        self.assertEqual(unified["context_type"], "pr")
        self.assertIn("inspect", unified["feedback_sources"])

    def test_schema_contract_inspector_to_feedback(self):
        """Inspector output + augmented fields = complete feedback file schema."""
        inspector_output = make_inspector_output(42, 7, verdict="MERGE")

        # Inspector must produce exactly these keys
        expected_inspector_keys = {
            "issue_number",
            "pr_number",
            "verdict",
            "dimensions",
            "rationale",
        }
        self.assertEqual(set(inspector_output.keys()), expected_inspector_keys)

        # All dimensions required
        self.assertEqual(
            set(inspector_output["dimensions"].keys()), set(REQUIRED_DIMENSIONS)
        )

        # Verdict must be valid
        self.assertIn(inspector_output["verdict"], VALID_VERDICTS)

        # After augmentation: adds polish_attempts and reviewed_at
        written = augment_and_write(self.repo_root, inspector_output)
        expected_feedback_keys = expected_inspector_keys | {
            "polish_attempts",
            "reviewed_at",
        }
        self.assertEqual(set(written.keys()), expected_feedback_keys)

    def test_escalation_preserves_original_rationale(self):
        """Escalated verdict includes both escalation notice and original rationale."""
        for _ in range(3):
            written = augment_and_write(
                self.repo_root, make_inspector_output(42, 7, verdict="POLISH")
            )

        self.assertIn("ESCALATED", written["rationale"])
        self.assertIn("Needs cleanup", written["rationale"])

    def test_synthesis_key_concerns_from_dimensions(self):
        """Broker extracts key concerns from dimension text containing 'needs'."""
        augment_and_write(
            self.repo_root, make_inspector_output(42, 7, verdict="POLISH")
        )

        unified = synthesize_feedback(self.repo_root, issue_number=42)
        # "Needs polish" in code_quality dimension should be flagged
        self.assertIn("code_quality", unified["summary"]["key_concerns"])


class TestFeedbackBrokerCLI(unittest.TestCase):
    """CLI smoke test: invoke feedback_broker.py with fixture data."""

    def setUp(self):
        self.repo_root = make_repo_root()
        self.addCleanup(shutil.rmtree, self.repo_root)
        self.broker_script = str(
            Path(__file__).parent.parent
            / "plugins"
            / "claude-code"
            / "scripts"
            / "feedback_broker.py"
        )

    def _write_fixture(self, issue_number=42, verdict="POLISH", polish_attempts=1):
        """Write a feedback fixture file."""
        feedback = {
            "issue_number": issue_number,
            "pr_number": 7,
            "verdict": verdict,
            "polish_attempts": polish_attempts,
            "dimensions": {dim: "test value" for dim in REQUIRED_DIMENSIONS},
            "rationale": "Test rationale",
            "reviewed_at": "2026-02-23T21:00:00Z",
        }
        feedback_file = (
            self.repo_root / ".beads" / "inspect-feedback" / f"issue-{issue_number}.json"
        )
        feedback_file.write_text(json.dumps(feedback, indent=2))

    def test_cli_issue_query(self):
        """CLI --issue returns valid synthesized JSON."""
        self._write_fixture()

        result = subprocess.run(
            [
                sys.executable,
                self.broker_script,
                "--issue", "42",
                "--repo", str(self.repo_root),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        output = json.loads(result.stdout)
        self.assertEqual(output["context_type"], "issue")
        self.assertEqual(output["context_id"], "42")
        self.assertIn("inspect", output["feedback_sources"])

    def test_cli_pr_cross_reference(self):
        """CLI --pr cross-references feedback by PR number."""
        self._write_fixture()

        result = subprocess.run(
            [
                sys.executable,
                self.broker_script,
                "--pr", "7",
                "--repo", str(self.repo_root),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        output = json.loads(result.stdout)
        self.assertEqual(output["context_type"], "pr")
        self.assertIn("inspect", output["feedback_sources"])

    def test_cli_no_args_fails(self):
        """CLI with no query args exits with error."""
        result = subprocess.run(
            [sys.executable, self.broker_script, "--repo", str(self.repo_root)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
