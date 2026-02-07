#!/usr/bin/env python3
"""
doctor-docs.py - Validate documentation quality and currency.

Usage:
    ./dev/doctor-docs.py                    # Markdown report
    ./dev/doctor-docs.py --json             # JSON output
    ./dev/doctor-docs.py --check-external   # Validate external URLs
    ./dev/doctor-docs.py --category links   # Links only
    ./dev/doctor-docs.py --fix              # Auto-fix simple issues (future)

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
import urllib.request
import urllib.error


@dataclass
class DocResult:
    """Result of a documentation check."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


# Required frontmatter fields for commands
COMMAND_REQUIRED_FIELDS = {"description", "allowed-tools"}

# Required frontmatter fields for agents
AGENT_REQUIRED_FIELDS = {"name", "description", "tools", "model"}

# Required sections in README.md
README_REQUIRED_SECTIONS = {"getting started", "installation", "usage"}

# Required sections in AGENTS.md
AGENTS_REQUIRED_SECTIONS = {"agents", "taster", "sous-chef", "maitre"}


def extract_frontmatter(content: str) -> Optional[dict[str, str]]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None

    # Find the closing ---
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None

    frontmatter = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()

    return frontmatter


def extract_markdown_links(content: str) -> list[tuple[str, str]]:
    """Extract markdown links as (text, url) tuples."""
    # Match [text](url) patterns
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    return re.findall(pattern, content)


def extract_markdown_headings(content: str) -> list[str]:
    """Extract markdown headings (all levels)."""
    pattern = r"^#{1,6}\s+(.+)$"
    return [m.lower().strip() for m in re.findall(pattern, content, re.MULTILINE)]


def check_internal_links(repo_root: Path) -> DocResult:
    """Check that internal markdown links are valid."""
    result = DocResult()

    # Find all markdown files
    md_files = list(repo_root.glob("**/*.md"))

    # Exclude node_modules, .git, etc.
    md_files = [f for f in md_files if ".git" not in str(f) and "node_modules" not in str(f)]

    for md_file in md_files:
        try:
            content = md_file.read_text()
        except Exception as e:
            result.warnings.append(f"Could not read {md_file}: {e}")
            continue

        links = extract_markdown_links(content)

        for text, url in links:
            # Skip external links
            if url.startswith(("http://", "https://", "mailto:")):
                continue

            # Skip anchor-only links
            if url.startswith("#"):
                continue

            # Handle relative paths
            if url.startswith("./"):
                target = md_file.parent / url[2:]
            elif url.startswith("../"):
                target = md_file.parent / url
            else:
                target = md_file.parent / url

            # Remove anchor from path
            target_path = str(target).split("#")[0]
            target = Path(target_path)

            # Check if target exists
            if not target.exists():
                result.errors.append(
                    f"Broken link in {md_file.relative_to(repo_root)}: [{text}]({url})"
                )

    result.info.append(f"Checked {len(md_files)} markdown files for internal links")

    return result


def check_command_frontmatter(repo_root: Path) -> DocResult:
    """Check that command files have required frontmatter."""
    result = DocResult()

    commands_dir = repo_root / "plugins" / "claude-code" / "commands"
    if not commands_dir.exists():
        result.warnings.append("Commands directory not found")
        return result

    for cmd_file in commands_dir.glob("*.md"):
        try:
            content = cmd_file.read_text()
        except Exception as e:
            result.warnings.append(f"Could not read {cmd_file}: {e}")
            continue

        frontmatter = extract_frontmatter(content)

        if frontmatter is None:
            result.errors.append(f"Command {cmd_file.name} has no frontmatter")
            continue

        missing = COMMAND_REQUIRED_FIELDS - set(frontmatter.keys())
        if missing:
            result.errors.append(
                f"Command {cmd_file.name} missing required fields: {missing}"
            )
        else:
            result.info.append(f"Command {cmd_file.name} has valid frontmatter")

    return result


