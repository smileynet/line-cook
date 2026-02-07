#!/usr/bin/env python3
"""
check-platform-parity.py - Validate commands and agents are consistent across
Claude Code, OpenCode, and Kiro platforms.

Usage:
    ./dev/check-platform-parity.py              # Human-readable report
    ./dev/check-platform-parity.py --json       # JSON output for CI
    ./dev/check-platform-parity.py --strict     # Exit 1 on warnings
    ./dev/check-platform-parity.py --check commands  # Commands only
    ./dev/check-platform-parity.py --check agents    # Agents only

Exit codes:
    0: All checks pass
    1: Errors found (missing required parity)
    2: Warnings found (with --strict)
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ParityResult:
    """Result of a parity check."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


@dataclass
class PlatformAssets:
    """Assets discovered on a platform."""
    commands: set[str] = field(default_factory=set)
    agents: set[str] = field(default_factory=set)


# Core commands that should exist on all platforms
CORE_COMMANDS = {
    "getting-started", "mise", "prep", "cook", "serve", "tidy", "plate"
}

# Commands with intentional differences
PLATFORM_SPECIFIC_COMMANDS = {
    "claude-code": {"service"},      # Claude Code only: service (full orchestration)
    "opencode": {"work"},            # OpenCode only: work (orchestration)
    "kiro": set(),                   # Kiro uses steering files, not commands
}

# Shared agents that should exist on Claude Code and Kiro
# OpenCode SDK supports agents but plugins/opencode hasn't implemented them yet
SHARED_AGENTS = {"taster", "sous-chef", "maitre", "polisher", "critic"}

# Kiro-only orchestrator agents (intentionally not on other platforms)
KIRO_ONLY_AGENTS = {"line-cook"}


def discover_claude_code_assets(repo_root: Path) -> PlatformAssets:
    """Discover commands and agents from Claude Code plugin."""
    assets = PlatformAssets()

    # Commands: plugins/claude-code/commands/*.md
    commands_dir = repo_root / "plugins" / "claude-code" / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("*.md"):
            assets.commands.add(cmd_file.stem)

    # Agents: plugins/claude-code/agents/*.md
    agents_dir = repo_root / "plugins" / "claude-code" / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            assets.agents.add(agent_file.stem)

    return assets


def discover_opencode_assets(repo_root: Path) -> PlatformAssets:
    """Discover commands and agents from OpenCode plugin."""
    assets = PlatformAssets()

    # Commands: plugins/opencode/commands/line-*.md
    commands_dir = repo_root / "plugins" / "opencode" / "commands"
    if commands_dir.exists():
        for cmd_file in commands_dir.glob("line-*.md"):
            # Strip "line-" prefix to normalize
            cmd_name = cmd_file.stem.replace("line-", "")
            assets.commands.add(cmd_name)

    # Agents: plugins/opencode/agents/*.md (if they exist)
    agents_dir = repo_root / "plugins" / "opencode" / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.md"):
            assets.agents.add(agent_file.stem)

    return assets


def discover_kiro_assets(repo_root: Path) -> PlatformAssets:
    """Discover commands (steering files) and agents from Kiro plugin."""
    assets = PlatformAssets()

    # Kiro uses a different architecture:
    # - Main orchestration via line-cook.md (routes to template-synced prompts)
    # - Individual agent steering files (taster, sous-chef, maitre)
    # - Supporting files (beads, session)
    #
    # Kiro does NOT have 1:1 command parity - it uses agents for workflow phases
    # Skip agent steering files when counting commands
    agent_steering = {"taster", "sous-chef", "maitre"}
    orchestrator_steering = {"line-cook"}
    supporting_steering = {"beads", "session"}

    steering_dir = repo_root / "plugins" / "kiro" / "steering"
    if steering_dir.exists():
        for steering_file in steering_dir.glob("*.md"):
            name = steering_file.stem
            # Only count actual commands (not agents or internal steering)
            if name not in agent_steering and name not in orchestrator_steering and name not in supporting_steering:
                assets.commands.add(name)

    # Agents: plugins/kiro/agents/*.json
    agents_dir = repo_root / "plugins" / "kiro" / "agents"
    if agents_dir.exists():
        for agent_file in agents_dir.glob("*.json"):
            assets.agents.add(agent_file.stem)

    return assets


