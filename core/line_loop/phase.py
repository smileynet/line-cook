"""Phase execution for line-loop.

Functions for running workflow phases:
- run_phase: Execute a single phase (cook, serve, tidy, plate, close-service)
- run_subprocess: Run command with timeout
- check_idle: Check if phase has been idle beyond threshold
- detect_kitchen_complete: Detect KITCHEN_COMPLETE signal
- detect_kitchen_idle: Detect KITCHEN_IDLE signal
"""

from __future__ import annotations

import logging
import select
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import (
    DEFAULT_FALLBACK_PHASE_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_PHASE_TIMEOUTS,
)
from .models import ActionRecord, PhaseResult
from .parsing import (
    extract_actions_from_event,
    extract_text_from_event,
    parse_stream_json_event,
    update_action_from_result,
)

logger = logging.getLogger(__name__)


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
    """Run subprocess with logging, timeout handling, and structured output.

    Executes an external command as a subprocess with consistent logging,
    timeout enforcement, and captured output. Used throughout the loop for
    bd commands, git operations, and other external tools.

    Args:
        cmd: Command and arguments as a list (e.g., ["bd", "ready", "--json"]).
             List form is used to prevent shell injection.
        timeout: Maximum seconds to wait for command completion.
        cwd: Working directory for the subprocess.

    Returns:
        CompletedProcess with returncode, stdout, and stderr captured as text.

    Raises:
        subprocess.TimeoutExpired: If command doesn't complete within timeout.
    """
    logger.debug(f"Running: {' '.join(cmd)} (timeout={timeout}s)")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        logger.debug(f"Completed in {time.time()-start:.1f}s, exit={result.returncode}")
        return result
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout after {timeout}s: {' '.join(cmd)}")
        raise


def detect_kitchen_complete(output: str) -> bool:
    """Detect KITCHEN_COMPLETE signal in cook phase output.

    The cook phase emits this signal when it believes the task is complete.
    Used as a supporting (not definitive) signal for completion detection.

    Args:
        output: Raw output from the cook phase.

    Returns:
        True if KITCHEN_COMPLETE or KITCHEN COMPLETE found in output.
    """
    return "KITCHEN_COMPLETE" in output or "KITCHEN COMPLETE" in output


def detect_kitchen_idle(output: str) -> bool:
    """Detect KITCHEN_IDLE signal in cook phase output.

    The cook phase emits this signal when no actionable work is found
    (e.g., all ready tasks are P4 parking lot items). This allows the
    loop to stop gracefully rather than continuing to run with no work.

    Args:
        output: Raw output from the cook phase.

    Returns:
        True if KITCHEN_IDLE or KITCHEN IDLE found in output.
    """
    return "KITCHEN_IDLE" in output or "KITCHEN IDLE" in output


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
    """Invoke a single Line Cook skill phase (cook, serve, tidy, plate, close-service).

    Args:
        phase: Phase name (cook, serve, tidy, plate, close-service)
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
