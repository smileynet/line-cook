#!/usr/bin/env python3
"""
check-plugin-health.py - Verify versions match and plugins have feature parity.

Usage:
    ./dev/check-plugin-health.py                # Full report
    ./dev/check-plugin-health.py --json         # JSON for CI
    ./dev/check-plugin-health.py --skip-changelog  # Skip CHANGELOG check
    ./dev/check-plugin-health.py --check version   # Version only

Exit codes:
    0: All checks pass
    1: Errors found
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class HealthResult:
    """Result of a health check."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


@dataclass
class VersionInfo:
    """Version information from various sources."""
    plugin_json: Optional[str] = None
    opencode_version: Optional[str] = None
    opencode_plugin_version: Optional[str] = None
    changelog_latest: Optional[str] = None


@dataclass
class MetadataInfo:
    """Metadata from various sources."""
    plugin_name: Optional[str] = None
    opencode_name: Optional[str] = None
    plugin_author: Optional[str] = None
    opencode_author: Optional[str] = None
    plugin_repo: Optional[str] = None
    opencode_repo: Optional[str] = None


def extract_plugin_json_info(repo_root: Path) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extract version and metadata from plugin.json."""
    plugin_path = repo_root / "plugins" / "claude-code" / ".claude-plugin" / "plugin.json"
    if not plugin_path.exists():
        return None, None, None, None

    try:
        data = json.loads(plugin_path.read_text())
        version = data.get("version")
        name = data.get("name")
        author = data.get("author", {})
        author_name = author.get("name") if isinstance(author, dict) else author
        repo = data.get("repository")
        return version, name, author_name, repo
    except (json.JSONDecodeError, KeyError):
        return None, None, None, None


def extract_opencode_info(repo_root: Path) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Extract version and metadata from OpenCode package.json."""
    package_path = repo_root / "plugins" / "opencode" / "package.json"
    if not package_path.exists():
        return None, None, None, None, None

    try:
        data = json.loads(package_path.read_text())
        version = data.get("version")
        opencode_data = data.get("opencode", {})
        opencode_version = opencode_data.get("version")
        name = opencode_data.get("name") or data.get("name")
        author = data.get("author", {})
        author_name = author.get("name") if isinstance(author, dict) else author
        repo = data.get("repository", {})
        repo_url = repo.get("url") if isinstance(repo, dict) else repo
        return version, opencode_version, name, author_name, repo_url
    except (json.JSONDecodeError, KeyError):
        return None, None, None, None, None


def extract_changelog_version(repo_root: Path) -> Optional[str]:
    """Extract latest version from CHANGELOG.md."""
    changelog_path = repo_root / "CHANGELOG.md"
    if not changelog_path.exists():
        return None

    content = changelog_path.read_text()

    # Match [X.Y.Z] version headers (skip [Unreleased])
    pattern = r"^## \[(\d+\.\d+\.\d+)\]"
    matches = re.findall(pattern, content, re.MULTILINE)

    return matches[0] if matches else None


def count_commands(repo_root: Path) -> dict[str, int]:
    """Count commands on each platform."""
    counts = {}

    # Claude Code commands
    claude_code_dir = repo_root / "plugins" / "claude-code" / "commands"
    if claude_code_dir.exists():
        counts["claude_code"] = len(list(claude_code_dir.glob("*.md")))
    else:
        counts["claude_code"] = 0

    # OpenCode commands
    opencode_dir = repo_root / "plugins" / "opencode" / "commands"
    if opencode_dir.exists():
        counts["opencode"] = len(list(opencode_dir.glob("*.md")))
    else:
        counts["opencode"] = 0

    # Kiro steering files (commands)
    kiro_dir = repo_root / "plugins" / "kiro" / "steering"
    if kiro_dir.exists():
        counts["kiro"] = len(list(kiro_dir.glob("*.md")))
    else:
        counts["kiro"] = 0

    return counts


def count_agents(repo_root: Path) -> dict[str, int]:
    """Count agents on each platform."""
    counts = {}

    # Claude Code agents
    claude_code_dir = repo_root / "plugins" / "claude-code" / "agents"
    if claude_code_dir.exists():
        counts["claude_code"] = len(list(claude_code_dir.glob("*.md")))
    else:
        counts["claude_code"] = 0

    # OpenCode agents
    opencode_dir = repo_root / "plugins" / "opencode" / "agents"
    if opencode_dir.exists():
        counts["opencode"] = len(list(opencode_dir.glob("*.md")))
    else:
        counts["opencode"] = 0

    # Kiro agents
    kiro_dir = repo_root / "plugins" / "kiro" / "agents"
    if kiro_dir.exists():
        counts["kiro"] = len(list(kiro_dir.glob("*.json")))
    else:
        counts["kiro"] = 0

    return counts


