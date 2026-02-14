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

# Epic titles to exclude from auto-selection (parking lot pattern)
# See .kiro/steering/line-cook.md, parking lot section
EXCLUDED_EPIC_TITLES = frozenset({"Retrospective", "Backlog"})

# Default phase timeouts (in seconds) - can be overridden via CLI
DEFAULT_PHASE_TIMEOUTS = {
    'cook': 1200,           # 20 min - Main work phase: TDD cycle, file edits, test runs
    'serve': 600,           # 10 min - Code review by sous-chef subagent
    'tidy': 240,            # 4 min - Commit, bd sync, git push
    'plate': 600,           # 10 min - BDD review via maître, acceptance doc
    'close-service': 900,   # 15 min - Critic E2E review + epic acceptance doc
}
