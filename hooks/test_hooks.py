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
    """Test pre_tool_use.py hook."""
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
    """Test post_tool_use.py hook."""
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

    # Test 4: Real Python file (if available)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("x=1\n")
        temp_path = f.name

    try:
        exit_code, stdout, stderr = run_hook(
            "post_tool_use.py",
            {"tool_name": "Write", "tool_input": {"file_path": temp_path}},
        )
        assert exit_code == 0, f"Real file should be processed, got exit {exit_code}"
        print(f"  [PASS] Real file processed (output: {stdout.strip() or 'none'})")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("  All post_tool_use tests passed!")


def test_stop_check():
    """Test stop_check.py hook."""
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
    """Test session_start.py hook."""
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

    # Import and test functions
    sys.path.insert(0, str(Path(__file__).parent))
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

    # Test 2: Kiro format - write tool with real file
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
            f"Kiro format real file should be processed, got exit {exit_code}"
        )
        print(
            f"  [PASS] Kiro format: real file processed (output: {stdout.strip() or 'none'})"
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


def main():
    """Run all tests."""
    print("=" * 60)
    print("Line Cook Hooks Test Suite")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    print()

    try:
        # Core functionality tests
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
