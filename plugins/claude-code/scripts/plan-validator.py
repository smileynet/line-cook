#!/usr/bin/env python3
"""
plan-validator.py - Structural validation of bead hierarchy and content quality.

Checks hierarchy depth, orphans, type consistency, acceptance criteria,
user story format, stale items, and auto-fixable issues.

Usage:
    python3 plugins/claude-code/scripts/plan-validator.py              # Active scope
    python3 plugins/claude-code/scripts/plan-validator.py full         # All beads
    python3 plugins/claude-code/scripts/plan-validator.py <bead-id>    # Specific bead
    python3 plugins/claude-code/scripts/plan-validator.py --fix        # Auto-fix safe issues
    python3 plugins/claude-code/scripts/plan-validator.py --json       # JSON output

Exit codes:
    0: No critical findings
    1: Critical findings or script error
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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


def _fetch_bead(bead_id):
    """Fetch a single bead by ID, returning dict or None."""
    if not _validate_bead_id(bead_id):
        return None
    rc, out, _ = run_cmd(["bd", "show", bead_id, "--json"], timeout=15)
    if rc != 0 or not out:
        return None
    try:
        data = json.loads(out)
        if isinstance(data, list) and len(data) == 1:
            data = data[0]
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _collect_children(parent_id, beads, seen, depth=0, max_depth=2):
    """Recursively collect children up to max_depth levels."""
    if depth >= max_depth:
        return
    if not _validate_bead_id(parent_id):
        return
    rc, out, _ = run_cmd(
        ["bd", "list", "--parent=" + parent_id, "--all", "--json"], timeout=15
    )
    if rc != 0 or not out:
        return
    try:
        data = json.loads(out)
        if not isinstance(data, list):
            return
        for child in data:
            if isinstance(child, dict):
                child_id = child.get("id", "")
                if child_id and child_id not in seen:
                    seen.add(child_id)
                    beads.append(child)
                    _collect_children(child_id, beads, seen, depth + 1, max_depth)
    except (json.JSONDecodeError, TypeError):
        pass


def load_beads(scope):
    """Load beads based on scope: active, full, or specific ID."""
    beads = []

    if scope == "active":
        for status in ("open", "in_progress"):
            rc, out, _ = run_cmd(
                ["bd", "list", "--status=" + status, "--json"], timeout=20
            )
            if rc == 0 and out:
                try:
                    data = json.loads(out)
                    if isinstance(data, list):
                        beads.extend(data)
                except (json.JSONDecodeError, TypeError):
                    pass
    elif scope == "full":
        rc, out, _ = run_cmd(["bd", "list", "--all", "--json"], timeout=30)
        if rc == 0 and out:
            try:
                data = json.loads(out)
                if isinstance(data, list):
                    beads = data
            except (json.JSONDecodeError, TypeError):
                pass
    else:
        # Specific bead ID — walk parent chain up, then get recursive children
        if not _validate_bead_id(scope):
            return []
        bead_data = _fetch_bead(scope)
        if bead_data:
            beads.append(bead_data)

            # Walk parent chain
            parent_id = bead_data.get("parent")
            seen = {scope}
            while parent_id and parent_id not in seen:
                seen.add(parent_id)
                parent_data = _fetch_bead(parent_id)
                if parent_data:
                    beads.append(parent_data)
                    parent_id = parent_data.get("parent")
                else:
                    break

            # Get recursive children (2 levels: children + grandchildren)
            _collect_children(scope, beads, seen, depth=0, max_depth=2)

    return [b for b in beads if isinstance(b, dict)]


def get_bead_type(bead):
    """Get bead type, normalizing field names (type vs issue_type)."""
    return bead.get("type") or bead.get("issue_type", "")


def _get_depth(bead_id, beads_by_id, max_depth=10):
    """Calculate hierarchy depth by walking parent chain."""
    depth = 0
    current = bead_id
    seen = set()
    while depth < max_depth:
        bead = beads_by_id.get(current)
        if not bead:
            break
        parent = bead.get("parent")
        if not parent or parent in seen:
            break
        seen.add(parent)
        current = parent
        depth += 1
    return depth


# --- Structural Checks ---

def check_hierarchy_depth(beads, beads_by_id):
    """Hierarchy depth should be <= 3 levels (epic→feature→task)."""
    findings = []
    for bead in beads:
        bid = bead.get("id", "")
        depth = _get_depth(bid, beads_by_id)
        if depth > 3:
            findings.append({
                "check": "DEPTH",
                "bead": bid,
                "severity": "critical",
                "message": "Hierarchy depth {} exceeds max 3".format(depth),
            })
    return findings


def check_orphans(beads, beads_by_id):
    """Parent must exist if referenced."""
    findings = []
    for bead in beads:
        bid = bead.get("id", "")
        parent = bead.get("parent")
        if parent and parent not in beads_by_id:
            findings.append({
                "check": "ORPHAN",
                "bead": bid,
                "severity": "critical",
                "message": "Parent {} not found".format(parent),
            })
    return findings


def check_type_consistency(beads, beads_by_id):
    """Tasks shouldn't have children; type tiers should be consistent."""
    findings = []
    children_of = {}
    for bead in beads:
        parent = bead.get("parent")
        if parent:
            children_of.setdefault(parent, []).append(bead.get("id", ""))

    for bead in beads:
        bid = bead.get("id", "")
        btype = get_bead_type(bead)

        if btype == "task" and bid in children_of:
            findings.append({
                "check": "TYPE_CONSISTENCY",
                "bead": bid,
                "severity": "warning",
                "message": "Task has {} children (tasks shouldn't have children)".format(
                    len(children_of[bid])
                ),
            })

    return findings


