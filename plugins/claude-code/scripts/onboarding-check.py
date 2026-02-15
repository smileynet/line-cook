#!/usr/bin/env python3
"""
onboarding-check.py - Shared diagnostic script for init and doctor commands.

Verifies environment setup: git repo, beads CLI, project configuration,
plugin health, and spice rack detection.

Usage:
    python3 onboarding-check.py              # Human-readable
    python3 onboarding-check.py --json       # JSON output
    python3 onboarding-check.py --check git  # Single category

Exit codes:
    0: All checks pass (warnings are informational, not failure)
    1: Script error or critical failure
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from helpers import run_cmd


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Single diagnostic check result."""
    name: str
    category: str
    status: str  # "pass", "warn", "fail"
    message: str
    fix_hint: Optional[str] = None


@dataclass
class SpiceInfo:
    """Info about a marketplace spice plugin."""
    name: str
    installed: bool = False
    local: bool = False  # True if it's the local "line" plugin, not an external spice
    version: Optional[str] = None


@dataclass
class DiagnosticReport:
    """Full diagnostic report."""
    checks: list[CheckResult] = field(default_factory=list)
    spices: list[SpiceInfo] = field(default_factory=list)
    version: Optional[str] = None

    @property
    def summary(self):
        passed = sum(1 for c in self.checks if c.status in ("pass", "info"))
        warned = sum(1 for c in self.checks if c.status == "warn")
        failed = sum(1 for c in self.checks if c.status == "fail")
        return {"passed": passed, "warned": warned, "failed": failed}


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_git_repo() -> CheckResult:
    """Check if inside a git repository."""
    rc, _, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if rc != 0:
        return CheckResult(
            name="git_repo", category="project", status="fail",
            message="Not inside a git repository",
            fix_hint="Run 'git init' to create a repository",
        )
    return CheckResult(
        name="git_repo", category="project", status="pass",
        message="Git repository configured",
    )


def check_git_remote() -> CheckResult:
    """Check if a git remote is configured."""
    rc, out, _ = run_cmd(["git", "remote"])
    if rc != 0 or not out.strip():
        return CheckResult(
            name="git_remote", category="project", status="warn",
            message="No git remote configured",
            fix_hint="Run 'git remote add origin <url>' to add a remote",
        )
    return CheckResult(
        name="git_remote", category="project", status="pass",
        message="Git remote configured",
    )


def check_bd_installed() -> CheckResult:
    """Check if bd command is available."""
    rc, _, _ = run_cmd(["bd", "--version"])
    if rc != 0:
        return CheckResult(
            name="bd_installed", category="system", status="fail",
            message="Beads CLI (bd) not installed",
            fix_hint="brew install beads (see https://github.com/steveyegge/beads)",
        )
    return CheckResult(
        name="bd_installed", category="system", status="pass",
        message="Beads CLI installed",
    )


def check_bd_version() -> CheckResult:
    """Check bd version string."""
    rc, out, _ = run_cmd(["bd", "--version"])
    if rc != 0 or not out.strip():
        return CheckResult(
            name="bd_version", category="system", status="warn",
            message="Could not determine beads version",
        )
    version = out.strip().split()[-1] if out.strip() else "unknown"
    return CheckResult(
        name="bd_version", category="system", status="pass",
        message="Beads {}".format(version),
    )


def check_bd_configured() -> CheckResult:
    """Check if .beads/ directory exists."""
    if not Path(".beads").is_dir():
        return CheckResult(
            name="bd_configured", category="project", status="warn",
            message="Beads not initialized in this project",
            fix_hint="Run 'bd init' to initialize beads tracking",
        )
    return CheckResult(
        name="bd_configured", category="project", status="pass",
        message="Beads initialized (.beads/)",
    )


def check_bd_health() -> CheckResult:
    """Run bd doctor for internal health check."""
    if not Path(".beads").is_dir():
        return CheckResult(
            name="bd_health", category="project", status="warn",
            message="Skipped (beads not initialized)",
        )
    rc, out, err = run_cmd(["bd", "doctor"], timeout=15)
    if rc != 0:
        return CheckResult(
            name="bd_health", category="project", status="warn",
            message="Beads doctor reported issues: {}".format(
                (err or out or "unknown").split("\n")[0]
            ),
            fix_hint="Run 'bd doctor' for full details",
        )
    return CheckResult(
        name="bd_health", category="project", status="pass",
        message="Beads health check passed",
    )


