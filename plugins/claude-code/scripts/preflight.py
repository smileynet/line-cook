#!/usr/bin/env python3
"""
preflight.py - Shared pre-flight gate for cook/serve/tidy phases.

Verifies environment before agent work begins: git repo state, beads
availability, and project tool detection.

Usage:
    python3 plugins/claude-code/scripts/preflight.py              # Full check
    python3 plugins/claude-code/scripts/preflight.py --json       # JSON output
    python3 plugins/claude-code/scripts/preflight.py --check git  # Git only

Exit codes:
    0: All checks pass (warnings are informational, not failures)
    1: Script error or critical failure
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GitInfo:
    """Git repository state."""
    clean: bool = True
    branch: Optional[str] = None
    has_remote: bool = False
    dirty_files: list[str] = field(default_factory=list)


@dataclass
class BeadsInfo:
    """Beads tracker state."""
    available: bool = False
    configured: bool = False
    ready_count: int = 0


@dataclass
class ToolsInfo:
    """Detected project tools."""
    test: Optional[str] = None
    build: Optional[str] = None
    lint: Optional[str] = None


@dataclass
class PreflightResult:
    """Combined pre-flight check result."""
    git: Optional[GitInfo] = None
    beads: Optional[BeadsInfo] = None
    tools: Optional[ToolsInfo] = None
    passed: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_cmd(args, timeout=10):
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "command not found: {}".format(args[0])
    except subprocess.TimeoutExpired:
        return -1, "", "timeout after {}s".format(timeout)


def check_git():
    """Check git repository state."""
    info = GitInfo()

    # Check if we're in a git repo
    rc, out, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if rc != 0:
        return info, ["Not inside a git repository"]

    # Current branch
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    if rc == 0:
        info.branch = out or "(detached HEAD)"

    # Remote tracking
    rc, out, _ = run_cmd(["git", "remote"])
    info.has_remote = rc == 0 and len(out) > 0

    # Dirty state
    rc, out, _ = run_cmd(["git", "status", "--porcelain"])
    if rc == 0 and out:
        info.dirty_files = out.splitlines()
        info.clean = False

    return info, []


def check_beads():
    """Check beads availability and configuration."""
    info = BeadsInfo()

    # Check .beads/ directory exists
    if Path(".beads").is_dir():
        info.configured = True

    # Check bd command exists
    rc, _, _ = run_cmd(["bd", "--version"])
    if rc != 0:
        return info, []

    info.available = True

    # Count ready items
    rc, out, _ = run_cmd(["bd", "ready", "--json"], timeout=15)
    if rc == 0 and out:
        try:
            data = json.loads(out)
            if isinstance(data, list):
                info.ready_count = len(data)
        except (json.JSONDecodeError, TypeError):
            pass

    return info, []


def detect_tools():
    """Detect project test/build/lint tools from project files."""
    info = ToolsInfo()
    warnings = []
    cwd = Path(".")

    # Test runner detection
    if (cwd / "package.json").exists():
        info.test = "npm test"
    elif (cwd / "pytest.ini").exists() or (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists():
        info.test = "pytest"
    elif (cwd / "go.mod").exists():
        info.test = "go test"
    elif (cwd / "Cargo.toml").exists():
        info.test = "cargo test"
    elif (cwd / "Makefile").exists():
        info.test = "make test"

    # Build tool detection
    if (cwd / "Makefile").exists():
        info.build = "make"
    elif (cwd / "package.json").exists():
        info.build = "npm run build"
    elif (cwd / "go.mod").exists():
        info.build = "go build"
    elif (cwd / "Cargo.toml").exists():
        info.build = "cargo build"

    # Lint tool detection
    if (cwd / "ruff.toml").exists() or (cwd / ".ruff.toml").exists():
        info.lint = "ruff"
    elif (cwd / ".eslintrc.js").exists() or (cwd / ".eslintrc.json").exists():
        info.lint = "eslint"
    elif (cwd / "pyproject.toml").exists():
        # Check if ruff or flake8 is configured in pyproject.toml
        try:
            content = (cwd / "pyproject.toml").read_text()
            if "[tool.ruff]" in content:
                info.lint = "ruff"
            elif "[tool.flake8]" in content:
                info.lint = "flake8"
        except OSError:
            pass
    elif (cwd / ".golangci.yml").exists():
        info.lint = "golangci-lint"

    if not info.test:
        warnings.append("No test runner detected")
    if not info.build:
        warnings.append("No build tool detected")
    if not info.lint:
        warnings.append("No lint tool detected")

    return info, warnings


def format_human(result):
    """Format PreflightResult as human-readable text."""
    lines = ["# Pre-flight Check", ""]

    if result.git:
        git = result.git
        status = "clean" if git.clean else "dirty ({} files)".format(len(git.dirty_files))
        lines.append("## Git")
        lines.append("  Branch: {}".format(git.branch or "unknown"))
        lines.append("  Status: {}".format(status))
        lines.append("  Remote: {}".format("yes" if git.has_remote else "no"))
        if git.dirty_files:
            lines.append("  Changed files:")
            for file_path in git.dirty_files[:20]:
                lines.append("    {}".format(file_path))
            if len(git.dirty_files) > 20:
                lines.append("    ... and {} more".format(len(git.dirty_files) - 20))
        lines.append("")

    if result.beads:
        beads = result.beads
        lines.append("## Beads")
        lines.append("  Available: {}".format("yes" if beads.available else "no"))
        lines.append("  Configured: {}".format("yes" if beads.configured else "no"))
        lines.append("  Ready items: {}".format(beads.ready_count))
        lines.append("")

    if result.tools:
        tools = result.tools
        lines.append("## Tools")
        lines.append("  Test: {}".format(tools.test or "not detected"))
        lines.append("  Build: {}".format(tools.build or "not detected"))
        lines.append("  Lint: {}".format(tools.lint or "not detected"))
        lines.append("")

    if result.errors:
        lines.append("## Errors")
        for error in result.errors:
            lines.append("  - {}".format(error))
        lines.append("")

    if result.warnings:
        lines.append("## Warnings")
        for warning in result.warnings:
            lines.append("  - {}".format(warning))
        lines.append("")

    verdict = "PASS" if result.passed else "FAIL"
    lines.append("Result: {}".format(verdict))

    return "\n".join(lines)


def format_json(result):
    """Format PreflightResult as JSON."""
    data = {
        "git": None,
        "beads": None,
        "tools": None,
        "passed": result.passed,
        "errors": result.errors,
        "warnings": result.warnings,
    }

    if result.git:
        git = result.git
        data["git"] = {
            "clean": git.clean,
            "branch": git.branch,
            "has_remote": git.has_remote,
            "dirty_files": git.dirty_files,
        }

    if result.beads:
        beads = result.beads
        data["beads"] = {
            "available": beads.available,
            "configured": beads.configured,
            "ready_count": beads.ready_count,
        }

    if result.tools:
        tools = result.tools
        data["tools"] = {
            "test": tools.test,
            "build": tools.build,
            "lint": tools.lint,
        }

    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Pre-flight environment check for cook/serve/tidy phases"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--check", choices=["git", "bd", "tools"],
        help="Only run specific check category"
    )

    args = parser.parse_args()

    result = PreflightResult()

    if args.check is None or args.check == "git":
        result.git, git_errors = check_git()
        result.errors.extend(git_errors)

    if args.check is None or args.check == "bd":
        result.beads, beads_errors = check_beads()
        result.errors.extend(beads_errors)

    if args.check is None or args.check == "tools":
        result.tools, tools_warnings = detect_tools()
        result.warnings.extend(tools_warnings)

    result.passed = len(result.errors) == 0

    if args.json:
        print(format_json(result))
    else:
        print(format_human(result))

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
