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
import os
import random
import re
import select
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# Constants
OUTPUT_SUMMARY_MAX_LENGTH = 200

# Phase timeouts (in seconds)
PHASE_TIMEOUTS = {
    'cook': 600,    # 10 min - Main work phase: TDD cycle, file edits, test runs
    'serve': 300,   # 5 min - Code review by sous-chef subagent
    'tidy': 120,    # 2 min - Commit, bd sync, git push
    'plate': 300,   # 5 min - BDD review via maître, acceptance doc
}

# Module-level logger
logger = logging.getLogger('line-loop')

# Global flag for graceful shutdown
_shutdown_requested = False


def _handle_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global _shutdown_requested
    _shutdown_requested = True
    logger.info(f"Shutdown requested (signal {signum})")


# Register signal handlers
signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)


def setup_logging(verbose: bool, log_file: Optional[Path] = None):
    """Configure logging with optional file output."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers
    )


def calculate_retry_delay(attempt: int, base: float = 2.0) -> float:
    """Exponential backoff with jitter: 2s, 4s, 8s... capped at 60s."""
    delay = min(base * (2 ** attempt), 60)
    return delay * random.uniform(0.8, 1.2)  # ±20% jitter


@dataclass
class CircuitBreaker:
    """Stops loop after too many consecutive failures."""
    failure_threshold: int = 5
    window_size: int = 10
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
        return input_data.get("file_path", "")[:100]
    elif tool_name == "Edit":
        path = input_data.get("file_path", "")
        return f"{path} (edit)"[:100]
    elif tool_name == "Bash":
        cmd = input_data.get("command", "")
        return cmd[:80] + ("..." if len(cmd) > 80 else "")
    elif tool_name == "Write":
        return f"{input_data.get('file_path', '')} (new)"[:100]
    elif tool_name in ("Glob", "Grep"):
        return input_data.get("pattern", "")[:60]
    elif tool_name == "Task":
        desc = input_data.get("description", "")
        return f"Task: {desc}"[:80]
    else:
        summary = str(input_data)
        return summary[:80] + ("..." if len(summary) > 80 else "")


@dataclass
class IterationResult:
    """Result of a single loop iteration."""
    iteration: int
    task_id: Optional[str]
    task_title: Optional[str]
    outcome: str  # "completed", "needs_retry", "blocked", "crashed", "timeout", "no_work"
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
    stop_reason: str  # "no_work", "max_iterations", "blocked", "error", "crashed", "epic_complete"
    completed_count: int
    failed_count: int
    duration_seconds: float


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


def get_bead_snapshot(cwd: Path) -> BeadSnapshot:
    """Capture ready/in_progress/closed issue IDs via bd --json."""
    snapshot = BeadSnapshot()

    # Get all ready items and filter work items (tasks + features, not epics)
    try:
        result = run_subprocess(["bd", "ready", "--json"], 30, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.ready_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
            # Filter work items (exclude epics) from the same parsed data
            snapshot.ready_work_ids = [
                i.get("id", "") for i in issues
                if isinstance(i, dict) and i.get("type") != "epic"
            ]
    except subprocess.TimeoutExpired:
        logger.warning("Timeout getting ready items")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse ready items JSON: {e}")
    except Exception as e:
        logger.debug(f"Error getting ready items: {e}")

    # Get in_progress tasks
    try:
        result = run_subprocess(["bd", "list", "--status=in_progress", "--json"], 30, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.in_progress_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except subprocess.TimeoutExpired:
        logger.warning("Timeout getting in_progress tasks")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse in_progress tasks JSON: {e}")
    except Exception as e:
        logger.debug(f"Error getting in_progress tasks: {e}")

    # Get recently closed tasks (limit 10 for performance)
    try:
        result = run_subprocess(["bd", "list", "--status=closed", "--limit=10", "--json"], 30, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.closed_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except subprocess.TimeoutExpired:
        logger.warning("Timeout getting closed tasks")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse closed tasks JSON: {e}")
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
        result = run_subprocess(["bd", "show", task_id, "--json"], 30, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issue = json.loads(result.stdout)
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
            result = run_subprocess(["bd", "show", task_id, "--json"], 10, cwd)
            if result.returncode == 0 and result.stdout.strip():
                task_data = json.loads(result.stdout)
                if task_data.get("status") == "closed":
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
                # Remove from pending after processing
                del pending_actions[tool_use_id]


def get_latest_commit(cwd: Path) -> Optional[str]:
    """Get the latest commit hash."""
    try:
        result = run_subprocess(["git", "log", "-1", "--format=%h"], 10, cwd)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Error getting latest commit: {e}")
    return None


def run_phase(
    phase: str,
    cwd: Path,
    args: str = "",
    timeout: Optional[int] = None
) -> PhaseResult:
    """Invoke a single Line Cook skill phase (cook, serve, tidy, plate).

    Args:
        phase: Phase name (cook, serve, tidy, plate)
        cwd: Working directory
        args: Optional arguments (e.g., task ID for cook)
        timeout: Override default phase timeout

    Returns:
        PhaseResult with output, signals, and success status
    """
    if timeout is None:
        timeout = PHASE_TIMEOUTS.get(phase, 600)

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
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Phase {phase} process did not terminate after kill")
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
            else:
                if process.poll() is not None:
                    break

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
    success = exit_code == 0

    logger.debug(f"Phase {phase} completed in {duration:.1f}s, exit={exit_code}, signals={signals}")

    return PhaseResult(
        phase=phase,
        success=success,
        output=output,
        exit_code=exit_code,
        duration_seconds=duration,
        signals=signals,
        actions=actions,
        error=None if success else f"Exit code {exit_code}"
    )


def get_task_info(task_id: str, cwd: Path) -> Optional[dict]:
    """Get task info including parent and status."""
    try:
        result = run_subprocess(["bd", "show", task_id, "--json"], 10, cwd)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get task info for {task_id}: {e}")
    except Exception as e:
        logger.debug(f"Error getting task info for {task_id}: {e}")
    return None


def get_children(parent_id: str, cwd: Path) -> list[dict]:
    """Get all children of a parent issue."""
    try:
        result = run_subprocess(
            ["bd", "list", f"--parent={parent_id}", "--all", "--json"],
            30, cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            children = json.loads(result.stdout)
            return [c for c in children if isinstance(c, dict)]
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        logger.warning(f"Failed to get children for {parent_id}: {e}")
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
        if len(goal) > 200:
            goal = goal[:197] + "..."
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
        result = run_subprocess(["bd", "show", epic_id, "--json"], 10, cwd)
        if result.returncode == 0 and result.stdout.strip():
            epic = json.loads(result.stdout)
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
            30, cwd
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
    width = max(62, len(header) + 4)

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
            30, cwd
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
        result = run_subprocess(["bd", "epic", "close-eligible"], 30, cwd)
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
    json_output: bool = False
) -> IterationResult:
    """Execute individual phases (cook→serve→tidy) with retry logic.

    This replaces the monolithic /line:run invocation with separate phase calls,
    enabling better error detection, retry on NEEDS_CHANGES, and feature/epic
    completion triggers.

    Phase timeouts are controlled by PHASE_TIMEOUTS dict (cook=600s, serve=300s,
    tidy=120s, plate=300s).

    Args:
        iteration: Current iteration number
        max_iterations: Maximum iterations for logging
        cwd: Working directory
        max_cook_retries: Max retries on NEEDS_CHANGES verdict
        json_output: If True, suppress human-readable phase output
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

    # ===== PHASE 1: COOK (with retry loop) =====
    cook_attempts = 0
    cook_succeeded = False

    while cook_attempts <= max_cook_retries:
        cook_attempts += 1
        logger.info(f"Cook phase attempt {cook_attempts}/{max_cook_retries + 1}")

        # Run cook phase
        cook_result = run_phase("cook", cwd)
        all_actions.extend(cook_result.actions)
        all_output.append(f"=== COOK PHASE (attempt {cook_attempts}) ===\n")
        all_output.append(cook_result.output)

        if cook_result.error and "Timeout" in cook_result.error:
            # Timeout during cook - check if task completed anyway
            after = get_bead_snapshot(cwd)
            task_id = detect_worked_task(before, after)
            if task_id:
                task_info = get_task_info(task_id, cwd)
                if task_info and task_info.get("status") == "closed":
                    logger.info(f"Cook timed out but task {task_id} was closed")
                    cook_succeeded = True
                    break

            logger.warning(f"Cook phase timed out on attempt {cook_attempts}")
            if cook_attempts > max_cook_retries:
                duration = (datetime.now() - start_time).total_seconds()
                after = get_bead_snapshot(cwd)
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
                    after_ready=len(after.ready_ids),
                    after_in_progress=len(after.in_progress_ids),
                    actions=all_actions
                )
            continue

        if not cook_result.success:
            logger.warning(f"Cook phase failed on attempt {cook_attempts}: {cook_result.error}")
            if cook_attempts > max_cook_retries:
                break
            continue

        # Cook succeeded, detect task
        after_cook = get_bead_snapshot(cwd)
        task_id = detect_worked_task(before, after_cook)
        logger.debug(f"Detected task: {task_id}")

        # Check for KITCHEN_COMPLETE signal
        if "kitchen_complete" in cook_result.signals:
            cook_succeeded = True
            break

        # ===== PHASE 2: SERVE =====
        logger.info("Serve phase")
        serve_result = run_phase("serve", cwd)
        all_actions.extend(serve_result.actions)
        all_output.append("\n=== SERVE PHASE ===\n")
        all_output.append(serve_result.output)

        if serve_result.error:
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
                cook_succeeded = True
                break
            elif serve_verdict == "NEEDS_CHANGES":
                logger.info(f"NEEDS_CHANGES - will retry cook (attempt {cook_attempts}/{max_cook_retries + 1})")
                # Cook will read the rework comment on next attempt
                if cook_attempts > max_cook_retries:
                    logger.warning("Max cook retries reached with NEEDS_CHANGES")
                    break
                continue
            elif serve_verdict == "BLOCKED":
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
                logger.info("Serve skipped (transient error) - continuing")
                cook_succeeded = True
                break
        else:
            # No SERVE_RESULT found - check signals
            if "serve_approved" in serve_result.signals:
                serve_verdict = "APPROVED"
                cook_succeeded = True
                break
            elif "serve_needs_changes" in serve_result.signals:
                serve_verdict = "NEEDS_CHANGES"
                if cook_attempts > max_cook_retries:
                    break
                continue
            else:
                # Assume success if serve completed without error
                logger.debug("No serve verdict found, assuming approved")
                serve_verdict = "APPROVED"
                cook_succeeded = True
                break

    # Check if we exhausted retries
    if not cook_succeeded:
        duration = (datetime.now() - start_time).total_seconds()
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
            after_ready=len(after.ready_ids) if after else len(before.ready_ids),
            after_in_progress=len(after.in_progress_ids) if after else len(before.in_progress_ids),
            actions=all_actions
        )

    # ===== PHASE 3: TIDY =====
    logger.info("Tidy phase")
    tidy_result = run_phase("tidy", cwd)
    all_actions.extend(tidy_result.actions)
    all_output.append("\n=== TIDY PHASE ===\n")
    all_output.append(tidy_result.output)

    if tidy_result.error:
        logger.warning(f"Tidy phase error: {tidy_result.error}")
        # Tidy errors are concerning but not fatal

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
            logger.info(f"Feature {feature_id} is complete, triggering plate phase")
            if not json_output:
                print(f"\n  Feature complete: {feature_id} - triggering plate phase")

            plate_result = run_phase("plate", cwd, args=feature_id)
            all_actions.extend(plate_result.actions)
            all_output.append("\n=== PLATE PHASE ===\n")
            all_output.append(plate_result.output)

            if plate_result.error:
                logger.warning(f"Plate phase error: {plate_result.error}")
            else:
                # Check if completing the feature completes an epic
                epic_complete, epic_id = check_epic_completion_after_feature(feature_id, cwd)
                if epic_complete and epic_id:
                    logger.info(f"Epic {epic_id} is complete")
                    report = generate_epic_closure_report(epic_id, cwd)
                    if not json_output:
                        print(report)

                    # Close the epic
                    try:
                        run_subprocess(["bd", "close", epic_id], 30, cwd)
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


