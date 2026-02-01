#!/usr/bin/env python3
"""Line Cook autonomous loop - runs /line:run until no tasks remain.

Provides robust feedback through bead state tracking and SERVE_RESULT parsing.

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
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class BeadSnapshot:
    """State of beads at a point in time."""
    ready_ids: list[str] = field(default_factory=list)
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
class IterationResult:
    """Result of a single loop iteration."""
    iteration: int
    task_id: Optional[str]
    task_title: Optional[str]
    outcome: str  # "completed", "needs_retry", "blocked", "crashed", "timeout", "no_tasks"
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


@dataclass
class LoopReport:
    """Final report for the entire loop run."""
    started_at: str
    ended_at: str
    iterations: list[IterationResult]
    stop_reason: str  # "no_tasks", "max_iterations", "blocked", "error", "crashed"
    completed_count: int
    failed_count: int
    duration_seconds: float


def get_bead_snapshot(cwd: Path) -> BeadSnapshot:
    """Capture ready/in_progress/closed task IDs via bd --json."""
    snapshot = BeadSnapshot()

    # Get ready tasks
    try:
        result = subprocess.run(
            ["bd", "ready", "--json"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.ready_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass

    # Get in_progress tasks
    try:
        result = subprocess.run(
            ["bd", "list", "--status=in_progress", "--json"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.in_progress_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass

    # Get recently closed tasks (limit 10 for performance)
    try:
        result = subprocess.run(
            ["bd", "list", "--status=closed", "--limit=10", "--json"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            issues = json.loads(result.stdout)
            snapshot.closed_ids = [i.get("id", "") for i in issues if isinstance(i, dict)]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass

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
        result = subprocess.run(
            ["bd", "show", task_id, "--json"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            issue = json.loads(result.stdout)
            return issue.get("title")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass
    return None


def detect_kitchen_complete(output: str) -> bool:
    """Detect KITCHEN_COMPLETE signal in output."""
    return "KITCHEN_COMPLETE" in output or "KITCHEN COMPLETE" in output


def get_latest_commit(cwd: Path) -> Optional[str]:
    """Get the latest commit hash."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def run_iteration(
    iteration: int,
    max_iterations: int,
    cwd: Path,
    timeout: int
) -> IterationResult:
    """Execute one claude --skill line:run with full tracking."""
    start_time = datetime.now()

    # Capture before state
    before = get_bead_snapshot(cwd)

    if not before.ready_ids:
        return IterationResult(
            iteration=iteration,
            task_id=None,
            task_title=None,
            outcome="no_tasks",
            duration_seconds=0.0,
            serve_verdict=None,
            commit_hash=None,
            success=False,
            before_ready=0,
            before_in_progress=len(before.in_progress_ids),
            after_ready=0,
            after_in_progress=len(before.in_progress_ids)
        )

    # Run claude with line:run skill
    try:
        result = subprocess.run(
            ["claude", "-p", "/line:run", "--dangerously-skip-permissions"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        after = get_bead_snapshot(cwd)
        return IterationResult(
            iteration=iteration,
            task_id=detect_worked_task(before, after),
            task_title=None,
            outcome="timeout",
            duration_seconds=duration,
            serve_verdict=None,
            commit_hash=None,
            success=False,
            before_ready=len(before.ready_ids),
            before_in_progress=len(before.in_progress_ids),
            after_ready=len(after.ready_ids),
            after_in_progress=len(after.in_progress_ids)
        )
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        after = get_bead_snapshot(cwd)
        return IterationResult(
            iteration=iteration,
            task_id=None,
            task_title=None,
            outcome="crashed",
            duration_seconds=duration,
            serve_verdict=None,
            commit_hash=None,
            success=False,
            before_ready=len(before.ready_ids),
            before_in_progress=len(before.in_progress_ids),
            after_ready=len(after.ready_ids),
            after_in_progress=len(after.in_progress_ids)
        )

    duration = (datetime.now() - start_time).total_seconds()

    # Capture after state
    after = get_bead_snapshot(cwd)

    # Detect which task was worked on
    task_id = detect_worked_task(before, after)
    task_title = get_task_title(task_id, cwd) if task_id else None

    # Parse outputs
    serve_result = parse_serve_result(output)
    intent, before_state, after_state = parse_intent_block(output)
    kitchen_complete = detect_kitchen_complete(output)
    commit_hash = get_latest_commit(cwd)

    # Determine outcome - prioritize bead state changes over exit code
    new_closed = set(after.closed_ids) - set(before.closed_ids)
    task_closed = bool(new_closed)

    if serve_result:
        if serve_result.verdict == "APPROVED":
            outcome = "completed"
            success = True
        elif serve_result.verdict == "NEEDS_CHANGES":
            outcome = "needs_retry"
            success = False
        elif serve_result.verdict == "BLOCKED":
            outcome = "blocked"
            success = False
        else:  # SKIPPED or unknown
            outcome = "completed" if (kitchen_complete or task_closed) else "needs_retry"
            success = kitchen_complete or task_closed
    elif task_closed:
        # Task was closed - this is the most reliable success indicator
        outcome = "completed"
        success = True
    elif kitchen_complete:
        outcome = "completed"
        success = True
    elif exit_code != 0:
        outcome = "crashed"
        success = False
    else:
        # No clear signal - assume needs retry
        outcome = "needs_retry"
        success = False

    return IterationResult(
        iteration=iteration,
        task_id=task_id,
        task_title=task_title,
        outcome=outcome,
        duration_seconds=duration,
        serve_verdict=serve_result.verdict if serve_result else None,
        commit_hash=commit_hash,
        success=success,
        before_ready=len(before.ready_ids),
        before_in_progress=len(before.in_progress_ids),
        after_ready=len(after.ready_ids),
        after_in_progress=len(after.in_progress_ids),
        intent=intent,
        before_state=before_state,
        after_state=after_state
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
        "no_tasks": "[DONE]"
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


def run_loop(
    max_iterations: int,
    timeout: int,
    stop_on_blocked: bool,
    stop_on_crash: bool,
    max_retries: int,
    json_output: bool,
    output_file: Optional[Path],
    cwd: Path
) -> LoopReport:
    """Main loop: check ready, run iteration, handle outcome, repeat."""
    started_at = datetime.now()
    iterations: list[IterationResult] = []
    completed_count = 0
    failed_count = 0
    stop_reason = "unknown"

    if not json_output:
        print(f"Line Cook Loop starting (max {max_iterations} iterations)")
        print("=" * 44)

    iteration = 0
    current_retries = 0
    last_task_id = None

    while iteration < max_iterations:
        # Check for ready tasks
        snapshot = get_bead_snapshot(cwd)
        ready_count = len(snapshot.ready_ids)

        if ready_count == 0:
            stop_reason = "no_tasks"
            if not json_output:
                print("\nNo tasks ready. Loop complete.")
            break

        iteration += 1

        if not json_output:
            print(f"\n[{iteration}/{max_iterations}] {ready_count} tasks ready")
            print("-" * 44)

        # Run iteration
        result = run_iteration(iteration, max_iterations, cwd, timeout)
        iterations.append(result)

        if not json_output:
            print_human_iteration(result, current_retries)

        # Handle outcome
        if result.outcome == "no_tasks":
            stop_reason = "no_tasks"
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

        elif result.outcome == "blocked":
            failed_count += 1
            if stop_on_blocked:
                stop_reason = "blocked"
                if not json_output:
                    print("\nTask blocked. Stopping loop (--stop-on-blocked).")
                break
            current_retries = 0
            last_task_id = None

        elif result.outcome in ("crashed", "timeout"):
            failed_count += 1
            if stop_on_crash:
                stop_reason = result.outcome
                if not json_output:
                    print(f"\nTask {result.outcome}. Stopping loop (--stop-on-crash).")
                break
            current_retries = 0
            last_task_id = None

    else:
        stop_reason = "max_iterations"
        if not json_output:
            print(f"\nReached iteration limit ({max_iterations}). Stopping.")

    ended_at = datetime.now()
    duration = (ended_at - started_at).total_seconds()

    report = LoopReport(
        started_at=started_at.isoformat(),
        ended_at=ended_at.isoformat(),
        iterations=iterations,
        stop_reason=stop_reason,
        completed_count=completed_count,
        failed_count=failed_count,
        duration_seconds=duration
    )

    # Print summary
    if not json_output:
        print()
        print("=" * 44)
        print("LOOP COMPLETE")
        print("=" * 44)
        print(f"Duration: {format_duration(duration)}")
        print(f"Completed: {completed_count} | Failed: {failed_count} | Blocked: {sum(1 for i in iterations if i.outcome == 'blocked')}")

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

    args = parser.parse_args()

    cwd = Path.cwd()

    report = run_loop(
        max_iterations=args.max_iterations,
        timeout=args.timeout,
        stop_on_blocked=args.stop_on_blocked,
        stop_on_crash=args.stop_on_crash,
        max_retries=args.max_retries,
        json_output=args.json,
        output_file=args.output,
        cwd=cwd
    )

    # Exit with appropriate code
    if report.stop_reason in ("no_tasks", "max_iterations"):
        sys.exit(0)
    elif report.stop_reason == "blocked":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
