"""Single iteration logic for line-loop.

Functions for executing one complete iteration:
- run_iteration: Execute prep→cook→serve→tidy→plate cycle
- check_task_completed: Verify task completion
- check_feature_completion: Check if feature is done
- check_epic_completion: Check if epic is done
- detect_worked_task: Find which task was worked on

Also includes helper functions for:
- Bead state queries (get_bead_snapshot, get_task_info, get_children)
- Retry context management (write_retry_context, clear_retry_context)
- Epic completion display (print_epic_completion, generate_epic_closure_report)
- Human-readable output (format_duration, print_phase_progress, print_human_iteration)
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import (
    BANNER_MIN_WIDTH,
    BD_COMMAND_TIMEOUT,
    CLOSED_TASKS_QUERY_LIMIT,
    DEFAULT_IDLE_ACTION,
    DEFAULT_IDLE_TIMEOUT,
    GIT_COMMAND_TIMEOUT,
    GOAL_TEXT_MAX_LENGTH,
)
from .models import (
    ActionRecord,
    BeadSnapshot,
    IterationResult,
    LoopError,
    ProgressState,
    ServeFeedback,
    ServeResult,
)
from .parsing import (
    parse_intent_block,
    parse_serve_feedback,
    parse_serve_result,
)
from .phase import (
    detect_kitchen_complete,
    run_phase,
    run_subprocess,
)

logger = logging.getLogger(__name__)


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


def parse_bd_json_item(data: Any) -> Optional[dict]:
    """Parse bd JSON output which may be a list or dict.

    bd commands like 'bd show' return either:
    - A single dict (issue object)
    - A list containing one dict
    - An empty list

    Args:
        data: Parsed JSON from bd command output.

    Returns:
        Issue dict, or None if data is empty or invalid.
    """
    if isinstance(data, list):
        if not data:
            return None
        return data[0] if isinstance(data[0], dict) else None
    elif isinstance(data, dict):
        return data
    return None


def detect_worked_task(before: BeadSnapshot, after: BeadSnapshot) -> Optional[str]:
    """Detect which task was worked on by comparing bead state snapshots.

    Uses state transitions to identify the task that was claimed or completed
    during an iteration. Handles three scenarios:
    1. Task moved from ready to in_progress (claimed)
    2. Task moved from ready to closed (completed in one go)
    3. Task was in_progress and is now closed (completed)

    Args:
        before: BeadSnapshot captured before the iteration.
        after: BeadSnapshot captured after the iteration.

    Returns:
        Task ID that was worked on, or None if no task state change detected.
        Returns the first matching task if multiple tasks changed (rare).
    """
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
    """Get the title for a task ID from bead database.

    Args:
        task_id: The bead issue ID (e.g., "lc-j6b.3").
        cwd: Working directory containing the .beads project.

    Returns:
        Task title string, or None if task not found or query fails.
    """
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


def get_bead_snapshot(cwd: Path) -> BeadSnapshot:
    """Capture current state of beads (issues) for before/after comparison.

    Queries bd for ready, in_progress, and recently closed issues. The snapshot
    enables detecting which task was worked on by comparing state before and
    after a loop iteration.

    Args:
        cwd: Working directory containing the .beads project.

    Returns:
        BeadSnapshot containing:
        - ready_ids: All ready issues (tasks, features, and epics)
        - ready_work_ids: Ready work items only (tasks + features, excluding epics)
        - in_progress_ids: Issues currently being worked on
        - closed_ids: Recently closed issues (limited for performance)
        - timestamp: When the snapshot was captured

    Note:
        Errors from bd commands are logged but don't raise exceptions.
        Returns partially-populated snapshot on individual query failures.
    """
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
                if isinstance(i, dict) and i.get("issue_type") != "epic"
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


def get_task_info(task_id: str, cwd: Path) -> Optional[dict]:
    """Get full task information including parent, status, and type.

    Queries bd for detailed issue data used in feature/epic completion
    checks and status reporting.

    Args:
        task_id: The bead issue ID (e.g., "lc-j6b.3").
        cwd: Working directory containing the .beads project.

    Returns:
        Dict with issue fields (id, title, status, type, parent, etc.),
        or None if task not found or query fails.
    """
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
    """Get all child issues of a parent epic or feature.

    Used in feature/epic completion checks to determine if all children
    are closed (enabling parent auto-closure).

    Args:
        parent_id: The bead issue ID of the parent (epic or feature).
        cwd: Working directory containing the .beads project.

    Returns:
        List of child issue dicts with fields (id, title, status, type),
        or empty list if parent has no children or query fails.
    """
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


def get_latest_commit(cwd: Path) -> Optional[str]:
    """Get the short hash of the latest git commit.

    Used to record which commit was created by the tidy phase for
    traceability in iteration results and status reports.

    Args:
        cwd: Working directory of the git repository.

    Returns:
        Short commit hash (e.g., "a1b2c3d"), or None if git command fails.
    """
    try:
        result = run_subprocess(["git", "log", "-1", "--format=%h"], GIT_COMMAND_TIMEOUT, cwd)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        logger.debug(f"Error getting latest commit: {e}")
    return None


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
    if not parent_info or parent_info.get("issue_type") != "feature":
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
    if not epic_info or epic_info.get("issue_type") != "epic":
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
    features = [c for c in children if c.get("issue_type") == "feature"]

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
                {"id": c.get("id"), "title": c.get("title"), "issue_type": c.get("issue_type")}
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
            t = c.get("issue_type", "item")
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
        idle_timeout: Seconds without tool actions before triggering idle
        idle_action: Action on idle - "warn" or "terminate"
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
