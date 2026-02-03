#!/usr/bin/env python3
# Requires Python 3.9+ for dataclasses and type hints (list[str] syntax)
"""Line Cook autonomous loop - runs individual phase skills until no tasks remain.

Provides robust feedback through bead state tracking and SERVE_RESULT parsing.

Platform Support:
    Linux, macOS, WSL - Fully supported
    Windows - NOT supported (select.select() requires Unix file descriptors)

Data Flow Architecture:
    BeadSnapshot - Captures ready/in_progress/closed task IDs at a point in time.
                   Used for before/after comparison to detect which task was worked on.

    ServeResult - Parses the SERVE_RESULT block from claude output to extract
                  verdict (APPROVED/NEEDS_CHANGES/BLOCKED/SKIPPED) and continuation flags.

    IterationResult - Tracks a single loop iteration including task ID, outcome,
                      duration, serve verdict, commit hash, and bead state changes.

    LoopReport - Aggregates all iteration results into a final summary with
                 completed/failed counts, total duration, and stop reason.
"""

import argparse
import json
import logging
import logging.handlers
import os
import random
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# Constants - Configuration values extracted for clarity and maintainability
# See docs/guidance/python-scripting.md for naming conventions

# Output and display limits
OUTPUT_SUMMARY_MAX_LENGTH = 200
INPUT_SUMMARY_FILE_PATH_LENGTH = 100
INPUT_SUMMARY_COMMAND_LENGTH = 80
INPUT_SUMMARY_PATTERN_LENGTH = 60
GOAL_TEXT_MAX_LENGTH = 200
BANNER_MIN_WIDTH = 62

# Task and iteration defaults
DEFAULT_MAX_TASK_FAILURES = 3       # Skip task after this many failures
DEFAULT_MAX_ITERATIONS = 25         # Default loop iterations
DEFAULT_IDLE_TIMEOUT = 180          # 3 minutes without tool actions triggers idle
DEFAULT_IDLE_ACTION = "warn"        # "warn" or "terminate"

# Subprocess timeouts (in seconds)
BD_COMMAND_TIMEOUT = 30             # Standard bd command timeout
GIT_COMMAND_TIMEOUT = 10            # Short git commands (log, show)
GIT_SYNC_TIMEOUT = 60               # Longer git operations (fetch, pull)
DEFAULT_FALLBACK_PHASE_TIMEOUT = 600  # Fallback for unknown phases

# Logging configuration
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB max per log file
LOG_FILE_BACKUP_COUNT = 3              # Keep 3 backup files

# Retry and backoff configuration
MAX_RETRY_DELAY_SECONDS = 60        # Cap for exponential backoff
CIRCUIT_BREAKER_WINDOW_SIZE = 10    # Sliding window for failure tracking

# History and status tracking
RECENT_ITERATIONS_LIMIT = 10        # Iterations to consider for analysis
RECENT_ITERATIONS_DISPLAY = 5       # Iterations to show in status/reports
CLOSED_TASKS_QUERY_LIMIT = 10       # Limit for closed tasks query

# Default phase timeouts (in seconds) - can be overridden via CLI
DEFAULT_PHASE_TIMEOUTS = {
    'cook': 1200,   # 20 min - Main work phase: TDD cycle, file edits, test runs
    'serve': 600,   # 10 min - Code review by sous-chef subagent
    'tidy': 240,    # 4 min - Commit, bd sync, git push
    'plate': 600,   # 10 min - BDD review via maître, acceptance doc
}

# Module-level logger
logger = logging.getLogger('line-loop')

# Global flag for graceful shutdown
_shutdown_requested = False


def _handle_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM/SIGHUP for graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True
    logger.info(f"Shutdown requested (signal {signum})")


# Register signal handlers
signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGHUP, _handle_shutdown)  # Common daemon restart signal


