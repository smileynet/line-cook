"""Phase execution for line-loop.

Functions for running workflow phases:
- build_phase_command: Build subprocess command list for a phase and CLI profile
- process_output_line: Process a single output line from a CLI subprocess
- run_phase: Execute a single phase (cook, serve, tidy, plate, close-service)
- run_subprocess: Run command with timeout
- check_idle: Check if phase has been idle beyond threshold
- detect_kitchen_complete: Detect KITCHEN_COMPLETE signal
- detect_kitchen_idle: Detect KITCHEN_IDLE signal
"""

from __future__ import annotations

import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .platform import (
    PipeReader,
    create_pty_reader_and_process,
    create_stderr_file,
    read_and_cleanup_stderr,
    cleanup_stderr_file,
    kill_process_tree,
    make_popen_kwargs,
)

from .config import (
    ACTIVE_EXTENSION_CAP,
    ACTIVE_EXTENSION_WINDOW,
    DEFAULT_CLI,
    DEFAULT_FALLBACK_PHASE_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_PHASE_IDLE_TIMEOUTS,
    DEFAULT_PHASE_TIMEOUTS,
    get_cli_profile,
)
from .models import ActionRecord, PhaseResult
from .parsing import (
    extract_actions_from_event,
    extract_kiro_actions_from_line,
    extract_opencode_actions_from_event,
    extract_opencode_text_from_event,
    extract_text_from_event,
    normalize_signal_text,
    parse_opencode_ndjson_event,
    parse_stream_json_event,
    strip_ansi,
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


def resolve_idle_timeout(phase: str, idle_timeout: Optional[int]) -> int:
    """Resolve the effective idle timeout for a phase.

    Args:
        phase: Phase name (cook, serve, tidy, plate, close-service)
        idle_timeout: Explicit override, or None to use per-phase default

    Returns:
        Effective idle timeout in seconds
    """
    if idle_timeout is not None:
        return idle_timeout
    return DEFAULT_PHASE_IDLE_TIMEOUTS.get(phase, DEFAULT_IDLE_TIMEOUT)


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
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, encoding='utf-8', errors='replace')
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


def build_phase_command(phase: str, args: str, cli_profile: dict) -> list[str]:
    """Build the subprocess command list for a given phase and CLI profile.

    Args:
        phase: Phase name (cook, serve, tidy, plate, close-service)
        args: Optional arguments (e.g., task ID)
        cli_profile: CLI profile dict from get_cli_profile()

    Returns:
        Command list suitable for subprocess.Popen
    """
    prompt = cli_profile['prompt_format'].format(phase=phase)

    cmd = [cli_profile['binary']]

    if 'subcommand' in cli_profile:
        cmd.append(cli_profile['subcommand'])

    if cli_profile.get('command_flag'):
        # OpenCode-style: --command <prompt> --format json <args>
        cmd.extend([cli_profile['command_flag'], prompt])
        cmd.extend(cli_profile.get('output_flags', []))
        cmd.extend(cli_profile.get('permission_flags', []))
        if args:
            cmd.append(args)
    elif cli_profile.get('has_streaming_json'):
        # Claude-style: -p prompt, then flags
        if args:
            injection = cli_profile.get('task_injection')
            if injection:
                prompt = f"{injection.format(args=args)}{prompt}"
            else:
                prompt = f"{prompt} {args}"
        cmd.extend(['-p', prompt])
        cmd.extend(cli_profile.get('permission_flags', []))
        cmd.extend(cli_profile.get('output_flags', []))
    else:
        # Kiro-style: flags first, prompt at end
        if args:
            injection = cli_profile.get('task_injection')
            if injection:
                prompt = f"{injection.format(args=args)}{prompt}"
            else:
                prompt = f"{prompt} {args}"
        cmd.extend(cli_profile.get('extra_flags', []))
        cmd.extend(cli_profile.get('permission_flags', []))
        cmd.append(prompt)

    return cmd


def process_output_line(
    line: str,
    cli_profile: dict,
    pending_actions: dict[str, ActionRecord]
) -> tuple[list[ActionRecord], str]:
    """Process a single output line from a CLI subprocess.

    Handles both streaming JSON (Claude) and plain-text (Kiro) output formats
    based on the cli_profile's has_streaming_json flag.

    Args:
        line: Raw output line from subprocess stdout
        cli_profile: CLI profile dict from get_cli_profile()
        pending_actions: Mutable dict mapping tool_use_id to ActionRecord

    Returns:
        Tuple of (new_actions, cleaned_text):
        - new_actions: ActionRecords created from tool calls in this line
        - cleaned_text: Human-readable text extracted from the line
    """
    if cli_profile.get('has_streaming_json'):
        # Claude: streaming JSON events
        event = parse_stream_json_event(line)
        if not event:
            return [], ""
        new_actions = extract_actions_from_event(event, pending_actions)
        update_action_from_result(event, pending_actions)
        text = ""
        if event.get("type") == "assistant":
            text = extract_text_from_event(event)
        return new_actions, text

    if cli_profile.get('has_ndjson'):
        # OpenCode: NDJSON events (one JSON object per line)
        event = parse_opencode_ndjson_event(line)
        if not event:
            return [], ""
        new_actions = extract_opencode_actions_from_event(event, pending_actions)
        text = extract_opencode_text_from_event(event)
        return new_actions, text

    # Kiro: plain-text output
    cleaned = strip_ansi(line.rstrip('\n'))
    new_actions = extract_kiro_actions_from_line(cleaned, pending_actions)
    return new_actions, cleaned


