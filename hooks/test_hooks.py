#!/usr/bin/env python3
"""
Test script for line-cook hooks.

Run this script to verify hooks work correctly on your platform.
Supports Windows, Linux, and macOS.

Usage:
    python3 hooks/test_hooks.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure hooks directory is in path for direct imports
sys.path.insert(0, str(Path(__file__).parent))


def run_hook(hook_script: str, input_data: dict) -> tuple[int, str, str]:
    """Run a hook script with JSON input and return (exit_code, stdout, stderr)."""
    hook_path = Path(__file__).parent / hook_script

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def test_pre_tool_use():
    """Integration test: pre_tool_use.py hook (runs as subprocess)."""
    print("Testing pre_tool_use.py...")

    # Test 1: Safe command should be allowed
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
    )
    assert exit_code == 0, f"Safe command should be allowed, got exit {exit_code}"
    print("  [PASS] Safe command allowed")

    # Test 2: Dangerous command should be blocked
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
        },
    )
    assert exit_code == 2, f"Dangerous command should be blocked, got exit {exit_code}"
    assert "deny" in stdout.lower() or "blocked" in stdout.lower(), (
        "Should output denial message"
    )
    print("  [PASS] Dangerous command blocked")

    # Test 3: Empty command should be allowed
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py", {"tool_name": "Bash", "tool_input": {"command": ""}}
    )
    assert exit_code == 0, f"Empty command should be allowed, got exit {exit_code}"
    print("  [PASS] Empty command handled")

    print("  All pre_tool_use tests passed!")


def test_post_tool_use():
    """Integration test: post_tool_use.py hook (runs as subprocess).

    Tests hook execution and graceful handling. Does not verify formatter output
    since that depends on installed tools.
    """
    print("Testing post_tool_use.py...")

    # Test 1: Non-existent file should be skipped
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {"tool_name": "Write", "tool_input": {"file_path": "/nonexistent/file.py"}},
    )
    assert exit_code == 0, f"Non-existent file should be skipped, got exit {exit_code}"
    print("  [PASS] Non-existent file skipped")

    # Test 2: Sensitive file should be skipped
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {"tool_name": "Write", "tool_input": {"file_path": "/home/user/.env"}},
    )
    assert exit_code == 0, f"Sensitive file should be skipped, got exit {exit_code}"
    print("  [PASS] Sensitive file skipped")

    # Test 3: Path traversal should be blocked
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "/some/path/../../../etc/passwd"},
        },
    )
    assert exit_code == 0, f"Path traversal should be skipped, got exit {exit_code}"
    print("  [PASS] Path traversal blocked")

    # Test 4: Real file handling (tests graceful execution, not formatter output)
    # The hook should complete without error whether or not formatters are installed
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("x=1\n")
        temp_path = f.name

    try:
        exit_code, stdout, stderr = run_hook(
            "post_tool_use.py",
            {"tool_name": "Write", "tool_input": {"file_path": temp_path}},
        )
        assert exit_code == 0, (
            f"Hook should complete successfully, got exit {exit_code}"
        )
        # Don't assert on stdout - it depends on installed tools
        print(
            f"  [PASS] Real file handled gracefully (formatters: {stdout.strip() or 'none'})"
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("  All post_tool_use tests passed!")


def test_stop_check():
    """Integration test: stop_check.py hook (runs as subprocess).

    Tests hook execution. Git output parsing is tested in unit tests.
    """
    print("Testing stop_check.py...")

    # Test 1: Basic execution (will check git status)
    exit_code, stdout, stderr = run_hook(
        "stop_check.py",
        {
            "session_id": "test-session",
        },
    )
    assert exit_code == 0, f"Stop check should complete, got exit {exit_code}"
    print(f"  [PASS] Stop check completed (output: {stdout.strip() or 'none'})")

    print("  All stop_check tests passed!")


def test_session_start():
    """Integration test: session_start.py hook (runs as subprocess)."""
    print("Testing session_start.py...")

    # Test 1: Basic execution
    exit_code, stdout, stderr = run_hook(
        "session_start.py",
        {
            "session_id": "test-session",
        },
    )
    assert exit_code == 0, f"Session start should complete, got exit {exit_code}"

    # Check if we're in a beads project
    beads_dir = Path(__file__).parent.parent / ".beads"
    if beads_dir.exists():
        assert "Beads" in stdout or "beads" in stdout, "Should output beads context"
        print("  [PASS] Session start primed beads context")
    else:
        print("  [PASS] Session start completed (no .beads directory)")

    print("  All session_start tests passed!")


def test_hook_utils():
    """Test hook_utils.py module."""
    print("Testing hook_utils.py...")

    from hook_utils import get_log_path, setup_logging

    # Test log path
    log_path = get_log_path()
    assert log_path.name == "hooks.log", (
        f"Log file should be hooks.log, got {log_path.name}"
    )
    print(f"  [PASS] Log path: {log_path}")

    # Test logger setup
    logger = setup_logging("test")
    assert logger.name == "line-cook.test", f"Logger name wrong: {logger.name}"
    print("  [PASS] Logger setup works")

    print("  All hook_utils tests passed!")


# ===========================================================================
# Kiro CLI JSON Format Tests
# ===========================================================================
#
# Kiro CLI passes different JSON structures to hooks than Claude Code.
# These tests verify hooks work correctly with Kiro's format.
#
# Key differences:
#   - Kiro includes "hook_event_name" field (e.g., "preToolUse")
#   - Kiro includes "cwd" for current working directory
#   - Kiro uses "shell" as tool_name (vs Claude Code's "Bash")
#   - Kiro's PostToolUse includes "tool_response" with execution results
#
# Note: pre_tool_use.py processes any tool with a "command" field, regardless of tool_name


def test_kiro_pre_tool_use_json_parsing():
    """Test pre_tool_use.py with Kiro JSON input format."""
    print("Testing pre_tool_use.py with Kiro JSON format...")

    # Test 1: Kiro format - safe shell command should be allowed
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "hook_event_name": "preToolUse",
            "cwd": "/home/user/project",
            "tool_name": "shell",
            "tool_input": {"command": "ls -la"},
        },
    )
    assert exit_code == 0, f"Kiro safe command should be allowed, got exit {exit_code}"
    print("  [PASS] Kiro format: safe shell command allowed")

    # Test 2: Kiro format - dangerous command should be blocked
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "hook_event_name": "preToolUse",
            "cwd": "/home/user/project",
            "tool_name": "shell",
            "tool_input": {"command": "git reset --hard HEAD~5"},
        },
    )
    assert exit_code == 2, (
        f"Kiro dangerous command should be blocked, got exit {exit_code}"
    )
    assert stdout, "Should have JSON output on block"
    output = json.loads(stdout)
    assert "hookSpecificOutput" in output, "Should have hookSpecificOutput"
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
    print("  [PASS] Kiro format: dangerous command blocked with correct JSON output")

    # Test 3: Kiro format - verify cwd field doesn't break parsing
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "hook_event_name": "preToolUse",
            "cwd": "/path/with spaces/and-special_chars",
            "tool_name": "shell",
            "tool_input": {"command": "echo hello"},
        },
    )
    assert exit_code == 0, (
        f"Kiro format with special cwd should work, got exit {exit_code}"
    )
    print("  [PASS] Kiro format: handles special characters in cwd")

    # Test 4: Kiro format - empty tool_input
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "hook_event_name": "preToolUse",
            "cwd": "/project",
            "tool_name": "shell",
            "tool_input": {},
        },
    )
    assert exit_code == 0, (
        f"Kiro format empty tool_input should be allowed, got exit {exit_code}"
    )
    print("  [PASS] Kiro format: empty tool_input handled")

    print("  All Kiro pre_tool_use JSON parsing tests passed!")


def test_kiro_post_tool_use_json_parsing():
    """Test post_tool_use.py with Kiro JSON input format."""
    print("Testing post_tool_use.py with Kiro JSON format...")

    # Test 1: Kiro format with tool_response (PostToolUse specific)
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {
            "hook_event_name": "postToolUse",
            "cwd": "/home/user/project",
            "tool_name": "write",
            "tool_input": {"file_path": "/nonexistent/file.py"},
            "tool_response": {"success": True, "result": ["File written successfully"]},
        },
    )
    assert exit_code == 0, (
        f"Kiro post_tool_use should handle tool_response, got exit {exit_code}"
    )
    print("  [PASS] Kiro format: handles tool_response field")

    # Test 2: Kiro format - write tool with real file (tests graceful execution)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("y=2\n")
        temp_path = f.name

    try:
        exit_code, stdout, stderr = run_hook(
            "post_tool_use.py",
            {
                "hook_event_name": "postToolUse",
                "cwd": str(Path(temp_path).parent),
                "tool_name": "write",
                "tool_input": {"file_path": temp_path},
                "tool_response": {"success": True},
            },
        )
        assert exit_code == 0, (
            f"Kiro format hook should complete successfully, got exit {exit_code}"
        )
        # Don't assert on stdout - it depends on installed tools
        print(
            f"  [PASS] Kiro format: real file handled (formatters: {stdout.strip() or 'none'})"
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)

    # Test 3: Kiro format - operations array (alternative input structure)
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {
            "hook_event_name": "postToolUse",
            "cwd": "/project",
            "tool_name": "write",
            "tool_input": {
                "operations": [{"mode": "Line", "path": "/project/file.py"}]
            },
        },
    )
    # This should gracefully handle the different structure (no file_path key)
    assert exit_code == 0, (
        f"Kiro operations format should not crash, got exit {exit_code}"
    )
    print("  [PASS] Kiro format: handles operations array (no file_path)")

    print("  All Kiro post_tool_use JSON parsing tests passed!")


def test_kiro_stop_hook_json_parsing():
    """Test stop_check.py with Kiro JSON input format."""
    print("Testing stop_check.py with Kiro JSON format...")

    # Test 1: Kiro stop hook format (minimal)
    exit_code, stdout, stderr = run_hook(
        "stop_check.py", {"hook_event_name": "stop", "cwd": "/home/user/project"}
    )
    assert exit_code == 0, f"Kiro stop hook should complete, got exit {exit_code}"
    print("  [PASS] Kiro format: stop hook completes")

    # Test 2: Kiro format with no fields at all
    exit_code, stdout, stderr = run_hook("stop_check.py", {})
    assert exit_code == 0, (
        f"Empty Kiro input should not crash stop hook, got exit {exit_code}"
    )
    print("  [PASS] Kiro format: handles empty input")

    print("  All Kiro stop_check JSON parsing tests passed!")


def test_tool_name_matching():
    """Test that hooks handle different tool name conventions."""
    print("Testing tool name matching across platforms...")

    # Claude Code uses "Bash", Kiro uses "shell"
    tool_name_variants = [
        ("Bash", "Claude Code style"),
        ("shell", "Kiro style"),
        ("bash", "lowercase"),
        ("Shell", "capitalized Kiro"),
        ("BASH", "uppercase"),
    ]

    for tool_name, description in tool_name_variants:
        exit_code, stdout, stderr = run_hook(
            "pre_tool_use.py",
            {"tool_name": tool_name, "tool_input": {"command": "echo test"}},
        )
        assert exit_code == 0, (
            f"Tool name '{tool_name}' ({description}) should be allowed, got exit {exit_code}"
        )
        print(f"  [PASS] Tool name '{tool_name}' ({description}) handled")

    # Test dangerous command blocking works regardless of tool name
    for tool_name in ["Bash", "shell", "Shell"]:
        exit_code, stdout, stderr = run_hook(
            "pre_tool_use.py",
            {"tool_name": tool_name, "tool_input": {"command": "rm -rf /"}},
        )
        assert exit_code == 2, (
            f"Dangerous command with '{tool_name}' should be blocked, got exit {exit_code}"
        )

    print("  [PASS] Dangerous command blocking works across tool name variants")

    print("  All tool name matching tests passed!")


def test_exit_codes():
    """Test correct exit codes for various scenarios."""
    print("Testing exit codes...")

    # Exit code 0: Allow (safe operation)
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py", {"tool_name": "Bash", "tool_input": {"command": "echo safe"}}
    )
    assert exit_code == 0, f"Safe command should return exit 0, got {exit_code}"
    print("  [PASS] Exit 0 for safe command")

    # Exit code 2: Deny (blocked operation)
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
        },
    )
    assert exit_code == 2, f"Blocked command should return exit 2, got {exit_code}"
    print("  [PASS] Exit 2 for blocked command")

    # Exit code 1: Error (invalid JSON)
    hook_path = Path(__file__).parent / "pre_tool_use.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input="not valid json",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1, (
        f"Invalid JSON should return exit 1, got {result.returncode}"
    )
    print("  [PASS] Exit 1 for invalid JSON input")

    # Post tool use always returns 0 (never blocks)
    exit_code, stdout, stderr = run_hook(
        "post_tool_use.py",
        {"tool_name": "Write", "tool_input": {"file_path": "/any/path"}},
    )
    assert exit_code == 0, f"post_tool_use should always return 0, got {exit_code}"
    print("  [PASS] post_tool_use returns 0")

    # Stop hook always returns 0 (logs warnings but doesn't block)
    exit_code, stdout, stderr = run_hook("stop_check.py", {})
    assert exit_code == 0, f"stop_check should always return 0, got {exit_code}"
    print("  [PASS] stop_check returns 0")

    print("  All exit code tests passed!")


def test_json_output_format():
    """Test that JSON output is correctly formatted for both platforms."""
    print("Testing JSON output format...")

    # Test blocked command JSON output structure
    exit_code, stdout, stderr = run_hook(
        "pre_tool_use.py",
        {"tool_name": "Bash", "tool_input": {"command": "dd if=/dev/zero of=/dev/sda"}},
    )
    assert exit_code == 2, f"Should block dangerous command, got exit {exit_code}"
    assert stdout.strip(), "Should have JSON output"

    output = json.loads(stdout)

    # Verify required fields for Claude Code/Kiro compatibility
    assert "hookSpecificOutput" in output, "Missing hookSpecificOutput"
    hook_output = output["hookSpecificOutput"]
    assert "hookEventName" in hook_output, "Missing hookEventName"
    assert "permissionDecision" in hook_output, "Missing permissionDecision"
    assert "permissionDecisionReason" in hook_output, "Missing permissionDecisionReason"

    # Verify values
    assert hook_output["hookEventName"] == "PreToolUse", (
        f"Wrong hookEventName: {hook_output['hookEventName']}"
    )
    assert hook_output["permissionDecision"] == "deny", (
        f"Wrong decision: {hook_output['permissionDecision']}"
    )
    assert hook_output["permissionDecisionReason"], "Reason should not be empty"

    # Verify systemMessage for user feedback
    assert "systemMessage" in output, "Missing systemMessage"
    assert output["systemMessage"], "systemMessage should not be empty"

    print("  [PASS] Blocked command JSON output has correct structure")

    # Test post_tool_use JSON output (additionalContext)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("z=3\n")
        temp_path = f.name

    try:
        exit_code, stdout, stderr = run_hook(
            "post_tool_use.py",
            {"tool_name": "Write", "tool_input": {"file_path": temp_path}},
        )
        if stdout.strip():
            output = json.loads(stdout)
            assert "additionalContext" in output, (
                "post_tool_use should use additionalContext key"
            )
            print(
                f"  [PASS] post_tool_use JSON output has additionalContext: {output['additionalContext']}"
            )
        else:
            print("  [PASS] post_tool_use returns no output (no formatters ran)")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("  All JSON output format tests passed!")


# ===========================================================================
# Unit Tests (with mocking - no external tool dependencies)
# ===========================================================================
#
# These tests import hook modules directly and use mocking to test core logic
# without depending on external tools like ruff, black, prettier, or git.


def test_unit_path_safety():
    """Unit test: path safety validation (no external deps)."""

    print("Testing path safety validation (unit test)...")

    from post_tool_use import is_path_safe

    # Test sensitive patterns blocked (these are checked on the resolved path)
    # Note: path traversal like "../../../etc/passwd" is normalized by os.path.normpath
    # The protection works because: 1) file must exist, 2) resolved path is checked
    assert not is_path_safe("/home/user/.env"), ".env files should be blocked"
    assert not is_path_safe("/project/.git/config"), ".git paths should be blocked"
    assert not is_path_safe("/home/user/.ssh/id_rsa"), ".ssh paths should be blocked"
    assert not is_path_safe("/path/to/credentials.json"), (
        "credentials should be blocked"
    )
    assert not is_path_safe("/path/to/secrets.yaml"), "secrets should be blocked"
    assert not is_path_safe("/path/to/file.key"), ".key files should be blocked"
    assert not is_path_safe("/path/to/server.pem"), ".pem files should be blocked"
    print("  [PASS] Sensitive patterns blocked")

    # Test normal paths allowed (mock realpath to avoid filesystem dependency)
    with patch("post_tool_use.os.path.realpath", side_effect=lambda x: x):
        assert is_path_safe("/home/user/project/src/main.py"), (
            "Normal paths should be allowed"
        )
        assert is_path_safe("/tmp/test.py"), "Temp paths should be allowed"
        assert is_path_safe("/var/www/app/index.js"), "Web paths should be allowed"
    print("  [PASS] Normal paths allowed")

    # Test OSError handling (invalid paths)
    with patch("post_tool_use.os.path.normpath", side_effect=OSError("invalid")):
        assert not is_path_safe("/bad/path"), "OSError should return False"
    print("  [PASS] OSError handled gracefully")

    print("  All path safety unit tests passed!")


def test_unit_formatter_lookup():
    """Unit test: formatter lookup logic with mocked shutil.which."""

    print("Testing formatter lookup (unit test)...")

    from post_tool_use import run_tool

    # Test formatter not found
    with patch("post_tool_use.shutil.which", return_value=None):
        result = run_tool("ruff", ["format", "{file}"], "/tmp/test.py")
        assert result["status"] == "not_found", "Missing tool should return not_found"
        assert result["tool"] == "ruff"
    print("  [PASS] Missing formatter returns not_found")

    # Test formatter found and succeeds
    with patch("post_tool_use.shutil.which", return_value="/usr/bin/ruff"):
        with patch("post_tool_use.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = run_tool("ruff", ["format", "{file}"], "/tmp/test.py")
            assert result["status"] == "success", "Successful run should return success"
            assert result["returncode"] == 0
    print("  [PASS] Found formatter returns success")

    # Test formatter found but fails
    with patch("post_tool_use.shutil.which", return_value="/usr/bin/ruff"):
        with patch("post_tool_use.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            result = run_tool("ruff", ["format", "{file}"], "/tmp/test.py")
            assert result["status"] == "error", "Failed run should return error"
            assert result["returncode"] == 1
    print("  [PASS] Failed formatter returns error")

    # Test timeout handling
    with patch("post_tool_use.shutil.which", return_value="/usr/bin/ruff"):
        with patch("post_tool_use.subprocess.run") as mock_run:
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired("ruff", 30)
            result = run_tool("ruff", ["format", "{file}"], "/tmp/test.py")
            assert result["status"] == "timeout", "Timeout should return timeout status"
    print("  [PASS] Timeout handled correctly")

    print("  All formatter lookup unit tests passed!")


def test_unit_git_parsing():
    """Unit test: git output parsing with mocked subprocess."""

    print("Testing git output parsing (unit test)...")

    from stop_check import count_uncommitted_changes, count_unpushed_commits

    # Test clean repo (no changes)
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        assert count_uncommitted_changes() == 0, "Clean repo should return 0"
    print("  [PASS] Clean repo returns 0 changes")

    # Test repo with changes
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="M file.py\nA new.py\n?? untracked.py", stderr=""
        )
        assert count_uncommitted_changes() == 3, "Should count all status lines"
    print("  [PASS] Changed repo returns correct count")

    # Test git unavailable (FileNotFoundError)
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")
        assert count_uncommitted_changes() == 0, (
            "Missing git should return 0 (graceful)"
        )
    print("  [PASS] Missing git handled gracefully")

    # Test git command fails
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="not a git repo"
        )
        assert count_uncommitted_changes() == 0, "Failed git should return 0"
    print("  [PASS] Failed git command handled gracefully")

    # Test unpushed commits parsing
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout="abc1234 commit 1\ndef5678 commit 2", stderr=""
        )
        assert count_unpushed_commits() == 2, "Should count unpushed commits"
    print("  [PASS] Unpushed commits counted correctly")

    # Test no upstream (returns error)
    with patch("stop_check.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=128, stdout="", stderr="no upstream"
        )
        assert count_unpushed_commits() == 0, "No upstream should return 0"
    print("  [PASS] No upstream handled gracefully")

    print("  All git parsing unit tests passed!")


def test_unit_dangerous_patterns():
    """Unit test: dangerous command pattern matching edge cases."""
    print("Testing dangerous pattern matching (unit test)...")

    from pre_tool_use import is_dangerous

    # Dangerous patterns - should all be blocked (based on current patterns)
    dangerous_commands = [
        ("git push --force origin main", "force push"),
        ("git reset --hard HEAD~5", "hard reset"),
        ("rm -rf /", "rm root"),
        ("rm -rf ~", "rm home"),
        ("rm -rf $HOME", "rm $HOME"),
        ("dd if=/dev/zero of=/dev/sda", "dd to disk"),
        (":(){ :|:& };:", "fork bomb"),
        ("mkfs.ext4 /dev/sda1", "format filesystem"),
    ]

    for cmd, desc in dangerous_commands:
        is_blocked, pattern = is_dangerous(cmd)
        assert is_blocked, f"'{desc}' should be blocked: {cmd}"
    print("  [PASS] All dangerous patterns blocked")

    # Safe patterns - should all be allowed
    safe_commands = [
        ("git push origin main", "normal push"),
        ("git push --set-upstream origin feature", "set upstream"),
        ("git reset --soft HEAD~1", "soft reset"),
        ("rm -rf ./temp", "rm relative path"),
        ("rm file.txt", "rm single file"),
        ("echo hello", "simple echo"),
        ("ls -la", "list files"),
        ("cat file.txt", "read file"),
        ("dd if=input.img of=output.img", "dd to file"),
    ]

    for cmd, desc in safe_commands:
        is_blocked, pattern = is_dangerous(cmd)
        assert not is_blocked, f"'{desc}' should be allowed: {cmd}"
    print("  [PASS] All safe patterns allowed")

    # Edge cases
    is_blocked, _ = is_dangerous("")
    assert not is_blocked, "Empty command should be allowed"

    is_blocked, _ = is_dangerous("   ")
    assert not is_blocked, "Whitespace command should be allowed"

    print("  [PASS] Edge cases handled")

    # Verify pattern returns the matched pattern
    is_blocked, pattern = is_dangerous("git push --force origin main")
    assert is_blocked and pattern, "Should return matched pattern"
    print("  [PASS] Pattern returned on match")

    print("  All dangerous pattern unit tests passed!")


def test_unit_format_file():
    """Unit test: format_file orchestration logic."""

    print("Testing format_file orchestration (unit test)...")

    from post_tool_use import format_file

    # Mock run_tool to avoid running real formatters
    with patch("post_tool_use.run_tool") as mock_run_tool:
        mock_run_tool.return_value = {
            "tool": "ruff",
            "status": "success",
            "returncode": 0,
        }

        result = format_file("/tmp/test.py")

        assert result["file"] == "/tmp/test.py"
        assert result["extension"] == ".py"
        assert "formatters" in result
        assert "linters" in result
        # Should have attempted to run formatters for .py files
        assert mock_run_tool.called, "Should call run_tool for .py files"
    print("  [PASS] format_file returns correct structure")

    # Test unknown extension (no formatters configured)
    with patch("post_tool_use.run_tool") as mock_run_tool:
        result = format_file("/tmp/test.xyz")
        assert result["extension"] == ".xyz"
        assert result["formatters"] == []
        assert not mock_run_tool.called, (
            "Should not call run_tool for unknown extension"
        )
    print("  [PASS] Unknown extension handled correctly")

    print("  All format_file unit tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Line Cook Hooks Test Suite")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    print()

    try:
        # Integration tests (run hooks as subprocesses)
        print("=" * 60)
        print("Integration Tests (Subprocess - May Depend on Tools)")
        print("=" * 60)
        print()
        test_hook_utils()
        print()
        test_pre_tool_use()
        print()
        test_post_tool_use()
        print()
        test_stop_check()
        print()
        test_session_start()
        print()

        # Kiro CLI JSON format tests
        print("=" * 60)
        print("Kiro CLI Integration Tests")
        print("=" * 60)
        print()
        test_kiro_pre_tool_use_json_parsing()
        print()
        test_kiro_post_tool_use_json_parsing()
        print()
        test_kiro_stop_hook_json_parsing()
        print()
        test_tool_name_matching()
        print()
        test_exit_codes()
        print()
        test_json_output_format()
        print()

        # Unit tests (with mocking - no external tool dependencies)
        print("=" * 60)
        print("Unit Tests (Mocked - No External Dependencies)")
        print("=" * 60)
        print()
        test_unit_path_safety()
        print()
        test_unit_formatter_lookup()
        print()
        test_unit_git_parsing()
        print()
        test_unit_dangerous_patterns()
        print()
        test_unit_format_file()
        print()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n[FAIL] {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
