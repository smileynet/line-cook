#!/usr/bin/env python3
"""Integration tests for helper scripts in plugins/claude-code/scripts/.

Tests run against the actual line-cook repo state (real git, real .beads/).
Each script is invoked as a subprocess and validated for:
  - Exit code 0
  - Valid JSON output with --json
  - Expected top-level keys in JSON schema
  - Non-empty human-readable output
  - --help flag works
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "plugins" / "claude-code" / "scripts"


def run_script(script_name, args=None, timeout=30):
    """Run a helper script and return (returncode, stdout, stderr)."""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + (args or [])
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, cwd=str(REPO_ROOT)
    )
    return result.returncode, result.stdout, result.stderr


def parse_json_output(script_name, args=None, timeout=30):
    """Run script with --json and parse output."""
    json_args = (args or []) + ["--json"]
    returncode, stdout, stderr = run_script(script_name, json_args, timeout=timeout)
    if returncode != 0:
        raise AssertionError(
            "{} exited with code {}: {}".format(script_name, returncode, stderr)
        )
    return json.loads(stdout)


def find_any_bead_id():
    """Find a real bead ID from bd list for testing, or None if unavailable."""
    try:
        result = subprocess.run(
            ["bd", "list", "--json"],
            capture_output=True, text=True, timeout=15,
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None

        data = json.loads(result.stdout)
        if isinstance(data, list) and data:
            for item in data:
                if isinstance(item, dict) and item.get("id"):
                    return item["id"]
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return None


class TestPreflight(unittest.TestCase):
    """Tests for preflight.py."""

    def test_help(self):
        """--help exits 0 with usage text."""
        rc, out, _ = run_script("preflight.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_human_output(self):
        """Human output is non-empty and contains section headers."""
        rc, out, _ = run_script("preflight.py")
        self.assertEqual(rc, 0)
        self.assertIn("Pre-flight Check", out)
        self.assertTrue(len(out) > 50)

    def test_json_output(self):
        """JSON output parses and has expected keys."""
        data = parse_json_output("preflight.py")
        self.assertIn("git", data)
        self.assertIn("beads", data)
        self.assertIn("tools", data)
        self.assertIn("passed", data)
        self.assertIn("errors", data)
        self.assertIn("warnings", data)

    def test_git_populated(self):
        """Git info has real values from this repo."""
        data = parse_json_output("preflight.py", ["--check", "git"])
        git = data["git"]
        self.assertIsNotNone(git)
        self.assertIn("branch", git)
        self.assertIn("clean", git)
        self.assertIn("has_remote", git)
        # We're in a git repo, so branch should be set
        self.assertIsNotNone(git["branch"])

    def test_beads_populated(self):
        """Beads info reflects actual .beads/ state."""
        data = parse_json_output("preflight.py", ["--check", "bd"])
        beads = data["beads"]
        self.assertIsNotNone(beads)
        self.assertIn("available", beads)
        self.assertIn("configured", beads)
        # .beads/ exists in this repo
        if Path(REPO_ROOT / ".beads").is_dir():
            self.assertTrue(beads["configured"])

    def test_check_filter(self):
        """--check git only returns git info."""
        data = parse_json_output("preflight.py", ["--check", "git"])
        self.assertIsNotNone(data["git"])
        self.assertIsNone(data["beads"])
        self.assertIsNone(data["tools"])


class TestStateSnapshot(unittest.TestCase):
    """Tests for state-snapshot.py."""

    def test_help(self):
        rc, out, _ = run_script("state-snapshot.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_human_output(self):
        rc, out, _ = run_script("state-snapshot.py", ["--no-sync"])
        self.assertEqual(rc, 0)
        self.assertIn("State Snapshot", out)

    def test_json_output(self):
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        self.assertIn("project", data)
        self.assertIn("sync", data)
        self.assertIn("roster", data)
        self.assertIn("hierarchy", data)
        self.assertIn("branch_recommendation", data)
        self.assertIn("suggest_next_task", data)
        suggestion_data = data["suggest_next_task"]
        self.assertIn("suggestion", suggestion_data)
        self.assertIn("drill_path", suggestion_data)
        self.assertIsInstance(suggestion_data["drill_path"], list)

    def test_project_info(self):
        """Project info reflects real repo state."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        proj = data["project"]
        self.assertIn("dir", proj)
        self.assertIn("branch", proj)
        self.assertTrue(len(proj["dir"]) > 0)

    def test_no_sync_skips(self):
        """--no-sync sets sync to skipped."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        self.assertEqual(data["sync"]["git"], "skipped")
        self.assertEqual(data["sync"]["beads"], "skipped")

    def test_roster_structure(self):
        """Roster has ready/in_progress/blocked lists."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        roster = data["roster"]
        self.assertIsInstance(roster["ready"], list)
        self.assertIsInstance(roster["in_progress"], list)
        self.assertIsInstance(roster["blocked"], list)

    def test_hierarchy_goal_field(self):
        """Hierarchy epic/feature entries include goal field when present."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        hierarchy = data["hierarchy"]
        # If there's a feature or epic, it should have a goal key
        if hierarchy.get("feature"):
            self.assertIn("goal", hierarchy["feature"])
        if hierarchy.get("epic"):
            self.assertIn("goal", hierarchy["epic"])

    def test_completed_siblings_have_titles(self):
        """Completed siblings are dicts with id and title, not bare strings."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        siblings = data["hierarchy"].get("completed_siblings", [])
        for sibling in siblings:
            self.assertIsInstance(sibling, dict)
            self.assertIn("id", sibling)
            self.assertIn("title", sibling)

    def test_branch_recommendation_structure(self):
        """Branch recommendation has expected fields."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        rec = data["branch_recommendation"]
        self.assertIn("expected", rec)
        self.assertIn("current", rec)
        self.assertIn("branch_exists", rec)
        self.assertNotIn("action", rec)
        self.assertNotIn("reason", rec)

    def test_no_manual_summary_field(self):
        """manual_summary field was removed (agent already has AGENTS.md)."""
        data = parse_json_output("state-snapshot.py", ["--no-sync"])
        self.assertNotIn("manual_summary", data)


class TestKitchenEquipment(unittest.TestCase):
    """Tests for kitchen-equipment.py."""

    def test_help(self):
        rc, out, _ = run_script("kitchen-equipment.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_no_id_returns_ready_list(self):
        """No task_id returns ready list for agent to choose from."""
        rc, out, _ = run_script("kitchen-equipment.py", ["--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertIn("ready_list", data)
        self.assertIsInstance(data["ready_list"], list)
        self.assertIsNone(data["task"])
        self.assertNotIn("auto_selected", data)
        self.assertNotIn("idle", data)
        self.assertNotIn("idle_reason", data)

    def test_bad_id_exits_1(self):
        """Non-existent bead ID returns error."""
        rc, out, _ = run_script("kitchen-equipment.py", ["nonexistent-id-xyz"])
        self.assertEqual(rc, 1)

    def test_bad_id_json(self):
        """Non-existent ID with --json returns error object."""
        rc, out, _ = run_script("kitchen-equipment.py", ["nonexistent-id-xyz", "--json"])
        self.assertEqual(rc, 1)
        data = json.loads(out)
        self.assertIn("error", data)

    def test_real_bead(self):
        """Test with a real bead ID from bd list (if available)."""
        bead_id = find_any_bead_id()
        if not bead_id:
            self.skipTest("No beads available")

        data = parse_json_output("kitchen-equipment.py", [bead_id])
        self.assertIn("task", data)
        self.assertIn("is_epic", data)
        self.assertIn("prior_context", data)
        self.assertIn("tools", data)
        self.assertNotIn("idle", data)
        self.assertNotIn("idle_reason", data)
        self.assertNotIn("auto_selected", data)
        self.assertEqual(data["task"]["id"], bead_id)

    def test_no_kitchen_manual_field(self):
        """kitchen_manual field was removed (agent already has AGENTS.md)."""
        bead_id = find_any_bead_id()
        if not bead_id:
            self.skipTest("No beads available")

        data = parse_json_output("kitchen-equipment.py", [bead_id])
        self.assertNotIn("kitchen_manual", data)

    def test_prior_context_has_truncation_flag(self):
        """Prior context includes serve_comments_truncated flag."""
        bead_id = find_any_bead_id()
        if not bead_id:
            self.skipTest("No beads available")

        data = parse_json_output("kitchen-equipment.py", [bead_id])
        prior = data.get("prior_context", {})
        self.assertIn("serve_comments_truncated", prior)
        self.assertIsInstance(prior["serve_comments_truncated"], bool)

    def test_real_bead_has_planning_context_key(self):
        """Planning context key is present in output."""
        bead_id = find_any_bead_id()
        if not bead_id:
            self.skipTest("No beads available")

        data = parse_json_output("kitchen-equipment.py", [bead_id])
        self.assertIn("planning_context", data)


class TestDiffCollector(unittest.TestCase):
    """Tests for diff-collector.py."""

    def test_help(self):
        rc, out, _ = run_script("diff-collector.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_human_output(self):
        rc, out, _ = run_script("diff-collector.py")
        self.assertEqual(rc, 0)
        self.assertIn("Diff Collection", out)

    def test_json_output(self):
        data = parse_json_output("diff-collector.py")
        self.assertIn("bead", data)
        self.assertIn("changes", data)
        self.assertNotIn("project_context", data)

    def test_changes_structure(self):
        """Changes section has expected fields including truncation flags."""
        data = parse_json_output("diff-collector.py")
        changes = data["changes"]
        self.assertIn("unstaged", changes)
        self.assertIn("staged", changes)
        self.assertIn("last_commit", changes)
        self.assertIn("files", changes)
        self.assertIsInstance(changes["files"], list)
        # Truncation flags present
        self.assertIn("unstaged_truncated", changes)
        self.assertIn("staged_truncated", changes)
        self.assertIn("last_commit_truncated", changes)
        self.assertIsInstance(changes["unstaged_truncated"], bool)
        self.assertIsInstance(changes["staged_truncated"], bool)
        self.assertIsInstance(changes["last_commit_truncated"], bool)

    def test_bead_has_status_and_priority(self):
        """Bead dict includes status and priority fields."""
        data = parse_json_output("diff-collector.py")
        bead = data.get("bead")
        if bead is not None:
            self.assertIn("status", bead)
            self.assertIn("priority", bead)
            self.assertIn("type", bead)

    def test_no_project_context_field(self):
        """project_context field was removed (agent already has CLAUDE.md)."""
        data = parse_json_output("diff-collector.py")
        self.assertNotIn("project_context", data)


class TestPlanValidator(unittest.TestCase):
    """Tests for plan-validator.py."""

    def test_help(self):
        rc, out, _ = run_script("plan-validator.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_human_output(self):
        rc, out, _ = run_script("plan-validator.py")
        # May exit 1 if critical findings
        self.assertIn("Plan Validation Report", out)

    def test_json_output(self):
        rc, out, _ = run_script("plan-validator.py", ["--json"])
        data = json.loads(out)
        self.assertIn("scope", data)
        self.assertIn("beads_scanned", data)
        self.assertIn("findings", data)
        self.assertIn("stats", data)

    def test_findings_structure(self):
        """Findings grouped by severity."""
        rc, out, _ = run_script("plan-validator.py", ["--json"])
        data = json.loads(out)
        findings = data["findings"]
        self.assertIn("critical", findings)
        self.assertIn("warning", findings)
        self.assertIn("info", findings)

    def test_stats_structure(self):
        """Stats have tier and status counts."""
        rc, out, _ = run_script("plan-validator.py", ["--json"])
        data = json.loads(out)
        stats = data["stats"]
        self.assertIn("by_tier", stats)
        self.assertIn("by_status", stats)
        self.assertIn("progress_pct", stats)

    def test_full_scope(self):
        """Full scope runs additional checks."""
        rc, out, _ = run_script("plan-validator.py", ["full", "--json"], timeout=45)
        data = json.loads(out)
        self.assertEqual(data["scope"], "full")

    def test_specific_bead_walks_parents(self):
        """Specific bead scope includes parent chain."""
        bead_id = find_any_bead_id()
        if not bead_id:
            self.skipTest("No beads available")

        rc, out, _ = run_script("plan-validator.py", [bead_id, "--json"])
        data = json.loads(out)
        # Should have scanned at least the bead itself
        self.assertGreaterEqual(data["beads_scanned"], 1)

    def test_type_inference_in_findings(self):
        """TYPE_MISSING findings include inferred type."""
        rc, out, _ = run_script("plan-validator.py", ["--json"])
        data = json.loads(out)
        for severity_list in data["findings"].values():
            for finding in severity_list:
                if finding.get("check") == "TYPE_MISSING":
                    self.assertIn("inferred", finding["message"])


class TestMetricsCollector(unittest.TestCase):
    """Tests for metrics-collector.py."""

    def test_help(self):
        rc, out, _ = run_script("metrics-collector.py", ["--help"])
        self.assertEqual(rc, 0)
        self.assertIn("usage", out.lower())

    def test_human_output(self):
        rc, out, _ = run_script("metrics-collector.py")
        self.assertEqual(rc, 0)
        self.assertIn("Architecture Metrics Report", out)

    def test_json_output(self):
        data = parse_json_output("metrics-collector.py")
        self.assertIn("scope", data)
        self.assertIn("validation_scripts", data)
        self.assertIn("findings", data)

    def test_validation_scripts_found(self):
        """Validation scripts are discovered and executed."""
        data = parse_json_output("metrics-collector.py")
        scripts = data["validation_scripts"]
        self.assertIsInstance(scripts, list)
        self.assertTrue(len(scripts) > 0)
        # check-plugin-health.py should exist
        names = [s["name"] for s in scripts]
        self.assertIn("check-plugin-health.py", names)

    def test_full_scope(self):
        """Full scope adds file analysis and smells."""
        data = parse_json_output("metrics-collector.py", ["full"], timeout=60)
        self.assertEqual(data["scope"], "full")
        self.assertIn("metrics", data)
        metrics = data["metrics"]
        self.assertIn("total_loc", metrics)
        self.assertIn("file_count", metrics)
        self.assertGreater(metrics["file_count"], 0)

    def test_full_scope_severity_thresholds(self):
        """Full scope classifies >1000 LOC as critical, >500 as high."""
        data = parse_json_output("metrics-collector.py", ["full"], timeout=60)
        findings = data["findings"]
        # Check that critical/high severity keys exist
        self.assertIn("critical", findings)
        self.assertIn("high", findings)
        # If there are BLOATER findings, verify severity mapping
        for finding in findings.get("critical", []):
            if finding.get("smell") == "BLOATER":
                self.assertGreater(finding.get("loc", 0), 1000)
        for finding in findings.get("high", []):
            if finding.get("smell") == "BLOATER":
                self.assertGreater(finding.get("loc", 0), 500)

    def test_full_scope_has_external_tools(self):
        """Full scope includes external tools section."""
        data = parse_json_output("metrics-collector.py", ["full"], timeout=60)
        self.assertIn("external_tools", data)
        ext = data["external_tools"]
        self.assertIn("tools_available", ext)
        self.assertIn("external", ext)

    def test_report_flag_accepted(self):
        """--report flag is accepted without error."""
        rc, out, _ = run_script("metrics-collector.py", ["--report", "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
