#!/usr/bin/env python3
"""
line-cook doctor command - validates hook configuration and detects orphaned configs.

Checks for:
1. Settings.json structure validity
2. Hook script file existence
3. Python syntax validation
4. Missing dependencies
5. Orphaned references (files that don't exist)

Cross-platform compatible (Windows, Linux, macOS)
"""

import ast
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class CheckResult(NamedTuple):
    """Result of a validation check."""

    passed: bool
    message: str
    details: list[str] | None = None


def get_project_dir() -> Path:
    """Get the project directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def find_settings_files(project_dir: Path) -> list[Path]:
    """Find all settings.json files that might contain hook configs."""
    candidates = [
        project_dir / ".claude" / "settings.json",
        project_dir / "hooks" / "settings.json",
    ]
    return [p for p in candidates if p.exists()]


def validate_json_syntax(file_path: Path) -> CheckResult:
    """Check if a file contains valid JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return CheckResult(True, f"Valid JSON: {file_path.name}")
    except json.JSONDecodeError as e:
        return CheckResult(False, f"Invalid JSON in {file_path.name}", [str(e)])
    except Exception as e:
        return CheckResult(False, f"Cannot read {file_path.name}", [str(e)])


def validate_hooks_structure(config: dict, file_path: Path) -> CheckResult:
    """Validate the structure of hooks configuration."""
    issues = []

    if "hooks" not in config:
        return CheckResult(True, "No hooks section (optional)")

    hooks = config["hooks"]
    if not isinstance(hooks, dict):
        return CheckResult(False, "Invalid hooks section", ["Expected object/dict"])

    valid_events = {
        "SessionStart",
        "PreToolUse",
        "PostToolUse",
        "Stop",
        "PreCompact",
        "Notification",
    }

    for event_name, event_config in hooks.items():
        if event_name not in valid_events:
            issues.append(f"Unknown hook event: {event_name}")

        if not isinstance(event_config, list):
            issues.append(f"{event_name}: expected array of hook definitions")
            continue

        for i, hook_def in enumerate(event_config):
            if not isinstance(hook_def, dict):
                issues.append(f"{event_name}[{i}]: expected object")
                continue

            if "hooks" not in hook_def:
                issues.append(f"{event_name}[{i}]: missing 'hooks' array")
                continue

            for j, hook in enumerate(hook_def.get("hooks", [])):
                if "type" not in hook:
                    issues.append(f"{event_name}[{i}].hooks[{j}]: missing 'type'")
                if "command" not in hook:
                    issues.append(f"{event_name}[{i}].hooks[{j}]: missing 'command'")

    if issues:
        return CheckResult(False, f"Structure issues in {file_path.name}", issues)
    return CheckResult(True, f"Valid structure: {file_path.name}")


def extract_script_paths(config: dict, project_dir: Path) -> list[tuple[str, str]]:
    """Extract script paths from hook commands.

    Returns list of (event_name, resolved_path) tuples.
    """
    paths = []
    hooks = config.get("hooks", {})

    for event_name, event_config in hooks.items():
        if not isinstance(event_config, list):
            continue

        for hook_def in event_config:
            for hook in hook_def.get("hooks", []):
                command = hook.get("command", "")
                # Extract paths from python3 "path" or similar patterns
                # Handle quoted paths and unquoted .py paths
                matches = re.findall(r'"([^"]+\.py)"', command)
                matches += re.findall(r"'([^']+\.py)'", command)
                # Also match unquoted paths ending in .py
                unquoted = re.findall(r'python3?\s+([^\s"\']+\.py)', command)
                matches += unquoted
                for match in matches:
                    # Expand environment variables
                    expanded = match.replace("$CLAUDE_PROJECT_DIR", str(project_dir))
                    expanded = expanded.replace(
                        "${CLAUDE_PROJECT_DIR}", str(project_dir)
                    )
                    expanded = os.path.expandvars(expanded)
                    paths.append((event_name, expanded))

    return paths


def validate_script_exists(event_name: str, script_path: str) -> CheckResult:
    """Check if a referenced script file exists."""
    path = Path(script_path)

    if not path.exists():
        return CheckResult(
            False,
            f"Missing script: {path.name}",
            [f"Event: {event_name}", f"Path: {script_path}", "File does not exist"],
        )

    if not path.is_file():
        return CheckResult(
            False,
            f"Not a file: {path.name}",
            [f"Event: {event_name}", f"Path: {script_path}"],
        )

    return CheckResult(True, f"Found: {path.name}")