def check_agent_frontmatter(repo_root: Path) -> DocResult:
    """Check that agent files have required frontmatter."""
    result = DocResult()

    agents_dir = repo_root / "plugins" / "claude-code" / "agents"
    if not agents_dir.exists():
        result.warnings.append("Agents directory not found")
        return result

    for agent_file in agents_dir.glob("*.md"):
        try:
            content = agent_file.read_text()
        except Exception as e:
            result.warnings.append(f"Could not read {agent_file}: {e}")
            continue

        frontmatter = extract_frontmatter(content)

        if frontmatter is None:
            result.errors.append(f"Agent {agent_file.name} has no frontmatter")
            continue

        missing = AGENT_REQUIRED_FIELDS - set(frontmatter.keys())
        if missing:
            result.errors.append(
                f"Agent {agent_file.name} missing required fields: {missing}"
            )
        else:
            # Check that name matches filename
            if frontmatter.get("name") != agent_file.stem:
                result.warnings.append(
                    f"Agent {agent_file.name}: name '{frontmatter.get('name')}' "
                    f"doesn't match filename '{agent_file.stem}'"
                )
            result.info.append(f"Agent {agent_file.name} has valid frontmatter")

    return result


def check_changelog_format(repo_root: Path) -> DocResult:
    """Check that CHANGELOG.md follows Keep a Changelog format."""
    result = DocResult()

    changelog_path = repo_root / "CHANGELOG.md"
    if not changelog_path.exists():
        result.errors.append("CHANGELOG.md not found")
        return result

    try:
        content = changelog_path.read_text()
    except Exception as e:
        result.errors.append(f"Could not read CHANGELOG.md: {e}")
        return result

    # Check for Keep a Changelog reference
    if "keepachangelog.com" not in content.lower():
        result.warnings.append(
            "CHANGELOG.md should reference Keep a Changelog format"
        )

    # Check for [Unreleased] section
    if "[Unreleased]" not in content:
        result.warnings.append("CHANGELOG.md should have an [Unreleased] section")

    # Check for version entries
    version_pattern = r"^## \[(\d+\.\d+\.\d+)\]"
    versions = re.findall(version_pattern, content, re.MULTILINE)

    if not versions:
        result.warnings.append("CHANGELOG.md has no version entries")
    else:
        result.info.append(f"CHANGELOG.md has {len(versions)} version entries: {versions[:5]}")

    # Check for section headers (Added, Changed, etc.)
    section_headers = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
    found_sections = set()
    for section in section_headers:
        if f"### {section}" in content:
            found_sections.add(section)

    result.info.append(f"CHANGELOG uses sections: {found_sections}")

    # Check for link definitions at bottom
    if "[Unreleased]:" not in content:
        result.warnings.append(
            "CHANGELOG.md should have link definitions at bottom (Keep a Changelog format)"
        )

    return result


def check_required_sections(repo_root: Path) -> DocResult:
    """Check that key docs have required sections."""
    result = DocResult()

    # Check README.md
    readme_path = repo_root / "README.md"
    if readme_path.exists():
        try:
            content = readme_path.read_text()
            headings = extract_markdown_headings(content)

            missing = []
            for section in README_REQUIRED_SECTIONS:
                if not any(section in h for h in headings):
                    missing.append(section)

            if missing:
                result.warnings.append(
                    f"README.md may be missing sections: {missing}"
                )
            else:
                result.info.append("README.md has expected sections")
        except Exception as e:
            result.warnings.append(f"Could not read README.md: {e}")
    else:
        result.errors.append("README.md not found")

    # Check AGENTS.md
    agents_doc_path = repo_root / "AGENTS.md"
    if agents_doc_path.exists():
        try:
            content = agents_doc_path.read_text()
            headings = extract_markdown_headings(content)

            missing = []
            for section in AGENTS_REQUIRED_SECTIONS:
                if not any(section in h for h in headings):
                    missing.append(section)

            if missing:
                result.warnings.append(
                    f"AGENTS.md may be missing sections: {missing}"
                )
            else:
                result.info.append("AGENTS.md has expected sections")
        except Exception as e:
            result.warnings.append(f"Could not read AGENTS.md: {e}")
    else:
        result.warnings.append("AGENTS.md not found")

    return result