# --- Content Quality Checks ---

def check_acceptance_criteria(beads):
    """Features should have 3-5 acceptance criteria."""
    findings = []
    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "feature":
            continue

        bid = bead.get("id", "")
        description = bead.get("description") or ""

        criteria_count = _count_acceptance_criteria(description)

        if criteria_count == 0:
            findings.append({
                "check": "ACCEPTANCE_CRITERIA",
                "bead": bid,
                "severity": "info",
                "message": "Feature has no acceptance criteria section",
            })
        elif criteria_count < 3:
            findings.append({
                "check": "ACCEPTANCE_CRITERIA",
                "bead": bid,
                "severity": "info",
                "message": "Feature has {} acceptance criteria (3-5 expected)".format(criteria_count),
            })

    return findings


def _count_acceptance_criteria(description):
    """Count acceptance criteria items in description text."""
    criteria_count = 0
    in_ac_section = False

    for line in description.splitlines():
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Check for AC section header
        if "acceptance criteria" in line_lower:
            in_ac_section = True
            continue

        if in_ac_section:
            # Count list items
            if line_stripped.startswith(("- ", "* ")) or re.match(r"^\d+\.", line_stripped):
                criteria_count += 1
            # Check for section end (new heading or "Deliverable")
            elif line_stripped.startswith("##") or line_stripped.startswith("Deliverable"):
                in_ac_section = False

    return criteria_count


def check_user_story(beads):
    """Features should have user story format."""
    findings = []
    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "feature":
            continue

        bid = bead.get("id", "")
        description_lower = (bead.get("description") or "").lower()

        has_story = all(phrase in description_lower for phrase in ("as a", "i want", "so that"))
        if not has_story:
            findings.append({
                "check": "USER_STORY",
                "bead": bid,
                "severity": "info",
                "message": "Feature missing user story format (As a...I want...so that)",
            })

    return findings


def check_deliverable(beads):
    """Tasks should have a deliverable statement."""
    findings = []
    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "task":
            continue

        bid = bead.get("id", "")
        description_lower = (bead.get("description") or "").lower()

        if "deliverable" not in description_lower:
            findings.append({
                "check": "DELIVERABLE",
                "bead": bid,
                "severity": "info",
                "message": "Task missing deliverable statement",
            })

    return findings


def check_priority_set(beads):
    """All beads should have priority set."""
    findings = []
    for bead in beads:
        bid = bead.get("id", "")
        priority = bead.get("priority")
        if priority is None:
            findings.append({
                "check": "PRIORITY",
                "bead": bid,
                "severity": "warning",
                "message": "Priority not set",
                "auto_fixable": True,
                "fix_cmd": ["bd", "update", bid, "--priority=2"],
            })
    return findings


def check_type_set(beads, beads_by_id):
    """All beads should have issue_type set."""
    findings = []
    for bead in beads:
        bid = bead.get("id", "")
        btype = get_bead_type(bead)
        if not btype:
            # Infer from parent type
            parent_id = bead.get("parent")
            inferred = "task"  # default
            if parent_id:
                parent = beads_by_id.get(parent_id)
                if parent:
                    parent_type = get_bead_type(parent)
                    if parent_type == "epic":
                        inferred = "feature"
                    elif parent_type == "feature":
                        inferred = "task"
            findings.append({
                "check": "TYPE_MISSING",
                "bead": bid,
                "severity": "warning",
                "message": "Issue type not set (inferred: {})".format(inferred),
                "auto_fixable": True,
                "fix_cmd": ["bd", "update", bid, "--type=" + inferred],
            })
    return findings


# --- Planning Hygiene Checks ---