def print_human_iteration(result: IterationResult, retries: int = 0):
    """Print iteration result in human-readable format."""
    # Status indicator
    status_map = {
        "completed": "[OK]",
        "needs_retry": "[RETRY]",
        "blocked": "[BLOCKED]",
        "crashed": "[CRASH]",
        "timeout": "[TIMEOUT]",
        "no_work": "[DONE]"
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


def write_status_file(
    status_file: Path,
    running: bool,
    iteration: int,
    max_iterations: int,
    current_task: Optional[str],
    last_verdict: Optional[str],
    tasks_completed: int,
    tasks_remaining: int,
    started_at: datetime,
    stop_reason: Optional[str] = None,
    iterations: Optional[list] = None
):
    """Write live status JSON for external monitoring.

    Includes recent_iterations array with last 5 completed iterations
    for watch mode milestone display.
    """
    status = {
        "running": running,
        "iteration": iteration,
        "max_iterations": max_iterations,
        "current_task": current_task,
        "last_verdict": last_verdict,
        "tasks_completed": tasks_completed,
        "tasks_remaining": tasks_remaining,
        "started_at": started_at.isoformat(),
        "last_update": datetime.now().isoformat()
    }
    if stop_reason:
        status["stop_reason"] = stop_reason

    # Add recent_iterations (last 5 completed iterations)
    if iterations:
        completed = [i for i in iterations if i.outcome == "completed"]
        recent = completed[-5:] if len(completed) > 5 else completed
        status["recent_iterations"] = [
            serialize_iteration_for_status(i) for i in recent
        ]
    else:
        status["recent_iterations"] = []

    try:
        status_file.write_text(json.dumps(status, indent=2))
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
        result = run_subprocess(["git", "fetch"], 60, cwd)
        if result.returncode != 0:
            logger.warning(f"git fetch failed: {result.stderr}")
        else:
            result = run_subprocess(["git", "pull", "--rebase"], 60, cwd)
            if result.returncode != 0:
                logger.warning(f"git pull --rebase failed: {result.stderr}")
                # Non-fatal - continue
    except subprocess.TimeoutExpired:
        logger.warning("git fetch/pull timed out")
    except Exception as e:
        logger.warning(f"git sync error: {e}")

    # Beads sync
    try:
        result = run_subprocess(["bd", "sync"], 60, cwd)
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
    timeout: int,  # Deprecated: phases use PHASE_TIMEOUTS instead
    stop_on_blocked: bool,
    stop_on_crash: bool,
    max_retries: int,
    json_output: bool,
    output_file: Optional[Path],
    cwd: Path,
    status_file: Optional[Path] = None,
    history_file: Optional[Path] = None,
    break_on_epic: bool = False,
    skip_initial_sync: bool = False
) -> LoopReport:
    """Main loop: check ready, run iteration, handle outcome, repeat.

    Note: The timeout parameter is kept for CLI compatibility but is no longer
    used. Individual phases have their own timeouts via PHASE_TIMEOUTS.
    """
    global _shutdown_requested

    started_at = datetime.now()
    iterations: list[IterationResult] = []
    completed_count = 0
    failed_count = 0
    stop_reason = "unknown"
    circuit_breaker = CircuitBreaker()

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

        iteration += 1

        if not json_output:
            print(f"\n[{iteration}/{max_iterations}] {ready_work_count} work items ready")
            print("-" * 44)

        # Run iteration with individual phase invocations
        result = run_iteration(
            iteration, max_iterations, cwd,
            max_cook_retries=max_retries,
            json_output=json_output
        )
        iterations.append(result)

        # Record result for circuit breaker
        circuit_breaker.record(result.success)

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

        if result.outcome == "completed":
            completed_count += 1
            current_retries = 0
            last_task_id = None

        elif result.outcome == "needs_retry":
            if result.task_id == last_task_id:
                current_retries += 1
            else:
                current_retries = 1
                last_task_id = result.task_id

            if current_retries >= max_retries:
                failed_count += 1
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
                        status_file.write_text(json.dumps(status_content, indent=2))
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

    # Write final status (running=false)
    if status_file:
        final_snapshot = get_bead_snapshot(cwd)
        write_status_file(
            status_file=status_file,
            running=False,
            iteration=iteration,
            max_iterations=max_iterations,
            current_task=iterations[-1].task_id if iterations else None,
            last_verdict=iterations[-1].serve_verdict if iterations else None,
            tasks_completed=completed_count,
            tasks_remaining=len(final_snapshot.ready_ids),
            started_at=started_at,
            stop_reason=stop_reason,
            iterations=iterations
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

        # Final state
        final_snapshot = get_bead_snapshot(cwd)
        print(f"Remaining ready: {len(final_snapshot.ready_ids)}")

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
        default=25,
        help="Maximum iterations (default: 25)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=600,
        help="Per-iteration timeout in seconds (default: 600)"
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
        help="Write live status JSON after each iteration"
    )
    parser.add_argument(
        "--history-file",
        type=Path,
        help="Write complete history JSONL (one JSON record per line) with all iterations and action details"
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

    args = parser.parse_args()

    cwd = Path.cwd()

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

    # Write PID file if requested
    if args.pid_file:
        try:
            args.pid_file.write_text(str(os.getpid()))
            logger.debug(f"Wrote PID {os.getpid()} to {args.pid_file}")
        except Exception as e:
            logger.warning(f"Failed to write PID file: {e}")

    try:
        report = run_loop(
            max_iterations=args.max_iterations,
            timeout=args.timeout,
            stop_on_blocked=args.stop_on_blocked,
            stop_on_crash=args.stop_on_crash,
            max_retries=args.max_retries,
            json_output=args.json,
            output_file=args.output,
            cwd=cwd,
            status_file=args.status_file,
            history_file=args.history_file,
            break_on_epic=args.break_on_epic,
            skip_initial_sync=args.skip_initial_sync
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
    if report.stop_reason in ("no_work", "max_iterations", "shutdown", "epic_complete"):
        sys.exit(0)
    elif report.stop_reason == "blocked":
        sys.exit(1)
    elif report.stop_reason == "circuit_breaker":
        sys.exit(3)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