def check_entity_existence(repo_root: Path) -> DocResult:
    """Check that commands/agents mentioned in docs actually exist."""
    result = DocResult()

    # Get actual commands
    actual_commands = set()
    commands_dir = repo_root / "plugins" / "claude-code" / "commands"
    if commands_dir.exists():
        actual_commands = {f.stem for f in commands_dir.glob("*.md")}

    # Get actual agents
    actual_agents = set()
    agents_dir = repo_root / "plugins" / "claude-code" / "agents"
    if agents_dir.exists():
        actual_agents = {f.stem for f in agents_dir.glob("*.md")}

    # Check README.md for referenced commands/agents
    readme_path = repo_root / "README.md"
    if readme_path.exists():
        try:
            content = readme_path.read_text()

            # Look for /line:xxx patterns
            command_refs = re.findall(r"/line:([\w-]+)", content)
            for cmd in command_refs:
                if cmd not in actual_commands and cmd not in {"*", "command"}:
                    result.warnings.append(
                        f"README.md references command '{cmd}' which may not exist"
                    )
        except Exception:
            pass

    result.info.append(f"Actual commands: {sorted(actual_commands)}")
    result.info.append(f"Actual agents: {sorted(actual_agents)}")

    return result


def check_external_links(repo_root: Path) -> DocResult:
    """Check that external links are reachable (optional, slow)."""
    result = DocResult()

    # Find all markdown files
    md_files = list(repo_root.glob("**/*.md"))
    md_files = [f for f in md_files if ".git" not in str(f) and "node_modules" not in str(f)]

    checked_urls = set()
    broken_urls = []

    for md_file in md_files:
        try:
            content = md_file.read_text()
        except Exception:
            continue

        links = extract_markdown_links(content)

        for text, url in links:
            # Only check external links
            if not url.startswith(("http://", "https://")):
                continue

            # Skip already checked URLs
            if url in checked_urls:
                continue
            checked_urls.add(url)

            # Try to fetch the URL
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "line-cook-doc-checker/1.0"}
                )
                urllib.request.urlopen(req, timeout=5)
            except urllib.error.HTTPError as e:
                if e.code >= 400:
                    broken_urls.append((url, f"HTTP {e.code}"))
            except urllib.error.URLError as e:
                broken_urls.append((url, str(e.reason)))
            except Exception as e:
                broken_urls.append((url, str(e)))

    for url, reason in broken_urls:
        result.warnings.append(f"External link may be broken: {url} ({reason})")

    result.info.append(f"Checked {len(checked_urls)} external URLs")

    return result


def format_human_report(results: dict[str, DocResult]) -> str:
    """Format results as human-readable report."""
    lines = ["# Documentation Health Report", ""]

    total_errors = 0
    total_warnings = 0

    for category, result in results.items():
        lines.append(f"## {category.replace('_', ' ').title()}")
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


def format_json_report(results: dict[str, DocResult]) -> str:
    """Format results as JSON."""
    report = {
        "categories": {},
        "summary": {
            "errors": 0,
            "warnings": 0,
            "passed": True
        }
    }

    for category, result in results.items():
        report["categories"][category] = {
            "errors": result.errors,
            "warnings": result.warnings,
            "info": result.info
        }
        report["summary"]["errors"] += len(result.errors)
        report["summary"]["warnings"] += len(result.warnings)

    report["summary"]["passed"] = report["summary"]["errors"] == 0
    report["overall"] = "pass" if report["summary"]["passed"] else "fail"

    return json.dumps(report, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Validate documentation quality and currency"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--check-external", action="store_true",
        help="Check external URLs (slow)"
    )
    parser.add_argument(
        "--category", choices=[
            "links", "frontmatter", "changelog", "sections", "entities", "external"
        ],
        help="Only check specific category"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-fix simple issues (not yet implemented)"
    )

    args = parser.parse_args()

    if args.fix:
        print("Warning: --fix is not yet implemented", file=sys.stderr)

    # Find repository root
    repo_root = Path(__file__).parent.parent

    results = {}

    # Run checks based on category filter
    if args.category is None or args.category == "links":
        results["internal_links"] = check_internal_links(repo_root)

    if args.category is None or args.category == "frontmatter":
        results["command_frontmatter"] = check_command_frontmatter(repo_root)
        results["agent_frontmatter"] = check_agent_frontmatter(repo_root)

    if args.category is None or args.category == "changelog":
        results["changelog_format"] = check_changelog_format(repo_root)

    if args.category is None or args.category == "sections":
        results["required_sections"] = check_required_sections(repo_root)

    if args.category is None or args.category == "entities":
        results["entity_existence"] = check_entity_existence(repo_root)

    if args.check_external or args.category == "external":
        results["external_links"] = check_external_links(repo_root)

    # Format output
    if args.json:
        print(format_json_report(results))
    else:
        print(format_human_report(results))

    # Determine exit code
    total_errors = sum(len(r.errors) for r in results.values())

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
