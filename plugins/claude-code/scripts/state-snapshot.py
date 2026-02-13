#!/usr/bin/env python3
"""
state-snapshot.py - Full state collection for the prep phase.

Replaces the inline "Collect State" block in prep: sync, roster gathering,
hierarchy walk, and branch recommendation.

Usage:
    python3 plugins/claude-code/scripts/state-snapshot.py              # Human output
    python3 plugins/claude-code/scripts/state-snapshot.py --json       # JSON output
    python3 plugins/claude-code/scripts/state-snapshot.py --sync       # Force sync
    python3 plugins/claude-code/scripts/state-snapshot.py --no-sync    # Skip sync

Exit codes:
    0: Success
    1: Script error
"""

import argparse
import json
import os
import re
import subprocess
import sys


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


def run_bd_json(args, timeout=15):
    """Run a bd command with --json and parse the result.

    Unwraps single-item list responses to dict. Returns None on error.
    """
    full_args = ["bd"] + args + ["--json"]
    rc, out, err = run_cmd(full_args, timeout=timeout)
    if rc != 0 or not out:
        return None
    try:
        data = json.loads(out)
        # bd sometimes returns a single-item list
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return data
    except (json.JSONDecodeError, TypeError):
        return None


def _validate_bead_id(bid):
    """Validate bead ID format to prevent malformed input in subprocess calls."""
    return bool(bid and re.match(r'^[a-zA-Z0-9._-]+$', bid))


def do_sync():
    """Sync git and beads, return status dict."""
    result = {"git": "skipped", "beads": "skipped"}

    # Git sync
    rc, _, _ = run_cmd(["git", "fetch", "origin"], timeout=30)
    if rc != 0:
        result["git"] = "fetch failed"
    else:
        rc_pull, _, _ = run_cmd(["git", "pull", "--rebase"], timeout=30)
        result["git"] = "ok" if rc_pull == 0 else "pull failed"

    # Beads sync
    rc, _, _ = run_cmd(["bd", "sync"], timeout=30)
    result["beads"] = "ok" if rc == 0 else "failed"

    return result


def get_project_info():
    """Get basic project info."""
    info = {"dir": os.getcwd(), "branch": None}
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    if rc == 0:
        info["branch"] = out or "(detached HEAD)"
    return info


def get_roster():
    """Gather ready, in_progress, and blocked items."""
    return {
        "ready": _fetch_bead_list(["bd", "ready", "--json"]),
        "in_progress": _fetch_bead_list(["bd", "list", "--status=in_progress", "--json"]),
        "blocked": _fetch_bead_list(["bd", "blocked", "--json"]),
    }


def _fetch_bead_list(cmd_args):
    """Fetch and parse a bead list command, returning summarized beads."""
    rc, out, _ = run_cmd(cmd_args, timeout=15)
    if rc != 0 or not out:
        return []
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return [_summarize_bead(b) for b in data]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _summarize_bead(bead):
    """Extract summary fields from a bead dict."""
    if not isinstance(bead, dict):
        return {"id": str(bead)}
    return {
        "id": bead.get("id", ""),
        "title": bead.get("title", ""),
        "priority": bead.get("priority"),
        "type": bead.get("type") or bead.get("issue_type", ""),
    }


def suggest_next_task(roster):
    """Suggest highest priority ready item. Drills into epics transparently.

    Returns dict with 'suggestion' (task detail or None) and 'drill_path'
    (list of IDs showing the drill-down reasoning).
    """
    ready = roster.get("ready", [])
    if not ready:
        return {"suggestion": None, "drill_path": []}

    # Build blocked IDs set to avoid suggesting blocked tasks during drill-down
    blocked_ids = {
        b.get("id", "") for b in roster.get("blocked", [])
        if isinstance(b, dict)
    }

    candidate = ready[0]
    candidate_id = candidate.get("id", "")
    if not _validate_bead_id(candidate_id):
        return {"suggestion": None, "drill_path": []}

    detail = run_bd_json(["show", candidate_id])
    if not detail or not isinstance(detail, dict):
        suggestion = _extract_task_detail(candidate) if isinstance(candidate, dict) else None
        return {"suggestion": suggestion, "drill_path": [candidate_id]}

    bead_type = detail.get("type") or detail.get("issue_type", "")
    if bead_type == "epic":
        return _drill_epic_transparent(candidate_id, [candidate_id], blocked_ids=blocked_ids)

    return {"suggestion": _extract_task_detail(detail), "drill_path": [candidate_id]}