def check_command_parity(
    claude_code: PlatformAssets,
    opencode: PlatformAssets,
    kiro: PlatformAssets
) -> ParityResult:
    """Check that commands are consistent across platforms."""
    result = ParityResult()

    # Check core commands on Claude Code and OpenCode (Kiro uses different architecture)
    for cmd in CORE_COMMANDS:
        if cmd not in claude_code.commands:
            result.errors.append(f"Claude Code missing core command: {cmd}")
        if cmd not in opencode.commands:
            result.errors.append(f"OpenCode missing core command: {cmd}")

    # Kiro intentionally uses a different architecture:
    # - Workflow phases are handled by agents, not individual commands
    # - getting-started is the main command entry point
    # So we don't check Kiro for 1:1 command parity
    result.info.append(
        "Kiro uses agent-based architecture (intentionally different from command-based)"
    )

    # Check for unexpected commands
    all_expected = CORE_COMMANDS.union(
        PLATFORM_SPECIFIC_COMMANDS["claude-code"],
        PLATFORM_SPECIFIC_COMMANDS["opencode"]
    )

    for cmd in claude_code.commands:
        if cmd not in all_expected:
            result.info.append(f"Claude Code has additional command: {cmd}")

    for cmd in opencode.commands:
        if cmd not in all_expected:
            result.info.append(f"OpenCode has additional command: {cmd}")

    # Check platform-specific commands are correctly exclusive
    if "service" not in claude_code.commands:
        result.warnings.append("Claude Code missing platform-specific: service")
    if "work" not in opencode.commands:
        result.warnings.append("OpenCode missing platform-specific: work")

    # Check naming conventions
    result.info.append(f"Claude Code commands: {sorted(claude_code.commands)}")
    result.info.append(f"OpenCode commands: {sorted(opencode.commands)}")
    result.info.append(f"Kiro steering: {sorted(kiro.commands)}")

    return result


def check_agent_parity(
    claude_code: PlatformAssets,
    opencode: PlatformAssets,
    kiro: PlatformAssets
) -> ParityResult:
    """Check that agents are consistent across platforms."""
    result = ParityResult()

    # Check shared agents on Claude Code
    for agent in SHARED_AGENTS:
        if agent not in claude_code.agents:
            result.errors.append(f"Claude Code missing shared agent: {agent}")

    # Check shared agents on Kiro
    for agent in SHARED_AGENTS:
        if agent not in kiro.agents:
            result.errors.append(f"Kiro missing shared agent: {agent}")

    # OpenCode missing agents is a WARNING (SDK supports it, but not implemented)
    if not opencode.agents:
        result.warnings.append(
            "OpenCode has no agents defined (SDK supports agents, "
            "but plugins/opencode hasn't implemented them)"
        )
    else:
        for agent in SHARED_AGENTS:
            if agent not in opencode.agents:
                result.warnings.append(f"OpenCode missing shared agent: {agent}")

    # Check Kiro-only agents are present on Kiro
    for agent in KIRO_ONLY_AGENTS:
        if agent not in kiro.agents:
            result.warnings.append(f"Kiro missing orchestrator agent: {agent}")

    # Check Kiro-only agents are NOT on other platforms (this is correct)
    for agent in KIRO_ONLY_AGENTS:
        if agent in claude_code.agents:
            result.info.append(
                f"Kiro-only agent {agent} found on Claude Code (may be intentional)"
            )
        if agent in opencode.agents:
            result.info.append(
                f"Kiro-only agent {agent} found on OpenCode (may be intentional)"
            )

    result.info.append(f"Claude Code agents: {sorted(claude_code.agents)}")
    result.info.append(f"OpenCode agents: {sorted(opencode.agents)}")
    result.info.append(f"Kiro agents: {sorted(kiro.agents)}")

    return result


