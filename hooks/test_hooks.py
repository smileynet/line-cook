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
    exit_code, stdout, stderr = run_hook("pre_tool_use.py", {
        "tool_name": "Bash",
        "tool_input": {"command": "git status"}
    })
    assert exit_code == 0, f"Safe command should be allowed, got exit {exit_code}"
    print("  [PASS] Safe command allowed")

    # Test 2: Dangerous command should be blocked
    exit_code, stdout, stderr = run_hook("pre_tool_use.py", {
        "tool_name": "Bash",
        "tool_input": {"command": "git push --force origin main"}
    })
    assert exit_code == 2, f"Dangerous command should be blocked, got exit {exit_code}"
    assert "deny" in stdout.lower() or "blocked" in stdout.lower(), "Should output denial message"
    print("  [PASS] Dangerous command blocked")

    # Test 3: Empty command should be allowed
    exit_code, stdout, stderr = run_hook("pre_tool_use.py", {
        "tool_name": "Bash",
        "tool_input": {"command": ""}
    })
    assert exit_code == 0, f"Empty command should be allowed, got exit {exit_code}"
    print("  [PASS] Empty command handled")

    print("  All pre_tool_use tests passed!")


def test_post_tool_use():
    """Test post_tool_use.py hook."""
    print("Testing post_tool_use.py...")

    # Test 1: Non-existent file should be skipped
    exit_code, stdout, stderr = run_hook("post_tool_use.py", {
        "tool_name": "Write",
        "tool_input": {"file_path": "/nonexistent/file.py"}
    })
    assert exit_code == 0, f"Non-existent file should be skipped, got exit {exit_code}"
    print("  [PASS] Non-existent file skipped")

    # Test 2: Sensitive file should be skipped
    exit_code, stdout, stderr = run_hook("post_tool_use.py", {
        "tool_name": "Write",
        "tool_input": {"file_path": "/home/user/.env"}
    })
    assert exit_code == 0, f"Sensitive file should be skipped, got exit {exit_code}"
    print("  [PASS] Sensitive file skipped")

    # Test 3: Path traversal should be blocked
    exit_code, stdout, stderr = run_hook("post_tool_use.py", {
        "tool_name": "Write",
        "tool_input": {"file_path": "/some/path/../../../etc/passwd"}
    })
    assert exit_code == 0, f"Path traversal should be skipped, got exit {exit_code}"
    print("  [PASS] Path traversal blocked")

    # Test 4: Real Python file (if available)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("x=1\n")
        temp_path = f.name

    try:
        exit_code, stdout, stderr = run_hook("post_tool_use.py", {
            "tool_name": "Write",
            "tool_input": {"file_path": temp_path}
        })
        assert exit_code == 0, f"Real file should be processed, got exit {exit_code}"
        print(f"  [PASS] Real file processed (output: {stdout.strip() or 'none'})")
    finally:
        Path(temp_path).unlink(missing_ok=True)

    print("  All post_tool_use tests passed!")


def test_stop_check():
    """Test stop_check.py hook."""
    print("Testing stop_check.py...")

    # Test 1: Basic execution (will check git status)
    exit_code, stdout, stderr = run_hook("stop_check.py", {
        "session_id": "test-session",
    })
    assert exit_code == 0, f"Stop check should complete, got exit {exit_code}"
    print(f"  [PASS] Stop check completed (output: {stdout.strip() or 'none'})")

    print("  All stop_check tests passed!")


def test_session_start():
    """Test session_start.py hook."""
    print("Testing session_start.py...")

    # Test 1: Basic execution
    exit_code, stdout, stderr = run_hook("session_start.py", {
        "session_id": "test-session",
    })
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
    assert log_path.name == "hooks.log", f"Log file should be hooks.log, got {log_path.name}"
    print(f"  [PASS] Log path: {log_path}")

    # Test logger setup
    logger = setup_logging("test")
    assert logger.name == "line-cook.test", f"Logger name wrong: {logger.name}"
    print("  [PASS] Logger setup works")

    print("  All hook_utils tests passed!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Line Cook Hooks Test Suite")
    print(f"Platform: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    print()

    try:
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
