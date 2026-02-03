# Python Scripting Best Practices

Research and patterns for Python automation scripts in AI agent workflows.

**Reference implementation**: `scripts/line-loop.py`

## When to Use

- Long-running automation scripts (daemons, loops)
- CLI tools with complex argument parsing
- Process management and subprocess orchestration
- Scripts requiring graceful shutdown handling

## Best Practices

### 1. Use Modern Python Features (3.9+)

```python
# Type hints with built-in generics (3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# Dataclasses for state containers
from dataclasses import dataclass, field

@dataclass
class Config:
    max_retries: int = 3
    timeout: int = 60
    items: list[str] = field(default_factory=list)
```

### 2. Subprocess Management

Always use `subprocess.run()` with explicit arguments:

```python
import subprocess
from pathlib import Path

def run_command(cmd: list[str], timeout: int, cwd: Path) -> subprocess.CompletedProcess:
    """Run subprocess with timeout and capture output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        # Log and handle timeout
        raise
```

**Key points:**
- Use list form for commands (avoids shell injection)
- Always set `timeout` for external commands
- Use `capture_output=True` for `stdout`/`stderr`
- Use `text=True` for string output (vs bytes)
- Check `returncode` - negative values indicate signal termination (POSIX)

### 3. Signal Handling for Graceful Shutdown

```python
import signal

_shutdown_requested = False

def _handle_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM/SIGHUP for graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True

# Register handlers (main thread only)
signal.signal(signal.SIGINT, _handle_shutdown)   # Ctrl+C
signal.signal(signal.SIGTERM, _handle_shutdown)  # kill command
signal.signal(signal.SIGHUP, _handle_shutdown)   # terminal hangup

# In main loop
while not _shutdown_requested:
    do_work()
```

**Key points:**
- Handlers run in main thread only
- Keep handlers minimal - set flag, don't do heavy work
- Never raise regular exceptions in handlers (use `BaseException` subclass if needed)
- For threads, main thread catches signal and notifies workers via Event/Queue

### 4. Argparse for CLI

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

    # Common patterns
    parser.add_argument("-n", "--max-iterations", type=int, default=25,
                        help="Maximum iterations (default: %(default)s)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON instead of human-readable")
    parser.add_argument("-o", "--output", type=Path,
                        help="Write output to file")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()
```

### 5. Logging with Rotation

```python
import logging
import logging.handlers
from pathlib import Path
from typing import Optional

def setup_logging(verbose: bool, log_file: Optional[Path] = None):
    """Configure logging with optional file rotation."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3
        ))

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )

logger = logging.getLogger('my-script')
```

### 6. Atomic File Operations

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

### 7. Retry Logic with Backoff

```python
import random
import time
from typing import Callable

def calculate_retry_delay(attempt: int, base: float = 2.0) -> float:
    """Exponential backoff with jitter: 2s, 4s, 8s... capped at 60s."""
    delay = min(base * (2 ** attempt), 60)
    return delay * random.uniform(0.8, 1.2)  # +/- 20% jitter

def retry_operation(operation: Callable, max_attempts: int = 3):
    """Retry operation with exponential backoff.

    Args:
        operation: Callable to retry on failure
        max_attempts: Maximum attempts before re-raising (default: 3)
    """
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = calculate_retry_delay(attempt)
            time.sleep(delay)
```

### 8. Circuit Breaker Pattern

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
        recent = self.window[-self.failure_threshold:]
        return sum(1 for s in recent if not s) >= self.failure_threshold
```

## Anti-Patterns to Avoid

### 1. Mutable Default Arguments

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

### 2. Missing Context Managers

```python
# BAD - file may not close on exception
f = open('file.txt')
data = f.read()
f.close()

# GOOD - automatic cleanup
with open('file.txt') as f:
    data = f.read()
```

### 3. Wildcard Imports

```python
# BAD - pollutes namespace, breaks static analysis
from os import *
from pathlib import *

# GOOD - explicit imports
from pathlib import Path
import os
```

### 4. Bare Exception Handling

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

### 5. Shell=True in Subprocess

```python
# BAD - vulnerable to shell injection
subprocess.run(f"ls {user_input}", shell=True)

# GOOD - use list form
subprocess.run(["ls", user_input])
```

### 6. String Path Manipulation

```python
# BAD - error-prone string concatenation
path = directory + "/" + filename

# GOOD - pathlib handles separators
from pathlib import Path
path = Path(directory) / filename
```

### 7. Print for Logging

```python
# BAD - no levels, timestamps, or file output
print(f"Error: {error}")

# GOOD - structured logging
logger.error(f"Operation failed: {error}", exc_info=True)
```

### 8. Blocking in Signal Handlers

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

### 9. Ignoring Return Codes

```python
# BAD - assumes success
result = subprocess.run(["git", "push"])

# GOOD - check return code
result = subprocess.run(["git", "push"], capture_output=True, text=True)
if result.returncode != 0:
    logger.error(f"Push failed: {result.stderr}")
```

### 10. Magic Numbers

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

## Sources

- [The Little Book of Python Anti-Patterns](https://docs.quantifiedcode.com/python-anti-patterns/)
- [Modern Good Practices for Python Development](https://www.stuartellis.name/articles/python-modern-practices/)
- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [Python signal documentation](https://docs.python.org/3/library/signal.html)
- [Signal Handling for Graceful Shutdowns](https://johal.in/signal-handling-in-python-custom-handlers-for-graceful-shutdowns/)
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