def _drill_epic_transparent(epic_id, drill_path, depth=0, blocked_ids=None):
    """Find first ready child of an epic, recording the drill path.

    Returns dict with 'suggestion' and 'drill_path'. When no ready children
    are found, returns None suggestion with drill_path showing what was checked.
    Skips children whose ID is in blocked_ids (already fetched from roster).
    """
    if depth >= 5:
        return {"suggestion": None, "drill_path": drill_path}

    if blocked_ids is None:
        blocked_ids = set()

    # Intentionally omit --all: we only want non-closed children for drill-down
    rc, out, _ = run_cmd(["bd", "list", "--parent=" + epic_id, "--json"], timeout=15)
    if rc != 0 or not out:
        return {"suggestion": None, "drill_path": drill_path}

    try:
        children = json.loads(out)
        if not isinstance(children, list):
            return {"suggestion": None, "drill_path": drill_path}
    except (json.JSONDecodeError, TypeError):
        return {"suggestion": None, "drill_path": drill_path}

    # Find first open/ready child, skipping blocked tasks
    for child in children:
        if not isinstance(child, dict):
            continue
        child_id = child.get("id", "")
        if child_id in blocked_ids:
            continue
        status = child.get("status", "")
        if status in ("open", "ready"):
            drill_path.append(child_id)
            child_type = child.get("type") or child.get("issue_type", "")
            if child_type in ("epic", "feature"):
                return _drill_epic_transparent(child_id, drill_path, depth + 1, blocked_ids=blocked_ids)
            return {"suggestion": _extract_task_detail(child), "drill_path": drill_path}

    return {"suggestion": None, "drill_path": drill_path}


def _extract_task_detail(detail):
    """Extract task detail from a bd show response."""
    if not isinstance(detail, dict):
        return None

    description = detail.get("description", "")

    # First paragraph as summary
    paragraphs = description.split("\n\n")
    summary = paragraphs[0].strip() if paragraphs else ""

    # Extract deliverables (lines starting with "- " after "Deliverable" heading)
    deliverables = []
    in_deliverables = False
    for line in description.splitlines():
        line_lower = line.lower().strip()
        if "deliverable" in line_lower and (":" in line_lower or line_lower.startswith("#")):
            in_deliverables = True
            continue
        if in_deliverables:
            stripped = line.strip()
            if stripped.startswith("- "):
                deliverables.append(stripped[2:])
            elif stripped and not stripped.startswith("-"):
                in_deliverables = False

    return {
        "id": detail.get("id", ""),
        "title": detail.get("title", ""),
        "priority": detail.get("priority"),
        "description_summary": summary[:500],
        "deliverables": deliverables,
    }


_parent_children_cache = {}


def _get_children(parent_id):
    """Fetch children of a parent, with caching to avoid duplicate subprocess calls."""
    if parent_id in _parent_children_cache:
        return _parent_children_cache[parent_id]

    if not _validate_bead_id(parent_id):
        _parent_children_cache[parent_id] = None
        return None

    rc, out, _ = run_cmd(["bd", "list", "--parent=" + parent_id, "--all", "--json"], timeout=15)
    if rc != 0 or not out:
        _parent_children_cache[parent_id] = None
        return None

    try:
        children = json.loads(out)
        if not isinstance(children, list):
            _parent_children_cache[parent_id] = None
            return None
        _parent_children_cache[parent_id] = children
        return children
    except (json.JSONDecodeError, TypeError):
        _parent_children_cache[parent_id] = None
        return None


def build_hierarchy(task_id):
    """Walk parent chain to build epic→feature→task hierarchy."""
    hierarchy = {"epic": None, "feature": None, "completed_siblings": []}

    if not _validate_bead_id(task_id):
        return hierarchy
    detail = run_bd_json(["show", task_id])
    if not detail or not isinstance(detail, dict):
        return hierarchy

    parent_id = detail.get("parent")
    if not parent_id or not _validate_bead_id(parent_id):
        return hierarchy

    # Parent = feature (usually)
    parent = run_bd_json(["show", parent_id])
    if parent and isinstance(parent, dict):
        parent_type = parent.get("type") or parent.get("issue_type", "")

        if parent_type == "feature":
            hierarchy["feature"] = {
                "id": parent.get("id", ""),
                "title": parent.get("title", ""),
                "goal": _extract_goal(parent),
                "progress": _calc_progress(parent_id),
            }

            # Walk up to epic
            grandparent_id = parent.get("parent")
            if grandparent_id:
                grandparent = run_bd_json(["show", grandparent_id])
                if grandparent and isinstance(grandparent, dict):
                    hierarchy["epic"] = {
                        "id": grandparent.get("id", ""),
                        "title": grandparent.get("title", ""),
                        "goal": _extract_goal(grandparent),
                        "progress": _calc_progress(grandparent_id),
                    }

        elif parent_type == "epic":
            hierarchy["epic"] = {
                "id": parent.get("id", ""),
                "title": parent.get("title", ""),
                "goal": _extract_goal(parent),
                "progress": _calc_progress(parent_id),
            }

        # Find completed siblings (uses cached data from _calc_progress)
        siblings = _get_children(parent_id)
        if siblings:
            hierarchy["completed_siblings"] = [
                {"id": s.get("id", ""), "title": s.get("title", "")}
                for s in siblings
                if isinstance(s, dict) and s.get("status") == "closed"
            ]

    return hierarchy


