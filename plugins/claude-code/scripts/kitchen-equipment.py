#!/usr/bin/env python3
"""
kitchen-equipment.py - Pre-conditions and context for cook phase.

Gathers task details, handles epic drill-down, loads prior serve
comments and retry context, detects project tools.

When no task_id is given, returns the ready list for the agent to choose from.

Usage:
    python3 plugins/claude-code/scripts/kitchen-equipment.py              # Returns ready list
    python3 plugins/claude-code/scripts/kitchen-equipment.py <task-id>    # Task details
    python3 plugins/claude-code/scripts/kitchen-equipment.py --json       # JSON output

Exit codes:
    0: Success
    1: Script error or task not found
"""

import argparse
import json
import re
import sys
from pathlib import Path

from helpers import run_cmd, run_bd_json


def _validate_bead_id(bid):
    """Validate bead ID format to prevent malformed input in subprocess calls."""
    return bool(bid and re.match(r'^[a-zA-Z0-9._-]+$', bid))


def get_task_detail(task_id):
    """Fetch full task details from bd."""
    if not _validate_bead_id(task_id):
        return None
    detail = run_bd_json(["show", task_id])
    if not detail or not isinstance(detail, dict):
        return None
    return {
        "id": detail.get("id", ""),
        "title": detail.get("title", ""),
        "type": detail.get("type") or detail.get("issue_type", ""),
        "status": detail.get("status", ""),
        "description": detail.get("description", ""),
        "priority": detail.get("priority"),
        "parent": detail.get("parent"),
    }


def find_epic_children(epic_id):
    """List children of an epic, finding first ready task."""
    rc, out, _ = run_cmd(["bd", "list", "--parent=" + epic_id, "--all", "--json"], timeout=15)
    if rc != 0 or not out:
        return []
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return [
                {
                    "id": c.get("id", ""),
                    "title": c.get("title", ""),
                    "type": c.get("type") or c.get("issue_type", ""),
                    "status": c.get("status", ""),
                }
                for c in data if isinstance(c, dict)
            ]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def get_prior_context(task_id):
    """Load prior serve comments and retry context."""
    context = {
        "serve_comments": None,
        "serve_comments_truncated": False,
        "retry_context": None,
        "has_rework": False,
    }

    # Extract serve comments from bd
    serve_result = _extract_serve_comments(task_id)
    if serve_result:
        context["serve_comments"] = serve_result["text"]
        context["serve_comments_truncated"] = serve_result["truncated"]
        context["has_rework"] = True

    # Load retry context file
    retry_path = Path(".line-cook") / "retry-context.json"
    if retry_path.exists():
        try:
            retry_data = json.loads(retry_path.read_text())
            context["retry_context"] = retry_data
            if retry_data.get("verdict") == "NEEDS_CHANGES":
                context["has_rework"] = True
        except (json.JSONDecodeError, OSError):
            pass

    return context


MAX_SERVE_COMMENT_CHARS = 2000


def _extract_serve_comments(task_id):
    """Extract PHASE: SERVE comments from bd comments list.

    Caps output at MAX_SERVE_COMMENT_CHARS to prevent context bloat.
    Returns dict with 'text' and 'truncated' keys, or None if no comments.
    """
    rc, out, _ = run_cmd(["bd", "comments", "list", task_id], timeout=15)
    if rc != 0 or not out:
        return None

    serve_lines = []
    in_serve_section = False

    for line in out.splitlines():
        if "PHASE: SERVE" in line:
            in_serve_section = True
        elif in_serve_section and line.startswith("PHASE:"):
            in_serve_section = False
        if in_serve_section:
            serve_lines.append(line)

    if not serve_lines:
        return None

    text = "\n".join(serve_lines)
    truncated = len(text) > MAX_SERVE_COMMENT_CHARS
    if truncated:
        text = text[:MAX_SERVE_COMMENT_CHARS] + "\n... [truncated]"
    return {"text": text, "truncated": truncated}


def detect_tools():
    """Detect project test/build/lint tools from project files.

    Returns dict with test/build/lint keys set to command string or None.
    """
    project_root = Path(".")
    return {
        "test": _detect_test_tool(project_root),
        "build": _detect_build_tool(project_root),
        "lint": _detect_lint_tool(project_root),
    }


