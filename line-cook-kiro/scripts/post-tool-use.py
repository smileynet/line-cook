#!/usr/bin/env python3
"""
line-cook PostToolUse hook for Edit/Write tools (Kiro CLI version).
Auto-formats edited files based on extension.

Cross-platform compatible (Windows, Linux, macOS)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from hook_utils import (
    log_hook_end,
    log_hook_start,
    output_json,
    read_hook_input,
    setup_logging,
)

# Formatter configurations: extension -> list of (formatter, args)
# Each formatter is tried in order; first available one is used
FORMATTERS = {
    ".py": [
        ("ruff", ["format", "{file}"]),
        ("ruff", ["check", "--fix", "{file}"]),
        ("black", ["{file}"]),
    ],
    ".ts": [
        ("prettier", ["--write", "{file}"]),
        ("biome", ["format", "--write", "{file}"]),
    ],
    ".tsx": [
        ("prettier", ["--write", "{file}"]),
        ("biome", ["format", "--write", "{file}"]),
    ],
    ".js": [
        ("prettier", ["--write", "{file}"]),
        ("biome", ["format", "--write", "{file}"]),
    ],
    ".jsx": [
        ("prettier", ["--write", "{file}"]),
        ("biome", ["format", "--write", "{file}"]),
    ],
    ".mjs": [("prettier", ["--write", "{file}"])],
    ".cjs": [("prettier", ["--write", "{file}"])],
    ".json": [("prettier", ["--write", "{file}"])],
    ".yaml": [("prettier", ["--write", "{file}"])],
    ".yml": [("prettier", ["--write", "{file}"])],
    ".md": [("prettier", ["--write", "{file}"])],
    ".go": [("goimports", ["-w", "{file}"]), ("gofmt", ["-w", "{file}"])],
    ".rs": [("rustfmt", ["{file}"])],
    ".sh": [("shfmt", ["-w", "{file}"])],
    ".bash": [("shfmt", ["-w", "{file}"])],
    ".rb": [("rubocop", ["-a", "{file}"])],
    ".gd": [("gdformat", ["{file}"])],
}

# Additional linters to run after formatting
LINTERS = {
    ".sh": [("shellcheck", ["{file}"])],
    ".bash": [("shellcheck", ["{file}"])],
}

# Sensitive paths to skip formatting
SENSITIVE_PATTERNS = [
    ".env",
    ".git/",
    ".ssh/",
    "id_rsa",
    "id_ed25519",
    ".pem",
    "credentials",
    "secrets",
    ".key",
]


def is_path_safe(file_path: str) -> bool:
    """Check if path is safe (no traversal, not sensitive)."""
    # Normalize path
    try:
        normalized = os.path.normpath(file_path)
        resolved = os.path.realpath(file_path)
    except (OSError, ValueError):
        return False

    # Check for path traversal attempts
    if ".." in normalized:
        return False

    # Check for sensitive paths
    path_lower = resolved.lower()
    for pattern in SENSITIVE_PATTERNS:
        if pattern in path_lower:
            return False

    return True


def find_executable(name: str) -> str | None:
    """Find executable in PATH, cross-platform."""
    return shutil.which(name)


def run_tool(tool: str, args: list[str], file_path: str) -> dict:
    """Run a formatter/linter tool on a file. Returns result dict."""
    executable = find_executable(tool)
    if not executable:
        return {"tool": tool, "status": "not_found"}

    # Substitute {file} placeholder
    cmd_args = [arg.replace("{file}", file_path) for arg in args]

    try:
        result = subprocess.run(
            [executable] + cmd_args,
            check=False,
            capture_output=True,
            timeout=30,
            text=True,
        )
        return {
            "tool": tool,
            "status": "success" if result.returncode == 0 else "error",
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"tool": tool, "status": "timeout"}
    except subprocess.SubprocessError as e:
        return {"tool": tool, "status": "error", "error": str(e)}


def format_file(file_path: str) -> dict:
    """Format a file based on its extension. Returns results dict."""
    path = Path(file_path)
    ext = path.suffix.lower()
    results = {
        "file": file_path,
        "extension": ext,
        "formatters": [],
        "linters": [],
    }

    # Run formatters - stop after first successful one
    formatters = FORMATTERS.get(ext, [])
    for tool, args in formatters:
        result = run_tool(tool, args, file_path)
        results["formatters"].append(result)
        if result["status"] == "success":
            break

    # Run linters
    linters = LINTERS.get(ext, [])
    for tool, args in linters:
        result = run_tool(tool, args, file_path)
        results["linters"].append(result)

    return results


def main():
    logger = setup_logging("post_tool_use")

    input_data = read_hook_input()
    if not input_data:
        log_hook_end(logger, 0, "invalid JSON input")
        sys.exit(0)

    log_hook_start(logger, input_data)

    # Only process Edit and Write tools
    tool_name = input_data.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        log_hook_end(logger, 0, f"skipping tool: {tool_name}")
        sys.exit(0)

    # Get file path from tool input
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Skip if no file path
    if not file_path:
        log_hook_end(logger, 0, "no file path")
        sys.exit(0)

    # Skip non-existent files
    if not os.path.isfile(file_path):
        log_hook_end(logger, 0, f"file not found: {file_path}")
        sys.exit(0)

    # Skip unsafe paths (traversal attempts, sensitive files)
    if not is_path_safe(file_path):
        log_hook_end(logger, 0, f"unsafe path skipped: {file_path}")
        sys.exit(0)

    # Format the file and get results
    results = format_file(file_path)

    # Output JSON for Kiro feedback (only if tools ran)
    if results["formatters"] or results["linters"]:
        successful = [
            r["tool"]
            for r in results["formatters"] + results["linters"]
            if r["status"] == "success"
        ]
        if successful:
            output_json(
                {
                    "additionalContext": f"Auto-formatted with: {', '.join(successful)}",
                }
            )
            log_hook_end(logger, 0, f"formatted with: {', '.join(successful)}")
        else:
            log_hook_end(logger, 0, "no formatters succeeded")
    else:
        log_hook_end(logger, 0, f"no formatters for {Path(file_path).suffix}")

    sys.exit(0)


if __name__ == "__main__":
    main()
