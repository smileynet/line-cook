#!/usr/bin/env python3
"""
Shared utilities for line-cook hooks.

Cross-platform compatible (Windows, Linux, macOS)
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


def get_log_path() -> Path:
    """Get path to hook log file."""
    # Use CLAUDE_PROJECT_DIR if available, otherwise ~/.claude/
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        log_dir = Path(project_dir) / ".claude"
    else:
        log_dir = Path.home() / ".claude"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "hooks.log"


def setup_logging(hook_name: str) -> logging.Logger:
    """Set up logging for a hook."""
    logger = logging.getLogger(f"line-cook.{hook_name}")
    logger.setLevel(logging.DEBUG)

    # Only add handler if not already present
    if not logger.handlers:
        try:
            log_path = get_log_path()
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except (OSError, PermissionError):
            # If we can't write to log, continue without logging
            pass

    return logger


def log_hook_start(logger: logging.Logger, input_data: dict) -> None:
    """Log hook execution start."""
    session_id = input_data.get("session_id", "unknown")
    tool_name = input_data.get("tool_name", "N/A")
    logger.info(f"START | session={session_id} | tool={tool_name}")


def log_hook_end(logger: logging.Logger, exit_code: int, message: str = "") -> None:
    """Log hook execution end."""
    status = "ALLOW" if exit_code == 0 else "BLOCK" if exit_code == 2 else "ERROR"
    logger.info(f"END | status={status} | exit={exit_code} | {message}")


def read_hook_input() -> dict:
    """Read and parse JSON input from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def output_json(data: dict) -> None:
    """Output JSON to stdout for Claude to consume."""
    print(json.dumps(data))
