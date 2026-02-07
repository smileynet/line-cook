#!/usr/bin/env python3
# Requires Python 3.9+ for dataclasses and type hints (list[str] syntax)
"""Line Cook autonomous loop - runs individual phase skills until no tasks remain.

This is a thin wrapper around the line_loop package, providing CLI interface
for the autonomous loop functionality.

Platform Support:
    Linux, macOS, WSL - Fully supported
    Windows - NOT supported (select.select() requires Unix file descriptors)
"""

import argparse
import json
import logging
import logging.handlers
import os
import shutil
import signal
import sys
from pathlib import Path
from typing import Optional

# Import everything from the line_loop package
from line_loop import (
    # Config constants
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TASK_FAILURES,
    DEFAULT_PHASE_TIMEOUTS,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    LOG_FILE_MAX_BYTES,
    LOG_FILE_BACKUP_COUNT,
    # Main loop function
    run_loop,
    request_shutdown,
    # Utilities
    atomic_write,
)

# Module-level logger
logger = logging.getLogger('line-loop')


def _handle_shutdown(signum, frame):
    """Handle SIGINT/SIGTERM/SIGHUP for graceful shutdown."""
    request_shutdown()
    logger.info(f"Shutdown requested (signal {signum})")


# Register signal handlers
signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGHUP, _handle_shutdown)


def setup_logging(verbose: bool, log_file: Optional[Path] = None):
    """Configure logging with optional file output and rotation."""
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    if log_file:
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


def check_health(cwd: Path) -> dict:
    """Verify environment before starting loop."""
    checks = {
        'claude_cli': shutil.which('claude') is not None,
        'bd_cli': shutil.which('bd') is not None,
        'git_repo': (cwd / '.git').exists(),
        'beads_init': (cwd / '.beads').exists(),
    }
    return {'healthy': all(checks.values()), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(
        description="Line Cook autonomous loop - runs /line:run until no tasks remain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with defaults (25 iterations)
  %(prog)s --max-iterations 10      # Limit to 10 iterations
  %(prog)s --epic                   # Auto-select first available epic
  %(prog)s --epic lc-001            # Focus on specific epic
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
        "--epic", nargs="?", const="auto", default=None,
        metavar="EPIC_ID",
        help="Focus on one epic (auto-select first available, or specify ID)"
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
            overall = "HEALTHY" if health['healthy'] else "UNHEALTHY"
            print(f"Overall: {overall}")
        exit_code = 0 if health['healthy'] else 1
        sys.exit(exit_code)

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
            idle_action=args.idle_action,
            epic_mode=args.epic
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
        # invalid_epic and any unknown stop reasons
        sys.exit(2)


if __name__ == "__main__":
    main()
