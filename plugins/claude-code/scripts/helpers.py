"""Shared helpers for Line Cook scripts.

Provides validate_bead_id, run_cmd, and run_bd_json to avoid duplication
across helper scripts.
"""

import json
import re
import subprocess


def validate_bead_id(bid):
    """Validate bead ID format to prevent malformed input in subprocess calls."""
    return bool(bid and re.match(r'^[a-zA-Z0-9._-]+$', bid))


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
    rc, out, _ = run_cmd(full_args, timeout=timeout)
    if rc != 0 or not out:
        return None
    try:
        data = json.loads(out)
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return data
    except (json.JSONDecodeError, TypeError):
        return None