def format_human_report(
    command_result: Optional[ParityResult],
    agent_result: Optional[ParityResult]
) -> str:
    """Format results as human-readable report."""
    lines = ["# Platform Parity Report", ""]

    total_errors = 0
    total_warnings = 0

    if command_result:
        lines.append("## Commands")
        lines.append("")

        if command_result.errors:
            lines.append("### Errors")
            for err in command_result.errors:
                lines.append(f"  - {err}")
            lines.append("")
            total_errors += len(command_result.errors)

        if command_result.warnings:
            lines.append("### Warnings")
            for warn in command_result.warnings:
                lines.append(f"  - {warn}")
            lines.append("")
            total_warnings += len(command_result.warnings)

        if command_result.info:
            lines.append("### Info")
            for info in command_result.info:
                lines.append(f"  - {info}")
            lines.append("")

    if agent_result:
        lines.append("## Agents")
        lines.append("")

        if agent_result.errors:
            lines.append("### Errors")
            for err in agent_result.errors:
                lines.append(f"  - {err}")
            lines.append("")
            total_errors += len(agent_result.errors)

        if agent_result.warnings:
            lines.append("### Warnings")
            for warn in agent_result.warnings:
                lines.append(f"  - {warn}")
            lines.append("")
            total_warnings += len(agent_result.warnings)

        if agent_result.info:
            lines.append("### Info")
            for info in agent_result.info:
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
    command_result: Optional[ParityResult],
    agent_result: Optional[ParityResult]
) -> str:
    """Format results as JSON."""
    report = {
        "commands": None,
        "agents": None,
        "summary": {
            "errors": 0,
            "warnings": 0,
            "passed": True
        }
    }

    if command_result:
        report["commands"] = {
            "errors": command_result.errors,
            "warnings": command_result.warnings,
            "info": command_result.info
        }
        report["summary"]["errors"] += len(command_result.errors)
        report["summary"]["warnings"] += len(command_result.warnings)

    if agent_result:
        report["agents"] = {
            "errors": agent_result.errors,
            "warnings": agent_result.warnings,
            "info": agent_result.info
        }
        report["summary"]["errors"] += len(agent_result.errors)
        report["summary"]["warnings"] += len(agent_result.warnings)

    report["summary"]["passed"] = report["summary"]["errors"] == 0

    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check platform parity across Claude Code, OpenCode, and Kiro"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit with error code on warnings"
    )
    parser.add_argument(
        "--check", choices=["commands", "agents"],
        help="Only check specific category"
    )

    args = parser.parse_args()

    # Find repository root
    repo_root = Path(__file__).parent.parent

    # Discover assets from each platform
    claude_code = discover_claude_code_assets(repo_root)
    opencode = discover_opencode_assets(repo_root)
    kiro = discover_kiro_assets(repo_root)

    # Run checks
    command_result = None
    agent_result = None

    if args.check is None or args.check == "commands":
        command_result = check_command_parity(claude_code, opencode, kiro)

    if args.check is None or args.check == "agents":
        agent_result = check_agent_parity(claude_code, opencode, kiro)

    # Format output
    if args.json:
        print(format_json_report(command_result, agent_result))
    else:
        print(format_human_report(command_result, agent_result))

    # Determine exit code
    total_errors = 0
    total_warnings = 0

    if command_result:
        total_errors += len(command_result.errors)
        total_warnings += len(command_result.warnings)
    if agent_result:
        total_errors += len(agent_result.errors)
        total_warnings += len(agent_result.warnings)

    if total_errors > 0:
        sys.exit(1)
    elif args.strict and total_warnings > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