def setup_logging(verbose: bool, log_file: Optional[Path] = None):
    """Configure logging with optional file output and rotation."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        # Use RotatingFileHandler to prevent unbounded disk usage
        handlers.append(logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT
        ))
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )


def atomic_write(path: Path, content: str) -> None:
    """Write file atomically via temp file + rename.

    This prevents partial reads by external processes (like monitors).
    The rename operation is atomic on POSIX systems.
    """
    tmp = path.with_suffix(path.suffix + '.tmp')
    try:
        tmp.write_text(content)
        tmp.replace(path)  # atomic on POSIX
    except Exception:
        # Clean up temp file on any failure
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def calculate_retry_delay(attempt: int, base: float = 2.0) -> float:
    """Exponential backoff with jitter: 2s, 4s, 8s... capped at MAX_RETRY_DELAY_SECONDS."""
    delay = min(base * (2 ** attempt), MAX_RETRY_DELAY_SECONDS)
    return delay * random.uniform(0.8, 1.2)  # ±20% jitter


@dataclass
class CircuitBreaker:
    """Stops loop after too many consecutive failures."""
    failure_threshold: int = 5
    window_size: int = CIRCUIT_BREAKER_WINDOW_SIZE
    window: list = field(default_factory=list)

    def record(self, success: bool):
        """Record a result (True=success, False=failure)."""
        self.window.append(success)
        if len(self.window) > self.window_size:
            self.window.pop(0)

    def is_open(self) -> bool:
        """Check if circuit breaker has tripped (too many failures)."""
        if len(self.window) < self.failure_threshold:
            return False
        recent_failures = sum(1 for s in self.window[-self.failure_threshold:] if not s)
        return recent_failures >= self.failure_threshold

    def reset(self):
        """Reset the circuit breaker."""
        self.window.clear()


@dataclass
class LoopError:
    """Structured error with context for debugging and logging.

    Captures rich context when errors occur during loop execution, making it
    easier to diagnose issues without losing important details. Follows the
    patterns from docs/guidance/python-scripting.md.

    Attributes:
        error_type: Category of error (timeout, json_decode, subprocess, io, unknown)
        message: Human-readable error description
        context: Additional context as key-value pairs (task_id, command, etc.)
        original: The original exception, if any
        timestamp: When the error occurred
    """
    error_type: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    original: Optional[Exception] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        """Format error for logging."""
        parts = [f"[{self.error_type}] {self.message}"]
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"({ctx_str})")
        if self.original:
            parts.append(f"cause: {type(self.original).__name__}: {self.original}")
        return " ".join(parts)

    @classmethod
    def from_timeout(cls, cmd: str, timeout: int, task_id: Optional[str] = None) -> "LoopError":
        """Create error for subprocess timeout."""
        ctx: dict[str, Any] = {"command": cmd, "timeout_seconds": timeout}
        if task_id:
            ctx["task_id"] = task_id
        return cls(
            error_type="timeout",
            message=f"Command timed out after {timeout}s",
            context=ctx
        )

    @classmethod
    def from_json_decode(cls, source: str, exc: json.JSONDecodeError,
                         task_id: Optional[str] = None) -> "LoopError":
        """Create error for JSON parsing failure."""
        ctx: dict[str, Any] = {"source": source, "position": exc.pos}
        if task_id:
            ctx["task_id"] = task_id
        return cls(
            error_type="json_decode",
            message=f"Failed to parse JSON from {source}",
            context=ctx,
            original=exc
        )

    @classmethod
    def from_subprocess(cls, cmd: str, returncode: int, stderr: str,
                        task_id: Optional[str] = None) -> "LoopError":
        """Create error for subprocess failure."""
        ctx: dict[str, Any] = {"command": cmd, "returncode": returncode}
        if stderr:
            ctx["stderr"] = stderr[:200]  # Truncate long stderr
        if task_id:
            ctx["task_id"] = task_id
        return cls(
            error_type="subprocess",
            message=f"Command failed with exit code {returncode}",
            context=ctx
        )

    @classmethod
    def from_io(cls, operation: str, path: Path, exc: Exception) -> "LoopError":
        """Create error for file I/O failure."""
        return cls(
            error_type="io",
            message=f"I/O error during {operation}",
            context={"path": str(path)},
            original=exc
        )


@dataclass
class SkipList:
    """Tracks tasks to skip due to repeated failures.

    When a task fails repeatedly (hitting max_failures), it gets added to a skip
    list so the loop doesn't keep retrying it. This prevents retry spirals where
    the same failing task burns through all iterations.
    """
    failed_tasks: dict[str, int] = field(default_factory=dict)
    max_failures: int = DEFAULT_MAX_TASK_FAILURES

    def record_failure(self, task_id: Optional[str]) -> bool:
        """Record a task failure.

        Args:
            task_id: The ID of the failed task

        Returns:
            True if the task has now hit the skip threshold and should be skipped
        """
        if not task_id:
            return False
        self.failed_tasks[task_id] = self.failed_tasks.get(task_id, 0) + 1
        return self.failed_tasks[task_id] >= self.max_failures

    def record_success(self, task_id: Optional[str]):
        """Clear failure count for a task on success."""
        if task_id:
            self.failed_tasks.pop(task_id, None)

    def is_skipped(self, task_id: Optional[str]) -> bool:
        """Check if a task should be skipped due to repeated failures."""
        if not task_id:
            return False
        return self.failed_tasks.get(task_id, 0) >= self.max_failures

    def get_skipped_ids(self) -> set[str]:
        """Get set of task IDs that should be skipped."""
        return {tid for tid, count in self.failed_tasks.items()
                if count >= self.max_failures}

    def get_skipped_tasks(self) -> list[dict]:
        """Get list of skipped tasks with their failure counts."""
        return [
            {"id": tid, "failure_count": count}
            for tid, count in self.failed_tasks.items()
            if count >= self.max_failures
        ]


def check_health(cwd: Path) -> dict:
    """Verify environment before starting loop."""
    checks = {
        'claude_cli': shutil.which('claude') is not None,
        'bd_cli': shutil.which('bd') is not None,
        'git_repo': (cwd / '.git').exists(),
        'beads_init': (cwd / '.beads').exists(),
    }
    return {'healthy': all(checks.values()), 'checks': checks}


@dataclass
class LoopMetrics:
    """Computed metrics for the loop run."""
    success_rate: float
    p50_duration: float
    p95_duration: float
    timeout_rate: float
    retry_rate: float

    @classmethod
    def from_iterations(cls, iterations: list) -> 'LoopMetrics':
        """Compute metrics from iteration results."""
        if not iterations:
            return cls(0.0, 0.0, 0.0, 0.0, 0.0)

        total = len(iterations)
        successes = sum(1 for i in iterations if i.success)
        timeouts = sum(1 for i in iterations if i.outcome == 'timeout')
        retries = sum(1 for i in iterations if i.outcome == 'needs_retry')

        durations = sorted(i.duration_seconds for i in iterations)
        p50_idx = int(len(durations) * 0.5)
        p95_idx = min(int(len(durations) * 0.95), len(durations) - 1)

        return cls(
            success_rate=successes / total if total else 0.0,
            p50_duration=durations[p50_idx] if durations else 0.0,
            p95_duration=durations[p95_idx] if durations else 0.0,
            timeout_rate=timeouts / total if total else 0.0,
            retry_rate=retries / total if total else 0.0
        )


@dataclass
class BeadSnapshot:
    """State of beads at a point in time."""
    ready_ids: list[str] = field(default_factory=list)
    ready_work_ids: list[str] = field(default_factory=list)  # Tasks + features (not epics)
    in_progress_ids: list[str] = field(default_factory=list)
    closed_ids: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ServeResult:
    """Parsed SERVE_RESULT block from claude output."""
    verdict: str  # APPROVED, NEEDS_CHANGES, BLOCKED, SKIPPED
    continue_: bool
    next_step: Optional[str]
    blocking_issues: int


@dataclass
class ServeFeedbackIssue:
    """A single issue from serve review feedback."""
    severity: str  # critical, major, minor, nit
    location: Optional[str]  # file:line or description
    problem: str
    suggestion: Optional[str]


@dataclass
class ServeFeedback:
    """Structured feedback from serve phase for cook retry.

    When NEEDS_CHANGES is returned, this captures the issues found
    so cook can prioritize addressing them on retry.
    """
    verdict: str
    summary: str
    issues: list[ServeFeedbackIssue] = field(default_factory=list)
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    attempt: int = 1


@dataclass
class PhaseResult:
    """Result from running a single workflow phase (cook, serve, tidy, plate)."""
    phase: str           # cook, serve, tidy, plate
    success: bool        # True if phase completed without error
    output: str          # Full output from the phase
    exit_code: int       # Process exit code
    duration_seconds: float
    signals: list[str] = field(default_factory=list)  # Detected signals (KITCHEN_COMPLETE, etc.)
    actions: list = field(default_factory=list)  # ActionRecords from this phase
    error: Optional[str] = None  # Error message if failed
    early_completion: bool = False  # True if phase emitted phase_complete signal


@dataclass
class ActionRecord:
    """Record of a single tool call during an iteration."""
    tool_name: str           # "Read", "Edit", "Bash", etc.
    tool_use_id: str         # For correlation with results
    input_summary: str       # Truncated input (file path, command, etc.)
    output_summary: str      # Truncated output or error message
    success: bool            # True if no error
    timestamp: str           # ISO timestamp

    @classmethod
    def from_tool_use(cls, block: dict) -> 'ActionRecord':
        """Create ActionRecord from a tool_use content block."""
        tool_name = block.get("name", "unknown")
        tool_input = block.get("input", {})
        return cls(
            tool_name=tool_name,
            tool_use_id=block.get("id", ""),
            input_summary=summarize_tool_input(tool_name, tool_input),
            output_summary="",  # Filled in when tool_result arrives
            success=True,       # Updated when tool_result arrives
            timestamp=datetime.now().isoformat()
        )


def summarize_tool_input(tool_name: str, input_data: dict) -> str:
    """Create concise summary of tool input."""
    if tool_name == "Read":
        return input_data.get("file_path", "")[:INPUT_SUMMARY_FILE_PATH_LENGTH]
    elif tool_name == "Edit":
        path = input_data.get("file_path", "")
        return f"{path} (edit)"[:INPUT_SUMMARY_FILE_PATH_LENGTH]
    elif tool_name == "Bash":
        cmd = input_data.get("command", "")
        return cmd[:INPUT_SUMMARY_COMMAND_LENGTH] + ("..." if len(cmd) > INPUT_SUMMARY_COMMAND_LENGTH else "")
    elif tool_name == "Write":
        return f"{input_data.get('file_path', '')} (new)"[:INPUT_SUMMARY_FILE_PATH_LENGTH]
    elif tool_name in ("Glob", "Grep"):
        return input_data.get("pattern", "")[:INPUT_SUMMARY_PATTERN_LENGTH]
    elif tool_name == "Task":
        desc = input_data.get("description", "")
        return f"Task: {desc}"[:INPUT_SUMMARY_COMMAND_LENGTH]
    else:
        summary = str(input_data)
        return summary[:INPUT_SUMMARY_COMMAND_LENGTH] + ("..." if len(summary) > INPUT_SUMMARY_COMMAND_LENGTH else "")


@dataclass
class IterationResult:
    """Result of a single loop iteration."""
    iteration: int
    task_id: Optional[str]
    task_title: Optional[str]
    outcome: str  # "completed", "needs_retry", "blocked", "crashed", "timeout", "no_work", "no_actionable_work"
    duration_seconds: float
    serve_verdict: Optional[str]
    commit_hash: Optional[str]
    success: bool

    # Before/after state for transparency
    before_ready: int = 0
    before_in_progress: int = 0
    after_ready: int = 0
    after_in_progress: int = 0

    # Intent extracted from cook output
    intent: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None

    # Action tracking (tool calls during iteration)
    actions: list[ActionRecord] = field(default_factory=list)

    @property
    def action_counts(self) -> dict[str, int]:
        """Count actions by tool name."""
        counts: dict[str, int] = {}
        for action in self.actions:
            counts[action.tool_name] = counts.get(action.tool_name, 0) + 1
        return counts

    @property
    def total_actions(self) -> int:
        """Total number of tool calls."""
        return len(self.actions)


@dataclass
class LoopReport:
    """Final report for the entire loop run."""
    started_at: str
    ended_at: str
    iterations: list[IterationResult]
    stop_reason: str  # "no_work", "no_actionable_work", "max_iterations", "blocked", "error", "crashed", "epic_complete"
    completed_count: int
    failed_count: int
    duration_seconds: float


@dataclass
class ProgressState:
    """Tracks progress for intra-iteration status updates.

    Enables real-time visibility into loop progress during long-running phases.
    Status updates are throttled to max 1 write per 5 seconds to avoid I/O overhead.

    Fields written to status.json:
        current_phase: The currently executing phase (cook, serve, tidy, plate)
        phase_start_time: When the current phase started
        current_action_count: Number of tool actions in current phase
        last_action_time: Timestamp of most recent tool action
        idle_detected: True if phase has been idle beyond threshold
        idle_since: Timestamp when idle was first detected
    """
    status_file: Optional[Path]
    iteration: int
    max_iterations: int
    current_task: Optional[str]
    current_task_title: Optional[str]
    tasks_completed: int
    tasks_remaining: int
    started_at: datetime
    iterations: list

    # Intra-iteration progress fields
    current_phase: Optional[str] = None
    phase_start_time: Optional[datetime] = None
    current_action_count: int = 0
    last_action_time: Optional[datetime] = None
    _last_write: float = 0.0  # Throttle to 1 write per 5 seconds

    # Idle detection fields
    idle_detected: bool = False
    idle_since: Optional[datetime] = None

    def start_phase(self, phase: str):
        """Mark the start of a new phase."""
        self.current_phase = phase
        self.phase_start_time = datetime.now()
        self.current_action_count = 0
        self._write_status()
        self._last_write = time.time()  # Reset throttle after phase start write

    def update_progress(self, action_count: int, last_action_time: str):
        """Called when new actions are detected during phase execution.

        Args:
            action_count: Total actions so far in current phase
            last_action_time: ISO timestamp of the most recent action
        """
        self.current_action_count = action_count
        try:
            self.last_action_time = datetime.fromisoformat(last_action_time)
        except (ValueError, TypeError):
            # Malformed timestamp - fall back to current time
            self.last_action_time = datetime.now()
        # Throttle writes to max 1 per 5 seconds
        if time.time() - self._last_write >= 5.0:
            self._write_status()
            self._last_write = time.time()

    def _write_status(self):
        """Write current progress to status file."""
        if not self.status_file:
            return
        write_status_file(
            status_file=self.status_file,
            running=True,
            iteration=self.iteration,
            max_iterations=self.max_iterations,
            current_task=self.current_task,
            current_task_title=self.current_task_title,
            last_verdict=None,  # Not known during phase execution
            tasks_completed=self.tasks_completed,
            tasks_remaining=self.tasks_remaining,
            started_at=self.started_at,
            iterations=self.iterations,
            current_phase=self.current_phase,
            phase_start_time=self.phase_start_time,
            current_action_count=self.current_action_count,
            last_action_time=self.last_action_time
        )


def check_idle(last_action_time: Optional[datetime], idle_timeout: int) -> bool:
    """Check if the phase has been idle beyond the threshold.

    Args:
        last_action_time: Timestamp of the most recent tool action, or None if no actions yet
        idle_timeout: Seconds without actions before considered idle

    Returns:
        True if idle beyond threshold, False otherwise
    """
    if last_action_time is None:
        return False  # No actions yet, not considered idle
    idle_seconds = (datetime.now() - last_action_time).total_seconds()
    return idle_seconds >= idle_timeout


def run_subprocess(cmd: list, timeout: int, cwd: Path) -> subprocess.CompletedProcess:
    """Run subprocess with logging."""
    logger.debug(f"Running: {' '.join(cmd)} (timeout={timeout}s)")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        logger.debug(f"Completed in {time.time()-start:.1f}s, exit={result.returncode}")
        return result
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout after {timeout}s: {' '.join(cmd)}")
        raise


def get_next_ready_task(cwd: Path, skip_ids: Optional[set[str]] = None) -> Optional[tuple[str, str]]:
    """Get the next ready task ID and title before cook runs.

    Mimics cook.md selection: highest priority work item (not epic).
    This allows logging the target task before the cook phase runs,
    which is useful for debugging when cook fails or times out.

    Args:
        cwd: Working directory
        skip_ids: Optional set of task IDs to skip (due to repeated failures)

    Returns:
        Tuple of (task_id, task_title) or None if no tasks ready
    """
    skip_ids = skip_ids or set()
    cmd = "bd ready --json"
    try:
        result = run_subprocess(["bd", "ready", "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            for issue in issues:
                if isinstance(issue, dict):
                    issue_id = issue.get("id", "")
                    issue_type = issue.get("type", "")
                    # Skip epics (they're not directly workable)
                    # Skip issues that are in the skip list
                    if issue_type != "epic" and issue_id and issue_id not in skip_ids:
                        return (issue_id, issue.get("title", ""))
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode("bd ready output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting next ready task: {e}")
    return None


def get_bead_snapshot(cwd: Path) -> BeadSnapshot:
    """Capture ready/in_progress/closed issue IDs via bd --json."""
    snapshot = BeadSnapshot()

    # Get all ready items and filter work items (tasks + features, not epics)
    cmd_ready = "bd ready --json"
    try:
        result = run_subprocess(["bd", "ready", "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.ready_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
            # Filter work items (exclude epics) from the same parsed data
            snapshot.ready_work_ids = [
                i.get("id", "") for i in issues
                if isinstance(i, dict) and i.get("type") != "epic"
            ]
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd_ready, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode("bd ready output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting ready items: {e}")

    # Get in_progress tasks
    cmd_in_progress = "bd list --status=in_progress --json"
    try:
        result = run_subprocess(["bd", "list", "--status=in_progress", "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.in_progress_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd_in_progress, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode("bd list in_progress output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting in_progress tasks: {e}")

    # Get recently closed tasks (limited for performance)
    cmd_closed = f"bd list --status=closed --limit={CLOSED_TASKS_QUERY_LIMIT} --json"
    try:
        result = run_subprocess(["bd", "list", "--status=closed", f"--limit={CLOSED_TASKS_QUERY_LIMIT}", "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.closed_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd_closed, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode("bd list closed output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting closed tasks: {e}")

    return snapshot


def parse_serve_result(output: str) -> Optional[ServeResult]:
    """Parse SERVE_RESULT block from claude output."""
    # Look for the SERVE_RESULT block
    pattern = r"SERVE_RESULT\s*\n(?:│\s*)?verdict:\s*(\w+).*?(?:│\s*)?continue:\s*(true|false).*?(?:│\s*)?(?:next_step:\s*(\S+))?.*?(?:│\s*)?blocking_issues:\s*(\d+)"
    match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)

    if match:
        return ServeResult(
            verdict=match.group(1).upper(),
            continue_=match.group(2).lower() == "true",
            next_step=match.group(3),
            blocking_issues=int(match.group(4))
        )

    # Try simpler patterns for each field
    verdict_match = re.search(r"verdict:\s*(APPROVED|NEEDS_CHANGES|BLOCKED|SKIPPED)", output, re.IGNORECASE)
    if verdict_match:
        continue_match = re.search(r"continue:\s*(true|false)", output, re.IGNORECASE)
        blocking_match = re.search(r"blocking_issues:\s*(\d+)", output, re.IGNORECASE)
        next_step_match = re.search(r"next_step:\s*(\S+)", output, re.IGNORECASE)

        return ServeResult(
            verdict=verdict_match.group(1).upper(),
            continue_=continue_match.group(1).lower() == "true" if continue_match else True,
            next_step=next_step_match.group(1) if next_step_match else None,
            blocking_issues=int(blocking_match.group(1)) if blocking_match else 0
        )

    return None


def parse_serve_feedback(output: str, task_id: Optional[str] = None, task_title: Optional[str] = None, attempt: int = 1) -> Optional[ServeFeedback]:
    """Parse detailed feedback from serve output for retry context.

    Extracts:
    - Summary from the "Summary:" section
    - Issues from "Issues to file" or issue list sections
    - Severity markers like [critical], [major], [minor], [nit], [P1], [P2], etc.

    Returns ServeFeedback or None if parsing fails.
    """
    # Extract summary - look for Summary: section
    summary = ""
    summary_match = re.search(
        r"Summary:\s*\n\s*(.+?)(?:\n\n|\nAuto-fixed:|\nIssues|\nPositive)",
        output,
        re.DOTALL | re.IGNORECASE
    )
    if summary_match:
        summary = summary_match.group(1).strip()

    # Extract issues - look for various patterns
    issues: list[ServeFeedbackIssue] = []

    # Pattern 1: Issues to file in /tidy section with severity markers
    # e.g., "- [P1] "title" - description" or "- [major] file:line - issue"
    issue_section_match = re.search(
        r"Issues to file[^\n]*:\s*\n((?:\s*-[^\n]+\n?)+)",
        output,
        re.IGNORECASE
    )

    # Pattern 2: Issues found section from sous-chef
    # e.g., "Issues found:\n  - Severity: major\n    File/line: src/foo.py:42\n    Issue: desc"
    issues_found_match = re.search(
        r"Issues found:\s*\n((?:.*?\n)+?)(?:\n\n|Positive|$)",
        output,
        re.DOTALL | re.IGNORECASE
    )

    # Parse simple issue list (Pattern 1)
    if issue_section_match:
        issue_text = issue_section_match.group(1)
        # Match lines like: - [P1] "title" - description or - [major] description
        issue_pattern = re.compile(
            r'-\s*\[([^\]]+)\]\s*(?:"([^"]+)"\s*-\s*)?(.+?)(?=\n\s*-|\n\n|$)',
            re.MULTILINE | re.DOTALL
        )
        for match in issue_pattern.finditer(issue_text):
            severity_raw = match.group(1).lower()
            # Normalize severity: P1/P2 -> major, P3 -> minor, P4 -> nit
            if severity_raw in ('p1', 'p2', 'critical'):
                severity = 'critical' if severity_raw in ('p1', 'critical') else 'major'
            elif severity_raw in ('p3', 'minor'):
                severity = 'minor'
            elif severity_raw in ('p4', 'nit', 'retro'):
                severity = 'nit'
            else:
                severity = severity_raw

            title = match.group(2)
            description = match.group(3).strip()

            issues.append(ServeFeedbackIssue(
                severity=severity,
                location=title,  # Use title as location hint
                problem=description,
                suggestion=None
            ))

    # Parse detailed issue format (Pattern 2) from sous-chef
    if issues_found_match and not issues:
        issue_text = issues_found_match.group(1)
        # Look for structured issue blocks
        severity_matches = re.findall(
            r"Severity:\s*(\w+).*?(?:File/line:|Location:)\s*([^\n]+).*?Issue:\s*([^\n]+)(?:.*?Suggestion:\s*([^\n]+))?",
            issue_text,
            re.DOTALL | re.IGNORECASE
        )
        for sev, loc, prob, sugg in severity_matches:
            issues.append(ServeFeedbackIssue(
                severity=sev.lower(),
                location=loc.strip(),
                problem=prob.strip(),
                suggestion=sugg.strip() if sugg else None
            ))

    # If we found a summary or issues, create feedback
    if summary or issues:
        # Get verdict from serve result
        serve_result = parse_serve_result(output)
        verdict = serve_result.verdict if serve_result else "NEEDS_CHANGES"

        return ServeFeedback(
            verdict=verdict,
            summary=summary,
            issues=issues,
            task_id=task_id,
            task_title=task_title,
            attempt=attempt
        )

    return None


def write_retry_context(cwd: Path, feedback: ServeFeedback) -> bool:
    """Write retry context file for cook to read on next attempt.

    Creates .line-cook/retry-context.json with structured feedback
    so cook can prioritize addressing review issues.

    Returns True if written successfully, False otherwise.
    """
    context_dir = cwd / ".line-cook"
    context_file = context_dir / "retry-context.json"

    try:
        context_dir.mkdir(parents=True, exist_ok=True)

        context = {
            "task_id": feedback.task_id,
            "task_title": feedback.task_title,
            "attempt": feedback.attempt,
            "verdict": feedback.verdict,
            "summary": feedback.summary,
            "issues": [
                {
                    "severity": issue.severity,
                    "location": issue.location,
                    "problem": issue.problem,
                    "suggestion": issue.suggestion
                }
                for issue in feedback.issues
            ],
            "written_at": datetime.now().isoformat()
        }

        atomic_write(context_file, json.dumps(context, indent=2))
        logger.info(f"Wrote retry context with {len(feedback.issues)} issues to {context_file}")
        return True

    except Exception as e:
        logger.warning(f"Failed to write retry context: {e}")
        return False


def clear_retry_context(cwd: Path) -> None:
    """Remove retry context file after successful completion."""
    context_file = cwd / ".line-cook" / "retry-context.json"
    try:
        if context_file.exists():
            context_file.unlink()
            logger.debug(f"Cleared retry context file {context_file}")
    except Exception as e:
        logger.debug(f"Failed to clear retry context: {e}")


def parse_intent_block(output: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse INTENT and BEFORE → AFTER from cook output.

    Looks for:
      INTENT:
        <description>
        Goal: <deliverable>

      BEFORE → AFTER:
        <before> → <after>

    Returns: (intent, before_state, after_state)
    """
    intent = None
    before_state = None
    after_state = None

    # Parse INTENT block
    intent_match = re.search(
        r"INTENT:\s*\n\s*(.+?)(?:\n\s*Goal:\s*(.+?))?(?:\n\n|\nBEFORE)",
        output,
        re.DOTALL
    )
    if intent_match:
        intent = intent_match.group(1).strip()
        if intent_match.group(2):
            intent = f"{intent} | Goal: {intent_match.group(2).strip()}"

    # Parse BEFORE → AFTER block
    before_after_match = re.search(
        r"BEFORE\s*→\s*AFTER:\s*\n\s*(.+?)\s*→\s*(.+?)(?:\n|$)",
        output,
        re.IGNORECASE
    )
    if before_after_match:
        before_state = before_after_match.group(1).strip()
        after_state = before_after_match.group(2).strip()

    return intent, before_state, after_state


