#!/usr/bin/env python3
"""
line-cook PreToolUse hook for Bash commands (Kiro CLI version)
Validates commands and prevents dangerous operations

Cross-platform compatible (Windows, Linux, macOS)
"""

import json
import re
import sys

from hook_utils import (
    log_hook_end,
    log_hook_start,
    setup_logging,
)

# Dangerous command patterns to block
DANGEROUS_PATTERNS = [
    r"git\s+push.*(?:--force|-f)",  # Force push (including -f shorthand)
    r"git\s+reset.*--hard",
    r"rm\s+-rf\s+/(?:\s|$)",  # rm -rf / (root)
    r"rm\s+-rf\s+~",  # rm -rf ~ (home)
    r"rm\s+-rf\s+\$HOME",  # rm -rf $HOME
    r"rm\s+-rf\s+%USERPROFILE%",  # Windows home
    r"rmdir\s+(?:/[sq]\s+)+C:\\",  # Windows root delete (flexible flag order)
    r"del\s+(?:/[fsq]\s+)+C:\\",  # Windows recursive delete (flexible flag order)
    r"format\s+[A-Z]:",  # Windows format drive
    r":\(\)\{ :\|:& \};:",  # Fork bomb (escaped special chars)
    r">\s*/dev/sda",  # Write to disk device
    r"dd\s+if=.*of=/dev/sd",  # dd to disk
    r"mkfs\.",  # Format filesystem
]


def is_dangerous(command: str) -> tuple[bool, str]:
    """Check if command matches any dangerous pattern."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern
    return False, ""


def main():
    logger = setup_logging("pre_tool_use")

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse hook input: {e}")
        sys.exit(1)

    log_hook_start(logger, input_data)

    # Get the command from tool input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        log_hook_end(logger, 0, "no command")
        sys.exit(0)

    # Check for dangerous commands
    dangerous, pattern = is_dangerous(command)
    if dangerous:
        # Output JSON for structured feedback
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Blocked dangerous command matching: {pattern}",
            },
            "systemMessage": f"Command blocked by safety hook: {command[:100]}{'...' if len(command) > 100 else ''}",
        }
        print(json.dumps(output))
        log_hook_end(logger, 2, f"blocked: {pattern}")
        sys.exit(2)

    # Allow the command
    log_hook_end(logger, 0, "allowed")
    sys.exit(0)


if __name__ == "__main__":
    main()
