#!/usr/bin/env python3
"""
line-cook Stop hook (Kiro CLI version).
Checks if workflow stage is complete before stopping.

Cross-platform compatible (Windows, Linux, macOS)
"""

import os
import subprocess
import sys

from hook_utils import log_hook_end, log_hook_start, read_hook_input, setup_logging


def run_git_command(args: list[str], cwd: str | None = None) -> tuple[int, str]:
    """Run a git command and return (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=cwd,
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def is_git_repo(project_dir: str) -> bool:
    """Check if directory is a git repo (handles worktrees and submodules)."""
    returncode, _ = run_git_command(["rev-parse", "--git-dir"], cwd=project_dir)
    return returncode == 0


def count_uncommitted_changes(cwd: str | None = None) -> int:
    """Count uncommitted changes in the working directory."""
    returncode, output = run_git_command(["status", "--porcelain"], cwd=cwd)
    if returncode != 0:
        return 0
    return len([line for line in output.split("\n") if line.strip()])


def count_unpushed_commits(cwd: str | None = None) -> int:
    """Count commits not yet pushed to upstream."""
    returncode, output = run_git_command(
        ["log", "@{upstream}..HEAD", "--oneline"], cwd=cwd
    )
    if returncode != 0:
        return 0
    return len([line for line in output.split("\n") if line.strip()])


def main():
    logger = setup_logging("stop_check")

    input_data = read_hook_input()
    log_hook_start(logger, input_data)

    # Get project directory - check KIRO_PROJECT_DIR first, then cwd from input
    project_dir = os.environ.get("KIRO_PROJECT_DIR", input_data.get("cwd", "."))

    # Check if we're in a git repo (handles worktrees and submodules)
    if not is_git_repo(project_dir):
        log_hook_end(logger, 0, "not a git repo")
        sys.exit(0)

    # Check for uncommitted changes
    uncommitted = count_uncommitted_changes(cwd=project_dir)
    unpushed = count_unpushed_commits(cwd=project_dir)

    # Build warnings list (log only, don't output to user)
    warnings = []
    if uncommitted > 0:
        warnings.append(f"{uncommitted} uncommitted changes")
    if unpushed > 0:
        warnings.append(f"{unpushed} unpushed commits")

    if warnings:
        log_hook_end(logger, 0, f"warn: {', '.join(warnings)}")
    else:
        log_hook_end(logger, 0, "all clear")

    # Allow stop - warnings logged but not shown to user
    sys.exit(0)


if __name__ == "__main__":
    main()
