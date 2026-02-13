#!/usr/bin/env python3
"""
metrics-collector.py - Static analysis metrics and code smell detection.

Runs validation scripts, collects file size metrics, detects code smells,
and reports tool availability.

Usage:
    python3 plugins/claude-code/scripts/metrics-collector.py              # Quick scope
    python3 plugins/claude-code/scripts/metrics-collector.py full         # Full analysis
    python3 plugins/claude-code/scripts/metrics-collector.py <path>       # Specific path
    python3 plugins/claude-code/scripts/metrics-collector.py --json       # JSON output

Exit codes:
    0: Success
    1: Script error
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from helpers import run_cmd


def tool_available(name):
    """Check if a command-line tool is available."""
    import shutil
    return shutil.which(name) is not None


def find_repo_root():
    """Find the git repository root."""
    rc, out, _ = run_cmd(["git", "rev-parse", "--show-toplevel"])
    if rc == 0 and out:
        return Path(out)
    return Path(".")


# --- Validation Scripts ---

def run_validation_scripts(repo_root):
    """Run dev/ validation scripts and collect results."""
    scripts = [
        "check-plugin-health.py",
        "check-platform-parity.py",
        "doctor-docs.py",
    ]

    results = []
    dev_dir = repo_root / "dev"

    for script_name in scripts:
        script_path = dev_dir / script_name
        if not script_path.exists():
            results.append({
                "name": script_name,
                "status": "not_found",
                "output": "",
            })
            continue

        rc, out, err = run_cmd(["python3", str(script_path)], timeout=60)
        raw_output = out or err
        is_truncated = len(raw_output) > 2000
        result_entry = {
            "name": script_name,
            "status": "passed" if rc == 0 else "failed",
            "output": raw_output[:2000],
        }
        if is_truncated:
            result_entry["truncated"] = True
        results.append(result_entry)

    return results


# --- File Analysis ---

def analyze_file_sizes(target_path):
    """Find files and flag large ones."""
    findings = []
    metrics = {"total_loc": 0, "file_count": 0}

    target = Path(target_path)

    # Walk source files, skip common non-source dirs
    skip_dirs = {
        ".git", "node_modules", "__pycache__", ".beads",
        "vendor", "dist", "build", ".venv", "venv",
    }

    extensions = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs",
        ".java", ".rb", ".sh", ".md", ".yaml", ".yml", ".toml",
    }

    for root, dirs, files in os.walk(str(target)):
        # Filter out skip dirs
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in extensions:
                continue

            try:
                content = fpath.read_text(errors="replace")
                loc = len(content.splitlines())
            except OSError:
                continue

            metrics["file_count"] += 1
            metrics["total_loc"] += loc

            if loc > 1000:
                findings.append({
                    "smell": "BLOATER",
                    "file": str(fpath),
                    "loc": loc,
                    "severity": "critical",
                    "message": "File has {} lines (>1000)".format(loc),
                })
            elif loc > 500:
                findings.append({
                    "smell": "BLOATER",
                    "file": str(fpath),
                    "loc": loc,
                    "severity": "high",
                    "message": "File has {} lines (>500)".format(loc),
                })
            elif loc < 20 and loc > 0 and fpath.suffix in (".py", ".ts", ".js") and fpath.name != "__init__.py":
                findings.append({
                    "smell": "LAZY_CLASS",
                    "file": str(fpath),
                    "loc": loc,
                    "severity": "low",
                    "message": "File has only {} lines (<20, potential lazy class)".format(loc),
                })

    return findings, metrics


def find_long_param_lists(target_path):
    """Find functions with >4 parameters."""
    findings = []
    target = Path(target_path)

    skip_dirs = {".git", "node_modules", "__pycache__", ".beads", "vendor"}

    for root, dirs, files in os.walk(str(target)):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix != ".py":
                continue

            try:
                content = fpath.read_text(errors="replace")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), 1):
                # Match def statements
                match = re.match(r"\s*def\s+\w+\s*\((.*)", line)
                if not match:
                    continue

                # Count params (rough: single-line only, exclude self/cls)
                param_str = match.group(1)
                if ")" in param_str:
                    param_str = param_str[:param_str.index(")")]

                params = [p.strip() for p in param_str.split(",") if p.strip()]
                params = [p for p in params if p not in ("self", "cls")]

                if len(params) > 4:
                    findings.append({
                        "smell": "LONG_PARAMS",
                        "file": "{}:{}".format(fpath, line_num),
                        "severity": "medium",
                        "message": "Function has {} parameters (>4)".format(len(params)),
                    })

    return findings


def find_message_chains(target_path):
    """Find deep method chains (4+ dots)."""
    findings = []
    target = Path(target_path)

    skip_dirs = {".git", "node_modules", "__pycache__", ".beads", "vendor"}

    for root, dirs, files in os.walk(str(target)):
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix != ".py":
                continue

            try:
                lines = fpath.read_text(errors="replace").splitlines()
            except OSError:
                continue

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments and docstrings
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Simple heuristic: count dots (may include false positives from strings)
                dot_count = stripped.count(".")
                if dot_count >= 4:
                    findings.append({
                        "smell": "MESSAGE_CHAIN",
                        "file": "{}:{}".format(fpath, line_num),
                        "severity": "low",
                        "message": "Possible message chain ({} dots)".format(dot_count),
                    })

    return findings


def analyze_git_churn(target_path):
    """Find files with highest change frequency (shotgun surgery candidates)."""
    findings = []
    rc, out, _ = run_cmd(
        ["git", "log", "--format=", "--name-only", "-50"],
        timeout=15,
    )
    if rc != 0 or not out:
        return findings

    # Count file occurrences in recent commits
    file_change_counts = {}
    for line in out.splitlines():
        filepath = line.strip()
        if filepath:
            file_change_counts[filepath] = file_change_counts.get(filepath, 0) + 1

    # Flag files changed frequently (15+ of last 50 commits)
    churn_threshold = 15
    for filepath, change_count in sorted(file_change_counts.items(), key=lambda x: -x[1]):
        if change_count >= churn_threshold:
            findings.append({
                "smell": "SHOTGUN_SURGERY",
                "file": filepath,
                "severity": "medium",
                "message": "Changed in {}/50 recent commits".format(change_count),
            })

    return findings


def analyze_import_coupling(target_path):
    """Analyze import frequency to find highly-coupled modules."""
    findings = []
    module_import_counts = {}
    target_root = Path(target_path)

    skip_dirs = {".git", "node_modules", "__pycache__", ".beads", "vendor", "venv", ".venv"}

    for root, dirs, files in os.walk(str(target_root)):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for filename in files:
            filepath = Path(root) / filename
            if filepath.suffix != ".py":
                continue
            try:
                for line in filepath.read_text(errors="replace").splitlines():
                    stripped = line.strip()
                    module_name = None

                    if stripped.startswith("from "):
                        parts = stripped.split()
                        module_name = parts[1] if len(parts) > 1 else None
                    elif stripped.startswith("import "):
                        parts = stripped.split()
                        module_name = parts[1].rstrip(",") if len(parts) > 1 else None

                    if module_name:
                        module_import_counts[module_name] = module_import_counts.get(module_name, 0) + 1
            except OSError:
                continue

    # Flag modules imported frequently (10+ times indicates high coupling)
    coupling_threshold = 10
    for module_name, import_count in sorted(module_import_counts.items(), key=lambda x: -x[1]):
        if import_count >= coupling_threshold:
            findings.append({
                "smell": "HIGH_COUPLING",
                "file": module_name,
                "severity": "medium",
                "message": "Imported {} times (high coupling)".format(import_count),
            })

    return findings


def analyze_co_changes(target_path):
    """Detect files frequently changed together (co-change patterns)."""
    findings = []
    rc, out, _ = run_cmd(
        ["git", "log", "--format=COMMIT", "--name-only", "-50"],
        timeout=15,
    )
    if rc != 0 or not out:
        return findings

    # Parse commits into groups of files
    commits = []
    current_commit = []
    for line in out.splitlines():
        if line == "COMMIT":
            if current_commit:
                commits.append(current_commit)
            current_commit = []
        elif line.strip():
            current_commit.append(line.strip())
    if current_commit:
        commits.append(current_commit)

    # Count file pairs changed together
    pair_counts = {}
    for files in commits:
        if len(files) < 2 or len(files) > 20:
            continue
        for i, file1 in enumerate(files):
            for file2 in files[i + 1:]:
                pair = tuple(sorted([file1, file2]))
                pair_counts[pair] = pair_counts.get(pair, 0) + 1

    # Flag pairs changed together 8+ times in last 50 commits
    for (file1, file2), count in sorted(pair_counts.items(), key=lambda x: -x[1]):
        if count >= 8:
            findings.append({
                "smell": "CO_CHANGE",
                "file": "{} <-> {}".format(file1, file2),
                "severity": "medium",
                "message": "Changed together in {}/50 recent commits".format(count),
            })

    return findings


def check_cli_specifics(repo_root):
    """CLI/plugin-specific checks: command file sizes, platform coupling."""
    findings = []

    # Check command file sizes
    for cmd_dir in repo_root.glob("**/commands"):
        if ".git" in str(cmd_dir) or "node_modules" in str(cmd_dir):
            continue
        for md_file in cmd_dir.glob("*.md"):
            try:
                line_count = len(md_file.read_text().splitlines())
                if line_count > 200:
                    findings.append({
                        "smell": "COMMAND_BLOAT",
                        "file": str(md_file),
                        "loc": line_count,
                        "severity": "medium",
                        "message": "Command file has {} lines (>200)".format(line_count),
                    })
            except OSError:
                continue

    # Check for platform coupling in shared scripts
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.is_dir():
        scripts_dir = repo_root / "plugins" / "claude-code" / "scripts"
    if scripts_dir.is_dir():
        for py_file in scripts_dir.glob("*.py"):
            try:
                content = py_file.read_text(errors="replace")
                for pattern in ("claude-code", "opencode", "kiro"):
                    if pattern in content.lower():
                        # Only flag if it's not in a comment
                        for line_num, line in enumerate(content.splitlines(), 1):
                            line_stripped = line.strip()
                            if pattern in line_stripped.lower() and not line_stripped.startswith("#"):
                                findings.append({
                                    "smell": "PLATFORM_COUPLING",
                                    "file": "{}:{}".format(py_file, line_num),
                                    "severity": "low",
                                    "message": "Platform-specific reference '{}' in shared script".format(pattern),
                                })
                                break
            except OSError:
                continue

    return findings


def count_adrs(repo_root):
    """Count ADRs and check for issues."""
    adr_dir = repo_root / "docs" / "decisions"
    if not adr_dir.is_dir():
        return 0, []

    adrs = list(adr_dir.glob("*.md"))
    findings = []

    # Check for superseded without replacement
    for adr in adrs:
        try:
            content = adr.read_text()
            if "superseded" in content.lower() and "superseded by" not in content.lower():
                findings.append({
                    "smell": "ADR_ORPHAN",
                    "file": str(adr),
                    "severity": "low",
                    "message": "ADR marked superseded without replacement reference",
                })
        except OSError:
            pass

    return len(adrs), findings


def _classify_complexity(avg_complexity):
    """Classify cyclomatic complexity into buckets."""
    if avg_complexity > 15:
        return "critical (>15)"
    elif avg_complexity > 10:
        return "warning (10-15)"
    elif avg_complexity > 7:
        return "refactor (8-10)"
    elif avg_complexity > 4:
        return "moderate (5-7)"
    else:
        return "good (1-4)"


def run_external_tools(target_path):
    """Run optional external analysis tools."""
    results = {}
    tools = {
        "radon": tool_available("radon"),
        "cloc": tool_available("cloc"),
        "pylint": tool_available("pylint"),
        "jscpd": tool_available("jscpd"),
    }

    results["tools_available"] = tools
    results["external"] = {}
    results["findings"] = []

    if tools["radon"]:
        rc, out, _ = run_cmd(
            ["radon", "cc", "-a", "-nc", str(target_path)], timeout=60
        )
        if rc == 0:
            # Parse average complexity from last line
            for line in reversed(out.splitlines()):
                match = re.search(r"Average complexity:\s+\w\s+\((\d+\.?\d*)\)", line)
                if match:
                    avg_complexity = float(match.group(1))
                    results["external"]["avg_complexity"] = avg_complexity
                    results["external"]["complexity_bucket"] = _classify_complexity(avg_complexity)
                    break

    if tools["cloc"]:
        rc, out, _ = run_cmd(
            ["cloc", "--quiet", "--json", str(target_path)], timeout=60
        )
        if rc == 0 and out:
            try:
                cloc_data = json.loads(out)
                results["external"]["cloc"] = cloc_data
            except (json.JSONDecodeError, TypeError):
                pass

    if tools["pylint"]:
        rc, out, _ = run_cmd(
            ["pylint", "--disable=all", "--enable=W0611",
             "--output-format=json", str(target_path)], timeout=60
        )
        if out:
            try:
                pylint_data = json.loads(out)
                if isinstance(pylint_data, list):
                    for item in pylint_data:
                        if isinstance(item, dict):
                            results["findings"].append({
                                "smell": "DEAD_IMPORT",
                                "file": "{}:{}".format(
                                    item.get("path", ""), item.get("line", "")
                                ),
                                "severity": "low",
                                "message": item.get("message", "Unused import"),
                            })
            except (json.JSONDecodeError, TypeError):
                pass

    if tools["jscpd"]:
        rc, out, _ = run_cmd(
            ["jscpd", "--threshold", "3", str(target_path),
             "--reporters", "json"], timeout=60
        )
        if out:
            try:
                jscpd_data = json.loads(out)
                dupes = jscpd_data.get("duplicates", [])
                if isinstance(dupes, list):
                    for dupe in dupes[:10]:
                        if isinstance(dupe, dict):
                            first = dupe.get("firstFile", {})
                            second = dupe.get("secondFile", {})
                            results["findings"].append({
                                "smell": "DUPLICATE_CODE",
                                "file": "{} <-> {}".format(
                                    first.get("name", "?"), second.get("name", "?")
                                ),
                                "severity": "medium",
                                "message": "Duplicate code block ({} lines)".format(
                                    dupe.get("lines", "?")
                                ),
                            })
                pct = jscpd_data.get("statistics", {}).get("total", {}).get("percentage")
                if pct is not None:
                    results["external"]["duplicate_pct"] = pct
            except (json.JSONDecodeError, TypeError):
                pass

    return results


# --- Output Formatting ---

def format_human(data):
    """Format as human-readable report."""
    lines = ["# Architecture Metrics Report", ""]
    lines.append("Scope: {}  |  Target: {}".format(
        data.get("scope", "?"), data.get("target_path", ".")
    ))
    lines.append("")

    # Validation scripts
    scripts = data.get("validation_scripts", [])
    if scripts:
        lines.append("## Validation Scripts")
        for script in scripts:
            icon = "PASS" if script["status"] == "passed" else "FAIL" if script["status"] == "failed" else "SKIP"
            lines.append("  [{}] {}".format(icon, script["name"]))
        lines.append("")

    # Metrics
    metrics = data.get("metrics", {})
    if metrics:
        lines.append("## Metrics")
        lines.append("  Total LOC: {}".format(metrics.get("total_loc", 0)))
        lines.append("  File count: {}".format(metrics.get("file_count", 0)))
        ext = data.get("external_tools", {}).get("external", {})
        if ext.get("avg_complexity"):
            bucket = ext.get("complexity_bucket", "")
            lines.append("  Avg complexity: {} ({})".format(
                ext["avg_complexity"], bucket
            ))
        if ext.get("duplicate_pct") is not None:
            lines.append("  Duplicate code: {}%".format(ext["duplicate_pct"]))
        lines.append("")

    # Findings by severity
    findings = data.get("findings", {})
    for severity in ("critical", "high", "medium", "low"):
        items = findings.get(severity, [])
        if not items:
            continue
        lines.append("## {} ({})".format(severity.upper(), len(items)))
        for finding in items:
            lines.append("  [{}] {} - {}".format(
                finding.get("smell", ""), finding.get("file", ""), finding.get("message", "")
            ))
        lines.append("")

    # Tool availability
    tools = data.get("external_tools", {}).get("tools_available", {})
    if tools:
        lines.append("## Tool Availability")
        for name, avail in sorted(tools.items()):
            lines.append("  {}: {}".format(name, "available" if avail else "not installed"))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Collect architecture metrics and detect code smells"
    )
    parser.add_argument(
        "scope", nargs="?", default="quick",
        help="Scope: quick (default), full, or a path"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Save report to docs/features/architecture-audit-YYYY-MM-DD.md"
    )

    args = parser.parse_args()

    repo_root = find_repo_root()

    # Determine target path
    if args.scope in ("quick", "full"):
        target_path = str(repo_root)
        scope = args.scope
    else:
        target_path = args.scope
        scope = "path"

    data = {
        "scope": scope,
        "target_path": target_path,
        "validation_scripts": [],
        "metrics": {},
        "findings": {"critical": [], "high": [], "medium": [], "low": []},
        "external_tools": {"tools_available": {}, "external": {}},
    }

    # Always run validation scripts
    data["validation_scripts"] = run_validation_scripts(repo_root)

    if scope in ("full", "path"):
        # File size analysis (includes lazy class detection)
        size_findings, file_metrics = analyze_file_sizes(target_path)
        data["metrics"] = file_metrics

        for finding in size_findings:
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # Long parameter lists
        for finding in find_long_param_lists(target_path):
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # Message chains
        for finding in find_message_chains(target_path):
            severity = finding.get("severity", "low")
            data["findings"].setdefault(severity, []).append(finding)

        # Import coupling analysis
        for finding in analyze_import_coupling(target_path):
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # Git churn
        for finding in analyze_git_churn(target_path):
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # Co-change patterns
        for finding in analyze_co_changes(target_path):
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # CLI/plugin-specific checks
        for finding in check_cli_specifics(repo_root):
            severity = finding.get("severity", "medium")
            data["findings"].setdefault(severity, []).append(finding)

        # ADR health
        adr_count, adr_findings = count_adrs(repo_root)
        data["metrics"]["adr_count"] = adr_count
        for finding in adr_findings:
            severity = finding.get("severity", "low")
            data["findings"].setdefault(severity, []).append(finding)

        # External tools (pylint, jscpd, radon, cloc)
        ext_results = run_external_tools(target_path)
        data["external_tools"] = ext_results

        # Merge external tool findings into main findings
        for finding in ext_results.get("findings", []):
            severity = finding.get("severity", "low")
            data["findings"].setdefault(severity, []).append(finding)

    output = None
    if args.json:
        output = json.dumps(data, indent=2)
        print(output)
    else:
        output = format_human(data)
        print(output)

    # Save report if requested
    if args.report and output:
        from datetime import date
        report_dir = repo_root / "docs" / "features"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "architecture-audit-{}.md".format(date.today().isoformat())
        report_path.write_text(output)
        print("\nReport saved to: {}".format(report_path))

    sys.exit(0)


if __name__ == "__main__":
    main()