def check_planning_context(beads):
    """Active epics should have a planning context folder."""
    findings = []
    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "epic":
            continue
        status = bead.get("status", "")
        if status == "closed":
            continue

        bid = bead.get("id", "")
        description = bead.get("description") or ""

        # Check for planning context reference in description
        has_context_ref = "planning context:" in description.lower()
        if has_context_ref:
            # Extract path and check existence
            for line in description.splitlines():
                if line.strip().lower().startswith("planning context:"):
                    path_str = line.strip().split(":", 1)[1].strip()
                    if not Path(path_str).exists():
                        findings.append({
                            "check": "PLANNING_CONTEXT",
                            "bead": bid,
                            "severity": "warning",
                            "message": "Planning context path not found: {}".format(path_str),
                        })
                    break
        else:
            findings.append({
                "check": "PLANNING_CONTEXT",
                "bead": bid,
                "severity": "info",
                "message": "Active epic has no planning context reference",
            })

    return findings


def check_acceptance_docs(beads):
    """Closed features should have acceptance documentation."""
    findings = []
    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "feature":
            continue
        if bead.get("status") != "closed":
            continue

        bid = bead.get("id", "")
        acceptance_path = Path("docs") / "features" / "{}-acceptance.md".format(bid)
        if not acceptance_path.exists():
            findings.append({
                "check": "ACCEPTANCE_DOC",
                "bead": bid,
                "severity": "info",
                "message": "Closed feature missing acceptance doc: {}".format(acceptance_path),
            })

    return findings


# --- Health Checks ---

def check_stale_in_progress(beads):
    """In-progress items older than 7 days."""
    findings = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)

    for bead in beads:
        if bead.get("status") != "in_progress":
            continue

        bid = bead.get("id", "")
        updated = bead.get("updated_at") or bead.get("updated") or bead.get("created_at") or ""

        if updated:
            try:
                dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    days = (now - dt).days
                    findings.append({
                        "check": "STALE",
                        "bead": bid,
                        "severity": "warning",
                        "message": "In-progress for {} days".format(days),
                        "auto_fixable": False,
                    })
            except (ValueError, AttributeError):
                pass

    return findings


def check_old_open(beads):
    """Open items older than 30 days."""
    findings = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    for bead in beads:
        if bead.get("status") != "open":
            continue

        bid = bead.get("id", "")
        created = bead.get("created_at") or bead.get("created") or ""

        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    days = (now - dt).days
                    findings.append({
                        "check": "OLD_OPEN",
                        "bead": bid,
                        "severity": "info",
                        "message": "Open for {} days".format(days),
                    })
            except (ValueError, AttributeError):
                pass

    return findings


def check_nearly_complete(beads, beads_by_id):
    """Features with >80% children closed."""
    findings = []
    children_of = {}
    for bead in beads:
        parent = bead.get("parent")
        if parent:
            children_of.setdefault(parent, []).append(bead)

    for bead in beads:
        btype = get_bead_type(bead)
        if btype != "feature":
            continue
        if bead.get("status") == "closed":
            continue

        bid = bead.get("id", "")
        children = children_of.get(bid, [])
        if len(children) < 2:
            continue

        closed_count = sum(1 for c in children if c.get("status") == "closed")
        pct = closed_count / len(children)
        if pct >= 0.8:
            findings.append({
                "check": "NEARLY_COMPLETE",
                "bead": bid,
                "severity": "info",
                "message": "Feature {}/{} children closed ({:.0%})".format(
                    closed_count, len(children), pct
                ),
            })

    return findings


# --- Full Scope Only ---

def check_close_reason(beads):
    """Closed beads should have a close reason or comment."""
    findings = []
    for bead in beads:
        if bead.get("status") != "closed":
            continue

        bid = bead.get("id", "")
        reason = bead.get("close_reason") or bead.get("reason")
        if not reason:
            findings.append({
                "check": "CLOSE_REASON",
                "bead": bid,
                "severity": "info",
                "message": "Closed without reason",
            })

    return findings


def check_orphan_parent(beads, beads_by_id):
    """Parent still open but all children closed."""
    findings = []
    children_of = {}
    for bead in beads:
        parent = bead.get("parent")
        if parent:
            children_of.setdefault(parent, []).append(bead)

    for parent_id, children in children_of.items():
        parent = beads_by_id.get(parent_id)
        if not parent:
            continue
        if parent.get("status") == "closed":
            continue

        all_closed = all(c.get("status") == "closed" for c in children)
        if all_closed and len(children) > 0:
            findings.append({
                "check": "ORPHAN_PARENT",
                "bead": parent_id,
                "severity": "warning",
                "message": "All {} children closed but parent still open".format(len(children)),
            })

    return findings


# --- Statistics ---