def check_version_parity(versions: VersionInfo, skip_changelog: bool = False) -> HealthResult:
    """Check that all versions match."""
    result = HealthResult()

    # Collect all versions
    all_versions = {}
    if versions.plugin_json:
        all_versions["plugin.json"] = versions.plugin_json
    if versions.opencode_version:
        all_versions["package.json (version)"] = versions.opencode_version
    if versions.opencode_plugin_version:
        all_versions["package.json (opencode.version)"] = versions.opencode_plugin_version
    if not skip_changelog and versions.changelog_latest:
        all_versions["CHANGELOG.md"] = versions.changelog_latest

    result.info.append(f"Versions found: {all_versions}")

    # Check if all versions are the same
    unique_versions = set(all_versions.values())

    if len(unique_versions) == 0:
        result.errors.append("No version information found")
    elif len(unique_versions) == 1:
        result.info.append(f"All versions match: {unique_versions.pop()}")
    else:
        result.errors.append(f"Version mismatch detected: {all_versions}")

    # Check that package.json version matches opencode.version
    if versions.opencode_version and versions.opencode_plugin_version:
        if versions.opencode_version != versions.opencode_plugin_version:
            result.errors.append(
                f"OpenCode version mismatch: package version={versions.opencode_version}, "
                f"opencode.version={versions.opencode_plugin_version}"
            )

    return result


def check_metadata_parity(metadata: MetadataInfo) -> HealthResult:
    """Check that metadata is consistent across platforms."""
    result = HealthResult()

    # Check names (allowing for namespace differences)
    if metadata.plugin_name and metadata.opencode_name:
        # Normalize names for comparison
        plugin_name = metadata.plugin_name.lower().replace("-", "").replace("_", "")
        opencode_name = metadata.opencode_name.lower().replace("-", "").replace("_", "").replace("@", "").replace("/", "")

        # Both should contain "line"
        if "line" not in plugin_name or "line" not in opencode_name:
            result.warnings.append(
                f"Plugin names may not match: plugin={metadata.plugin_name}, opencode={metadata.opencode_name}"
            )

    # Check authors
    if metadata.plugin_author and metadata.opencode_author:
        if metadata.plugin_author != metadata.opencode_author:
            result.warnings.append(
                f"Author mismatch: plugin={metadata.plugin_author}, opencode={metadata.opencode_author}"
            )

    # Check repositories
    if metadata.plugin_repo and metadata.opencode_repo:
        # Normalize repo URLs
        plugin_repo = metadata.plugin_repo.rstrip("/").rstrip(".git")
        opencode_repo = metadata.opencode_repo.rstrip("/").rstrip(".git")

        if plugin_repo != opencode_repo:
            result.warnings.append(
                f"Repository mismatch: plugin={metadata.plugin_repo}, opencode={metadata.opencode_repo}"
            )

    result.info.append(f"Plugin metadata: name={metadata.plugin_name}, author={metadata.plugin_author}")
    result.info.append(f"OpenCode metadata: name={metadata.opencode_name}, author={metadata.opencode_author}")

    return result


def check_command_counts(counts: dict[str, int]) -> HealthResult:
    """Check command counts are reasonable."""
    result = HealthResult()

    result.info.append(f"Command counts: {counts}")

    # All platforms should have at least some commands
    for platform, count in counts.items():
        if count == 0:
            result.warnings.append(f"{platform} has no commands")
        elif count < 6:
            result.warnings.append(f"{platform} has fewer than expected commands ({count})")

    # Check for significant disparity
    if counts:
        max_count = max(counts.values())
        min_count = min(counts.values())
        if max_count > min_count * 2 and min_count > 0:
            result.warnings.append(
                f"Large command count disparity: max={max_count}, min={min_count}"
            )

    return result


def check_agent_counts(counts: dict[str, int]) -> HealthResult:
    """Check agent counts are reasonable."""
    result = HealthResult()

    result.info.append(f"Agent counts: {counts}")

    # Claude Code and Kiro should have agents
    if counts.get("claude_code", 0) == 0:
        result.warnings.append("Claude Code has no agents defined")

    if counts.get("kiro", 0) == 0:
        result.warnings.append("Kiro has no agents defined")

    # OpenCode missing agents is expected (flagged as info, not warning)
    if counts.get("opencode", 0) == 0:
        result.info.append("OpenCode has no agents (expected - not yet implemented)")

    return result