def find_plugin_json() -> Optional[Path]:
    """Discover plugin.json by searching up from script location and CWD."""
    # Check relative to this script (typical installed location)
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir.parent / ".claude-plugin" / "plugin.json"
    if candidate.is_file():
        return candidate

    # Check CWD (e.g., running from line-cook repo root)
    cwd_candidate = Path(".claude-plugin") / "marketplace.json"
    if cwd_candidate.is_file():
        # In the repo root, the plugin.json is under plugins/claude-code/
        repo_plugin = Path("plugins/claude-code/.claude-plugin/plugin.json")
        if repo_plugin.is_file():
            return repo_plugin

    return None


def check_plugin_version() -> CheckResult:
    """Read version from discoverable plugin.json."""
    pj = find_plugin_json()
    if pj is None:
        return CheckResult(
            name="plugin_version", category="plugin", status="warn",
            message="Could not locate plugin.json",
        )
    try:
        data = json.loads(pj.read_text())
        version = data.get("version", "unknown")
        return CheckResult(
            name="plugin_version", category="plugin", status="pass",
            message="Line Cook v{}".format(version),
        )
    except (json.JSONDecodeError, OSError) as exc:
        return CheckResult(
            name="plugin_version", category="plugin", status="warn",
            message="Error reading plugin.json: {}".format(exc),
        )


def check_scripts_available() -> CheckResult:
    """Check that helper scripts are discoverable."""
    script_dir = Path(__file__).resolve().parent
    expected = ["preflight.py", "state-snapshot.py", "helpers.py"]
    missing = [s for s in expected if not (script_dir / s).is_file()]
    if missing:
        return CheckResult(
            name="scripts_available", category="plugin", status="warn",
            message="Missing scripts: {}".format(", ".join(missing)),
            fix_hint="Reinstall the plugin: /plugin update line",
        )
    return CheckResult(
        name="scripts_available", category="plugin", status="pass",
        message="Helper scripts available",
    )


# ---------------------------------------------------------------------------
# Spice rack detection
# ---------------------------------------------------------------------------

def find_marketplace_json() -> Optional[Path]:
    """Locate marketplace.json."""
    script_dir = Path(__file__).resolve().parent

    # Installed plugin: scripts/ -> line/ -> marketplace-root/
    candidate_2 = script_dir.parent.parent / ".claude-plugin" / "marketplace.json"
    if candidate_2.is_file():
        return candidate_2

    # Repo layout: scripts/ -> claude-code/ -> plugins/ -> repo-root/
    candidate_3 = script_dir.parent.parent.parent / ".claude-plugin" / "marketplace.json"
    if candidate_3.is_file():
        return candidate_3

    # CWD is repo root
    cwd_candidate = Path(".claude-plugin") / "marketplace.json"
    if cwd_candidate.is_file():
        return cwd_candidate

    return None