def parse_bd_json_item(data: Any) -> Optional[dict]:
    """Extract single item from bd --json response.

    bd commands may return either [{"id": ...}] or {"id": ...}.
    This helper normalizes both formats to a single dict.

    Returns:
        The dict item, or None if data is invalid.
    """
    if isinstance(data, list) and len(data) > 0:
        return data[0] if isinstance(data[0], dict) else None
    elif isinstance(data, dict):
        return data
    return None


def detect_worked_task(before: BeadSnapshot, after: BeadSnapshot) -> Optional[str]:
    """Detect which task was worked on by state diff."""
    # Check for task that moved from ready to in_progress
    new_in_progress = set(after.in_progress_ids) - set(before.in_progress_ids)
    if new_in_progress:
        return next(iter(new_in_progress))

    # Check for task that moved from ready to closed
    new_closed = set(after.closed_ids) - set(before.closed_ids)
    disappeared_ready = set(before.ready_ids) - set(after.ready_ids)
    worked = new_closed & disappeared_ready
    if worked:
        return next(iter(worked))

    # Check for any task that was in_progress and is now closed
    was_in_progress = set(before.in_progress_ids)
    now_closed = set(after.closed_ids)
    completed = was_in_progress & now_closed
    if completed:
        return next(iter(completed))

    return None


