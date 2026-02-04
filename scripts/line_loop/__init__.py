"""Line Loop - Autonomous loop execution for Line Cook workflow.

This package modularizes line-loop.py into focused modules:

- config: Constants and configuration values
- models: Dataclasses for state tracking (BeadSnapshot, ServeResult, etc.)
- parsing: Output parsing functions (serve_result, intent, feedback)
- phase: Phase execution (run_phase, streaming)
- iteration: Single iteration logic
- loop: Main loop orchestration

Usage:
    from line_loop import run_loop
    run_loop(cwd=Path.cwd(), max_iterations=25)
"""

__version__ = "0.1.0"

# Re-export config constants for convenience
from .config import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TASK_FAILURES,
    DEFAULT_PHASE_TIMEOUTS,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    BD_COMMAND_TIMEOUT,
    GIT_COMMAND_TIMEOUT,
    GIT_SYNC_TIMEOUT,
    LOG_FILE_MAX_BYTES,
    LOG_FILE_BACKUP_COUNT,
)

# Re-export models for convenience
from .models import (
    BeadDelta,
    BeadInfo,
    CircuitBreaker,
    LoopError,
    SkipList,
    LoopMetrics,
    BeadSnapshot,
    ServeResult,
    ServeFeedbackIssue,
    ServeFeedback,
    PhaseResult,
    ActionRecord,
    IterationResult,
    LoopReport,
    ProgressState,
    summarize_tool_input,
)

# Re-export parsing functions for convenience
from .parsing import (
    parse_serve_result,
    parse_serve_feedback,
    parse_intent_block,
    parse_stream_json_event,
    extract_text_from_event,
    extract_actions_from_event,
    update_action_from_result,
)

# Re-export phase execution functions
from .phase import (
    run_phase,
    run_subprocess,
    check_idle,
    detect_kitchen_complete,
    detect_kitchen_idle,
)

# Re-export iteration functions
from .iteration import (
    run_iteration,
    build_hierarchy_chain,
    check_task_completed,
    check_feature_completion,
    check_epic_completion_after_feature,
    check_epic_completion,
    detect_worked_task,
    get_bead_snapshot,
    get_task_info,
    get_task_title,
    get_children,
    get_latest_commit,
    format_duration,
    print_phase_progress,
    print_human_iteration,
    print_feature_completion,
    atomic_write,
)

# Re-export loop functions
from .loop import (
    run_loop,
    sync_at_start,
    write_status_file,
    generate_escalation_report,
    format_escalation_report,
    get_next_ready_task,
    calculate_retry_delay,
    request_shutdown,
    reset_shutdown_flag,
)

# Type-only export for StatusWriter protocol
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import StatusWriter

__all__ = [
    # Config
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_MAX_TASK_FAILURES",
    "DEFAULT_PHASE_TIMEOUTS",
    "DEFAULT_IDLE_TIMEOUT",
    "DEFAULT_IDLE_ACTION",
    "BD_COMMAND_TIMEOUT",
    "GIT_COMMAND_TIMEOUT",
    "GIT_SYNC_TIMEOUT",
    "LOG_FILE_MAX_BYTES",
    "LOG_FILE_BACKUP_COUNT",
    # Models
    "BeadDelta",
    "BeadInfo",
    "CircuitBreaker",
    "LoopError",
    "SkipList",
    "LoopMetrics",
    "BeadSnapshot",
    "ServeResult",
    "ServeFeedbackIssue",
    "ServeFeedback",
    "PhaseResult",
    "ActionRecord",
    "IterationResult",
    "LoopReport",
    "ProgressState",
    "summarize_tool_input",
    # Parsing
    "parse_serve_result",
    "parse_serve_feedback",
    "parse_intent_block",
    "parse_stream_json_event",
    "extract_text_from_event",
    "extract_actions_from_event",
    "update_action_from_result",
    # Phase execution
    "run_phase",
    "run_subprocess",
    "check_idle",
    "detect_kitchen_complete",
    "detect_kitchen_idle",
    # Iteration
    "run_iteration",
    "build_hierarchy_chain",
    "check_task_completed",
    "check_feature_completion",
    "check_epic_completion_after_feature",
    "check_epic_completion",
    "detect_worked_task",
    "get_bead_snapshot",
    "get_task_info",
    "get_task_title",
    "get_children",
    "get_latest_commit",
    "format_duration",
    "print_phase_progress",
    "print_human_iteration",
    "print_feature_completion",
    "atomic_write",
    # Loop
    "run_loop",
    "sync_at_start",
    "write_status_file",
    "generate_escalation_report",
    "format_escalation_report",
    "get_next_ready_task",
    "calculate_retry_delay",
    "request_shutdown",
    "reset_shutdown_flag",
]
# Note: StatusWriter is available under TYPE_CHECKING for type hints only