def detect_spices() -> tuple[list[SpiceInfo], CheckResult]:
    """Detect installed spice rack plugins from marketplace.json."""
    mp = find_marketplace_json()
    if mp is None:
        return [], CheckResult(
            name="spice_plugins", category="plugin", status="warn",
            message="Could not locate marketplace.json",
        )

    try:
        data = json.loads(mp.read_text())
    except (json.JSONDecodeError, OSError):
        return [], CheckResult(
            name="spice_plugins", category="plugin", status="warn",
            message="Error reading marketplace.json",
        )

    plugins = data.get("plugins", [])
    spices: list[SpiceInfo] = []
    marketplace_name = data.get("name", "line-cook")
    cache_base = Path.home() / ".claude" / "plugins" / "cache" / "{}-marketplace".format(marketplace_name)

    for entry in plugins:
        name = entry.get("name", "")
        source = entry.get("source", "")

        # Local plugin (not an external spice)
        if isinstance(source, str) and source.startswith("./"):
            spices.append(SpiceInfo(name=name, local=True, installed=True))
            continue

        # External spice — check if installed
        spice_dir = cache_base / name
        installed = spice_dir.is_dir()
        version = None
        if installed:
            pj = spice_dir / ".claude-plugin" / "plugin.json"
            if pj.is_file():
                try:
                    pj_data = json.loads(pj.read_text())
                    version = pj_data.get("version")
                except (json.JSONDecodeError, OSError):
                    pass

        spices.append(SpiceInfo(name=name, installed=installed, version=version))

    external = [s for s in spices if not s.local]
    installed_count = sum(1 for s in external if s.installed)
    total = len(external)

    if total == 0:
        msg = "No spice plugins listed in marketplace"
    elif installed_count == total:
        msg = "All {} spice(s) installed".format(total)
    else:
        uninstalled = [s.name for s in external if not s.installed]
        msg = "{}/{} spice(s) installed ({} available: {})".format(
            installed_count, total, len(uninstalled), ", ".join(uninstalled)
        )

    return spices, CheckResult(
        name="spice_plugins", category="plugin",
        status="pass" if installed_count == total else "info",
        message=msg,
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_checks(category: Optional[str] = None) -> DiagnosticReport:
    """Run all diagnostic checks, optionally filtered by category."""
    report = DiagnosticReport()

    all_checks = [
        ("project", check_git_repo),
        ("project", check_git_remote),
        ("system", check_bd_installed),
        ("system", check_bd_version),
        ("project", check_bd_configured),
        ("project", check_bd_health),
        ("plugin", check_plugin_version),
        ("plugin", check_scripts_available),
    ]

    for cat, fn in all_checks:
        if category and cat != category:
            continue
        report.checks.append(fn())

    # Spice detection (part of plugin category)
    if category is None or category == "plugin":
        spices, spice_check = detect_spices()
        report.spices = spices
        report.checks.append(spice_check)

    # Extract version from plugin check
    for c in report.checks:
        if c.name == "plugin_version" and c.status == "pass":
            report.version = c.message.replace("Line Cook v", "")
            break

    return report


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

STATUS_ICON = {"pass": "✓", "warn": "⚠", "fail": "✗", "info": "○"}


def format_human(report: DiagnosticReport) -> str:
    """Format as human-readable report."""
    lines = []

    # Group by category
    categories = {}
    for c in report.checks:
        categories.setdefault(c.category, []).append(c)

    for cat in ["system", "project", "plugin"]:
        group = categories.get(cat, [])
        if not group:
            continue
        lines.append(cat.upper())
        for c in group:
            icon = STATUS_ICON.get(c.status, "?")
            lines.append("  {} {}".format(icon, c.message))
            if c.fix_hint and c.status in ("fail", "warn"):
                lines.append("    Fix: {}".format(c.fix_hint))
        lines.append("")

    # Spice rack
    external_spices = [s for s in report.spices if not s.local]
    if external_spices:
        lines.append("SPICE RACK")
        for s in external_spices:
            if s.installed:
                ver = " v{}".format(s.version) if s.version else ""
                lines.append("  ✓ {} (installed{})".format(s.name, ver))
            else:
                lines.append("  ○ {} (available, not installed)".format(s.name))
        lines.append("")

    # Summary
    summary = report.summary
    lines.append("Result: {} passed, {} warnings, {} failed".format(
        summary["passed"], summary["warned"], summary["failed"]
    ))

    return "\n".join(lines)


def format_json(report: DiagnosticReport) -> str:
    """Format as JSON."""
    data = {
        "checks": [
            {
                "name": c.name,
                "category": c.category,
                "status": c.status,
                "message": c.message,
                "fix_hint": c.fix_hint,
            }
            for c in report.checks
        ],
        "spices": [
            {
                "name": s.name,
                "installed": s.installed,
                "local": s.local,
                "version": s.version,
            }
            for s in report.spices
        ],
        "summary": report.summary,
        "version": report.version,
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Onboarding diagnostic checks for Line Cook"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format",
    )
    parser.add_argument(
        "--check", choices=["git", "system", "project", "plugin"],
        help="Only run checks for a specific category",
    )
    args = parser.parse_args()

    # Map convenience aliases
    category = args.check
    if category == "git":
        category = "project"

    report = run_checks(category)

    if args.json:
        print(format_json(report))
    else:
        print(format_human(report))

    has_failures = report.summary["failed"] > 0
    sys.exit(1 if has_failures else 0)


if __name__ == "__main__":
    main()
