---
name: python-scripting
description: Python scripting patterns for agent automation scripts. Use when writing or maintaining Python scripts that integrate with Claude Code, managing subprocess calls, handling signals, or working with argparse patterns.
---

# Python Scripting for Agent Scripts

Best practices and patterns for Python scripts in AI agent workflows.

## When to Use

- Writing automation scripts (like line-loop.py)
- Managing subprocess calls to claude/opencode CLI
- Signal handling for graceful shutdown
- Argparse patterns for CLI scripts
- File watching and process management

## Quick Reference

### Subprocess with Timeout

```python
import subprocess
from pathlib import Path

def run_subprocess(cmd: list[str], timeout: int, cwd: Path) -> subprocess.CompletedProcess:
    """Run subprocess with logging and timeout handling."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return result
    except subprocess.TimeoutExpired:
        # Handle timeout - log, retry, or raise
        raise
```

### Signal Handling for Graceful Shutdown

```python
import signal

_shutdown_requested = False

def _handle_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True

signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGHUP, _handle_shutdown)

# In main loop:
while not _shutdown_requested:
    # ... do work ...
```

### Dataclass for State Containers

```python
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class IterationResult:
    """Result of a single loop iteration."""
    iteration: int
    task_id: Optional[str]
    outcome: str  # "completed", "timeout", "error"
    duration_seconds: float
    success: bool
    actions: list[Any] = field(default_factory=list)  # e.g., list of ActionRecord

    @property
    def action_counts(self) -> dict[str, int]:
        """Count actions by tool name."""
        counts: dict[str, int] = {}
        for action in self.actions:
            counts[action.tool_name] = counts.get(action.tool_name, 0) + 1
        return counts
```

### Argparse for CLI Scripts

```python
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Script description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --max-iterations 10
  %(prog)s --json --output report.json
"""
    )

    parser.add_argument("-n", "--max-iterations", type=int, default=25)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
```

### Logging with Rotation

```python
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

def setup_logging(verbose: bool, log_file: Optional[Path] = None):
    """Configure logging with optional file output and rotation."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3
        ))

    logging.basicConfig(level=level, format='%(asctime)s [%(levelname)s] %(message)s', handlers=handlers)

logger = logging.getLogger('my-script')
```

### Atomic File Writes

```python
from pathlib import Path

def atomic_write(path: Path, content: str) -> None:
    """Write file atomically via temp file + rename."""
    tmp = path.with_suffix(path.suffix + '.tmp')
    try:
        tmp.write_text(content)
        tmp.replace(path)  # atomic on POSIX
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
```

### Exponential Backoff with Jitter

```python
import random

def calculate_retry_delay(attempt: int, base: float = 2.0) -> float:
    """Exponential backoff with jitter: 2s, 4s, 8s... capped at 60s."""
    delay = min(base * (2 ** attempt), 60)
    return delay * random.uniform(0.8, 1.2)  # ±20% jitter
```

## Topics

<!-- lc-hhv.3: Fill in topic sections -->

## See Also

- `scripts/line-loop.py` - Reference implementation
- `AGENTS.md` - Line Cook documentation
