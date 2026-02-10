#!/usr/bin/env python3
"""
diff-collector.py - Gather review context for serve phase.

Identifies the target bead, collects git diffs (unstaged, staged,
last commit), and reads project context.

Usage:
    python3 plugins/claude-code/scripts/diff-collector.py               # Auto-detect bead
    python3 plugins/claude-code/scripts/diff-collector.py <bead-id>     # Specific bead
    python3 plugins/claude-code/scripts/diff-collector.py --json        # JSON output

Exit codes:
    0: Success
    1: Script error
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run_cmd(args, timeout=15):
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


def _validate_bead_id(bid):
    """Validate bead ID format to prevent malformed input in subprocess calls."""
    return bool(bid and re.match(r'^[a-zA-Z0-9._-]+$', bid))


def find_target_bead(explicit_id=None):
    """Find the bead to review. Checks explicit, then recent closed, then in_progress."""
    if explicit_id:
        if not _validate_bead_id(explicit_id):
            return None
        return _get_bead_detail(explicit_id)

    # Try recently closed first (matches template: serve reviews completed work)
    rc, out, _ = run_cmd(["bd", "list", "--status=closed", "--json"], timeout=15)
    if rc == 0 and out:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                first_item = data[0] if isinstance(data[0], dict) else None
                if first_item:
                    return _normalize_bead(first_item)
        except (json.JSONDecodeError, TypeError):
            pass

    # Fall back to in-progress
    rc, out, _ = run_cmd(["bd", "list", "--status=in_progress", "--json"], timeout=15)
    if rc == 0 and out:
        try:
            data = json.loads(out)
            if isinstance(data, list) and data:
                first_item = data[0] if isinstance(data[0], dict) else None
                if first_item:
                    return _normalize_bead(first_item)
        except (json.JSONDecodeError, TypeError):
            pass

    return None


def _get_bead_detail(bead_id):
    """Fetch full bead details via bd show --json."""
    rc, out, _ = run_cmd(["bd", "show", bead_id, "--json"], timeout=15)
    if rc != 0 or not out:
        return None
    try:
        data = json.loads(out)
        if isinstance(data, list) and len(data) == 1:
            data = data[0]
        if isinstance(data, dict):
            return _normalize_bead(data)
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _normalize_bead(bead):
    """Extract standard fields from a bead dict."""
    return {
        "id": bead.get("id", ""),
        "title": bead.get("title", ""),
        "type": bead.get("type") or bead.get("issue_type", ""),
        "status": bead.get("status", ""),
        "priority": bead.get("priority"),
        "description": bead.get("description", ""),
    }


def collect_changes():
    """Collect git diff information."""
    changes = {
        "unstaged": "",
        "staged": "",
        "last_commit": "",
        "files": [],
    }

    # Unstaged diff
    rc, out, _ = run_cmd(["git", "diff"], timeout=30)
    if rc == 0:
        changes["unstaged"] = out

    # Staged diff
    rc, out, _ = run_cmd(["git", "diff", "--cached"], timeout=30)
    if rc == 0:
        changes["staged"] = out

    # Last commit diff (skip if repo has no prior commit)
    rc, _, _ = run_cmd(["git", "rev-parse", "HEAD~1"])
    if rc == 0:
        rc, out, _ = run_cmd(["git", "diff", "HEAD~1"], timeout=30)
        if rc == 0:
            changes["last_commit"] = out

    # File status list
    rc, out, _ = run_cmd(["git", "status", "--porcelain"])
    if rc == 0 and out:
        for line in out.splitlines():
            if len(line) >= 4:  # porcelain format: XY<space>path (min 4 chars)
                status = line[:2].strip()
                path = line[3:]
                changes["files"].append({"path": path, "status": status})

    return changes


def get_project_context():
    """Read first 50 lines of CLAUDE.md for project context."""
    claude_md = Path("CLAUDE.md")
    if not claude_md.exists():
        return None
    try:
        lines = claude_md.read_text().splitlines()[:50]
        return "\n".join(lines)
    except OSError:
        return None


def format_human(data):
    """Format result as human-readable text."""
    lines = ["# Diff Collection for Serve", ""]

    bead = data.get("bead")
    if bead:
        lines.append("## Target Bead")
        lines.append("  ID: {}".format(bead.get("id", "")))
        lines.append("  Title: {}".format(bead.get("title", "")))
        lines.append("  Type: {}".format(bead.get("type", "")))
        lines.append("")
    else:
        lines.append("## Target Bead")
        lines.append("  No bead identified")
        lines.append("")

    changes = data.get("changes", {})
    files = changes.get("files", [])
    lines.append("## Changed Files ({})".format(len(files)))
    for file_info in files:
        lines.append("  {} {}".format(file_info.get("status", "?"), file_info.get("path", "")))
    lines.append("")

    # Show diff summary (not full content in human mode)
    unstaged_lines = len(changes.get("unstaged", "").splitlines())
    staged_lines = len(changes.get("staged", "").splitlines())
    commit_lines = len(changes.get("last_commit", "").splitlines())
    lines.append("## Diff Summary")
    lines.append("  Unstaged: {} lines".format(unstaged_lines))
    lines.append("  Staged: {} lines".format(staged_lines))
    lines.append("  Last commit: {} lines".format(commit_lines))
    lines.append("")

    if data.get("project_context"):
        lines.append("## Project Context")
        lines.append("  (First 50 lines of CLAUDE.md loaded)")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Gather review context for serve phase"
    )
    parser.add_argument(
        "bead_id", nargs="?", default=None,
        help="Bead ID to review (auto-detected if omitted)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )

    args = parser.parse_args()

    bead = find_target_bead(args.bead_id)
    changes = collect_changes()
    project_context = get_project_context()

    data = {
        "bead": bead,
        "changes": changes,
        "project_context": project_context,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