def _detect_test_tool(project_root):
    """Detect test command from project files."""
    if (project_root / "package.json").exists():
        return "npm test"
    if (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
        return "pytest"
    if (project_root / "go.mod").exists():
        return "go test"
    if (project_root / "Cargo.toml").exists():
        return "cargo test"
    if (project_root / "Makefile").exists():
        return "make test"
    return None


def _detect_build_tool(project_root):
    """Detect build command from project files."""
    if (project_root / "Makefile").exists():
        return "make"
    if (project_root / "package.json").exists():
        return "npm run build"
    if (project_root / "go.mod").exists():
        return "go build"
    if (project_root / "Cargo.toml").exists():
        return "cargo build"
    return None


def _detect_lint_tool(project_root):
    """Detect lint command from project files."""
    if (project_root / "ruff.toml").exists() or (project_root / ".ruff.toml").exists():
        return "ruff"
    if (project_root / ".eslintrc.js").exists() or (project_root / ".eslintrc.json").exists():
        return "eslint"
    if (project_root / "pyproject.toml").exists():
        try:
            content = (project_root / "pyproject.toml").read_text()
            if "[tool.ruff]" in content:
                return "ruff"
        except OSError:
            pass
    return None


def get_ready_list():
    """Fetch ready task list from bd ready."""
    rc, out, _ = run_cmd(["bd", "ready", "--json"], timeout=15)
    if rc != 0 or not out:
        return []
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return [
                {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "type": item.get("type") or item.get("issue_type", ""),
                    "priority": item.get("priority"),
                }
                for item in data if isinstance(item, dict) and item.get("id")
            ]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def load_planning_context(description):
    """Parse description for 'Planning context:' path and read if exists.

    Only reads paths within the current working directory tree.
    """
    if not description:
        return None

    context_path = _extract_planning_context_path(description)
    if not context_path:
        return None

    if context_path.is_dir():
        return _read_directory_context(context_path)
    if context_path.is_file():
        return _read_file_safe(context_path, max_chars=5000)
    return None


def _extract_planning_context_path(description):
    """Extract and validate planning context path from description."""
    cwd = Path.cwd().resolve()
    for line in description.splitlines():
        if line.strip().lower().startswith("planning context:"):
            path_str = line.strip().split(":", 1)[1].strip()
            ctx_path = Path(path_str)
            try:
                resolved = ctx_path.resolve()
                if resolved.is_relative_to(cwd):
                    return ctx_path
            except (OSError, ValueError):
                pass
    return None


def _read_directory_context(directory):
    """Read README.md or first .md file from directory."""
    readme = directory / "README.md"
    if readme.exists():
        return _read_file_safe(readme, max_chars=5000)

    md_files = list(directory.glob("*.md"))
    if md_files:
        return _read_file_safe(md_files[0], max_chars=5000)
    return None


def _read_file_safe(file_path, max_chars=5000):
    """Read file content safely with size limit."""
    try:
        return file_path.read_text()[:max_chars]
    except OSError:
        return None


def format_human(data):
    """Format result as human-readable text."""
    lines = ["# Kitchen Equipment Check", ""]

    ready_list = data.get("ready_list")
    if ready_list is not None:
        lines.append("## Ready Tasks ({})".format(len(ready_list)))
        for item in ready_list:
            lines.append("  [{}] {} (P{}, {})".format(
                item.get("id", ""),
                item.get("title", ""),
                item.get("priority", "?"),
                item.get("type", ""),
            ))
        lines.append("")
        return "\n".join(lines)

    task = data.get("task", {})
    lines.append("## Task")
    lines.append("  ID: {}".format(task.get("id", "")))
    lines.append("  Title: {}".format(task.get("title", "")))
    lines.append("  Type: {}".format(task.get("type", "")))
    lines.append("  Status: {}".format(task.get("status", "")))
    lines.append("")

    if data.get("is_epic"):
        lines.append("## Epic Drill-Down")
        lines.append("  This is an epic. Children:")
        for child in (data.get("epic_children") or []):
            lines.append("    [{}] {} ({}) - {}".format(
                child.get("id", ""),
                child.get("title", ""),
                child.get("type", ""),
                child.get("status", ""),
            ))
        lines.append("")

    context = data.get("prior_context", {})
    if context.get("has_rework"):
        lines.append("## Prior Context (REWORK)")
        if context.get("serve_comments"):
            lines.append("  Serve feedback{}:".format(
                " (TRUNCATED)" if context.get("serve_comments_truncated") else ""
            ))
            for line in context["serve_comments"].splitlines()[:10]:
                lines.append("    {}".format(line))
        if context.get("retry_context"):
            retry = context["retry_context"]
            lines.append("  Retry: attempt {}, verdict {}".format(
                retry.get("attempt", "?"), retry.get("verdict", "?")
            ))
        lines.append("")

    tools = data.get("tools", {})
    lines.append("## Tools")
    lines.append("  Test: {}".format(tools.get("test") or "not detected"))
    lines.append("  Build: {}".format(tools.get("build") or "not detected"))
    lines.append("  Lint: {}".format(tools.get("lint") or "not detected"))
    lines.append("")

    if data.get("planning_context"):
        lines.append("## Planning Context")
        lines.append("  (Loaded from description path)")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Gather pre-conditions and context for cook phase"
    )
    parser.add_argument(
        "task_id", nargs="?", default=None,
        help="Bead ID of the task to cook (returns ready list if omitted)"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output JSON instead of human-readable format"
    )

    args = parser.parse_args()

    task_id = args.task_id

    # No task_id: return ready list for agent to choose from
    if not task_id:
        ready_list = get_ready_list()
        data = {"ready_list": ready_list, "task": None}
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(format_human(data))
        sys.exit(0)

    task = get_task_detail(task_id)
    if not task:
        msg = "Task not found: {}".format(task_id)
        if args.json:
            print(json.dumps({"error": msg}))
        else:
            print("ERROR: {}".format(msg))
        sys.exit(1)

    bead_type = task.get("type", "")
    is_epic = bead_type == "epic"

    epic_children = None
    if is_epic:
        epic_children = find_epic_children(task_id)

    prior_context = get_prior_context(task_id)
    tools = detect_tools()

    # Load planning context from description
    planning_context = load_planning_context(task.get("description", ""))

    data = {
        "task": task,
        "is_epic": is_epic,
        "epic_children": epic_children,
        "prior_context": prior_context,
        "tools": tools,
        "planning_context": planning_context,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