def format_human_report(
    version_result: Optional[HealthResult],
    metadata_result: Optional[HealthResult],
    command_result: Optional[HealthResult],
    agent_result: Optional[HealthResult]
) -> str:
    """Format results as human-readable report."""
    lines = ["# Plugin Health Report", ""]

    total_errors = 0
    total_warnings = 0

    sections = [
        ("Versions", version_result),
        ("Metadata", metadata_result),
        ("Commands", command_result),
        ("Agents", agent_result),
    ]

    for section_name, result in sections:
        if result is None:
            continue

        lines.append(f"## {section_name}")
        lines.append("")

        if result.errors:
            lines.append("### Errors")
            for err in result.errors:
                lines.append(f"  - {err}")
            lines.append("")
            total_errors += len(result.errors)

        if result.warnings:
            lines.append("### Warnings")
            for warn in result.warnings:
                lines.append(f"  - {warn}")
            lines.append("")
            total_warnings += len(result.warnings)

        if result.info:
            lines.append("### Info")
            for info in result.info:
                lines.append(f"  - {info}")
            lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"  Errors: {total_errors}")
    lines.append(f"  Warnings: {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        lines.append("")
        lines.append("  All checks passed!")

    return "\n".join(lines)


def format_json_report(
    version_result: Optional[HealthResult],
    metadata_result: Optional[HealthResult],
    command_result: Optional[HealthResult],
    agent_result: Optional[HealthResult]
) -> str:
    """Format results as JSON."""
    report = {
        "versions": None,
        "metadata": None,
        "commands": None,
        "agents": None,
        "summary": {
            "errors": 0,
            "warnings": 0,
            "passed": True
        }
    }

    sections = [
        ("versions", version_result),
        ("metadata", metadata_result),
        ("commands", command_result),
        ("agents", agent_result),
    ]

    for key, result in sections:
        if result:
            report[key] = {
                "errors": result.errors,
                "warnings": result.warnings,
                "info": result.info
            }
            report["summary"]["errors"] += len(result.errors)
            report["summary"]["warnings"] += len(result.warnings)

    report["summary"]["passed"] = report["summary"]["errors"] == 0

    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check plugin health and version parity"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--skip-changelog", action="store_true",
        help="Skip CHANGELOG version check"
    )
    parser.add_argument(
        "--check", choices=["version", "metadata", "commands", "agents"],
        help="Only check specific category"
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI mode: JSON output and strict exit codes"
    )

    args = parser.parse_args()

    if args.ci:
        args.json = True

    # Find repository root
    repo_root = Path(__file__).parent.parent

    # Extract information
    plugin_version, plugin_name, plugin_author, plugin_repo = extract_plugin_json_info(repo_root)
    opencode_version, opencode_plugin_version, opencode_name, opencode_author, opencode_repo = extract_opencode_info(repo_root)
    changelog_version = extract_changelog_version(repo_root)

    versions = VersionInfo(
        plugin_json=plugin_version,
        opencode_version=opencode_version,
        opencode_plugin_version=opencode_plugin_version,
        changelog_latest=changelog_version
    )

    metadata = MetadataInfo(
        plugin_name=plugin_name,
        opencode_name=opencode_name,
        plugin_author=plugin_author,
        opencode_author=opencode_author,
        plugin_repo=plugin_repo,
        opencode_repo=opencode_repo
    )

    command_counts = count_commands(repo_root)
    agent_counts = count_agents(repo_root)

    # Run checks
    version_result = None
    metadata_result = None
    command_result = None
    agent_result = None

    if args.check is None or args.check == "version":
        version_result = check_version_parity(versions, args.skip_changelog)

    if args.check is None or args.check == "metadata":
        metadata_result = check_metadata_parity(metadata)

    if args.check is None or args.check == "commands":
        command_result = check_command_counts(command_counts)

    if args.check is None or args.check == "agents":
        agent_result = check_agent_counts(agent_counts)

    # Format output
    if args.json:
        print(format_json_report(version_result, metadata_result, command_result, agent_result))
    else:
        print(format_human_report(version_result, metadata_result, command_result, agent_result))

    # Determine exit code
    total_errors = 0
    for result in [version_result, metadata_result, command_result, agent_result]:
        if result:
            total_errors += len(result.errors)

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
