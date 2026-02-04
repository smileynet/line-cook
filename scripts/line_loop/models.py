"""Data models for line-loop state tracking.

Dataclasses for:
- CircuitBreaker: Failure rate tracking with sliding window
- LoopError: Structured error with severity and context
- SkipList: Track tasks to skip after repeated failures
- LoopMetrics: Computed metrics from iterations
- BeadSnapshot: Task state at a point in time
- ServeResult: Parsed SERVE_RESULT block
- ServeFeedbackIssue: Single issue from review
- ServeFeedback: Detailed review feedback
- PhaseResult: Outcome of a single phase
- ActionRecord: Tool action tracking
- IterationResult: Single loop iteration outcome
- LoopReport: Final summary
- ProgressState: Current progress for status file
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

from .config import (
    CIRCUIT_BREAKER_WINDOW_SIZE,
    DEFAULT_MAX_TASK_FAILURES,
    INPUT_SUMMARY_COMMAND_LENGTH,
    INPUT_SUMMARY_FILE_PATH_LENGTH,
    INPUT_SUMMARY_PATTERN_LENGTH,
)

if TYPE_CHECKING:
    from typing import Protocol

    class StatusWriter(Protocol):
        """Protocol for status file writing callback."""
        def __call__(
            self,
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
            iterations: list,
            current_phase: Optional[str] = None,
            phase_start_time: Optional[datetime] = None,
            current_action_count: int = 0,
            last_action_time: Optional[datetime] = None
        ) -> None: ...


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
class BeadInfo:
    """Metadata for a single bead (issue).

    Stores the essential fields from bd JSON output so callers
    don't need to re-query for title, type, or hierarchy info.
    """
    id: str
    title: str
    issue_type: str  # "epic", "feature", "task"
    parent: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None


@dataclass
class BeadSnapshot:
    """State of beads at a point in time.

    Stores full BeadInfo objects for each bead, with backwards-compatible
    properties that return ID lists for existing callers.
    """
    ready: list[BeadInfo] = field(default_factory=list)
    in_progress: list[BeadInfo] = field(default_factory=list)
    closed: list[BeadInfo] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    @property
    def ready_ids(self) -> list[str]:
        return [b.id for b in self.ready]

    @property
    def ready_work_ids(self) -> list[str]:
        """Ready work items (tasks + features, excluding epics)."""
        return [b.id for b in self.ready if b.issue_type != "epic"]

    @property
    def ready_work(self) -> list[BeadInfo]:
        """Ready work items as BeadInfo objects (tasks + features, excluding epics)."""
        return [b for b in self.ready if b.issue_type != "epic"]

    @property
    def in_progress_ids(self) -> list[str]:
        return [b.id for b in self.in_progress]

    @property
    def closed_ids(self) -> list[str]:
        return [b.id for b in self.closed]

    def get_by_id(self, bead_id: str) -> Optional[BeadInfo]:
        """Look up a BeadInfo by ID across all lists."""
        for b in self.ready + self.in_progress + self.closed:
            if b.id == bead_id:
                return b
        return None


@dataclass
class BeadDelta:
    """Diff between two snapshots showing what changed during an iteration."""
    newly_closed: list[BeadInfo]
    newly_filed: list[BeadInfo]

    @classmethod
    def compute(cls, before: "BeadSnapshot", after: "BeadSnapshot") -> "BeadDelta":
        """Compute the delta between two snapshots.

        newly_closed: beads in after.closed that weren't in before.closed
        newly_filed: beads in after.ready that weren't in any before list
        """
        before_closed = set(before.closed_ids)
        newly_closed = [b for b in after.closed if b.id not in before_closed]

        before_all = set(before.ready_ids + before.in_progress_ids + before.closed_ids)
        newly_filed = [b for b in after.ready if b.id not in before_all]

        return cls(newly_closed=newly_closed, newly_filed=newly_filed)


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


def summarize_tool_input(tool_name: str, input_data: dict) -> str:
    """Create concise summary of tool input for action tracking.

    Generates a human-readable summary of what a tool call is doing,
    truncated to fit in logs and status displays. Different tools have
    different relevant fields to summarize.

    Args:
        tool_name: Name of the tool (Read, Edit, Bash, Write, Glob, Grep, Task, etc.)
        input_data: The input parameters passed to the tool.

    Returns:
        Truncated summary string (max ~100 chars depending on tool type).
    """
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

    # Bead delta (what changed during this iteration)
    delta: Optional[BeadDelta] = None

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

    Note:
        The _status_writer callback must be injected for status file updates to work.
        If status_file is set but _status_writer is None, updates are silently skipped.
        This design avoids circular imports between models and I/O modules.
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

    # Status writer callback (injected to avoid circular imports)
    _status_writer: Optional[Callable] = None

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
        if not self.status_file or not self._status_writer:
            return
        self._status_writer(
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
