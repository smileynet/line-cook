"""Main loop orchestration for line-loop.

Functions for the outer loop:
- run_loop: Main entry point for autonomous loop execution
- sync_at_start: Initial git/bead sync
- write_status_file: Progress tracking for external monitoring
- generate_escalation_report: Report failures for human intervention

Also includes helper functions for:
- Serialization (serialize_iteration_for_status, serialize_action, serialize_full_iteration)
- History tracking (append_iteration_to_history, write_history_summary)
- Retry delay calculation (calculate_retry_delay)
- Task selection (get_next_ready_task)
"""

from __future__ import annotations

import json
import logging
import random
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import (
    BD_COMMAND_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_MAX_TASK_FAILURES,
    EXCLUDED_EPIC_TITLES,
    GIT_SYNC_TIMEOUT,
    MAX_RETRY_DELAY_SECONDS,
    PERIODIC_SYNC_INTERVAL,
    RECENT_ITERATIONS_DISPLAY,
    RECENT_ITERATIONS_LIMIT,
)
from .models import (
    ActionRecord,
    BeadInfo,
    BeadSnapshot,
    CircuitBreaker,
    IterationResult,
    LoopError,
    LoopMetrics,
    LoopReport,
    ProgressState,
    SkipList,
)
from .iteration import (
    atomic_write,
    build_epic_ancestor_map,
    build_hierarchy_chain,
    check_epic_completion,
    find_epic_ancestor,
    format_duration,
    get_bead_snapshot,
    get_current_branch,
    get_epic_for_task,
    get_task_title,
    is_descendant_of_epic,
    is_first_epic_work,
    parse_bd_json_item,
    print_human_iteration,
    run_iteration,
)
from .phase import run_subprocess

logger = logging.getLogger(__name__)

# Global shutdown flag for graceful termination
_shutdown_requested = False


def request_shutdown() -> None:
    """Request graceful shutdown of the loop.

    Sets the internal flag that run_loop checks between iterations.
    Call this from a signal handler (e.g., SIGINT, SIGTERM) to stop
    the loop gracefully after the current iteration completes.

    Example:
        import signal
        from line_loop import request_shutdown

        signal.signal(signal.SIGINT, lambda s, f: request_shutdown())
        signal.signal(signal.SIGTERM, lambda s, f: request_shutdown())
    """
    global _shutdown_requested
    _shutdown_requested = True


def reset_shutdown_flag() -> None:
    """Reset the shutdown flag (for testing or loop restart)."""
    global _shutdown_requested
    _shutdown_requested = False


def calculate_retry_delay(attempt: int, base: float = 2.0) -> float:
    """Exponential backoff with jitter: 2s, 4s, 8s... capped at MAX_RETRY_DELAY_SECONDS."""
    delay = min(base * (2 ** attempt), MAX_RETRY_DELAY_SECONDS)
    jitter = random.uniform(0.8, 1.2)
    return delay * jitter


def should_periodic_sync(iteration: int, interval: int) -> bool:
    """Check if periodic sync should run at this iteration.

    Returns True when iteration is a positive multiple of interval.
    Returns False at iteration 0 (before first iteration).
    """
    return iteration > 0 and iteration % interval == 0


