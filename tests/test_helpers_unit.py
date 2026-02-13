#!/usr/bin/env python3
"""Unit tests for plugins/claude-code/scripts/helpers.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins" / "claude-code" / "scripts"))

from helpers import run_cmd, run_bd_json


class TestRunCmd(unittest.TestCase):
    """Test run_cmd() function."""

    @patch("helpers.subprocess.run")
    def test_successful_command(self, mock_run):
        """Successful command returns (0, stdout, stderr)."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="  output  ", stderr="  warn  "
        )
        rc, out, err = run_cmd(["echo", "hello"])
        self.assertEqual(rc, 0)
        self.assertEqual(out, "output")
        self.assertEqual(err, "warn")

    @patch("helpers.subprocess.run")
    def test_strips_whitespace(self, mock_run):
        """Output is stripped of leading/trailing whitespace."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="\n  hello\n  ", stderr=""
        )
        rc, out, err = run_cmd(["echo"])
        self.assertEqual(out, "hello")

    @patch("helpers.subprocess.run")
    def test_nonzero_returncode(self, mock_run):
        """Non-zero return code is passed through."""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error msg"
        )
        rc, out, err = run_cmd(["false"])
        self.assertEqual(rc, 1)
        self.assertEqual(err, "error msg")

    @patch("helpers.subprocess.run")
    def test_command_not_found(self, mock_run):
        """FileNotFoundError returns (-1, '', 'command not found: ...')."""
        mock_run.side_effect = FileNotFoundError()
        rc, out, err = run_cmd(["nonexistent"])
        self.assertEqual(rc, -1)
        self.assertEqual(out, "")
        self.assertIn("command not found", err)
        self.assertIn("nonexistent", err)

    @patch("helpers.subprocess.run")
    def test_timeout(self, mock_run):
        """TimeoutExpired returns (-1, '', 'timeout after ...')."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=15)
        rc, out, err = run_cmd(["slow"], timeout=15)
        self.assertEqual(rc, -1)
        self.assertIn("timeout", err)
        self.assertIn("15", err)

    @patch("helpers.subprocess.run")
    def test_custom_timeout_passed(self, mock_run):
        """Custom timeout is forwarded to subprocess.run."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_cmd(["cmd"], timeout=30)
        mock_run.assert_called_once_with(
            ["cmd"], capture_output=True, text=True, timeout=30
        )

    @patch("helpers.subprocess.run")
    def test_default_timeout(self, mock_run):
        """Default timeout is 15 seconds."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_cmd(["cmd"])
        mock_run.assert_called_once_with(
            ["cmd"], capture_output=True, text=True, timeout=15
        )


class TestRunBdJson(unittest.TestCase):
    """Test run_bd_json() function."""

    @patch("helpers.run_cmd")
    def test_parses_json_dict(self, mock_cmd):
        """Dict response is returned as-is."""
        mock_cmd.return_value = (0, json.dumps({"id": "lc-1", "title": "test"}), "")
        result = run_bd_json(["show", "lc-1"])
        self.assertEqual(result, {"id": "lc-1", "title": "test"})
        mock_cmd.assert_called_once_with(["bd", "show", "lc-1", "--json"], timeout=15)

    @patch("helpers.run_cmd")
    def test_unwraps_single_item_list(self, mock_cmd):
        """Single-item list is unwrapped to dict."""
        mock_cmd.return_value = (0, json.dumps([{"id": "lc-1"}]), "")
        result = run_bd_json(["show", "lc-1"])
        self.assertEqual(result, {"id": "lc-1"})

    @patch("helpers.run_cmd")
    def test_preserves_multi_item_list(self, mock_cmd):
        """Multi-item list is returned as-is."""
        items = [{"id": "lc-1"}, {"id": "lc-2"}]
        mock_cmd.return_value = (0, json.dumps(items), "")
        result = run_bd_json(["list"])
        self.assertEqual(result, items)

    @patch("helpers.run_cmd")
    def test_returns_none_on_error(self, mock_cmd):
        """Non-zero exit code returns None."""
        mock_cmd.return_value = (1, "", "error")
        result = run_bd_json(["show", "bad"])
        self.assertIsNone(result)

    @patch("helpers.run_cmd")
    def test_returns_none_on_empty_output(self, mock_cmd):
        """Empty stdout returns None."""
        mock_cmd.return_value = (0, "", "")
        result = run_bd_json(["show", "lc-1"])
        self.assertIsNone(result)

    @patch("helpers.run_cmd")
    def test_returns_none_on_invalid_json(self, mock_cmd):
        """Invalid JSON returns None."""
        mock_cmd.return_value = (0, "not json", "")
        result = run_bd_json(["show", "lc-1"])
        self.assertIsNone(result)

    @patch("helpers.run_cmd")
    def test_custom_timeout_forwarded(self, mock_cmd):
        """Custom timeout is forwarded to run_cmd."""
        mock_cmd.return_value = (0, json.dumps({"id": "lc-1"}), "")
        run_bd_json(["show", "lc-1"], timeout=30)
        mock_cmd.assert_called_once_with(["bd", "show", "lc-1", "--json"], timeout=30)


if __name__ == "__main__":
    unittest.main()
