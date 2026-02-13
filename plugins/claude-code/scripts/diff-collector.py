#!/usr/bin/env python3
"""
diff-collector.py - Gather review context for serve phase.

Identifies the target bead, collects git diffs (unstaged, staged,
last commit) with truncation to prevent context window blowout.

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
import sys

from helpers import run_cmd

MAX_DIFF_LINES = 200


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
    closed_bead = _find_first_bead_by_status("closed")
    if closed_bead:
        return closed_bead

    # Fall back to in-progress
    return _find_first_bead_by_status("in_progress")


def _find_first_bead_by_status(status):
    """Find first bead with given status, returning normalized dict or None.

    For closed status, sorts by most recently updated to pick the right bead
    in multi-task sessions.
    """
    cmd = ["bd", "list", "--status={}".format(status), "--json"]
    if status == "closed":
        cmd.extend(["--sort=updated", "--reverse", "--limit=5"])
    rc, out, _ = run_cmd(cmd, timeout=15)
    if rc != 0 or not out:
        return None
    try:
        data = json.loads(out)
        if isinstance(data, list) and data:
            first_item = data[0] if isinstance(data[0], dict) else None
            if first_item and _validate_bead_id(first_item.get("id", "")):
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


def _truncate_diff(diff_text):
    """Truncate diff to MAX_DIFF_LINES. Returns (text, was_truncated)."""
    if not diff_text:
        return "", False
    lines = diff_text.splitlines()
    if len(lines) <= MAX_DIFF_LINES:
        return diff_text, False
    truncated = "\n".join(lines[:MAX_DIFF_LINES])
    truncated += "\n... [{} lines truncated]".format(len(lines) - MAX_DIFF_LINES)
    return truncated, True


def collect_changes():
    """Collect git diff information with truncation."""
    changes = {
        "unstaged": "",
        "unstaged_truncated": False,
        "staged": "",
        "staged_truncated": False,
        "last_commit": "",
        "last_commit_truncated": False,
        "files": [],
    }

    # Unstaged diff
    rc, out, _ = run_cmd(["git", "diff"], timeout=30)
    if rc == 0:
        changes["unstaged"], changes["unstaged_truncated"] = _truncate_diff(out)

    # Staged diff
    rc, out, _ = run_cmd(["git", "diff", "--cached"], timeout=30)
    if rc == 0:
        changes["staged"], changes["staged_truncated"] = _truncate_diff(out)

    # Last commit diff (skip if repo has no prior commit)
    rc, _, _ = run_cmd(["git", "rev-parse", "HEAD~1"])
    if rc == 0:
        rc, out, _ = run_cmd(["git", "diff", "HEAD~1"], timeout=30)
        if rc == 0:
            changes["last_commit"], changes["last_commit_truncated"] = _truncate_diff(out)

    # File status list
    rc, out, _ = run_cmd(["git", "status", "--porcelain"])
    if rc == 0 and out:
        for line in out.splitlines():
            if len(line) >= 4:  # porcelain: "XY path" (renames show "XY old -> new")
                status = line[:2].strip()
                path = line[3:]
                changes["files"].append({"path": path, "status": status})

    return changes


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
    lines.append("  Unstaged: {} lines{}".format(
        unstaged_lines, " (TRUNCATED)" if changes.get("unstaged_truncated") else ""
    ))
    lines.append("  Staged: {} lines{}".format(
        staged_lines, " (TRUNCATED)" if changes.get("staged_truncated") else ""
    ))
    lines.append("  Last commit: {} lines{}".format(
        commit_lines, " (TRUNCATED)" if changes.get("last_commit_truncated") else ""
    ))
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

    data = {
        "bead": bead,
        "changes": changes,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
