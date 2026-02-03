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
)

# Re-export models for convenience
from .models import (
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
    # Models
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
]
# Note: StatusWriter is available under TYPE_CHECKING for type hints only
