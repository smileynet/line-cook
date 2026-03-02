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
    ACTIVE_EXTENSION_CAP,
    ACTIVE_EXTENSION_WINDOW,
    BACKLOG_PRIORITY_THRESHOLD,
    CLI_PROFILES,
    CONSECUTIVE_SAME_TASK_LIMIT,
    DEFAULT_CLI,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_MAX_TASK_FAILURES,
    DEFAULT_PHASE_TIMEOUTS,
    DEFAULT_PHASE_IDLE_TIMEOUTS,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_IDLE_ACTION,
    BD_COMMAND_TIMEOUT,
    GIT_COMMAND_TIMEOUT,
    GIT_SYNC_TIMEOUT,
    EXCLUDED_EPIC_TITLES,
    HIERARCHY_MAX_DEPTH,
    LOG_FILE_MAX_BYTES,
    LOG_FILE_BACKUP_COUNT,
    MAX_FEEDBACK_HISTORY,
    PERIODIC_SYNC_INTERVAL,
    get_cli_profile,
)

# Re-export models for convenience
from .models import (
    BeadDelta,
    BeadInfo,
    CircuitBreaker,
    ENVIRONMENTAL_INDICATORS,
    FailureCategory,
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
    TRANSIENT_INDICATORS,
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
    strip_ansi,
    normalize_signal_text,
    parse_kiro_tool_action,
    parse_kiro_tool_result,
    extract_kiro_actions_from_line,
)

# Re-export phase execution functions
from .phase import (
    build_phase_command,
    process_output_line,
    run_phase,
    run_subprocess,
    check_idle,
    resolve_idle_timeout,
    detect_kitchen_complete,
    detect_kitchen_idle,
)

# Re-export iteration functions
from .iteration import (
    run_iteration,
    build_epic_ancestor_map,
    build_hierarchy_chain,
    check_task_completed,
    check_feature_completion,
    check_epic_completion_after_feature,
    check_epic_completion,
    detect_eligible_epics,
    detect_premature_completion,
    detect_worked_task,
    find_epic_ancestor,
    get_bead_snapshot,
    get_task_info,
    get_task_title,
    get_children,
    get_latest_commit,
    get_current_branch,
    get_epic_for_task,
    is_descendant_of_epic,
    is_first_epic_work,
    format_duration,
    print_phase_progress,
    print_human_iteration,
    print_feature_completion,
    print_epic_completion,
    atomic_write,
)

# Re-export loop functions
from .loop import (
    run_loop,
    sync_at_start,
    write_status_file,
    generate_escalation_report,
    format_escalation_report,
    get_excluded_epic_ids,
    detect_first_epic,
    validate_epic_id,
    get_next_ready_task,
    classify_iteration_failure,
    calculate_retry_delay,
    request_shutdown,
    reset_shutdown_flag,
    has_uncommitted_changes,
    auto_commit_wip,
    ensure_epic_branch,
    merge_epic_on_close,
    merge_completed_epic,
    periodic_sync,
    should_periodic_sync,
)

# Type-only export for StatusWriter protocol
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import StatusWriter

__all__ = [
    # Config
    "ACTIVE_EXTENSION_CAP",
    "ACTIVE_EXTENSION_WINDOW",
    "BACKLOG_PRIORITY_THRESHOLD",
    "CLI_PROFILES",
    "CONSECUTIVE_SAME_TASK_LIMIT",
    "DEFAULT_CLI",
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_MAX_TASK_FAILURES",
    "DEFAULT_PHASE_TIMEOUTS",
    "DEFAULT_PHASE_IDLE_TIMEOUTS",
    "DEFAULT_IDLE_TIMEOUT",
    "DEFAULT_IDLE_ACTION",
    "BD_COMMAND_TIMEOUT",
    "GIT_COMMAND_TIMEOUT",
    "GIT_SYNC_TIMEOUT",
    "EXCLUDED_EPIC_TITLES",
    "HIERARCHY_MAX_DEPTH",
    "LOG_FILE_MAX_BYTES",
    "LOG_FILE_BACKUP_COUNT",
    "MAX_FEEDBACK_HISTORY",
    "PERIODIC_SYNC_INTERVAL",
    "get_cli_profile",
    # Models
    "BeadDelta",
    "BeadInfo",
    "CircuitBreaker",
    "ENVIRONMENTAL_INDICATORS",
    "FailureCategory",
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
    "TRANSIENT_INDICATORS",
    "summarize_tool_input",
    # Parsing
    "parse_serve_result",
    "parse_serve_feedback",
    "parse_intent_block",
    "parse_stream_json_event",
    "extract_text_from_event",
    "extract_actions_from_event",
    "update_action_from_result",
    "strip_ansi",
    "normalize_signal_text",
    "parse_kiro_tool_action",
    "parse_kiro_tool_result",
    "extract_kiro_actions_from_line",
    # Phase execution
    "build_phase_command",
    "process_output_line",
    "run_phase",
    "run_subprocess",
    "check_idle",
    "resolve_idle_timeout",
    "detect_kitchen_complete",
    "detect_kitchen_idle",
    # Iteration
    "run_iteration",
    "build_epic_ancestor_map",
    "build_hierarchy_chain",
    "check_task_completed",
    "check_feature_completion",
    "check_epic_completion_after_feature",
    "check_epic_completion",
    "detect_eligible_epics",
    "detect_premature_completion",
    "detect_worked_task",
    "find_epic_ancestor",
    "get_bead_snapshot",
    "get_task_info",
    "get_task_title",
    "get_children",
    "get_latest_commit",
    "get_current_branch",
    "get_epic_for_task",
    "is_descendant_of_epic",
    "is_first_epic_work",
    "format_duration",
    "print_phase_progress",
    "print_human_iteration",
    "print_feature_completion",
    "print_epic_completion",
    "atomic_write",
    # Loop
    "run_loop",
    "sync_at_start",
    "write_status_file",
    "generate_escalation_report",
    "format_escalation_report",
    "get_excluded_epic_ids",
    "detect_first_epic",
    "validate_epic_id",
    "get_next_ready_task",
    "classify_iteration_failure",
    "calculate_retry_delay",
    "request_shutdown",
    "reset_shutdown_flag",
    "has_uncommitted_changes",
    "auto_commit_wip",
    "ensure_epic_branch",
    "merge_epic_on_close",
    "merge_completed_epic",
    "periodic_sync",
    "should_periodic_sync",
]
# Note: StatusWriter is available under TYPE_CHECKING for type hints only
