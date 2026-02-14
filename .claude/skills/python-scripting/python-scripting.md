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

### Subprocess Management

**Key principles:**
- Use list form for commands (avoids shell injection)
- Always set `timeout` for external commands
- Use `capture_output=True` for `stdout`/`stderr`
- Use `text=True` for string output (vs bytes)
- Check `returncode` - negative values indicate signal termination (POSIX)

```python
# BAD - vulnerable to shell injection
subprocess.run(f"ls {user_input}", shell=True)

# GOOD - use list form
subprocess.run(["ls", user_input])

# Check return codes (assumes logger from Quick Reference above)
result = subprocess.run(["git", "push"], capture_output=True, text=True)
if result.returncode != 0:
    logger.error(f"Push failed: {result.stderr}")
```

### Signal Handling Details

**Key points:**
- Handlers run in main thread only
- Keep handlers minimal - set flag, don't do heavy work
- Never raise regular exceptions in handlers
- For threads, main thread catches signal and notifies workers via Event/Queue

```python
# BAD - heavy work in handler
def handler(sig, frame):
    save_all_state()  # May block
    cleanup_resources()  # May raise
    sys.exit(0)

# GOOD - set flag, handle in main loop
def handler(sig, frame):
    global _shutdown_requested
    _shutdown_requested = True

# In main loop
if _shutdown_requested:
    save_all_state()
    cleanup_resources()
    break
```

### Retry Logic with Backoff

```python
import random
import time
from typing import Callable

def retry_operation(operation: Callable, max_attempts: int = 3):
    """Retry operation with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception:
            if attempt == max_attempts - 1:
                raise
            delay = calculate_retry_delay(attempt)
            time.sleep(delay)
```

### Circuit Breaker Pattern

Stop after too many consecutive failures:

```python
from dataclasses import dataclass, field

@dataclass
class CircuitBreaker:
    """Stop after too many consecutive failures."""
    failure_threshold: int = 5
    window_size: int = 10
    window: list[bool] = field(default_factory=list)

    def record(self, success: bool):
        self.window.append(success)
        if len(self.window) > self.window_size:
            self.window.pop(0)

    def is_open(self) -> bool:
        """True if too many recent failures."""
        if len(self.window) < self.failure_threshold:
            return False
        return sum(1 for s in self.window if not s) >= self.failure_threshold
```

## Anti-Patterns

### Mutable Default Arguments

```python
# BAD - list is shared across calls
def add_item(item, items=[]):
    items.append(item)
    return items

# GOOD - use None and create new list
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# BEST - use dataclass field factory
@dataclass
class Container:
    items: list[str] = field(default_factory=list)
```

### Missing Context Managers

```python
# BAD - file may not close on exception
f = open('file.txt')
data = f.read()
f.close()

# GOOD - automatic cleanup
with open('file.txt') as f:
    data = f.read()
```

### Bare Exception Handling

```python
# BAD - catches everything including KeyboardInterrupt
try:
    do_something()
except:
    pass

# GOOD - catch specific exceptions
try:
    do_something()
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
except subprocess.TimeoutExpired:
    logger.error("Command timed out")
```

### Wildcard Imports

```python
# BAD - pollutes namespace, breaks static analysis
from os import *

# GOOD - explicit imports
from pathlib import Path
import os
```

### String Path Manipulation

```python
# BAD - error-prone string concatenation
path = directory + "/" + filename

# GOOD - pathlib handles separators
from pathlib import Path
path = Path(directory) / filename
```

### Print for Logging

```python
# BAD - no levels, timestamps, or file output
print(f"Error: {error}")

# GOOD - structured logging
logger.error(f"Operation failed: {error}", exc_info=True)
```

### Magic Numbers

```python
# BAD - unclear meaning
if retry_count > 5:
    timeout = 60

# GOOD - named constants
MAX_RETRIES = 5
MAX_TIMEOUT_SECONDS = 60

if retry_count > MAX_RETRIES:
    timeout = MAX_TIMEOUT_SECONDS
```

## Recommended Tools

- **ruff** - Fast linter and formatter (replaces black, isort, flake8)
- **mypy** - Static type checking
- **pytest** - Testing framework
- **structlog** / **loguru** - Enhanced logging

## See Also

- `plugins/claude-code/scripts/line-loop.py` - Reference implementation
- `AGENTS.md` - Line Cook documentation
