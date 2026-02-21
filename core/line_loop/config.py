"""Configuration constants for line-loop.

Extracted from line-loop.py for maintainability.
See docs/guidance/python-scripting.md for naming conventions.
"""

# Output and display limits
OUTPUT_SUMMARY_MAX_LENGTH = 200
INPUT_SUMMARY_FILE_PATH_LENGTH = 100
INPUT_SUMMARY_COMMAND_LENGTH = 80
INPUT_SUMMARY_PATTERN_LENGTH = 60
GOAL_TEXT_MAX_LENGTH = 200
BANNER_MIN_WIDTH = 62

# Task and iteration defaults
DEFAULT_MAX_TASK_FAILURES = 3       # Skip task after this many failures
DEFAULT_MAX_ITERATIONS = 25         # Default loop iterations
DEFAULT_IDLE_TIMEOUT = 180          # 3 minutes without tool actions triggers idle
DEFAULT_IDLE_ACTION = "warn"        # "warn" or "terminate"

# Periodic sync (long-running loop resilience)
PERIODIC_SYNC_INTERVAL = 5          # Run bd sync every N iterations

# Subprocess timeouts (in seconds)
BD_COMMAND_TIMEOUT = 30             # Standard bd command timeout
GIT_COMMAND_TIMEOUT = 10            # Short git commands (log, show)
GIT_SYNC_TIMEOUT = 60               # Longer git operations (fetch, pull)
DEFAULT_FALLBACK_PHASE_TIMEOUT = 600  # Fallback for unknown phases

# Logging configuration
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB max per log file
LOG_FILE_BACKUP_COUNT = 3              # Keep 3 backup files

# Retry and backoff configuration
MAX_RETRY_DELAY_SECONDS = 60        # Cap for exponential backoff
CIRCUIT_BREAKER_WINDOW_SIZE = 10    # Sliding window for failure tracking

# History and status tracking
RECENT_ITERATIONS_LIMIT = 10        # Iterations to consider for analysis
RECENT_ITERATIONS_DISPLAY = 5       # Iterations to show in status/reports
CLOSED_TASKS_QUERY_LIMIT = 10       # Limit for closed tasks query

# Hierarchy traversal
HIERARCHY_MAX_DEPTH = 10            # Max depth for epic/feature/task hierarchy walks

# CLI profiles for multi-CLI support
CLI_PROFILES = {
    'claude': {
        'binary': 'claude',
        'prompt_format': '/line:{phase}',
        'permission_flags': ['--dangerously-skip-permissions'],
        'output_flags': ['--output-format', 'stream-json', '--verbose'],
        'has_streaming_json': True,
        'install_hint': 'Install Claude Code: https://docs.anthropic.com/en/docs/claude-code',
        'phase_timeout_multiplier': 1.0,
    },
    'kiro': {
        'binary': 'kiro-cli',
        'subcommand': 'chat',
        'prompt_format': '@line-{phase}',
        'permission_flags': ['--trust-all-tools'],
        'extra_flags': ['--no-interactive', '--wrap', 'never', '--agent', 'line-cook'],
        'has_streaming_json': False,
        'install_hint': 'Install Kiro CLI: https://kiro.dev/docs/cli',
        'phase_timeout_multiplier': 1.5,
        # Kiro bug #4141: args after @ commands are silently dropped.
        # Inject task ID as text before the @ command so the agent receives it.
        'task_injection': '[task-id: {args}] ',
    },
}

DEFAULT_CLI = 'claude'


def get_cli_profile(name: str) -> dict:
    """Get CLI profile by name.

    Args:
        name: Profile name ('claude' or 'kiro').

    Returns:
        Profile dict with binary, prompt_format, flags, etc.

    Raises:
        KeyError: If profile name is not found.
    """
    return CLI_PROFILES[name]


# Epic titles to exclude from auto-selection (parking lot pattern)
# See .kiro/steering/line-cook.md, parking lot section
EXCLUDED_EPIC_TITLES = frozenset({"Retrospective", "Backlog"})

# Default phase timeouts (in seconds) - can be overridden via CLI
DEFAULT_PHASE_TIMEOUTS = {
    'cook': 1200,           # 20 min - Main work phase: TDD cycle, file edits, test runs
    'serve': 450,           # 7.5 min - Code review by sous-chef subagent
    'tidy': 240,            # 4 min - Commit, bd sync, git push
    'plate': 450,           # 7.5 min - BDD review via maître, acceptance doc
    'close-service': 750,   # 12.5 min - Critic E2E review + epic acceptance doc
}

# Per-phase idle timeouts (in seconds) - used when no explicit idle_timeout passed
# Phases with longer expected pauses (e.g., serve waiting for subagent) get longer idle thresholds
DEFAULT_PHASE_IDLE_TIMEOUTS = {
    'cook': 180,            # 3 min - Active coding, frequent tool use expected
    'serve': 300,           # 5 min - Review may have long pauses between actions
    'tidy': 90,             # 1.5 min - Quick commit/push, should be fast
    'plate': 300,           # 5 min - BDD review, subagent pauses expected
    'close-service': 600,   # 10 min - Epic close involves extensive review
}
