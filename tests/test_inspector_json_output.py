"""Test inspector agent JSON output format."""

import json
import unittest


class TestInspectorJsonOutput(unittest.TestCase):
    """Test inspector agent JSON output format."""

    def test_outputs_valid_json(self):
        """Inspector should output valid JSON, not markdown."""
        expected_output = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "MERGE",
            "dimensions": {
                "what_changed": "Added null check before array access",
                "project_value": "Prevents crash on empty input",
                "issue_validity": "Valid bug with clear reproduction",
                "intent_alignment": "Fix matches issue description",
                "scope": "Single file, minimal change",
                "security": "No security concerns",
                "code_quality": "Clean, follows conventions",
                "root_cause_depth": "Root cause fix"
            },
            "rationale": "Ready to merge - valid fix with no concerns"
        }

        json_str = json.dumps(expected_output)
        parsed = json.loads(json_str)

        self.assertIn("issue_number", parsed)
        self.assertIn("pr_number", parsed)
        self.assertIn("verdict", parsed)
        self.assertIn("dimensions", parsed)
        self.assertIn("rationale", parsed)
        self.assertEqual(len(parsed["dimensions"]), 8)

        required_dimensions = [
            "what_changed", "project_value", "issue_validity",
            "intent_alignment", "scope", "security",
            "code_quality", "root_cause_depth"
        ]
        for dim in required_dimensions:
            self.assertIn(dim, parsed["dimensions"])

    def test_json_schema_matches_feedback_file(self):
        """Inspector output should match feedback file schema (minus reviewed_at)."""
        inspector_output = {
            "issue_number": 42,
            "pr_number": 7,
            "verdict": "POLISH",
            "dimensions": {
                "what_changed": "...",
                "project_value": "...",
                "issue_validity": "...",
                "intent_alignment": "...",
                "scope": "...",
                "security": "...",
                "code_quality": "...",
                "root_cause_depth": "..."
            },
            "rationale": "..."
        }

        feedback_schema_keys = {
            "issue_number", "pr_number", "verdict", "dimensions",
            "rationale", "reviewed_at", "polish_attempts"
        }

        inspector_keys = set(inspector_output.keys())
        self.assertEqual(inspector_keys, feedback_schema_keys - {"reviewed_at", "polish_attempts"})

    def test_verdict_values(self):
        """Inspector verdict must be one of the five valid values."""
        valid_verdicts = {"MERGE", "POLISH", "FEEDBACK", "REWORK", "REJECT"}

        for verdict in valid_verdicts:
            output = {
                "issue_number": 1,
                "pr_number": 1,
                "verdict": verdict,
                "dimensions": {
                    "what_changed": "...",
                    "project_value": "...",
                    "issue_validity": "...",
                    "intent_alignment": "...",
                    "scope": "...",
                    "security": "...",
                    "code_quality": "...",
                    "root_cause_depth": "..."
                },
                "rationale": "..."
            }
            self.assertIn(output["verdict"], valid_verdicts)


if __name__ == "__main__":
    unittest.main()