def validate_python_syntax(script_path: str) -> CheckResult:
    """Validate Python syntax of a script file."""
    path = Path(script_path)

    if path.suffix != ".py":
        return CheckResult(True, f"Skipped (not Python): {path.name}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return CheckResult(True, f"Valid Python: {path.name}")
    except SyntaxError as e:
        return CheckResult(
            False,
            f"Syntax error: {path.name}",
            [f"Line {e.lineno}: {e.msg}"],
        )
    except Exception as e:
        return CheckResult(False, f"Cannot parse: {path.name}", [str(e)])


def check_python_available() -> CheckResult:
    """Check if Python 3 is available."""
    if shutil.which("python3"):
        return CheckResult(True, "Python 3 available")
    if shutil.which("python"):
        return CheckResult(True, "Python available (as 'python')")
    return CheckResult(False, "Python not found in PATH")


def check_hook_imports(script_path: str, project_dir: Path) -> CheckResult:
    """Check if a Python hook can import its dependencies."""
    path = Path(script_path)

    if path.suffix != ".py":
        return CheckResult(True, f"Skipped (not Python): {path.name}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        # Check for local imports (like hook_utils)
        # Use the script's parent directory for local import resolution
        hooks_dir = path.parent
        missing = []

        # Only check known local imports - stdlib checking is unreliable
        local_imports = {"hook_utils"}

        for imp in imports:
            if imp in local_imports:
                local_path = hooks_dir / f"{imp}.py"
                if not local_path.exists():
                    missing.append(f"{imp} (expected at {local_path})")

        if missing:
            return CheckResult(False, f"Missing imports: {path.name}", missing)
        return CheckResult(True, f"Imports OK: {path.name}")

    except Exception as e:
        return CheckResult(False, f"Cannot check imports: {path.name}", [str(e)])


def run_doctor() -> tuple[list[CheckResult], int]:
    """Run all doctor checks and return results."""
    results = []
    project_dir = get_project_dir()

    # Header
    results.append(CheckResult(True, f"Project: {project_dir}"))

    # Check Python availability
    results.append(check_python_available())

    # Find and validate settings files
    settings_files = find_settings_files(project_dir)

    if not settings_files:
        results.append(
            CheckResult(
                True, "No settings.json files found (OK if no hooks configured)"
            )
        )
        return results, 0

    all_script_paths = []

    for settings_path in settings_files:
        # JSON syntax
        json_result = validate_json_syntax(settings_path)
        results.append(json_result)

        if not json_result.passed:
            continue

        # Load and validate structure
        with open(settings_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        structure_result = validate_hooks_structure(config, settings_path)
        results.append(structure_result)

        if not structure_result.passed:
            continue

        # Extract script paths for validation
        script_paths = extract_script_paths(config, project_dir)
        all_script_paths.extend(script_paths)

    # Validate each referenced script
    seen_scripts = set()
    for event_name, script_path in all_script_paths:
        if script_path in seen_scripts:
            continue
        seen_scripts.add(script_path)

        # Check file exists
        exists_result = validate_script_exists(event_name, script_path)
        results.append(exists_result)

        if not exists_result.passed:
            continue

        # Check Python syntax
        syntax_result = validate_python_syntax(script_path)
        results.append(syntax_result)

        # Check imports
        imports_result = check_hook_imports(script_path, project_dir)
        results.append(imports_result)

    # Count issues
    issues = sum(1 for r in results if not r.passed)
    return results, issues


def format_output(results: list[CheckResult], issue_count: int) -> str:
    """Format results for display."""
    lines = []
    lines.append("LINE DOCTOR")
    lines.append("━" * 50)
    lines.append("")

    for result in results:
        icon = "✓" if result.passed else "✗"
        lines.append(f"  {icon} {result.message}")

        if result.details:
            for detail in result.details:
                lines.append(f"      {detail}")

    lines.append("")
    lines.append("━" * 50)

    if issue_count == 0:
        lines.append("✓ All checks passed")
    else:
        lines.append(f"✗ {issue_count} issue(s) found")
        lines.append("")
        lines.append("To fix orphaned configs:")
        lines.append("  1. Update paths in .claude/settings.json")
        lines.append("  2. Or remove unused hook configurations")

    return "\n".join(lines)


def main():
    """Main entry point."""
    results, issue_count = run_doctor()
    output = format_output(results, issue_count)
    print(output)

    # Exit with error code if issues found
    sys.exit(1 if issue_count > 0 else 0)


if __name__ == "__main__":
    main()