def periodic_sync(cwd: Path) -> bool:
    """Run bd sync for periodic state refresh during long loops.

    Args:
        cwd: Working directory containing the .beads project.

    Returns:
        True if sync succeeded, False on any failure.
    """
    try:
        result = run_subprocess(["bd", "sync"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"Periodic bd sync failed: {result.stderr}")
            return False
        logger.info("Periodic bd sync completed")
        return True
    except subprocess.TimeoutExpired:
        logger.warning("Periodic bd sync timed out")
        return False
    except Exception as e:
        logger.warning(f"Periodic bd sync error: {e}")
        return False


def get_excluded_epic_ids(snapshot: BeadSnapshot) -> set[str]:
    """Find IDs of Retrospective/Backlog epics in the snapshot.

    Scans snapshot.ready (not all beads) for epics whose title matches
    EXCLUDED_EPIC_TITLES. This is sufficient because excluded epics must
    be in the ready list to affect task selection.

    Args:
        snapshot: Current BeadSnapshot.

    Returns:
        Set of epic IDs that should be excluded from auto-selection.
    """
    return {
        b.id for b in snapshot.ready
        if b.issue_type == "epic" and b.title in EXCLUDED_EPIC_TITLES
    }


def detect_first_epic(
    snapshot: BeadSnapshot, excluded_ids: set[str],
    skip_ids: set[str], cwd: Path,
    exhausted_ids: Optional[set[str]] = None,
    ancestor_map: Optional[dict[str, Optional[str]]] = None
) -> Optional[tuple[str, str]]:
    """Find the epic of the highest-priority ready work item.

    For --epic (no ID) mode: auto-detect the first non-excluded epic,
    scanning ready work items in priority order.

    Args:
        snapshot: Current BeadSnapshot.
        excluded_ids: Set of epic IDs to exclude (Retrospective/Backlog).
        skip_ids: Set of task IDs to skip (from failure tracking).
        cwd: Working directory containing the .beads project.
        exhausted_ids: Set of epic IDs already tried with no remaining work.
        ancestor_map: Pre-computed bead→epic map (avoids per-item hierarchy walks).

    Returns:
        Tuple of (epic_id, epic_title) or None if no epic found.
    """
    exhausted_set = exhausted_ids or set()
    for bead in snapshot.ready_work:
        if bead.id in skip_ids:
            continue
        if ancestor_map is not None:
            epic_id = ancestor_map.get(bead.id)
            if epic_id and epic_id not in excluded_ids and epic_id not in exhausted_set:
                epic_info = snapshot.get_by_id(epic_id)
                title = epic_info.title if epic_info else ""
                return (epic_id, title)
        else:
            epic = find_epic_ancestor(bead, snapshot, cwd)
            if epic and epic.id not in excluded_ids and epic.id not in exhausted_set:
                return (epic.id, epic.title)
    return None


def validate_epic_id(epic_id: str, cwd: Path) -> Optional[str]:
    """Validate that an ID refers to an epic and return its title.

    Args:
        epic_id: The bead ID to validate.
        cwd: Working directory containing the .beads project.

    Returns:
        Epic title if valid, or None if not found or not an epic.
    """
    try:
        result = run_subprocess(["bd", "show", epic_id, "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            issue = parse_bd_json_item(data)
            if issue and issue.get("issue_type") == "epic":
                return issue.get("title", "")
    except Exception as e:
        logger.debug(f"Error validating epic {epic_id}: {e}")
    return None


def _filter_excluded_epics(
    beads: list[BeadInfo], excluded_ids: set[str],
    snapshot: BeadSnapshot, cwd: Path,
    ancestor_map: Optional[dict[str, Optional[str]]] = None
) -> list[BeadInfo]:
    """Filter out beads that descend from excluded epics."""
    if ancestor_map is not None:
        result = []
        for b in beads:
            epic_id = ancestor_map.get(b.id)
            if epic_id is None or epic_id not in excluded_ids:
                result.append(b)
        return result
    result = []
    for b in beads:
        ancestor = find_epic_ancestor(b, snapshot, cwd)
        if ancestor is None or ancestor.id not in excluded_ids:
            result.append(b)
    return result


def get_next_ready_task(
    cwd: Path,
    skip_ids: Optional[set[str]] = None,
    snapshot: Optional[BeadSnapshot] = None,
    epic_filter: Optional[str] = None,
    excluded_epic_ids: Optional[set[str]] = None,
    ancestor_map: Optional[dict[str, Optional[str]]] = None
) -> Optional[tuple[str, str]]:
    """Get the next ready task ID and title before cook runs.

    Mimics cook.md selection: highest priority work item (not epic).
    Prefers tasks over features when both are available, since tasks
    are more granular and directly workable.

    Args:
        cwd: Working directory
        skip_ids: Optional set of task IDs to skip (due to repeated failures)
        snapshot: Optional BeadSnapshot to use instead of re-querying bd
        epic_filter: Only return tasks under this epic ID
        excluded_epic_ids: Skip tasks under these epic IDs
        ancestor_map: Pre-computed bead→epic map (avoids per-item hierarchy walks).

    Returns:
        Tuple of (task_id, task_title) or None if no tasks ready
    """
    skip_ids = skip_ids or set()

    if snapshot:
        candidates = snapshot.ready_work
        if epic_filter:
            if ancestor_map is not None:
                candidates = [
                    b for b in candidates
                    if ancestor_map.get(b.id) == epic_filter
                ]
            else:
                candidates = [
                    b for b in candidates
                    if is_descendant_of_epic(b, epic_filter, snapshot, cwd)
                ]
        elif excluded_epic_ids:
            candidates = _filter_excluded_epics(
                candidates, excluded_epic_ids, snapshot, cwd,
                ancestor_map=ancestor_map
            )
        # Two-pass: prefer tasks over features
        for bead in candidates:
            if bead.id not in skip_ids and bead.issue_type == "task":
                return (bead.id, bead.title)
        for bead in candidates:
            if bead.id not in skip_ids:
                return (bead.id, bead.title)
        return None

    # Fallback: query bd directly (no snapshot available for hierarchy walks)
    if epic_filter or excluded_epic_ids:
        logger.warning(
            "get_next_ready_task called with epic_filter=%s excluded_epic_ids=%s "
            "but no snapshot — filtering cannot be applied in fallback path",
            epic_filter, excluded_epic_ids
        )
    cmd = "bd ready --json"
    try:
        result = run_subprocess(["bd", "ready", "--json"], BD_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            # Two-pass: prefer tasks over features
            work_items = [
                i for i in issues
                if isinstance(i, dict) and i.get("issue_type") != "epic"
                and i.get("id", "") and i.get("id", "") not in skip_ids
            ]
            for issue in work_items:
                if issue.get("issue_type") == "task":
                    return (issue["id"], issue.get("title", ""))
            for issue in work_items:
                return (issue["id"], issue.get("title", ""))
    except subprocess.TimeoutExpired:
        err = LoopError.from_timeout(cmd, BD_COMMAND_TIMEOUT)
        logger.warning(str(err))
    except json.JSONDecodeError as e:
        err = LoopError.from_json_decode("bd ready output", e)
        logger.warning(str(err))
    except Exception as e:
        logger.debug(f"Error getting next ready task: {e}")
    return None


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
        "action_types": result.action_counts,
        # Findings filed during iteration
        "findings_count": result.findings_count
    }


def serialize_action(action: ActionRecord) -> dict:
    """Serialize an ActionRecord for history JSONL."""
    data = {
        "tool": action.tool_name,
        "timestamp": action.timestamp,
    }
    if action.duration_ms is not None:
        data["duration_ms"] = round(action.duration_ms)
    return data


def serialize_full_iteration(result: IterationResult) -> dict:
    """Serialize an IterationResult with full action details for history.json."""
    data = {
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
        "findings_count": result.findings_count,
        "actions": [serialize_action(a) for a in result.actions]
    }
    if result.delta:
        data["delta"] = {
            "newly_closed": [
                {"id": b.id, "title": b.title, "type": b.issue_type}
                for b in result.delta.newly_closed
            ],
            "newly_filed": [
                {"id": b.id, "title": b.title, "type": b.issue_type}
                for b in result.delta.newly_filed
            ],
        }
    return data


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

    skipped_tasks = escalation['skipped_tasks']
    if skipped_tasks:
        lines.append("SKIPPED TASKS (too many failures):")
        for task in skipped_tasks:
            lines.append(f"  - {task['id']}: {task['failure_count']} failures")
        lines.append("")

    recent_failures = escalation['recent_failures']
    if recent_failures:
        lines.append("RECENT FAILURES:")
        for failure in recent_failures[-RECENT_ITERATIONS_DISPLAY:]:
            task_info = failure['task_id'] if failure['task_id'] else "unknown"
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
    escalation: Optional[dict] = None,
    epic_mode: Optional[str] = None,
    current_epic: Optional[str] = None
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

    # Add epic mode fields
    if epic_mode:
        status["epic_mode"] = epic_mode
    if current_epic:
        status["current_epic"] = current_epic

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
        if len(completed) > RECENT_ITERATIONS_DISPLAY:
            recent = completed[-RECENT_ITERATIONS_DISPLAY:]
        else:
            recent = completed
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

    Performs git fetch + pull --rebase and bd sync to ensure the loop
    starts with the latest code and bead state. Runs once at startup
    rather than per-iteration for efficiency.

    Args:
        cwd: Working directory of the git repository.
        json_output: If True, suppress human-readable progress messages.

    Returns:
        True if sync completed (even with warnings), False on fatal error.

    Note:
        Individual sync failures (git fetch, git pull, bd sync) are logged
        as warnings but don't fail the overall sync. The loop can proceed
        with potentially stale state.
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
                if "no tracking information" in result.stderr.lower():
                    logger.debug(f"git pull skipped (no upstream): {result.stderr}")
                else:
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


def has_uncommitted_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes in the working directory.

    Args:
        cwd: Working directory of the git repository.

    Returns:
        True if there are uncommitted changes, False otherwise.
    """
    try:
        result = run_subprocess(["git", "status", "--porcelain"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            return False
        return bool(result.stdout.strip())
    except Exception as e:
        logger.debug(f"Error checking uncommitted changes: {e}")
        return False


def auto_commit_wip(current_branch: str, cwd: Path) -> bool:
    """Auto-commit work in progress when switching epics.

    Commits any uncommitted changes with a WIP message before
    switching to a different epic branch.

    Args:
        current_branch: Current branch name for the commit message.
        cwd: Working directory of the git repository.

    Returns:
        True if WIP was committed, False if no changes or commit failed.
    """
    if not has_uncommitted_changes(cwd):
        return False

    try:
        result = run_subprocess(["git", "add", "-A"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"git add failed: {result.stderr}")
            return False
        result = run_subprocess(
            ["git", "commit", "-m", f"WIP: work in progress on {current_branch}"],
            GIT_SYNC_TIMEOUT, cwd
        )
        if result.returncode != 0:
            logger.warning(f"git commit failed: {result.stderr}")
            return False
        push_result = run_subprocess(["git", "push", "origin", current_branch], GIT_SYNC_TIMEOUT, cwd)
        if push_result.returncode != 0:
            logger.warning(f"git push failed (commit succeeded locally): {push_result.stderr}")
        logger.info(f"Auto-committed WIP on {current_branch}")
        return True
    except Exception as e:
        logger.warning(f"Failed to auto-commit WIP on {current_branch}: {e}")
        return False


def ensure_epic_branch(task_id: str, cwd: Path) -> tuple[Optional[str], bool]:
    """Ensure we're on the correct branch for the task's epic.

    If the task belongs to an epic, ensures we're on the epic's branch.
    Creates the branch if this is the first work on the epic.
    If switching between epics, auto-commits any uncommitted work first.

    Args:
        task_id: The bead issue ID of the task.
        cwd: Working directory of the git repository.

    Returns:
        Tuple of (branch_name, was_created):
        - (branch_name, True) if a new branch was created
        - (branch_name, False) if switched to existing branch
        - (None, False) if no change needed or error occurred
    """
    epic_id = get_epic_for_task(task_id, cwd)
    if not epic_id:
        return (None, False)

    # Validate epic_id contains only valid git branch characters
    if not re.match(r'^[a-zA-Z0-9._-]+$', epic_id):
        logger.warning(f"Epic ID '{epic_id}' contains invalid branch characters, skipping branch switch")
        return (None, False)

    expected_branch = f"epic/{epic_id}"
    current_branch = get_current_branch(cwd)

    if current_branch == expected_branch:
        return (None, False)

    # Auto-commit WIP if switching from another epic branch
    is_switching_from_epic = current_branch and current_branch.startswith("epic/")
    if is_switching_from_epic and has_uncommitted_changes(cwd):
        if not auto_commit_wip(current_branch, cwd):
            logger.warning(f"Failed to commit WIP on {current_branch}, aborting branch switch to preserve work")
            return (None, False)

    try:
        if is_first_epic_work(epic_id, cwd):
            # Create new branch from main
            result = run_subprocess(["git", "checkout", "main"], GIT_SYNC_TIMEOUT, cwd)
            if result.returncode != 0:
                logger.warning(f"Failed to checkout main: {result.stderr}")
                return (None, False)
            result = run_subprocess(["git", "pull", "--rebase"], GIT_SYNC_TIMEOUT, cwd)
            if result.returncode != 0:
                # Pull failed but we're on main - continue with possibly stale state
                logger.warning(f"Failed to pull main (continuing anyway): {result.stderr}")
            result = run_subprocess(["git", "checkout", "-b", expected_branch], GIT_SYNC_TIMEOUT, cwd)
            if result.returncode != 0:
                logger.warning(f"Failed to create branch {expected_branch}: {result.stderr}")
                return (None, False)
            logger.info(f"Created epic branch: {expected_branch}")
            return (expected_branch, True)
        else:
            # Try to checkout existing branch (may be local or remote)
            result = run_subprocess(["git", "checkout", expected_branch], GIT_SYNC_TIMEOUT, cwd)
            if result.returncode != 0:
                # Branch might exist on remote but not locally
                run_subprocess(["git", "fetch", "origin", expected_branch], GIT_SYNC_TIMEOUT, cwd)
                result = run_subprocess(
                    ["git", "checkout", "-b", expected_branch, f"origin/{expected_branch}"],
                    GIT_SYNC_TIMEOUT, cwd
                )
                if result.returncode != 0:
                    # Remote doesn't have it either, create fresh from main
                    result = run_subprocess(["git", "checkout", "main"], GIT_SYNC_TIMEOUT, cwd)
                    if result.returncode != 0:
                        logger.warning(f"Failed to checkout main: {result.stderr}")
                        return (None, False)
                    run_subprocess(["git", "pull", "--rebase"], GIT_SYNC_TIMEOUT, cwd)
                    result = run_subprocess(["git", "checkout", "-b", expected_branch], GIT_SYNC_TIMEOUT, cwd)
                    if result.returncode != 0:
                        logger.warning(f"Failed to create branch {expected_branch}: {result.stderr}")
                        return (None, False)
                    # Created fresh branch in this fallback path
                    logger.info(f"Created epic branch: {expected_branch}")
                    return (expected_branch, True)
            logger.info(f"Switched to epic branch: {expected_branch}")
            return (expected_branch, False)
    except Exception as e:
        logger.warning(f"Failed to ensure epic branch {expected_branch}: {e}")
        return (None, False)


def merge_epic_on_close(epic_id: str, epic_title: str, cwd: Path) -> tuple[bool, Optional[str]]:
    """Merge epic branch to main when epic closes.

    Performs a --no-ff merge to main, deletes the epic branch locally
    and remotely, and pushes main. On merge conflict, aborts the merge
    and creates a bug bead for follow-up.

    Args:
        epic_id: The epic bead issue ID.
        epic_title: The epic title for commit message.
        cwd: Working directory of the git repository.

    Returns:
        Tuple of (success, error_type). error_type values:
        - None: No error (success=True) or generic failure (success=False)
        - "merge_conflict": Merge failed due to conflicts
        - "merge_abort_failed": Failed to abort merge after conflict
        - "checkout_failed": Failed to return to epic branch after abort
    """
    epic_branch = f"epic/{epic_id}"
    current = get_current_branch(cwd)

    if current != epic_branch:
        logger.debug(f"Not on epic branch {epic_branch}, skipping merge")
        return (False, None)

    try:
        # Checkout main and pull
        result = run_subprocess(["git", "checkout", "main"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            logger.warning(f"Failed to checkout main for merge: {result.stderr}")
            return (False, None)
        result = run_subprocess(["git", "pull", "--rebase"], GIT_SYNC_TIMEOUT, cwd)
        if result.returncode != 0:
            # Pull failed but continue - merge might still work
            logger.warning(f"Failed to pull main (continuing anyway): {result.stderr}")

        # Attempt merge
        merge_result = run_subprocess(
            ["git", "merge", "--no-ff", epic_branch, "-m", f"Merge epic {epic_id}: {epic_title}"],
            GIT_SYNC_TIMEOUT, cwd
        )

        if merge_result.returncode != 0:
            # Merge conflict - abort and restore state
            abort_result = run_subprocess(["git", "merge", "--abort"], GIT_SYNC_TIMEOUT, cwd)
            if abort_result.returncode != 0:
                logger.error(f"Failed to abort merge for epic {epic_id}: {abort_result.stderr}")
                return (False, "merge_abort_failed")

            checkout_result = run_subprocess(["git", "checkout", epic_branch], GIT_SYNC_TIMEOUT, cwd)
            if checkout_result.returncode != 0:
                logger.error(f"Failed to return to epic branch {epic_branch}: {checkout_result.stderr}")
                return (False, "checkout_failed")

            # Create bug bead for follow-up
            run_subprocess(
                [
                    "bd", "create",
                    "--title", f"Resolve merge conflict for epic {epic_id}",
                    "--type", "bug",
                    "--priority", "1",
                    "--description", f"Epic {epic_id} ({epic_title}) completed but merge to main failed due to conflicts."
                ],
                BD_COMMAND_TIMEOUT, cwd
            )

            logger.warning(f"Merge conflict for epic {epic_id}, created bug bead")
            return (False, "merge_conflict")

        # Success - delete branch and push
        run_subprocess(["git", "branch", "-d", epic_branch], GIT_SYNC_TIMEOUT, cwd)
        run_subprocess(["git", "push", "origin", "main"], GIT_SYNC_TIMEOUT, cwd)

        # Try to delete remote branch (may not exist)
        run_subprocess(["git", "push", "origin", "--delete", epic_branch], GIT_SYNC_TIMEOUT, cwd)

        logger.info(f"Merged and deleted epic branch: {epic_branch}")
        return (True, None)
    except Exception as e:
        logger.warning(f"Failed to merge epic branch {epic_branch}: {e}")
        return (False, None)


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
    idle_action: str = DEFAULT_IDLE_ACTION,
    epic_mode: Optional[str] = None
) -> LoopReport:
    """Main loop: check ready, run iteration, handle outcome, repeat.

    Individual phases have their own timeouts via phase_timeouts dict
    or DEFAULT_PHASE_TIMEOUTS.

    Idle detection: If idle_timeout > 0, phases will be checked for idle
    (no tool actions within threshold). idle_action determines response:
    "warn" logs a warning, "terminate" stops the phase.

    Epic mode: If epic_mode is set, filters task selection:
    - None: default mode, excludes Retrospective/Backlog epics
    - "auto": auto-detect first non-excluded epic, work only its tasks
    - "<id>": work only the specified epic's tasks
    """
    global _shutdown_requested

    started_at = datetime.now()
    iterations: list[IterationResult] = []
    completed_count = 0
    failed_count = 0
    stop_reason = "unknown"
    circuit_breaker = CircuitBreaker()
    skip_list = SkipList(max_failures=max_task_failures)
    current_epic_id: Optional[str] = None
    current_epic_title: Optional[str] = None
    exhausted_epic_ids: set[str] = set()  # Epics already tried in auto mode

    logger.info(f"Loop starting: max_iterations={max_iterations}, epic_mode={epic_mode}")

    # Validate explicit epic ID upfront
    if epic_mode and epic_mode != "auto":
        title = validate_epic_id(epic_mode, cwd)
        if title is None:
            logger.error(f"Epic {epic_mode} not found or not an epic type")
            if not json_output:
                print(f"Error: {epic_mode} is not a valid epic ID.")
            return LoopReport(
                started_at=datetime.now().isoformat(),
                ended_at=datetime.now().isoformat(),
                iterations=[],
                stop_reason="invalid_epic",
                completed_count=0,
                failed_count=0,
                duration_seconds=0.0
            )
        current_epic_id = epic_mode
        current_epic_title = title

    if not json_output:
        print(f"Line Cook Loop starting (max {max_iterations} iterations)")
        if epic_mode == "auto":
            print("  Mode: epic (auto-detect)")
        elif epic_mode:
            print(f"  Mode: epic ({current_epic_id} - {current_epic_title})")
        print("=" * 44)
        print()

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

        # Compute excluded epic IDs (Retrospective/Backlog) each iteration
        excluded_ids = get_excluded_epic_ids(snapshot)

        # Build ancestor cache once per iteration (eliminates repeated parent walks)
        ancestor_map = build_epic_ancestor_map(snapshot, cwd)

        # Determine effective epic filter for this iteration
        if epic_mode and epic_mode != "auto":
            # Explicit epic ID mode
            effective_epic = epic_mode
        elif epic_mode == "auto":
            # Auto-detect first epic if not already locked
            if current_epic_id is None:
                skipped_ids_for_detect = skip_list.get_skipped_ids()
                result_detect = detect_first_epic(snapshot, excluded_ids, skipped_ids_for_detect, cwd, exhausted_epic_ids, ancestor_map=ancestor_map)
                if result_detect is None:
                    stop_reason = "no_work"
                    logger.info("No non-excluded epic found for auto-detect mode")
                    if not json_output:
                        print("\nNo epic with ready work found. Loop complete.")
                    break
                current_epic_id, current_epic_title = result_detect
                if not json_output:
                    print(f"  Epic: {current_epic_id} - {current_epic_title}")
            effective_epic = current_epic_id
        else:
            # Default mode: all work, just exclude retro/backlog
            effective_epic = None

        # Count ready work with filtering applied
        if effective_epic:
            ready_work_count = sum(
                1 for b in snapshot.ready_work
                if ancestor_map.get(b.id) == effective_epic
            )
        elif excluded_ids:
            ready_work_count = len(_filter_excluded_epics(
                snapshot.ready_work, excluded_ids, snapshot, cwd,
                ancestor_map=ancestor_map
            ))
        else:
            ready_work_count = len(snapshot.ready_work_ids)

        if ready_work_count == 0:
            if epic_mode == "auto" and current_epic_id is not None:
                # Current epic done, try next (track to avoid re-detection)
                if not json_output:
                    print(f"\n  Epic {current_epic_id} has no remaining work.")
                exhausted_epic_ids.add(current_epic_id)
                current_epic_id = None
                current_epic_title = None
                continue
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
        next_task = get_next_ready_task(
            cwd, skip_ids=skipped_ids, snapshot=snapshot,
            epic_filter=effective_epic,
            excluded_epic_ids=excluded_ids if not effective_epic else None,
            ancestor_map=ancestor_map
        )

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
            print("=" * 44)
            print(f"Iteration {iteration}/{max_iterations} | Ready: {ready_work_count}")
            if target_task_id:
                skipped_count = len(skipped_ids)
                skip_note = f" ({skipped_count} skipped)" if skipped_count > 0 else ""
                print(f"  Target: {target_task_id} - {target_task_title}{skip_note}")
                # Show hierarchy context (parent feature/epic chain)
                hierarchy = build_hierarchy_chain(target_task_id, snapshot, cwd)
                if hierarchy:
                    chain_parts = [f"{b.id} ({b.title})" if b.title else b.id for b in hierarchy]
                    print(f"    under: {' > '.join(chain_parts)}")
            print("-" * 44)

        # Pre-cook: ensure correct branch for epic work
        if target_task_id:
            branch_name, was_created = ensure_epic_branch(target_task_id, cwd)
            if branch_name and not json_output:
                if was_created:
                    print(f"  Branch: main → {branch_name} (new)")
                else:
                    print(f"  Branch: → {branch_name}")

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
            idle_action=idle_action,
            before_snapshot=snapshot,
            target_task_id=target_task_id
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
            completed_for_status = completed_count + (1 if result.success else 0)
            write_status_file(
                status_file=status_file,
                running=True,
                iteration=iteration,
                max_iterations=max_iterations,
                current_task=result.task_id,
                current_task_title=result.task_title,
                last_verdict=result.serve_verdict,
                tasks_completed=completed_for_status,
                tasks_remaining=result.after_ready,
                started_at=started_at,
                iterations=iterations,
                epic_mode=epic_mode,
                current_epic=current_epic_id
            )

        # Append iteration to history JSONL file (full action details)
        if history_file:
            project_name = cwd.name
            append_iteration_to_history(
                history_file=history_file,
                result=result,
                project=project_name
            )

        # Periodic bd sync to keep bead state fresh during long runs
        if should_periodic_sync(iteration, PERIODIC_SYNC_INTERVAL):
            sync_ok = periodic_sync(cwd)
            if not json_output:
                if sync_ok:
                    print("  Periodic sync: ✓")
                else:
                    print("  Periodic sync: ⚠️ failed (continuing)")

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
            is_same_task = result.task_id == last_task_id
            if is_same_task:
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

        # Merge epic branches closed during this iteration
        if result.success and result.closed_epics:
            for closed_epic_id in result.closed_epics:
                epic_title = get_task_title(closed_epic_id, cwd) or ""
                merged, merge_error = merge_epic_on_close(closed_epic_id, epic_title, cwd)
                if merged and not json_output:
                    print(f"  Branch: epic/{closed_epic_id} merged to main")
                elif merge_error == "merge_conflict" and not json_output:
                    print(f"  WARNING: Merge conflict for epic/{closed_epic_id}")
                    print(f"           Bug bead created for manual resolution")

        # Check for epic completions after each successful iteration
        # Catch-all: detect epics eligible for closure that iteration missed
        # (e.g., external closes, or iteration's hierarchy walk didn't reach epic)
        if result.success:
            already_handled = set(result.closed_epics)
            epic_summaries = check_epic_completion(cwd, exclude_ids=already_handled)
            if epic_summaries:
                # Merge epic branches to main for each completed epic
                for epic in epic_summaries:
                    epic_id = epic.get("id")
                    if not epic_id or epic_id in already_handled:
                        continue
                    epic_title = epic.get("title", "")
                    merged, merge_error = merge_epic_on_close(epic_id, epic_title, cwd)
                    if merged and not json_output:
                        print(f"  Branch: epic/{epic_id} merged to main")
                    elif merge_error == "merge_conflict" and not json_output:
                        print(f"  WARNING: Merge conflict for epic/{epic_id}")
                        print(f"           Bug bead created for manual resolution")

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

                # In auto-epic mode, reset to re-detect next epic
                if epic_mode == "auto":
                    current_epic_id = None
                    current_epic_title = None

                if break_on_epic:
                    stop_reason = "epic_complete"
                    logger.info(f"Epic(s) {[e['id'] for e in epic_summaries]} completed, breaking as requested")
                    if not json_output:
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
            escalation=escalation,
            epic_mode=epic_mode,
            current_epic=current_epic_id
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
                    },
                    "findings_count": i.findings_count,
                    **({
                        "delta": {
                            "newly_closed": [{"id": b.id, "title": b.title, "type": b.issue_type} for b in i.delta.newly_closed],
                            "newly_filed": [{"id": b.id, "title": b.title, "type": b.issue_type} for b in i.delta.newly_filed],
                        }
                    } if i.delta else {})
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