def _extract_goal(bead):
    """Extract goal text (first line of description, max 200 chars)."""
    description = bead.get("description", "").strip()
    if not description:
        return None
    first_line = description.split("\n")[0].strip()
    if not first_line:
        return None
    return first_line[:200]


def _calc_progress(parent_id):
    """Calculate child progress as 'closed/total' string."""
    children = _get_children(parent_id)
    if children is None:
        return None
    total = len(children)
    closed = sum(
        1 for c in children
        if isinstance(c, dict) and c.get("status") == "closed"
    )
    return "{}/{}".format(closed, total)


def get_branch_recommendation(hierarchy, current_branch):
    """Determine expected branch based on hierarchy.

    Returns deterministic data: expected branch name, current branch,
    and whether the expected branch exists. Agent decides what action to take.
    """
    epic = hierarchy.get("epic")
    feature = hierarchy.get("feature")

    if not epic and not feature:
        return {
            "expected": current_branch or "main",
            "current": current_branch,
            "branch_exists": True,
        }

    if epic:
        expected = "epic/{}".format(epic.get("id", ""))
    else:
        expected = "feature/{}".format(feature.get("id", ""))

    rc, out, _ = run_cmd(["git", "branch", "--list", expected])
    branch_exists = rc == 0 and bool(out.strip())

    return {
        "expected": expected,
        "current": current_branch,
        "branch_exists": branch_exists,
    }


def detect_plate_ready():
    """Detect features and epics that are ready to plate/close-service.

    A feature is plate-ready when all its children are closed.
    An epic is close-service-ready when all its children are closed.

    Reuses _parent_children_cache to avoid extra subprocess calls.

    Returns dict with 'features' and 'epics' lists.
    """
    result = {"features": [], "epics": []}

    # Get all open features and epics
    for issue_type, key in [("feature", "features"), ("epic", "epics")]:
        rc, out, _ = run_cmd(
            ["bd", "list", "--status=open", "--type=" + issue_type, "--json"],
            timeout=15
        )
        if rc != 0 or not out:
            continue
        try:
            items = json.loads(out)
            if not isinstance(items, list):
                continue
        except (json.JSONDecodeError, TypeError):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id", "")
            if not _validate_bead_id(item_id):
                continue

            children = _get_children(item_id)
            if children is None or not children:
                continue

            total = len(children)
            closed = sum(
                1 for c in children
                if isinstance(c, dict) and c.get("status") == "closed"
            )
            if total == closed:
                result[key].append({
                    "id": item_id,
                    "title": item.get("title", ""),
                    "progress": "{}/{}".format(closed, total),
                })

    return result