def get_task_title(task_id: str, cwd: Path) -> Optional[str]:
    """Get the title for a task ID."""
    try:
        result = run_subprocess(["bd", "show", task_id, "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            issue = parse_bd_json_item(data)
            if issue:
                return issue.get("title")
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout getting title for {task_id}")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse task JSON for {task_id}: {e}")
    except Exception as e:
        logger.debug(f"Error getting task title for {task_id}: {e}")
    return None


def detect_kitchen_complete(output: str) -> bool:
    """Detect KITCHEN_COMPLETE signal in output."""
    return "KITCHEN_COMPLETE" in output or "KITCHEN COMPLETE" in output


def detect_kitchen_idle(output: str) -> bool:
    """Detect KITCHEN_IDLE signal in output."""
    return "KITCHEN_IDLE" in output or "KITCHEN IDLE" in output


def check_task_completed(
    task_id: Optional[str],
    before: BeadSnapshot,
    after: BeadSnapshot,
    output: str,
    cwd: Path,
    streamed_signals: Optional[list[str]] = None
) -> tuple[bool, str]:
    """Check if task completed using multiple signals.

    Returns (completed: bool, reason: str).

    Requires at least one DEFINITIVE signal:
    - bd_status_closed: Task status is "closed" via bd show
    - bead_closed: Task moved to closed in snapshot diff
    - serve_approved: SERVE_RESULT verdict is APPROVED
    - serve_approved_stream: SERVE_RESULT APPROVED detected during streaming
    - kitchen_complete_stream: KITCHEN_COMPLETE detected during streaming

    Supporting signals alone are NOT sufficient:
    - kitchen_complete: KITCHEN_COMPLETE marker in output (post-hoc)
    """
    definitive_signals = []
    supporting_signals = []

    # Include any signals detected during streaming (these are definitive)
    if streamed_signals:
        definitive_signals.extend(streamed_signals)

    # DEFINITIVE: Bead state - task moved to closed
    new_closed = set(after.closed_ids) - set(before.closed_ids)
    # Use ready_work_ids for consistency with loop focus (tasks + features, not epics)
    disappeared = set(before.ready_work_ids) - set(after.ready_work_ids) - set(after.in_progress_ids)
    if new_closed or disappeared:
        definitive_signals.append("bead_closed")

    # DEFINITIVE: Check task status directly via bd
    if task_id:
        try:
            result = run_subprocess(["bd", "show", task_id, "--json"], GIT_COMMAND_TIMEOUT, cwd)
            if result.returncode == 0 and result.stdout.strip():
                task_data = parse_bd_json_item(json.loads(result.stdout))
                if isinstance(task_data, dict) and task_data.get("status") == "closed":
                    definitive_signals.append("bd_status_closed")
        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout checking task status for {task_id}")
        except json.JSONDecodeError:
            logger.debug(f"Failed to parse task status JSON for {task_id}")
        except Exception as e:
            logger.debug(f"Error checking task status for {task_id}: {e}")

    # DEFINITIVE: SERVE_RESULT with APPROVED in partial output
    serve = parse_serve_result(output)
    if serve and serve.verdict == "APPROVED":
        definitive_signals.append("serve_approved")

    # SUPPORTING ONLY: KITCHEN_COMPLETE in output
    if detect_kitchen_complete(output):
        supporting_signals.append("kitchen_complete")

    all_signals = definitive_signals + supporting_signals
    completed = len(definitive_signals) > 0  # Must have at least one definitive signal
    return completed, ",".join(all_signals) if all_signals else "none"


def parse_stream_json_event(line: str) -> Optional[dict]:
    """Parse a single line of stream-json output.

    Returns the parsed event dict or None if not valid JSON.
    """
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def extract_text_from_event(event: dict) -> str:
    """Extract text content from assistant message event."""
    if event.get("type") != "assistant":
        return ""
    content = event.get("message", {}).get("content", [])
    return "\n".join(
        b.get("text", "") for b in content if b.get("type") == "text"
    )


def extract_actions_from_event(
    event: dict,
    pending_actions: dict[str, ActionRecord]
) -> list[ActionRecord]:
    """Extract tool_use blocks from an assistant message event.

    Also updates pending_actions dict with new tool uses for later correlation.
    Returns list of new ActionRecords.
    """
    actions = []
    if event.get("type") != "assistant":
        return actions

    message = event.get("message", {})
    content = message.get("content", [])

    for block in content:
        if block.get("type") == "tool_use":
            action = ActionRecord.from_tool_use(block)
            actions.append(action)
            # Track for correlation with tool_result
            pending_actions[action.tool_use_id] = action

    return actions


def update_action_from_result(
    event: dict,
    pending_actions: dict[str, ActionRecord]
) -> None:
    """Update a pending action with its tool_result.

    Looks for tool_result content blocks and updates the corresponding
    ActionRecord with output_summary and success status.
    """
    if event.get("type") != "user":
        return

    message = event.get("message", {})
    content = message.get("content", [])

    for block in content:
        if block.get("type") == "tool_result":
            tool_use_id = block.get("tool_use_id", "")
            if tool_use_id in pending_actions:
                action = pending_actions[tool_use_id]
                # Check for error
                is_error = block.get("is_error", False)
                action.success = not is_error
                # Extract output summary
                result_content = block.get("content", "")
                if isinstance(result_content, list):
                    # Handle array of content blocks
                    text_parts = []
                    for part in result_content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    result_content = "\n".join(text_parts)
                if isinstance(result_content, str):
                    # Truncate output summary
                    if len(result_content) > OUTPUT_SUMMARY_MAX_LENGTH:
                        action.output_summary = result_content[:OUTPUT_SUMMARY_MAX_LENGTH] + "..."
                    else:
                        action.output_summary = result_content
                    # Prefix with ERROR: if this was an error result
                    if is_error and not action.output_summary.startswith("ERROR:"):
                        action.output_summary = f"ERROR: {action.output_summary}"
                # Remove from pending after processing
                del pending_actions[tool_use_id]


def get_latest_commit(cwd: Path) -> Optional[str]:
    """Get the latest commit hash."""
    try:
        result = run_subprocess(["git", "log", "-1", "--format=%h"], GIT_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Error getting latest commit: {e}")
    return None


def run_phase(
    phase: str,
    cwd: Path,
    args: str = "",
    timeout: Optional[int] = None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    phase_timeouts: Optional[dict[str, int]] = None,
    idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    idle_action: str = DEFAULT_IDLE_ACTION
) -> PhaseResult:
    """Invoke a single Line Cook skill phase (cook, serve, tidy, plate).

    Args:
        phase: Phase name (cook, serve, tidy, plate)
        cwd: Working directory
        args: Optional arguments (e.g., task ID for cook)
        timeout: Override default phase timeout (takes precedence over phase_timeouts)
        on_progress: Optional callback for progress updates.
            Called with (action_count, last_action_timestamp) when new actions detected.
        phase_timeouts: Optional dict of phase-specific timeouts (overrides defaults)
        idle_timeout: Seconds without tool actions before triggering idle (default: 180)
        idle_action: Action on idle - "warn" logs warning, "terminate" stops phase (default: warn)

    Returns:
        PhaseResult with output, signals, and success status
    """
    if timeout is None:
        timeouts = phase_timeouts or DEFAULT_PHASE_TIMEOUTS
        timeout = timeouts.get(phase, DEFAULT_PHASE_TIMEOUTS.get(phase, DEFAULT_FALLBACK_PHASE_TIMEOUT))

    skill = f"/line:{phase}"
    if args:
        skill = f"{skill} {args}"

    logger.debug(f"Running phase {phase}: claude -p '{skill}' (timeout={timeout}s)")
    start_time = time.time()

    actions: list[ActionRecord] = []
    pending_actions: dict[str, ActionRecord] = {}
    output_lines: list[str] = []
    signals: list[str] = []
    exit_code = 0
    error: Optional[str] = None
    last_action_time: Optional[datetime] = None
    idle_warned: bool = False

    try:
        process = subprocess.Popen(
            ["claude", "-p", skill,
             "--dangerously-skip-permissions",
             "--output-format", "stream-json",
             "--verbose"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            cwd=cwd
        )

        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                # Graceful termination: SIGTERM first, then SIGKILL as fallback
                logger.debug(f"Phase {phase} timeout - sending SIGTERM")
                process.terminate()  # SIGTERM
                try:
                    process.wait(timeout=5)
                    logger.debug(f"Phase {phase} terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Phase {phase} did not respond to SIGTERM, sending SIGKILL")
                    process.kill()  # SIGKILL as fallback
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        logger.warning(f"Phase {phase} process did not terminate after SIGKILL")
                raise subprocess.TimeoutExpired(cmd=f"claude -p {skill}", timeout=timeout)

            ready, _, _ = select.select([process.stdout], [], [], min(1.0, remaining))
            if ready:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line)
                event = parse_stream_json_event(line)
                if event:
                    # Extract tool_use from assistant messages
                    new_actions = extract_actions_from_event(event, pending_actions)
                    actions.extend(new_actions)
                    # Update actions with tool_result from user messages
                    update_action_from_result(event, pending_actions)
                    # Track last action time for idle detection
                    if new_actions:
                        last_action_time = datetime.now()
                        idle_warned = False  # Reset idle warning on new activity
                    # Notify progress callback when new actions detected
                    if new_actions and on_progress:
                        last_ts = new_actions[-1].timestamp
                        on_progress(len(actions), last_ts)
                    # Detect signals during streaming
                    if event.get("type") == "assistant":
                        text = extract_text_from_event(event)
                        if "SERVE_RESULT" in text:
                            if "APPROVED" in text and "serve_approved" not in signals:
                                signals.append("serve_approved")
                            elif "NEEDS_CHANGES" in text and "serve_needs_changes" not in signals:
                                signals.append("serve_needs_changes")
                            elif "BLOCKED" in text and "serve_blocked" not in signals:
                                signals.append("serve_blocked")
                        if ("KITCHEN_COMPLETE" in text or "KITCHEN COMPLETE" in text) and "kitchen_complete" not in signals:
                            signals.append("kitchen_complete")
                        if detect_kitchen_idle(text) and "kitchen_idle" not in signals:
                            signals.append("kitchen_idle")
                        # Detect phase completion signal for early termination
                        if "<phase_complete>DONE</phase_complete>" in text and "phase_complete" not in signals:
                            signals.append("phase_complete")
                            logger.info(f"Phase {phase} signaled completion, terminating early")
                            # Graceful early termination
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait(timeout=5)
                            break
            else:
                if process.poll() is not None:
                    break
                # Check for idle when no output is ready
                if idle_timeout > 0 and last_action_time is not None:
                    if check_idle(last_action_time, idle_timeout):
                        if idle_action == "terminate":
                            logger.warning(f"Phase {phase} idle for {idle_timeout}s, terminating")
                            signals.append("idle_terminated")
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill()
                                process.wait(timeout=5)
                            error = f"Idle timeout after {idle_timeout}s without tool actions"
                            break
                        elif idle_action == "warn" and not idle_warned:
                            idle_seconds = (datetime.now() - last_action_time).total_seconds()
                            logger.warning(f"Phase {phase} idle for {idle_seconds:.0f}s (threshold: {idle_timeout}s)")
                            idle_warned = True

        # Read any remaining output
        remaining_out = process.stdout.read()
        if remaining_out:
            output_lines.extend(remaining_out.splitlines(keepends=True))
        process.wait()
        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.warning(f"Phase {phase} timed out after {duration:.1f}s")
        return PhaseResult(
            phase=phase,
            success=False,
            output="".join(output_lines),
            exit_code=-1,
            duration_seconds=duration,
            signals=signals,
            actions=actions,
            error=f"Timeout after {timeout}s"
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Phase {phase} crashed: {e}")
        return PhaseResult(
            phase=phase,
            success=False,
            output="".join(output_lines),
            exit_code=-1,
            duration_seconds=duration,
            signals=signals,
            actions=actions,
            error=str(e)
        )

    duration = time.time() - start_time
    output = "".join(output_lines)
    # Phase is successful if exit code is 0 OR if it signaled early completion
    early_completion = "phase_complete" in signals
    success = exit_code == 0 or early_completion

    logger.debug(f"Phase {phase} completed in {duration:.1f}s, exit={exit_code}, signals={signals}, early_completion={early_completion}")

    return PhaseResult(
        phase=phase,
        success=success,
        output=output,
        exit_code=exit_code,
        duration_seconds=duration,
        signals=signals,
        actions=actions,
        error=None if success else f"Exit code {exit_code}",
        early_completion=early_completion
    )


def get_task_info(task_id: str, cwd: Path) -> Optional[dict]:
    """Get task info including parent and status."""
    cmd = f"bd show {task_id} --json"
    try:
        result = run_subprocess(["bd", "show", task_id, "--json"], GIT_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return parse_bd_json_item(data)
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd, GIT_COMMAND_TIMEOUT, task_id=task_id)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode(f"bd show {task_id} output", e, task_id=task_id)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting task info for {task_id}: {e}")
    return None


def get_children(parent_id: str, cwd: Path) -> list[dict]:
    """Get all children of a parent issue."""
    cmd = f"bd list --parent={parent_id} --all --json"
    try:
        result = run_subprocess(
            ["bd", "list", f"--parent={parent_id}", "--all", "--json"],
            BD_COMMAND_TIMEOUT, cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            children = json.loads(result.stdout)
            if isinstance(children, list):
                return [c for c in children if isinstance(c, dict)]
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode(f"bd list --parent={parent_id} output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting children for {parent_id}: {e}")
    return []


def check_feature_completion(task_id: str, cwd: Path) -> tuple[bool, Optional[str]]:
    """Check if completing a task completes its parent feature.

    Returns: (feature_complete, feature_id)
    """
    task_info = get_task_info(task_id, cwd)
    if not task_info or not task_info.get("parent"):
        return False, None

    parent_id = task_info["parent"]
    parent_info = get_task_info(parent_id, cwd)

    # Only proceed if parent is a feature
    if not parent_info or parent_info.get("type") != "feature":
        return False, None

    # Check if all siblings are closed
    siblings = get_children(parent_id, cwd)
    for sibling in siblings:
        if sibling.get("status") != "closed":
            return False, None

    return True, parent_id


def check_epic_completion_after_feature(feature_id: str, cwd: Path) -> tuple[bool, Optional[str]]:
    """Check if completing a feature completes its parent epic.

    Returns: (epic_complete, epic_id)
    """
    feature_info = get_task_info(feature_id, cwd)
    if not feature_info or not feature_info.get("parent"):
        return False, None

    epic_id = feature_info["parent"]
    epic_info = get_task_info(epic_id, cwd)

    # Only proceed if parent is an epic
    if not epic_info or epic_info.get("type") != "epic":
        return False, None

    # Check if all children are closed
    children = get_children(epic_id, cwd)
    for child in children:
        if child.get("status") != "closed":
            return False, None

    return True, epic_id


def generate_epic_closure_report(epic_id: str, cwd: Path) -> str:
    """Generate a formatted epic closure report."""
    epic_info = get_task_info(epic_id, cwd)
    if not epic_info:
        return f"EPIC COMPLETE: {epic_id} (details unavailable)"

    title = epic_info.get("title", "Unknown")
    description = epic_info.get("description", "")

    children = get_children(epic_id, cwd)
    features = [c for c in children if c.get("type") == "feature"]

    lines = [
        "",
        f"EPIC COMPLETE: {epic_id} - {title}",
        "━" * 60,
        "",
        "JOURNEY SUMMARY",
        f"What this epic set out to accomplish:",
    ]

    # Extract first sentence or paragraph from description
    if description:
        goal = description.split('\n')[0].strip()
        if len(goal) > GOAL_TEXT_MAX_LENGTH:
            goal = goal[:GOAL_TEXT_MAX_LENGTH - 3] + "..."
        lines.append(f"  {goal}")
    else:
        lines.append("  (No description provided)")

    lines.append("")
    lines.append("FEATURES DELIVERED")

    for feature in features:
        f_id = feature.get("id", "?")
        f_title = feature.get("title", "Unknown")
        lines.append(f"  ✓ {f_id}: {f_title}")

    lines.append("")
    lines.append("COLLECTIVE IMPACT")
    lines.append(f"  {len(features)} feature(s) completed under this epic.")

    lines.append("")
    lines.append("━" * 60)
    lines.append("")

    return "\n".join(lines)


def get_epic_summary(epic_id: str, cwd: Path) -> dict:
    """Get epic details and all completed children."""
    epic_data = {"id": epic_id, "title": None, "description": None, "children": []}

    # Get epic details
    try:
        result = run_subprocess(["bd", "show", epic_id, "--json"], GIT_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            epic = parse_bd_json_item(json.loads(result.stdout))
            if epic:
                epic_data["title"] = epic.get("title")
                epic_data["description"] = epic.get("description")
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get epic details for {epic_id}: {e}")
    except Exception as e:
        logger.debug(f"Error getting epic details for {epic_id}: {e}")

    # Get all children
    try:
        result = run_subprocess(
            ["bd", "list", f"--parent={epic_id}", "--all", "--json"],
            BD_COMMAND_TIMEOUT, cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            children = json.loads(result.stdout)
            epic_data["children"] = [
                {"id": c.get("id"), "title": c.get("title"), "type": c.get("type")}
                for c in children if isinstance(c, dict)
            ]
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get children for epic {epic_id}: {e}")
    except Exception as e:
        logger.debug(f"Error getting children for epic {epic_id}: {e}")

    return epic_data


def print_epic_completion(epic: dict):
    """Print epic completion banner."""
    title = epic.get("title", "Unknown")
    epic_id = epic.get("id", "?")
    description = epic.get("description", "")
    children = epic.get("children", [])

    # Build header
    header = f"EPIC COMPLETE: {epic_id} - {title}"
    width = max(BANNER_MIN_WIDTH, len(header) + 4)

    print()
    print("╔" + "═" * width + "╗")
    print(f"║  {header:<{width-2}}║")
    print("╚" + "═" * width + "╝")

    # Intent (from description, first sentence)
    if description:
        intent = description.split(".")[0].strip()
        if intent:
            print(f"\nIntent: {intent}")

    # Features delivered
    if children:
        print(f"\nFeatures delivered ({len(children)}):")
        for child in children:
            child_id = child.get("id", "?")
            child_title = child.get("title", "Unknown")
            print(f"  [x] {child_id}: {child_title}")

    # Summary line
    if children:
        types = {}
        for c in children:
            t = c.get("type", "item")
            types[t] = types.get(t, 0) + 1
        type_summary = ", ".join(
            f"{count} {t}" if count == 1 else f"{count} {t}s"
            for t, count in types.items()
        )
        print(f"\nSummary: Completed {type_summary} under this epic.")

    print()
    print("═" * (width + 2))


def check_epic_completion(cwd: Path) -> list[dict]:
    """Check for newly completable epics and close them.

    Returns list of completed epic summaries for display.
    """
    # Check what's eligible for closure
    try:
        result = run_subprocess(
            ["bd", "epic", "close-eligible", "--dry-run", "--json"],
            BD_COMMAND_TIMEOUT, cwd
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        eligible = json.loads(result.stdout)
        if not eligible:
            return []

        # eligible is a list of epic IDs or epic objects
        epic_ids = []
        for item in eligible:
            if isinstance(item, str) and item:
                epic_ids.append(item)
            elif isinstance(item, dict):
                epic_id = item.get("id", "")
                if epic_id:
                    epic_ids.append(epic_id)

        if not epic_ids:
            return []

        logger.info(f"Found {len(epic_ids)} epic(s) eligible for closure: {epic_ids}")

    except subprocess.TimeoutExpired:
        logger.warning("Timeout checking epic closure eligibility")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse epic closure eligibility JSON: {e}")
        return []
    except Exception as e:
        logger.debug(f"Error checking epic closure eligibility: {e}")
        return []

    # Close eligible epics
    try:
        result = run_subprocess(["bd", "epic", "close-eligible"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"Failed to close eligible epics: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        logger.warning("Timeout closing eligible epics")
        return []
    except Exception as e:
        logger.warning(f"Error closing eligible epics: {e}")
        return []

    # Build and display summaries
    summaries = []
    for epic_id in epic_ids:
        epic = get_epic_summary(epic_id, cwd)
        summaries.append(epic)
        print_epic_completion(epic)

    return summaries


def run_iteration(
    iteration: int,
    max_iterations: int,
    cwd: Path,
    max_cook_retries: int = 2,
    json_output: bool = False,
    progress_state: Optional[ProgressState] = None,
    phase_timeouts: Optional[dict[str, int]] = None,
    idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    idle_action: str = DEFAULT_IDLE_ACTION
) -> IterationResult:
    """Execute individual phases (cook→serve→tidy) with retry logic.

    This replaces the monolithic /line:run invocation with separate phase calls,
    enabling better error detection, retry on NEEDS_CHANGES, and feature/epic
    completion triggers.

    Phase timeouts are controlled by phase_timeouts dict or DEFAULT_PHASE_TIMEOUTS
    (cook=1200s, serve=600s, tidy=240s, plate=600s).

    Args:
        iteration: Current iteration number
        max_iterations: Maximum iterations for logging
        cwd: Working directory
        max_cook_retries: Max retries on NEEDS_CHANGES verdict
        json_output: If True, suppress human-readable phase output
        progress_state: Optional progress state for real-time status updates
        phase_timeouts: Optional dict of phase-specific timeouts (overrides defaults)
    """
    start_time = datetime.now()
    logger.info(f"Starting iteration {iteration}/{max_iterations}")

    # Capture before state
    before = get_bead_snapshot(cwd)
    logger.debug(f"Before state: {len(before.ready_ids)} ready ({len(before.ready_work_ids)} work items), {len(before.in_progress_ids)} in_progress")

    # Check for ready work items (tasks + features, not epics - epics can't be executed)
    if not before.ready_work_ids:
        if before.ready_ids:
            logger.info(f"No work items ready ({len(before.ready_ids)} epics ready)")
        else:
            logger.info("No work items ready")
        return IterationResult(
            iteration=iteration,
            task_id=None,
            task_title=None,
            outcome="no_work",
            duration_seconds=0.0,
            serve_verdict=None,
            commit_hash=None,
            success=False,
            before_ready=len(before.ready_ids),
            before_in_progress=len(before.in_progress_ids),
            after_ready=len(before.ready_ids),
            after_in_progress=len(before.in_progress_ids)
        )

    # Collect all actions across phases
    all_actions: list[ActionRecord] = []
    all_output: list[str] = []
    serve_verdict: Optional[str] = None
    task_id: Optional[str] = None
    after: Optional[BeadSnapshot] = None  # Will be set during phase execution

    # Create progress callback if progress_state is available
    def progress_callback(action_count: int, last_action_time: str):
        if progress_state:
            progress_state.update_progress(action_count, last_action_time)

    # ===== PHASE 1: COOK (with retry loop) =====
    cook_attempts = 0
    cook_succeeded = False

    while cook_attempts <= max_cook_retries:
        cook_attempts += 1
        logger.info(f"Cook phase attempt {cook_attempts}/{max_cook_retries + 1}")

        # Run cook phase
        retry_info = f" (retry {cook_attempts - 1})" if cook_attempts > 1 else ""
        if not json_output:
            print_phase_progress(f"cook{retry_info}", "start")

        if progress_state:
            progress_state.start_phase("cook")
        cook_result = run_phase("cook", cwd, on_progress=progress_callback, phase_timeouts=phase_timeouts, idle_timeout=idle_timeout, idle_action=idle_action)
        all_actions.extend(cook_result.actions)
        all_output.append(f"=== COOK PHASE (attempt {cook_attempts}) ===\n")
        all_output.append(cook_result.output)

        # Track if task completed despite timeout (still need serve review)
        task_completed_despite_timeout = False

        if cook_result.error and "Timeout" in cook_result.error:
            # Timeout during cook - check if task completed anyway
            after_cook = get_bead_snapshot(cwd)
            task_id = detect_worked_task(before, after_cook)
            if task_id:
                task_info = get_task_info(task_id, cwd)
                if task_info and task_info.get("status") == "closed":
                    logger.info(f"Cook timed out but task {task_id} was closed")
                    if not json_output:
                        print_phase_progress("cook", "done", cook_result.duration_seconds,
                                           f"{len(cook_result.actions)} actions (timed out but completed)")
                    task_completed_despite_timeout = True
                    # Fall through to serve for code review validation

            if not task_completed_despite_timeout:
                if not json_output:
                    print_phase_progress("cook", "error", cook_result.duration_seconds, "timeout")
                logger.warning(f"Cook phase timed out on attempt {cook_attempts}")
                if cook_attempts > max_cook_retries:
                    duration = (datetime.now() - start_time).total_seconds()
                    # Reuse after_cook snapshot from above
                    return IterationResult(
                        iteration=iteration,
                        task_id=task_id,
                        task_title=get_task_title(task_id, cwd) if task_id else None,
                        outcome="timeout",
                        duration_seconds=duration,
                        serve_verdict=None,
                        commit_hash=get_latest_commit(cwd),
                        success=False,
                        before_ready=len(before.ready_ids),
                        before_in_progress=len(before.in_progress_ids),
                        after_ready=len(after_cook.ready_ids),
                        after_in_progress=len(after_cook.in_progress_ids),
                        actions=all_actions
                    )
                continue

        if not cook_result.success and not task_completed_despite_timeout:
            if not json_output:
                print_phase_progress("cook", "error", cook_result.duration_seconds,
                                   cook_result.error or "failed")
            logger.warning(f"Cook phase failed on attempt {cook_attempts}: {cook_result.error}")
            if cook_attempts > max_cook_retries:
                break
            continue

        # Check for KITCHEN_IDLE signal (no actionable work found)
        # Skip if task completed despite timeout (task closure contradicts IDLE)
        if "kitchen_idle" in cook_result.signals and not task_completed_despite_timeout:
            if not json_output:
                print_phase_progress("cook", "done", cook_result.duration_seconds, "IDLE")
            logger.info("Cook found no actionable work (KITCHEN_IDLE)")
            duration = (datetime.now() - start_time).total_seconds()
            # State unchanged since no work was done - reuse before snapshot values
            return IterationResult(
                iteration=iteration,
                task_id=None,
                task_title=None,
                outcome="no_actionable_work",
                duration_seconds=duration,
                serve_verdict=None,
                commit_hash=None,
                success=False,
                before_ready=len(before.ready_ids),
                before_in_progress=len(before.in_progress_ids),
                after_ready=len(before.ready_ids),
                after_in_progress=len(before.in_progress_ids),
                actions=all_actions
            )

        # Cook succeeded - print progress (we'll report actions after serve since we continue to serve)
        # Skip if already printed for timeout-but-completed case
        if not json_output and not task_completed_despite_timeout:
            print_phase_progress("cook", "done", cook_result.duration_seconds,
                               f"{len(cook_result.actions)} actions")

        # Cook succeeded, detect task (skip if already detected in timeout path)
        if not task_completed_despite_timeout:
            after_cook = get_bead_snapshot(cwd)
            task_id = detect_worked_task(before, after_cook)
        logger.debug(f"Detected task: {task_id}")

        # Update progress state with detected task for status visibility
        if progress_state and task_id:
            progress_state.current_task = task_id
            progress_state.current_task_title = get_task_title(task_id, cwd)

        # Note: KITCHEN_COMPLETE signal indicates cook is confident, but we
        # still run serve for code review validation

        # ===== PHASE 2: SERVE =====
        logger.info("Serve phase")
        if not json_output:
            print_phase_progress("serve", "start")

        if progress_state:
            progress_state.start_phase("serve")
        serve_result = run_phase("serve", cwd, on_progress=progress_callback, phase_timeouts=phase_timeouts, idle_timeout=idle_timeout, idle_action=idle_action)
        all_actions.extend(serve_result.actions)
        all_output.append("\n=== SERVE PHASE ===\n")
        all_output.append(serve_result.output)

        if serve_result.error:
            if not json_output:
                print_phase_progress("serve", "error", serve_result.duration_seconds, "skipped")
            logger.warning(f"Serve phase error: {serve_result.error}")
            # Treat serve errors as SKIPPED - transient, continue
            serve_verdict = "SKIPPED"
            cook_succeeded = True
            break

        # Parse serve verdict
        parsed_serve = parse_serve_result(serve_result.output)
        if parsed_serve:
            serve_verdict = parsed_serve.verdict
            logger.info(f"Serve verdict: {serve_verdict}")

            if serve_verdict == "APPROVED":
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "APPROVED")
                # Clear retry context on success
                clear_retry_context(cwd)
                cook_succeeded = True
                break
            elif serve_verdict == "NEEDS_CHANGES":
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "NEEDS_CHANGES")
                logger.info(f"NEEDS_CHANGES - will retry cook (attempt {cook_attempts}/{max_cook_retries + 1})")
                # Write structured retry context for cook to read
                feedback = parse_serve_feedback(
                    serve_result.output,
                    task_id=task_id,
                    task_title=get_task_title(task_id, cwd) if task_id else None,
                    attempt=cook_attempts
                )
                if feedback:
                    write_retry_context(cwd, feedback)
                if cook_attempts > max_cook_retries:
                    logger.warning("Max cook retries reached with NEEDS_CHANGES")
                    break
                continue
            elif serve_verdict == "BLOCKED":
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "BLOCKED")
                logger.warning("Serve returned BLOCKED verdict")
                duration = (datetime.now() - start_time).total_seconds()
                after = get_bead_snapshot(cwd)
                return IterationResult(
                    iteration=iteration,
                    task_id=task_id,
                    task_title=get_task_title(task_id, cwd) if task_id else None,
                    outcome="blocked",
                    duration_seconds=duration,
                    serve_verdict="BLOCKED",
                    commit_hash=get_latest_commit(cwd),
                    success=False,
                    before_ready=len(before.ready_ids),
                    before_in_progress=len(before.in_progress_ids),
                    after_ready=len(after.ready_ids),
                    after_in_progress=len(after.in_progress_ids),
                    actions=all_actions
                )
            elif serve_verdict == "SKIPPED":
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "SKIPPED")
                logger.info("Serve skipped (transient error) - continuing")
                cook_succeeded = True
                break
        else:
            # No SERVE_RESULT found - check signals
            if "serve_approved" in serve_result.signals:
                serve_verdict = "APPROVED"
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "APPROVED")
                # Clear retry context on success
                clear_retry_context(cwd)
                cook_succeeded = True
                break
            elif "serve_needs_changes" in serve_result.signals:
                serve_verdict = "NEEDS_CHANGES"
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "NEEDS_CHANGES")
                # Write structured retry context for cook to read
                feedback = parse_serve_feedback(
                    serve_result.output,
                    task_id=task_id,
                    task_title=get_task_title(task_id, cwd) if task_id else None,
                    attempt=cook_attempts
                )
                if feedback:
                    write_retry_context(cwd, feedback)
                if cook_attempts > max_cook_retries:
                    break
                continue
            elif "serve_blocked" in serve_result.signals:
                serve_verdict = "BLOCKED"
                if not json_output:
                    print_phase_progress("serve", "done", serve_result.duration_seconds, "BLOCKED")
                logger.warning("Serve returned BLOCKED verdict (from signal)")
                duration = (datetime.now() - start_time).total_seconds()
                after = get_bead_snapshot(cwd)
                return IterationResult(
                    iteration=iteration,
                    task_id=task_id,
                    task_title=get_task_title(task_id, cwd) if task_id else None,
                    outcome="blocked",
                    duration_seconds=duration,
                    serve_verdict="BLOCKED",
                    commit_hash=get_latest_commit(cwd),
                    success=False,
                    before_ready=len(before.ready_ids),
                    before_in_progress=len(before.in_progress_ids),
                    after_ready=len(after.ready_ids),
                    after_in_progress=len(after.in_progress_ids),
                    actions=all_actions
                )
            else:
                # No verdict parsed and no signals detected - retry full cook→serve cycle
                # (serve-only retry not supported; full cycle ensures clean state)
                if cook_attempts <= max_cook_retries:
                    logger.warning("Could not parse serve verdict, retrying cook→serve cycle")
                    if not json_output:
                        print_phase_progress("serve", "error", serve_result.duration_seconds, "no verdict, retrying")
                    continue
                else:
                    # Max retries reached - fail conservatively
                    logger.warning("Could not parse serve verdict after max retries")
                    serve_verdict = None
                    if not json_output:
                        print_phase_progress("serve", "error", serve_result.duration_seconds, "no verdict")
                    break

    # Check if we exhausted retries
    if not cook_succeeded:
        duration = (datetime.now() - start_time).total_seconds()
        # Safety fallback: after snapshot may be None if we failed before any snapshot
        # was taken (e.g., immediate cook failure before post-cook snapshot)
        if after is None:
            after = get_bead_snapshot(cwd)
        return IterationResult(
            iteration=iteration,
            task_id=task_id,
            task_title=get_task_title(task_id, cwd) if task_id else None,
            outcome="needs_retry",
            duration_seconds=duration,
            serve_verdict=serve_verdict,
            commit_hash=get_latest_commit(cwd),
            success=False,
            before_ready=len(before.ready_ids),
            before_in_progress=len(before.in_progress_ids),
            after_ready=len(after.ready_ids),
            after_in_progress=len(after.in_progress_ids),
            actions=all_actions
        )

    # ===== PHASE 3: TIDY =====
    logger.info("Tidy phase")
    if not json_output:
        print_phase_progress("tidy", "start")

    if progress_state:
        progress_state.start_phase("tidy")
    tidy_result = run_phase("tidy", cwd, on_progress=progress_callback, phase_timeouts=phase_timeouts, idle_timeout=idle_timeout, idle_action=idle_action)
    all_actions.extend(tidy_result.actions)
    all_output.append("\n=== TIDY PHASE ===\n")
    all_output.append(tidy_result.output)

    # Get commit hash for tidy completion message
    commit_hash = get_latest_commit(cwd)

    if tidy_result.error:
        if not json_output:
            print_phase_progress("tidy", "error", tidy_result.duration_seconds, tidy_result.error or "failed")
        logger.warning(f"Tidy phase error: {tidy_result.error}")
        # Tidy errors are concerning but not fatal
    else:
        if not json_output:
            extra = f"committed {commit_hash[:7]}" if commit_hash else "done"
            print_phase_progress("tidy", "done", tidy_result.duration_seconds, extra)

    # Capture final state
    after = get_bead_snapshot(cwd)

    # Determine final outcome
    task_id = detect_worked_task(before, after) or task_id
    task_title = get_task_title(task_id, cwd) if task_id else None
    commit_hash = get_latest_commit(cwd)

    # Check if task was closed
    new_closed = set(after.closed_ids) - set(before.closed_ids)
    task_closed = bool(new_closed) or (task_id and task_id not in after.ready_work_ids and task_id not in after.in_progress_ids)

    # Parse intent from cook output
    combined_output = "".join(all_output)
    intent, before_state, after_state = parse_intent_block(combined_output)

    # ===== PHASE 4: FEATURE/EPIC COMPLETION CHECK =====
    if task_id and task_closed:
        # Check if completing this task completes a feature
        feature_complete, feature_id = check_feature_completion(task_id, cwd)
        if feature_complete and feature_id:
            logger.info(f"Feature {feature_id} complete - running plate phase")
            if not json_output:
                print(f"\n  Feature complete: {feature_id}")
                print_phase_progress("plate", "start")

            if progress_state:
                progress_state.start_phase("plate")
            plate_result = run_phase("plate", cwd, args=feature_id, on_progress=progress_callback, phase_timeouts=phase_timeouts, idle_timeout=idle_timeout, idle_action=idle_action)
            all_actions.extend(plate_result.actions)
            all_output.append("\n=== PLATE PHASE ===\n")
            all_output.append(plate_result.output)

            if plate_result.error:
                if not json_output:
                    print_phase_progress("plate", "error", plate_result.duration_seconds,
                                       plate_result.error or "failed")
                logger.warning(f"Plate phase error for feature {feature_id}: {plate_result.error}")
            else:
                if not json_output:
                    print_phase_progress("plate", "done", plate_result.duration_seconds,
                                       f"feature {feature_id} validated")
                logger.info(f"Plate phase completed for feature {feature_id}")
                # Check if completing the feature completes an epic
                epic_complete, epic_id = check_epic_completion_after_feature(feature_id, cwd)
                if epic_complete and epic_id:
                    logger.info(f"Epic {epic_id} complete - all features closed")
                    report = generate_epic_closure_report(epic_id, cwd)
                    if not json_output:
                        print(report)

                    # Close the epic
                    try:
                        run_subprocess(["bd", "close", epic_id], BD_COMMAND_TIMEOUT, cwd)
                        logger.info(f"Closed epic {epic_id}")
                    except Exception as e:
                        logger.warning(f"Failed to close epic {epic_id}: {e}")

    duration = (datetime.now() - start_time).total_seconds()

    success = task_closed or serve_verdict == "APPROVED"
    outcome = "completed" if success else "needs_retry"

    logger.info(f"Iteration {iteration} {outcome}: task={task_id}, duration={duration:.1f}s, actions={len(all_actions)}")

    return IterationResult(
        iteration=iteration,
        task_id=task_id,
        task_title=task_title,
        outcome=outcome,
        duration_seconds=duration,
        serve_verdict=serve_verdict,
        commit_hash=commit_hash,
        success=success,
        before_ready=len(before.ready_ids),
        before_in_progress=len(before.in_progress_ids),
        after_ready=len(after.ready_ids),
        after_in_progress=len(after.in_progress_ids),
        intent=intent,
        before_state=before_state,
        after_state=after_state,
        actions=all_actions
    )


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes}m {secs:.0f}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def print_phase_progress(phase: str, status: str, duration: float = 0, extra: str = ""):
    """Print phase progress indicator.

    Args:
        phase: Phase name (cook, serve, tidy, plate)
        status: "start", "done", or "error"
        duration: Phase duration in seconds (for done/error status)
        extra: Additional info to append (e.g., action count, verdict)
    """
    symbols = {"start": "▶", "done": "✓", "error": "✗"}
    symbol = symbols.get(status, "?")
    if status == "start":
        print(f"  {symbol} {phase.upper()} phase...")
    else:
        msg = f"  {symbol} {phase.upper()} complete ({format_duration(duration)})"
        if extra:
            msg += f" - {extra}"
        print(msg)


def print_human_iteration(result: IterationResult, retries: int = 0):
    """Print iteration result in human-readable format."""
    # Status indicator
    status_map = {
        "completed": "[OK]",
        "needs_retry": "[RETRY]",
        "blocked": "[BLOCKED]",
        "crashed": "[CRASH]",
        "timeout": "[TIMEOUT]",
        "no_work": "[DONE]",
        "no_actionable_work": "[IDLE]"
    }
    status = status_map.get(result.outcome, "[?]")

    task_info = f"{result.task_id}: {result.task_title}" if result.task_id else "Unknown task"
    print(f"  {status} {task_info}")

    if result.intent:
        print(f"  Intent: {result.intent}")
    if result.before_state:
        print(f"  Before: {result.before_state}")
    if result.after_state:
        print(f"  After:  {result.after_state}")

    # Duration and verdict
    details = [f"Duration: {format_duration(result.duration_seconds)}"]
    if result.serve_verdict:
        details.append(f"Verdict: {result.serve_verdict}")
    if result.commit_hash:
        details.append(f"Commit: {result.commit_hash}")
    print(f"  {' | '.join(details)}")

    # Action summary
    if result.total_actions > 0:
        action_parts = [f"{name}: {count}" for name, count in sorted(result.action_counts.items())]
        print(f"  Actions: {result.total_actions} total ({', '.join(action_parts)})")

    # Bead state changes
    ready_delta = result.after_ready - result.before_ready
    in_prog_delta = result.after_in_progress - result.before_in_progress
    ready_str = f"ready {result.before_ready}→{result.after_ready}"
    in_prog_str = f"in_progress {result.before_in_progress}→{result.after_in_progress}"
    closed_str = "+1" if result.success else ""
    print(f"\n  Beads: {ready_str} | {in_prog_str}" + (f" | closed {closed_str}" if closed_str else ""))

    if result.outcome == "needs_retry" and retries > 0:
        print(f"\n  Retrying ({retries})...")


def serialize_iteration_for_status(result: IterationResult) -> dict:
    """Serialize an IterationResult for the status file's recent_iterations array."""
    return {
        "iteration": result.iteration,
        "task_id": result.task_id,
        "task_title": result.task_title,
        "outcome": result.outcome,
        "serve_verdict": result.serve_verdict,
        "commit_hash": result.commit_hash,
        "duration_seconds": result.duration_seconds,
        "intent": result.intent,
        "before_state": result.before_state,
        "after_state": result.after_state,
        "completed_at": datetime.now().isoformat(),
        # Action counts for watch mode
        "action_count": result.total_actions,
        "action_types": result.action_counts
    }


def serialize_action(action: ActionRecord) -> dict:
    """Serialize an ActionRecord for history.json."""
    return {
        "tool_name": action.tool_name,
        "tool_use_id": action.tool_use_id,
        "input_summary": action.input_summary,
        "output_summary": action.output_summary,
        "success": action.success,
        "timestamp": action.timestamp
    }


def serialize_full_iteration(result: IterationResult) -> dict:
    """Serialize an IterationResult with full action details for history.json."""
    return {
        "iteration": result.iteration,
        "task_id": result.task_id,
        "task_title": result.task_title,
        "outcome": result.outcome,
        "serve_verdict": result.serve_verdict,
        "commit_hash": result.commit_hash,
        "duration_seconds": result.duration_seconds,
        "success": result.success,
        "intent": result.intent,
        "before_state": result.before_state,
        "after_state": result.after_state,
        "beads_before": {
            "ready": result.before_ready,
            "in_progress": result.before_in_progress
        },
        "beads_after": {
            "ready": result.after_ready,
            "in_progress": result.after_in_progress
        },
        "action_count": result.total_actions,
        "action_types": result.action_counts,
        "actions": [serialize_action(a) for a in result.actions]
    }


def append_iteration_to_history(
    history_file: Path,
    result: IterationResult,
    project: str
):
    """Append a single iteration record to the history JSONL file.

    Uses JSONL format (one JSON object per line) for efficient append-only writes
    and streaming reads. Each line contains a complete iteration record.
    """
    record = serialize_full_iteration(result)
    record["project"] = project
    record["recorded_at"] = datetime.now().isoformat()
    try:
        with open(history_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning(f"Failed to append to history file: {e}")


def write_history_summary(
    history_file: Path,
    project: str,
    started_at: datetime,
    ended_at: datetime,
    iteration_count: int,
    total_actions: int,
    stop_reason: str
):
    """Write a summary record to mark the end of a loop run.

    Written as a special record type at the end of the JSONL file.
    """
    summary = {
        "type": "loop_summary",
        "project": project,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "iteration_count": iteration_count,
        "total_actions": total_actions,
        "stop_reason": stop_reason
    }
    try:
        with open(history_file, "a") as f:
            f.write(json.dumps(summary) + "\n")
    except Exception as e:
        logger.warning(f"Failed to write history summary: {e}")


def generate_escalation_report(
    iterations: list[IterationResult],
    skip_list: SkipList,
    stop_reason: str
) -> dict:
    """Generate an actionable escalation report when the loop fails.

    Called when circuit breaker trips or all tasks are skipped.
    Provides context for human intervention.

    Returns:
        Dict with escalation details for status.json and logging
    """
    # Get recent failures from the last N iterations that weren't successful
    recent_failures = [
        {
            "iteration": i.iteration,
            "task_id": i.task_id,
            "task_title": i.task_title,
            "outcome": i.outcome,
            "serve_verdict": i.serve_verdict,
            "duration_seconds": i.duration_seconds
        }
        for i in iterations[-RECENT_ITERATIONS_LIMIT:]
        if not i.success
    ]

    # Get skipped tasks
    skipped_tasks = skip_list.get_skipped_tasks()

    # Suggested actions based on stop reason
    if stop_reason == "all_tasks_skipped":
        suggested_actions = [
            "Review the skipped tasks to understand failure patterns",
            "Check if tasks have missing dependencies or unclear requirements",
            "Consider breaking down complex tasks into smaller pieces",
            "Use 'bd show <task_id>' to see full task details",
            "Restart loop after fixing blocking issues: '/line:loop start'"
        ]
    elif stop_reason == "circuit_breaker":
        suggested_actions = [
            "Check recent failures for common patterns (timeouts, test failures, etc.)",
            "Review loop logs: '/line:loop tail --lines 100'",
            "Ensure test environment is healthy (database, services, etc.)",
            "Consider reducing task complexity or adding more context",
            "Restart loop after investigation: '/line:loop start'"
        ]
    else:
        suggested_actions = [
            "Review loop status: '/line:loop status'",
            "Check logs: '/line:loop tail --lines 100'"
        ]

    return {
        "stop_reason": stop_reason,
        "recent_failures": recent_failures,
        "skipped_tasks": skipped_tasks,
        "suggested_actions": suggested_actions,
        "generated_at": datetime.now().isoformat()
    }


def format_escalation_report(escalation: dict) -> str:
    """Format escalation report for human-readable output."""
    lines = [
        "",
        "=" * 60,
        "ESCALATION REPORT",
        "=" * 60,
        f"Stop reason: {escalation['stop_reason']}",
        ""
    ]

    if escalation['skipped_tasks']:
        lines.append("SKIPPED TASKS (too many failures):")
        for task in escalation['skipped_tasks']:
            lines.append(f"  - {task['id']}: {task['failure_count']} failures")
        lines.append("")

    if escalation['recent_failures']:
        lines.append("RECENT FAILURES:")
        for failure in escalation['recent_failures'][-RECENT_ITERATIONS_DISPLAY:]:
            task_info = f"{failure['task_id']}" if failure['task_id'] else "unknown"
            lines.append(f"  - #{failure['iteration']}: {task_info} ({failure['outcome']})")
        lines.append("")

    lines.append("SUGGESTED ACTIONS:")
    for action in escalation['suggested_actions']:
        lines.append(f"  • {action}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def write_status_file(
    status_file: Path,
    running: bool,
    iteration: int,
    max_iterations: int,
    current_task: Optional[str],
    current_task_title: Optional[str],
    last_verdict: Optional[str],
    tasks_completed: int,
    tasks_remaining: int,
    started_at: datetime,
    stop_reason: Optional[str] = None,
    iterations: Optional[list] = None,
    current_phase: Optional[str] = None,
    phase_start_time: Optional[datetime] = None,
    current_action_count: int = 0,
    last_action_time: Optional[datetime] = None,
    skipped_tasks: Optional[list] = None,
    escalation: Optional[dict] = None
):
    """Write live status JSON for external monitoring.

    Includes recent_iterations array with last 5 completed iterations
    for watch mode milestone display.

    Intra-iteration progress fields (for real-time visibility):
        current_phase: Currently executing phase (cook, serve, tidy, plate)
        phase_start_time: When the current phase started
        current_action_count: Number of tool actions in current phase
        last_action_time: Timestamp of most recent tool action

    Additional fields on failure:
        skipped_tasks: List of tasks skipped due to repeated failures
        escalation: Escalation report with suggested actions
    """
    status = {
        "running": running,
        "iteration": iteration,
        "max_iterations": max_iterations,
        "current_task": current_task,
        "current_task_title": current_task_title,
        "last_verdict": last_verdict,
        "tasks_completed": tasks_completed,
        "tasks_remaining": tasks_remaining,
        "started_at": started_at.isoformat(),
        "last_update": datetime.now().isoformat()
    }
    if stop_reason:
        status["stop_reason"] = stop_reason

    # Add intra-iteration progress fields
    if current_phase:
        status["current_phase"] = current_phase
    if phase_start_time:
        status["phase_start_time"] = phase_start_time.isoformat()
    if current_action_count > 0:
        status["current_action_count"] = current_action_count
    if last_action_time:
        status["last_action_time"] = last_action_time.isoformat()

    # Add recent_iterations (limited for display)
    if iterations:
        completed = [i for i in iterations if i.outcome == "completed"]
        recent = completed[-RECENT_ITERATIONS_DISPLAY:] if len(completed) > RECENT_ITERATIONS_DISPLAY else completed
        status["recent_iterations"] = [
            serialize_iteration_for_status(i) for i in recent
        ]
    else:
        status["recent_iterations"] = []

    # Add skipped tasks if any
    if skipped_tasks:
        status["skipped_tasks"] = skipped_tasks

    # Add escalation report if provided
    if escalation:
        status["escalation"] = escalation

    try:
        atomic_write(status_file, json.dumps(status, indent=2))
    except Exception as e:
        logger.warning(f"Failed to write status file: {e}")


def sync_at_start(cwd: Path, json_output: bool = False) -> bool:
    """Sync git and beads at loop start (once, not per-iteration).

    Returns True if sync succeeded, False on error.
    """
    logger.info("Syncing git and beads at loop start")

    if not json_output:
        print("Syncing...")

    # Git fetch and pull
    try:
        result = run_subprocess(["git", "fetch"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"git fetch failed: {result.stderr}")
        else:
            result = run_subprocess(["git", "pull", "--rebase"], GIT_SYNC_TIMEOUT, cwd)
            if result.returncode != 0:
                logger.warning(f"git pull --rebase failed: {result.stderr}")
                # Non-fatal - continue
    except subprocess.TimeoutExpired:
        logger.warning("git fetch/pull timed out")
    except Exception as e:
        logger.warning(f"git sync error: {e}")

    # Beads sync
    try:
        result = run_subprocess(["bd", "sync"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"bd sync failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.warning("bd sync timed out")
    except Exception as e:
        logger.warning(f"bd sync error: {e}")

    if not json_output:
        print("Sync complete.")

    return True


def run_loop(
    max_iterations: int,
    stop_on_blocked: bool,
    stop_on_crash: bool,
    max_retries: int,
    json_output: bool,
    output_file: Optional[Path],
    cwd: Path,
    status_file: Optional[Path] = None,
    history_file: Optional[Path] = None,
    break_on_epic: bool = False,
    skip_initial_sync: bool = False,
    phase_timeouts: Optional[dict[str, int]] = None,
    max_task_failures: int = DEFAULT_MAX_TASK_FAILURES,
    idle_timeout: int = DEFAULT_IDLE_TIMEOUT,
    idle_action: str = DEFAULT_IDLE_ACTION
) -> LoopReport:
    """Main loop: check ready, run iteration, handle outcome, repeat.

    Individual phases have their own timeouts via phase_timeouts dict
    or DEFAULT_PHASE_TIMEOUTS.

    Idle detection: If idle_timeout > 0, phases will be checked for idle
    (no tool actions within threshold). idle_action determines response:
    "warn" logs a warning, "terminate" stops the phase.
    """
    global _shutdown_requested

    started_at = datetime.now()
    iterations: list[IterationResult] = []
    completed_count = 0
    failed_count = 0
    stop_reason = "unknown"
    circuit_breaker = CircuitBreaker()
    skip_list = SkipList(max_failures=max_task_failures)

    logger.info(f"Loop starting: max_iterations={max_iterations}")

    if not json_output:
        print(f"Line Cook Loop starting (max {max_iterations} iterations)")
        print("=" * 44)

    # Sync git and beads once at loop start
    if not skip_initial_sync:
        sync_at_start(cwd, json_output)

    iteration = 0
    current_retries = 0
    last_task_id = None

    while iteration < max_iterations:
        # Check for shutdown request
        if _shutdown_requested:
            stop_reason = "shutdown"
            logger.info("Shutdown requested, stopping gracefully")
            if not json_output:
                print("\nShutdown requested. Stopping gracefully.")
            break

        # Check circuit breaker
        if circuit_breaker.is_open():
            stop_reason = "circuit_breaker"
            logger.warning("Circuit breaker tripped after consecutive failures")
            if not json_output:
                print("\nCircuit breaker tripped: too many consecutive failures. Stopping.")
            break

        # Check for ready work items (tasks + features, not epics)
        snapshot = get_bead_snapshot(cwd)
        ready_work_count = len(snapshot.ready_work_ids)

        if ready_work_count == 0:
            stop_reason = "no_work"
            if snapshot.ready_ids:
                logger.info(f"No work items ready ({len(snapshot.ready_ids)} epics ready), loop complete")
                if not json_output:
                    print(f"\nNo work items ready ({len(snapshot.ready_ids)} epics remain). Loop complete.")
            else:
                logger.info("No work items ready, loop complete")
                if not json_output:
                    print("\nNo work items ready. Loop complete.")
            break

        # Pre-cook task detection: identify target task before running cook
        # This helps correlate failures with specific tasks even if cook times out
        skipped_ids = skip_list.get_skipped_ids()
        next_task = get_next_ready_task(cwd, skip_ids=skipped_ids)

        if next_task:
            target_task_id, target_task_title = next_task
            logger.info(f"Target task: {target_task_id} - {target_task_title}")
        else:
            # All ready tasks are in skip list
            if skipped_ids:
                stop_reason = "all_tasks_skipped"
                logger.warning(f"All remaining tasks are skipped due to repeated failures: {skipped_ids}")
                if not json_output:
                    print(f"\nAll remaining tasks are skipped due to repeated failures.")
                    print(f"Skipped tasks: {', '.join(skipped_ids)}")
                break
            target_task_id, target_task_title = None, None

        iteration += 1

        if not json_output:
            print(f"\n[{iteration}/{max_iterations}] {ready_work_count} work items ready")
            if target_task_id:
                skipped_count = len(skipped_ids)
                skip_note = f" ({skipped_count} skipped)" if skipped_count > 0 else ""
                print(f"  Target: {target_task_id} - {target_task_title}{skip_note}")
            print("-" * 44)

        # Create progress state for real-time status updates during iteration
        progress_state = None
        if status_file:
            progress_state = ProgressState(
                status_file=status_file,
                iteration=iteration,
                max_iterations=max_iterations,
                current_task=target_task_id,  # Pre-detected target task
                current_task_title=target_task_title,
                tasks_completed=completed_count,
                tasks_remaining=ready_work_count,
                started_at=started_at,
                iterations=iterations
            )

        # Run iteration with individual phase invocations
        result = run_iteration(
            iteration, max_iterations, cwd,
            max_cook_retries=max_retries,
            json_output=json_output,
            progress_state=progress_state,
            phase_timeouts=phase_timeouts,
            idle_timeout=idle_timeout,
            idle_action=idle_action
        )
        iterations.append(result)

        # Circuit breaker: track failures, reset on success
        if result.success:
            # Reset on success to give fresh chances after recovery
            circuit_breaker.reset()
        else:
            # Only record failures for tracking
            circuit_breaker.record(False)

        if not json_output:
            print_human_iteration(result, current_retries)

        # Write status file after each iteration
        if status_file:
            # Note: completed_count hasn't been incremented yet, so add 1 if this iteration succeeded
            write_status_file(
                status_file=status_file,
                running=True,
                iteration=iteration,
                max_iterations=max_iterations,
                current_task=result.task_id,
                current_task_title=result.task_title,
                last_verdict=result.serve_verdict,
                tasks_completed=completed_count + (1 if result.success else 0),
                tasks_remaining=result.after_ready,  # Use data from iteration result
                started_at=started_at,
                iterations=iterations
            )

        # Append iteration to history JSONL file (full action details)
        if history_file:
            project_name = cwd.name
            append_iteration_to_history(
                history_file=history_file,
                result=result,
                project=project_name
            )

        # Handle outcome
        if result.outcome == "no_work":
            stop_reason = "no_work"
            break

        if result.outcome == "no_actionable_work":
            stop_reason = "no_actionable_work"
            logger.info("No actionable work found (e.g., only P4 parking lot items)")
            if not json_output:
                print("\nNo actionable tasks available. Stopping loop.")
            break

        if result.outcome == "completed":
            completed_count += 1
            current_retries = 0
            last_task_id = None
            # Clear failure count on success
            if result.task_id:
                skip_list.record_success(result.task_id)

        elif result.outcome == "needs_retry":
            if result.task_id == last_task_id:
                current_retries += 1
            else:
                current_retries = 1
                last_task_id = result.task_id

            if current_retries >= max_retries:
                failed_count += 1
                # Record failure to skip_list - may trigger skip
                if result.task_id:
                    now_skipped = skip_list.record_failure(result.task_id)
                    if now_skipped:
                        logger.warning(f"Task {result.task_id} added to skip list after {skip_list.max_failures} failures")
                        if not json_output:
                            print(f"\n  Task {result.task_id} added to skip list (too many failures).")
                current_retries = 0
                last_task_id = None
                if not json_output:
                    print(f"\n  Max retries ({max_retries}) reached. Moving on.")
            else:
                # Apply exponential backoff before retry
                delay = calculate_retry_delay(current_retries)
                logger.info(f"Retry {current_retries}/{max_retries} for {result.task_id}, waiting {delay:.1f}s")
                if not json_output:
                    print(f"\n  Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

        elif result.outcome == "blocked":
            failed_count += 1
            # Record failure to skip_list for blocked tasks
            if result.task_id:
                now_skipped = skip_list.record_failure(result.task_id)
                if now_skipped:
                    logger.warning(f"Task {result.task_id} added to skip list after repeated blocks")
                    if not json_output:
                        print(f"\n  Task {result.task_id} added to skip list (repeatedly blocked).")
            if stop_on_blocked:
                stop_reason = "blocked"
                logger.info("Task blocked, stopping (--stop-on-blocked)")
                if not json_output:
                    print("\nTask blocked. Stopping loop (--stop-on-blocked).")
                break
            current_retries = 0
            last_task_id = None

        elif result.outcome in ("crashed", "timeout"):
            failed_count += 1
            # Record failure to skip_list for crashed/timeout tasks
            if result.task_id:
                now_skipped = skip_list.record_failure(result.task_id)
                if now_skipped:
                    logger.warning(f"Task {result.task_id} added to skip list after {result.outcome}")
                    if not json_output:
                        print(f"\n  Task {result.task_id} added to skip list ({result.outcome}).")
            if stop_on_crash:
                stop_reason = result.outcome
                logger.info(f"Task {result.outcome}, stopping (--stop-on-crash)")
                if not json_output:
                    print(f"\nTask {result.outcome}. Stopping loop (--stop-on-crash).")
                break
            current_retries = 0
            last_task_id = None

        # Check for epic completions after each successful iteration
        if result.success and not json_output:
            epic_summaries = check_epic_completion(cwd)
            if epic_summaries:
                # Update status file with epic completions
                if status_file:
                    try:
                        status_content = json.loads(status_file.read_text())
                        status_content["epic_completions"] = [
                            {
                                "id": epic["id"],
                                "title": epic["title"],
                                "children_count": len(epic["children"]),
                                "completed_at": datetime.now().isoformat()
                            }
                            for epic in epic_summaries
                        ]
                        atomic_write(status_file, json.dumps(status_content, indent=2))
                    except Exception as e:
                        logger.debug(f"Failed to update status with epic completions: {e}")

                if break_on_epic:
                    stop_reason = "epic_complete"
                    logger.info(f"Epic(s) {[e['id'] for e in epic_summaries]} completed, breaking as requested")
                    print("\nEpic completed. Pausing loop (--break-on-epic).")
                    break

    else:
        stop_reason = "max_iterations"
        logger.info(f"Reached iteration limit ({max_iterations})")
        if not json_output:
            print(f"\nReached iteration limit ({max_iterations}). Stopping.")

    ended_at = datetime.now()
    duration = (ended_at - started_at).total_seconds()

    # Compute metrics
    metrics = LoopMetrics.from_iterations(iterations)

    report = LoopReport(
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        iterations=iterations,
        stop_reason=stop_reason,
        completed_count=completed_count,
        failed_count=failed_count,
        duration_seconds=duration
    )

    logger.info(f"Loop complete: {completed_count} completed, {failed_count} failed, reason={stop_reason}")

    # Generate escalation report if stopped due to failures
    escalation = None
    if stop_reason in ("circuit_breaker", "all_tasks_skipped"):
        escalation = generate_escalation_report(iterations, skip_list, stop_reason)
        # Print escalation report to console
        if not json_output:
            print(format_escalation_report(escalation))
        logger.warning(f"Escalation: {stop_reason} - {len(escalation.get('skipped_tasks', []))} tasks skipped")

    # Write final status (running=false)
    if status_file:
        final_snapshot = get_bead_snapshot(cwd)
        write_status_file(
            status_file=status_file,
            running=False,
            iteration=iteration,
            max_iterations=max_iterations,
            current_task=iterations[-1].task_id if iterations else None,
            current_task_title=iterations[-1].task_title if iterations else None,
            last_verdict=iterations[-1].serve_verdict if iterations else None,
            tasks_completed=completed_count,
            tasks_remaining=len(final_snapshot.ready_work_ids),
            started_at=started_at,
            stop_reason=stop_reason,
            iterations=iterations,
            skipped_tasks=skip_list.get_skipped_tasks(),
            escalation=escalation
        )

    # Write history summary record to mark end of loop
    if history_file:
        project_name = cwd.name
        write_history_summary(
            history_file=history_file,
            project=project_name,
            started_at=started_at,
            ended_at=ended_at,
            iteration_count=len(iterations),
            total_actions=sum(i.total_actions for i in iterations),
            stop_reason=stop_reason
        )

    # Print summary
    if not json_output:
        print()
        print("=" * 44)
        print("LOOP COMPLETE")
        print("=" * 44)
        print(f"Duration: {format_duration(duration)}")
        print(f"Completed: {completed_count} | Failed: {failed_count} | Blocked: {sum(1 for i in iterations if i.outcome == 'blocked')}")

        # Metrics
        if iterations:
            print(f"Success rate: {metrics.success_rate:.0%} | P50: {format_duration(metrics.p50_duration)} | P95: {format_duration(metrics.p95_duration)}")

        # Final state (show work items, note if epics remain)
        final_snapshot = get_bead_snapshot(cwd)
        work_count = len(final_snapshot.ready_work_ids)
        epic_count = len(final_snapshot.ready_ids) - work_count
        if epic_count > 0:
            print(f"Remaining ready: {work_count} work items ({epic_count} epics)")
        else:
            print(f"Remaining ready: {work_count}")

    # Output JSON
    if json_output or output_file:
        json_data = {
            "stop_reason": report.stop_reason,
            "summary": {
                "completed": report.completed_count,
                "failed": report.failed_count,
                "duration_seconds": report.duration_seconds
            },
            "metrics": {
                "success_rate": metrics.success_rate,
                "p50_duration": metrics.p50_duration,
                "p95_duration": metrics.p95_duration,
                "timeout_rate": metrics.timeout_rate,
                "retry_rate": metrics.retry_rate
            },
            "iterations": [
                {
                    "iteration": i.iteration,
                    "task_id": i.task_id,
                    "task_title": i.task_title,
                    "intent": i.intent,
                    "before_state": i.before_state,
                    "after_state": i.after_state,
                    "outcome": i.outcome,
                    "duration_seconds": i.duration_seconds,
                    "serve_verdict": i.serve_verdict,
                    "commit_hash": i.commit_hash,
                    "beads_before": {
                        "ready": i.before_ready,
                        "in_progress": i.before_in_progress
                    },
                    "beads_after": {
                        "ready": i.after_ready,
                        "in_progress": i.after_in_progress
                    }
                }
                for i in report.iterations
            ]
        }

        if json_output:
            print(json.dumps(json_data, indent=2))

        if output_file:
            output_file.write_text(json.dumps(json_data, indent=2))
            if not json_output:
                print(f"\nReport written to: {output_file}")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Line Cook autonomous loop - runs /line:run until no tasks remain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with defaults (25 iterations)
  %(prog)s --max-iterations 10      # Limit to 10 iterations
  %(prog)s --json                   # Output JSON instead of human-readable
  %(prog)s --json --output report.json  # Write JSON to file
  %(prog)s --stop-on-blocked        # Stop if any task is blocked
  %(prog)s --health-check           # Verify environment and exit
  %(prog)s --verbose --log-file loop.log  # Enable debug logging to file
"""
    )

    parser.add_argument(
        "-n", "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum iterations (default: {DEFAULT_MAX_ITERATIONS})"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of human-readable"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Write final report to file"
    )
    parser.add_argument(
        "--stop-on-blocked",
        action="store_true",
        help="Stop if task is BLOCKED (default: continue)"
    )
    parser.add_argument(
        "--stop-on-crash",
        action="store_true",
        help="Stop on claude crash (default: continue)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Max retries per task on NEEDS_CHANGES (default: 2)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Check environment health and exit"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file"
    )
    parser.add_argument(
        "--pid-file",
        type=Path,
        help="Write PID to file for external process management"
    )
    parser.add_argument(
        "--status-file",
        type=Path,
        help="Write live status JSON (default: /tmp/line-loop-{project}/status.json)"
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Write history JSONL (default: /tmp/line-loop-{project}/history.jsonl)"
    )
    parser.add_argument(
        "--break-on-epic",
        action="store_true",
        help="Pause loop when an epic completes (default: continue with summary)"
    )
    parser.add_argument(
        "--skip-initial-sync",
        action="store_true",
        help="Skip git fetch/pull and bd sync at loop start"
    )
    parser.add_argument(
        "--cook-timeout",
        type=int,
        default=DEFAULT_PHASE_TIMEOUTS['cook'],
        help=f"Cook phase timeout in seconds (default: {DEFAULT_PHASE_TIMEOUTS['cook']})"
    )
    parser.add_argument(
        "--serve-timeout",
        type=int,
        default=DEFAULT_PHASE_TIMEOUTS['serve'],
        help=f"Serve phase timeout in seconds (default: {DEFAULT_PHASE_TIMEOUTS['serve']})"
    )
    parser.add_argument(
        "--tidy-timeout",
        type=int,
        default=DEFAULT_PHASE_TIMEOUTS['tidy'],
        help=f"Tidy phase timeout in seconds (default: {DEFAULT_PHASE_TIMEOUTS['tidy']})"
    )
    parser.add_argument(
        "--plate-timeout",
        type=int,
        default=DEFAULT_PHASE_TIMEOUTS['plate'],
        help=f"Plate phase timeout in seconds (default: {DEFAULT_PHASE_TIMEOUTS['plate']})"
    )
    parser.add_argument(
        "--max-task-failures",
        type=int,
        default=DEFAULT_MAX_TASK_FAILURES,
        help=f"Skip task after this many failures (default: {DEFAULT_MAX_TASK_FAILURES})"
    )
    parser.add_argument(
        "--idle-timeout",
        type=int,
        default=DEFAULT_IDLE_TIMEOUT,
        help=f"Seconds without tool actions before idle triggers (default: {DEFAULT_IDLE_TIMEOUT}). Set to 0 to disable."
    )
    parser.add_argument(
        "--idle-action",
        choices=["warn", "terminate"],
        default=DEFAULT_IDLE_ACTION,
        help=f"Action to take when idle detected: warn (log warning) or terminate (stop phase) (default: {DEFAULT_IDLE_ACTION})"
    )

    args = parser.parse_args()

    cwd = Path.cwd()

    # Generate default paths for status/history files if not provided
    if args.status_file is None or args.history_file is None:
        loop_dir = Path("/tmp") / f"line-loop-{cwd.name}"
        loop_dir.mkdir(parents=True, exist_ok=True)

        if args.status_file is None:
            args.status_file = loop_dir / "status.json"

        if args.history_file is None:
            args.history_file = loop_dir / "history.jsonl"

    # Set up logging
    setup_logging(args.verbose, args.log_file)

    # Health check mode
    if args.health_check:
        health = check_health(cwd)
        if args.json:
            print(json.dumps(health, indent=2))
        else:
            print("Environment Health Check")
            print("=" * 30)
            for check, passed in health['checks'].items():
                status = "OK" if passed else "FAIL"
                print(f"  {check}: {status}")
            print("=" * 30)
            print(f"Overall: {'HEALTHY' if health['healthy'] else 'UNHEALTHY'}")
        sys.exit(0 if health['healthy'] else 1)

    # Write PID file if requested (atomic to prevent race on concurrent starts)
    if args.pid_file:
        try:
            atomic_write(args.pid_file, str(os.getpid()))
            logger.debug(f"Wrote PID {os.getpid()} to {args.pid_file}")
        except Exception as e:
            logger.warning(f"Failed to write PID file: {e}")

    # Build phase timeouts from CLI args
    phase_timeouts = {
        'cook': args.cook_timeout,
        'serve': args.serve_timeout,
        'tidy': args.tidy_timeout,
        'plate': args.plate_timeout,
    }

    try:
        report = run_loop(
            max_iterations=args.max_iterations,
            stop_on_blocked=args.stop_on_blocked,
            stop_on_crash=args.stop_on_crash,
            max_retries=args.max_retries,
            json_output=args.json,
            output_file=args.output,
            cwd=cwd,
            status_file=args.status_file,
            history_file=args.history_file,
            break_on_epic=args.break_on_epic,
            skip_initial_sync=args.skip_initial_sync,
            phase_timeouts=phase_timeouts,
            max_task_failures=args.max_task_failures,
            idle_timeout=args.idle_timeout,
            idle_action=args.idle_action
        )
    finally:
        # Clean up PID file on exit
        if args.pid_file and args.pid_file.exists():
            try:
                args.pid_file.unlink()
                logger.debug(f"Removed PID file {args.pid_file}")
            except Exception as e:
                logger.warning(f"Failed to remove PID file: {e}")

    # Exit with appropriate code
    if report.stop_reason in ("no_work", "no_actionable_work", "max_iterations", "shutdown", "epic_complete"):
        sys.exit(0)
    elif report.stop_reason == "blocked":
        sys.exit(1)
    elif report.stop_reason in ("circuit_breaker", "all_tasks_skipped"):
        sys.exit(3)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
