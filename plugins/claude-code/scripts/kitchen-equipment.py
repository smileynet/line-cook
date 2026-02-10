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
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return data
    except (json.JSONDecodeError, TypeError):
        return None


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
        "retry_context": None,
        "has_rework": False,
    }

    # Extract serve comments from bd
    serve_comments = _extract_serve_comments(task_id)
    if serve_comments:
        context["serve_comments"] = serve_comments
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


def _extract_serve_comments(task_id):
    """Extract PHASE: SERVE comments from bd comments list."""
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

    return "\n".join(serve_lines) if serve_lines else None


def detect_tools():
    """Detect project test/build/lint tools from project files.

    Returns dict with test/build/lint keys set to command string or None.
    """
    tools = {"test": None, "build": None, "lint": None}
    project_root = Path(".")

    # Test tool detection
    if (project_root / "package.json").exists():
        tools["test"] = "npm test"
    elif (project_root / "pytest.ini").exists() or (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
        tools["test"] = "pytest"
    elif (project_root / "go.mod").exists():
        tools["test"] = "go test"
    elif (project_root / "Cargo.toml").exists():
        tools["test"] = "cargo test"
    elif (project_root / "Makefile").exists():
        tools["test"] = "make test"

    # Build tool detection
    if (project_root / "Makefile").exists():
        tools["build"] = "make"
    elif (project_root / "package.json").exists():
        tools["build"] = "npm run build"
    elif (project_root / "go.mod").exists():
        tools["build"] = "go build"
    elif (project_root / "Cargo.toml").exists():
        tools["build"] = "cargo build"

    # Lint tool detection
    if (project_root / "ruff.toml").exists() or (project_root / ".ruff.toml").exists():
        tools["lint"] = "ruff"
    elif (project_root / ".eslintrc.js").exists() or (project_root / ".eslintrc.json").exists():
        tools["lint"] = "eslint"
    elif (project_root / "pyproject.toml").exists():
        try:
            content = (project_root / "pyproject.toml").read_text()
            if "[tool.ruff]" in content:
                tools["lint"] = "ruff"
        except OSError:
            pass

    return tools


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
    cwd = Path.cwd().resolve()
    for line in description.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("planning context:"):
            path_str = line.strip().split(":", 1)[1].strip()
            ctx_path = Path(path_str)
            # Validate path is within project directory
            try:
                resolved = ctx_path.resolve()
                if not resolved.is_relative_to(cwd):
                    return None
            except (OSError, ValueError):
                return None
            if ctx_path.is_dir():
                # Read README.md or first .md file in the directory
                readme = ctx_path / "README.md"
                if readme.exists():
                    try:
                        return readme.read_text()[:5000]
                    except OSError:
                        return None
                md_files = list(ctx_path.glob("*.md"))
                if md_files:
                    try:
                        return md_files[0].read_text()[:5000]
                    except OSError:
                        return None
            elif ctx_path.is_file():
                try:
                    return ctx_path.read_text()[:5000]
                except OSError:
                    return None
    return None


def get_kitchen_manual():
    """Read first 100 lines of AGENTS.md."""
    agents_path = Path("AGENTS.md")
    if not agents_path.exists():
        return None
    try:
        lines = agents_path.read_text().splitlines()[:100]
        return "\n".join(lines)
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
            lines.append("  Serve feedback:")
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

    if data.get("kitchen_manual"):
        lines.append("## Kitchen Manual")
        lines.append("  (First 100 lines of AGENTS.md loaded)")
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

    # Load kitchen manual (AGENTS.md)
    kitchen_manual = get_kitchen_manual()

    data = {
        "task": task,
        "is_epic": is_epic,
        "epic_children": epic_children,
        "prior_context": prior_context,
        "tools": tools,
        "planning_context": planning_context,
        "kitchen_manual": kitchen_manual,
    }

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(format_human(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