def format_human(data):
    """Format snapshot data as human-readable text."""
    lines = ["# State Snapshot", ""]

    project = data.get("project", {})
    lines.append("## Project")
    lines.append("  Directory: {}".format(project.get("dir", "")))
    lines.append("  Branch: {}".format(project.get("branch", "unknown")))
    lines.append("")

    sync = data.get("sync", {})
    if sync:
        lines.append("## Sync")
        lines.append("  Git: {}".format(sync.get("git", "skipped")))
        lines.append("  Beads: {}".format(sync.get("beads", "skipped")))
        lines.append("")

    roster = data.get("roster", {})
    lines.append("## Task Roster")
    lines.append("  Ready: {}".format(len(roster.get("ready", []))))
    lines.append("  In Progress: {}".format(len(roster.get("in_progress", []))))
    lines.append("  Blocked: {}".format(len(roster.get("blocked", []))))

    for item in roster.get("ready", [])[:5]:
        lines.append("    [{}] {} (P{})".format(
            item.get("id", "?"), item.get("title", ""), item.get("priority", "?")
        ))
    lines.append("")

    suggestion_data = data.get("suggest_next_task", {})
    suggestion = suggestion_data.get("suggestion") if suggestion_data else None
    drill_path = suggestion_data.get("drill_path", []) if suggestion_data else []
    if suggestion:
        lines.append("## Suggested Next Task")
        lines.append("  ID: {}".format(suggestion.get("id", "")))
        lines.append("  Title: {}".format(suggestion.get("title", "")))
        if suggestion.get("deliverables"):
            lines.append("  Deliverables:")
            for deliverable in suggestion["deliverables"]:
                lines.append("    - {}".format(deliverable))
        if drill_path:
            lines.append("  Drill path: {}".format(" -> ".join(drill_path)))
        lines.append("")
    elif drill_path:
        lines.append("## Suggested Next Task")
        lines.append("  No ready task found")
        lines.append("  Drill path checked: {}".format(" -> ".join(drill_path)))
        lines.append("")

    hierarchy = data.get("hierarchy", {})
    if hierarchy.get("epic") or hierarchy.get("feature"):
        lines.append("## Hierarchy")
        if hierarchy.get("epic"):
            epic = hierarchy["epic"]
            lines.append("  Epic: {} - {} ({})".format(
                epic.get("id", ""), epic.get("title", ""), epic.get("progress", "?")
            ))
        if hierarchy.get("feature"):
            feature = hierarchy["feature"]
            lines.append("  Feature: {} - {} ({})".format(
                feature.get("id", ""), feature.get("title", ""), feature.get("progress", "?")
            ))
        if hierarchy.get("completed_siblings"):
            sibling_strs = []
            for s in hierarchy["completed_siblings"]:
                if isinstance(s, dict):
                    sibling_strs.append("{} ({})".format(
                        s.get("id", ""), s.get("title", "")
                    ))
                else:
                    sibling_strs.append(str(s))
            lines.append("  Completed siblings: {}".format(
                ", ".join(sibling_strs)
            ))
        lines.append("")

    branch = data.get("branch_recommendation", {})
    if branch.get("expected") and branch.get("expected") != branch.get("current"):
        lines.append("## Branch Info")
        lines.append("  Expected: {}".format(branch.get("expected", "")))
        lines.append("  Current: {}".format(branch.get("current", "")))
        lines.append("  Branch exists: {}".format(branch.get("branch_exists", False)))
        lines.append("")

    plate_ready = data.get("plate_ready", {})
    ready_features = plate_ready.get("features", [])
    ready_epics = plate_ready.get("epics", [])
    if ready_features or ready_epics:
        lines.append("## Ready to Close")
        for f in ready_features:
            lines.append("  FEATURE: {} - {} ({} tasks closed)".format(
                f.get("id", ""), f.get("title", ""), f.get("progress", "?")
            ))
        for e in ready_epics:
            lines.append("  EPIC: {} - {} ({} features closed)".format(
                e.get("id", ""), e.get("title", ""), e.get("progress", "?")
            ))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Collect full state snapshot for prep phase"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    sync_group = parser.add_mutually_exclusive_group()
    sync_group.add_argument(
        "--sync", action="store_true", default=False,
        help="Force git fetch/pull and bd sync"
    )
    sync_group.add_argument(
        "--no-sync", action="store_true", default=False,
        help="Skip sync step entirely"
    )

    args = parser.parse_args()

    _parent_children_cache.clear()

    data = {}

    # Sync (default is to sync; --no-sync skips it)
    if args.no_sync:
        data["sync"] = {"git": "skipped", "beads": "skipped"}
    else:
        data["sync"] = do_sync()

    # Project info
    data["project"] = get_project_info()

    # Roster
    data["roster"] = get_roster()

    # Suggest next task
    data["suggest_next_task"] = suggest_next_task(data["roster"])

    # Hierarchy (only if we have a suggestion)
    task_id = None
    suggestion = data["suggest_next_task"].get("suggestion")
    if suggestion and isinstance(suggestion, dict):
        task_id = suggestion.get("id")

    if task_id:
        data["hierarchy"] = build_hierarchy(task_id)
    else:
        data["hierarchy"] = {"epic": None, "feature": None, "completed_siblings": []}

    # Branch recommendation
    current_branch = data["project"].get("branch")
    data["branch_recommendation"] = get_branch_recommendation(
        data["hierarchy"], current_branch
    )

    # Plate readiness detection
    data["plate_ready"] = detect_plate_ready()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