def run_phase(
    phase: str,
    cwd: Path,
    args: str = "",
    timeout: Optional[int] = None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    phase_timeouts: Optional[dict[str, int]] = None,
    idle_timeout: Optional[int] = None,
    idle_action: str = DEFAULT_IDLE_ACTION,
    cli_profile: Optional[dict] = None,
    extension_cap: int = ACTIVE_EXTENSION_CAP
) -> PhaseResult:
    """Invoke a single Line Cook skill phase (cook, serve, tidy, plate, close-service).

    Active extension: Each tool action extends the deadline by ACTIVE_EXTENSION_WINDOW
    seconds, up to extension_cap from start. This keeps productive tasks alive while
    still enforcing an absolute ceiling.

    Args:
        phase: Phase name (cook, serve, tidy, plate, close-service)
        cwd: Working directory
        args: Optional arguments (e.g., task ID for cook)
        timeout: Override default phase timeout (takes precedence over phase_timeouts)
        on_progress: Optional callback for progress updates.
            Called with (action_count, last_action_timestamp) when new actions detected.
        phase_timeouts: Optional dict of phase-specific timeouts (overrides defaults)
        idle_timeout: Override idle timeout, or None to use per-phase default from
            DEFAULT_PHASE_IDLE_TIMEOUTS (falls back to DEFAULT_IDLE_TIMEOUT)
        idle_action: Action on idle - "warn" logs warning, "terminate" stops phase (default: terminate)
        cli_profile: CLI profile dict, or None to use DEFAULT_CLI (backward compatible)
        extension_cap: Absolute maximum phase duration in seconds (default: ACTIVE_EXTENSION_CAP)

    Returns:
        PhaseResult with output, signals, and success status
    """
    if cli_profile is None:
        cli_profile = get_cli_profile(DEFAULT_CLI)

    idle_timeout = resolve_idle_timeout(phase, idle_timeout)
    if timeout is None:
        timeouts = phase_timeouts or DEFAULT_PHASE_TIMEOUTS
        fallback = DEFAULT_PHASE_TIMEOUTS.get(phase, DEFAULT_FALLBACK_PHASE_TIMEOUT)
        timeout = timeouts.get(phase, fallback)

    # Apply per-CLI timeout multiplier
    multiplier = cli_profile.get('phase_timeout_multiplier', 1.0)
    timeout = int(timeout * multiplier)
    idle_timeout = int(idle_timeout * multiplier)

    cmd = build_phase_command(phase, args, cli_profile)

    # Cap is the larger of extension_cap and timeout, so user-specified
    # timeouts beyond the cap are never shrunk by active extension.
    effective_cap = max(extension_cap, timeout)
    logger.debug(f"Running phase {phase}: {' '.join(cmd)} (timeout={timeout}s, cap={effective_cap}s)")
    start_time = time.time()
    hard_cap = start_time + effective_cap

    actions: list[ActionRecord] = []
    pending_actions: dict[str, ActionRecord] = {}
    output_lines: list[str] = []
    signals: list[str] = []
    exit_code = 0
    error: Optional[str] = None
    last_action_time: Optional[datetime] = None
    idle_warned: bool = False
    stderr_output: str = ""
    timeout_base = timeout  # Base after multiplier, before active extensions
    deadline = time.time() + timeout  # Default deadline (set before try for crash safety)

    stderr_file = create_stderr_file(phase)
    reader = None

    try:
        if cli_profile.get('needs_pty'):
            # PTY wrapper for CLIs that need a pseudo-TTY (e.g., OpenCode)
            popen_kwargs = make_popen_kwargs(cwd, stderr_file)
            reader, process = create_pty_reader_and_process(
                cmd, cwd, stderr_file, popen_kwargs['env']
            )
        else:
            process = subprocess.Popen(cmd, **make_popen_kwargs(cwd, stderr_file))
            reader = PipeReader.create(process.stdout)

        deadline = time.time() + timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                # Graceful termination: SIGTERM first, then kill tree as fallback
                logger.debug(f"Phase {phase} timeout - sending SIGTERM")
                process.terminate()  # SIGTERM
                try:
                    process.wait(timeout=5)
                    logger.debug(f"Phase {phase} terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Phase {phase} did not respond to SIGTERM, killing process tree")
                    kill_process_tree(process)
                raise subprocess.TimeoutExpired(cmd=' '.join(cmd), timeout=timeout)

            line = reader.readline(timeout=min(1.0, remaining))
            if line == '':
                break  # EOF
            if line is not None:
                output_lines.append(line)
                new_actions, text = process_output_line(line, cli_profile, pending_actions)
                actions.extend(new_actions)
                # Track last action time for idle detection + active extension
                if new_actions:
                    last_action_time = datetime.now()
                    idle_warned = False  # Reset idle warning on new activity
                    # Active extension: push deadline forward on each action (never shrink)
                    extended = time.time() + ACTIVE_EXTENSION_WINDOW
                    deadline = max(deadline, min(extended, hard_cap))
                # Notify progress callback when new actions detected
                if new_actions and on_progress:
                    last_ts = new_actions[-1].timestamp
                    on_progress(len(actions), last_ts)
                # Detect signals from text output
                if text:
                    # Normalize to strip code fences/box-drawing that might wrap signals (GAP 6)
                    sig_text = normalize_signal_text(text)
                    if "SERVE_RESULT" in sig_text:
                        if "APPROVED" in sig_text and "serve_approved" not in signals:
                            signals.append("serve_approved")
                        elif "NEEDS_CHANGES" in sig_text and "serve_needs_changes" not in signals:
                            signals.append("serve_needs_changes")
                        elif "BLOCKED" in sig_text and "serve_blocked" not in signals:
                            signals.append("serve_blocked")
                    if detect_kitchen_complete(sig_text) and "kitchen_complete" not in signals:
                        signals.append("kitchen_complete")
                    if detect_kitchen_idle(sig_text) and "kitchen_idle" not in signals:
                        signals.append("kitchen_idle")
                    # Detect phase completion signal for early termination
                    if "<phase_complete>DONE</phase_complete>" in sig_text and "phase_complete" not in signals:
                        signals.append("phase_complete")
                        logger.info(f"Phase {phase} signaled completion, terminating early")
                        # Graceful early termination
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            kill_process_tree(process)
                        break
            else:
                # timeout — no data available yet
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
                                kill_process_tree(process)
                            error = f"Idle timeout after {idle_timeout}s without tool actions"
                            break
                        elif idle_action == "warn" and not idle_warned:
                            idle_seconds = (datetime.now() - last_action_time).total_seconds()
                            logger.warning(f"Phase {phase} idle for {idle_seconds:.0f}s (threshold: {idle_timeout}s)")
                            idle_warned = True

        # Read any remaining buffered output
        output_lines.extend(reader.drain())
        reader.close()
        process.wait()

        # Flush unresolved pending actions (e.g., CLI crashed mid-tool-use).
        # Actions are already in the actions list from initial detection;
        # just mark them unresolved in-place.
        for tool_use_id, action in pending_actions.items():
            action.success = None
            logger.debug(f"Unresolved pending action: {action.tool_name} ({tool_use_id})")
        pending_actions.clear()

        # Read stderr from temp file
        stderr_output = read_and_cleanup_stderr(stderr_file)

        if stderr_output:
            logger.debug(f"Phase {phase} stderr: {stderr_output[:500]}")

        exit_code = process.returncode

    except subprocess.TimeoutExpired:
        if reader:
            reader.close()
        cleanup_stderr_file(stderr_file)
        duration = time.time() - start_time
        effective_timeout = int(deadline - start_time) if deadline > start_time else timeout
        logger.warning(f"Phase {phase} timed out after {duration:.1f}s (base={timeout_base}s, effective={effective_timeout}s)")
        return PhaseResult(
            phase=phase,
            success=False,
            output="".join(output_lines),
            exit_code=-1,
            duration_seconds=duration,
            signals=signals,
            actions=actions,
            error=f"Timeout after {int(duration)}s ({len(actions)} actions)",
            timeout_base=timeout_base,
            timeout_effective=effective_timeout,
        )
    except Exception as e:
        if reader:
            reader.close()
        cleanup_stderr_file(stderr_file)
        duration = time.time() - start_time
        effective_timeout = int(deadline - start_time) if deadline > start_time else timeout
        logger.error(f"Phase {phase} crashed: {e}")
        return PhaseResult(
            phase=phase,
            success=False,
            output="".join(output_lines),
            exit_code=-1,
            duration_seconds=duration,
            signals=signals,
            actions=actions,
            error=str(e),
            timeout_base=timeout_base,
            timeout_effective=effective_timeout,
        )

    duration = time.time() - start_time
    output = "".join(output_lines)
    # Phase is successful if exit code is 0 OR if it signaled early completion
    early_completion = "phase_complete" in signals
    success = exit_code == 0 or early_completion

    logger.debug(f"Phase {phase} completed in {duration:.1f}s, exit={exit_code}, signals={signals}, early_completion={early_completion}")

    # Include stderr in error for failed phases
    error_msg = None
    if not success:
        error_msg = f"Exit code {exit_code}"
        if stderr_output:
            error_msg = f"{error_msg}. stderr: {stderr_output[:200]}"

    return PhaseResult(
        phase=phase,
        success=success,
        output=output,
        exit_code=exit_code,
        duration_seconds=duration,
        signals=signals,
        actions=actions,
        error=error_msg,
        early_completion=early_completion,
        timeout_base=timeout_base,
        timeout_effective=int(deadline - start_time),
    )
