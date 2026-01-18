#!/usr/bin/env python3
"""
line-cook Stop hook
Checks if workflow stage is complete before stopping

Cross-platform compatible (Windows, Linux, macOS)
"""

import json
import os
import subprocess
import sys

from hook_utils import log_hook_end, log_hook_start, setup_logging


def run_git_command(args: list[str]) -> tuple[int, str]:
    """Run a git command and return (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def count_uncommitted_changes() -> int:
    """Count uncommitted changes in the working directory."""
    returncode, output = run_git_command(["status", "--porcelain"])
    if returncode != 0:
        return 0
    return len([line for line in output.split("\n") if line.strip()])


def count_unpushed_commits() -> int:
    """Count commits not yet pushed to upstream."""
    returncode, output = run_git_command(["log", "@{upstream}..HEAD", "--oneline"])
    if returncode != 0:
        return 0
    return len([line for line in output.split("\n") if line.strip()])


def main():
    logger = setup_logging("stop_check")

    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        input_data = {}

    log_hook_start(logger, input_data)

    # Get project directory
    project_dir = os.environ.get(
        "CLAUDE_PROJECT_DIR", input_data.get("cwd", ".")
    )

    # Check if we're in a git repo
    git_dir = os.path.join(project_dir, ".git")
    if not os.path.isdir(git_dir):
        log_hook_end(logger, 0, "not a git repo")
        sys.exit(0)

    # Check for uncommitted changes
    uncommitted = count_uncommitted_changes()
    if uncommitted > 0:
        output = {
            "continue": False,
            "systemMessage": f"Warning: {uncommitted} uncommitted changes. Consider running /line:tidy before stopping.",
        }
        print(json.dumps(output))
        log_hook_end(logger, 0, f"warned: {uncommitted} uncommitted changes")
        sys.exit(0)

    # Check for unpushed commits
    unpushed = count_unpushed_commits()
    if unpushed > 0:
        output = {
            "continue": False,
            "systemMessage": f"Warning: {unpushed} unpushed commits. Consider running git push before stopping.",
        }
        print(json.dumps(output))
        log_hook_end(logger, 0, f"warned: {unpushed} unpushed commits")
        sys.exit(0)

    # All clear - allow stop
    log_hook_end(logger, 0, "all clear")
    sys.exit(0)


if __name__ == "__main__":
    main()