def calc_stats(beads):
    """Calculate counts by tier and status."""
    by_tier = {"epic": 0, "feature": 0, "task": 0, "other": 0}
    by_status = {}

    for bead in beads:
        btype = get_bead_type(bead)
        if btype in by_tier:
            by_tier[btype] += 1
        else:
            by_tier["other"] += 1

        status = bead.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    total = len(beads)
    closed = by_status.get("closed", 0)
    progress_pct = round(100 * closed / total) if total > 0 else 0

    return {
        "by_tier": by_tier,
        "by_status": by_status,
        "progress_pct": progress_pct,
    }


# --- Auto-fix ---

def apply_fixes(findings):
    """Apply auto-fixable findings."""
    applied = []
    for finding in findings:
        if not finding.get("auto_fixable"):
            continue
        cmd = finding.get("fix_cmd")
        if not cmd:
            continue
        rc, _, _ = run_cmd(cmd)
        if rc == 0:
            applied.append({
                "bead": finding["bead"],
                "check": finding["check"],
                "cmd": " ".join(cmd),
            })
    return applied


# --- Formatting ---

def format_human(data):
    """Format as human-readable report."""
    lines = ["# Plan Validation Report", ""]
    lines.append("Scope: {}  |  Beads scanned: {}".format(
        data["scope"], data["beads_scanned"]
    ))
    lines.append("")

    findings = data["findings"]
    for severity in ("critical", "warning", "info"):
        items = findings.get(severity, [])
        if not items:
            continue
        lines.append("## {} ({})".format(severity.upper(), len(items)))
        for finding in items:
            lines.append("  [{}] {} - {}".format(
                finding.get("check", ""), finding.get("bead", ""), finding.get("message", "")
            ))
            if finding.get("auto_fixable"):
                lines.append("         ^ auto-fixable")
        lines.append("")

    stats = data["stats"]
    lines.append("## Statistics")
    lines.append("  By tier: {}".format(stats["by_tier"]))
    lines.append("  By status: {}".format(stats["by_status"]))
    lines.append("  Progress: {}%".format(stats["progress_pct"]))
    lines.append("")

    fixes = data.get("fixes_applied", [])
    if fixes:
        lines.append("## Fixes Applied")
        for fix in fixes:
            lines.append("  [{}] {} - {}".format(fix["check"], fix["bead"], fix["cmd"]))
        lines.append("")

    avail = data.get("fixes_available", 0)
    if avail > 0 and not fixes:
        lines.append("  {} auto-fixable issues (run with --fix to apply)".format(avail))
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate bead hierarchy structure, content quality, and health"
    )
    parser.add_argument(
        "scope", nargs="?", default="active",
        help="Scope: active (default), full, or a bead ID"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-fix safe issues (missing priority, type)"
    )

    args = parser.parse_args()

    # Load beads
    beads = load_beads(args.scope)
    beads_by_id = {b.get("id", ""): b for b in beads}

    # Run checks
    all_findings = []

    # Structural
    all_findings.extend(check_hierarchy_depth(beads, beads_by_id))
    all_findings.extend(check_orphans(beads, beads_by_id))
    all_findings.extend(check_type_consistency(beads, beads_by_id))

    # Content quality
    all_findings.extend(check_acceptance_criteria(beads))
    all_findings.extend(check_user_story(beads))
    all_findings.extend(check_deliverable(beads))
    all_findings.extend(check_priority_set(beads))
    all_findings.extend(check_type_set(beads, beads_by_id))

    # Planning hygiene
    all_findings.extend(check_planning_context(beads))

    # Health
    all_findings.extend(check_stale_in_progress(beads))
    all_findings.extend(check_old_open(beads))
    all_findings.extend(check_nearly_complete(beads, beads_by_id))

    # Full scope additions
    if args.scope == "full":
        all_findings.extend(check_acceptance_docs(beads))
        all_findings.extend(check_close_reason(beads))
        all_findings.extend(check_orphan_parent(beads, beads_by_id))

    # Group by severity
    grouped = {"critical": [], "warning": [], "info": []}
    for f in all_findings:
        severity = f.get("severity", "info")
        grouped.setdefault(severity, []).append(f)

    # Count auto-fixable
    fixes_available = sum(1 for f in all_findings if f.get("auto_fixable"))

    # Apply fixes if requested
    fixes_applied = []
    if args.fix:
        fixes_applied = apply_fixes(all_findings)

    stats = calc_stats(beads)

    data = {
        "scope": args.scope,
        "beads_scanned": len(beads),
        "findings": grouped,
        "stats": stats,
        "fixes_applied": fixes_applied,
        "fixes_available": fixes_available,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    has_critical = len(grouped.get("critical", [])) > 0
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
