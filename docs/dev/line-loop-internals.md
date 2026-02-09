# Line Loop Developer Reference

Developer internals for the autonomous loop implementation. For usage documentation, see the loop command (`/line:loop` or equivalent).

## Applied Best Practices

| Pattern | Implementation |
|---------|----------------|
| Named constants | `DEFAULT_*`, `*_TIMEOUT`, `*_MAX_*` in `config.py` |
| Structured errors | `LoopError` dataclass with context and factory methods |
| Signal handling | Minimal handlers set `_shutdown_requested` flag |
| Dataclasses | `BeadSnapshot`, `ServeResult`, `IterationResult`, `LoopReport` in `models.py` |
| Atomic writes | `atomic_write()` for status/history files |
| Exponential backoff | `calculate_retry_delay()` with jitter |
| Circuit breaker | `CircuitBreaker` class for failure throttling |

---

## Architecture Overview

The loop is implemented as a modular Python package with clear separation of concerns. The thin CLI wrapper (`line-loop.py`) handles argument parsing and signal setup, then delegates to the `line_loop/` package for all logic.

### Package Structure

```
core/
├── line-loop-cli.py      # CLI wrapper source (bundled into line-loop.py)
└── line_loop/            # Core package
    ├── __init__.py       # Re-exports public API
    ├── config.py         # Constants: DEFAULT_*, timeouts, limits
    ├── models.py         # Dataclasses: CircuitBreaker, LoopError, BeadSnapshot,
    │                     #   ServeResult, IterationResult, LoopReport, etc.
    ├── parsing.py        # Output parsing: serve_result, intent, feedback
    ├── phase.py          # Phase execution: run_phase, streaming, idle detection
    ├── iteration.py      # Single iteration: run_iteration, completion checks
    └── loop.py           # Main orchestration: run_loop, sync, status writing

plugins/claude-code/scripts/
└── line-loop.py          # Bundled script (auto-generated from core/)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           line-loop.py (CLI)                            │
│  - Parse CLI args                                                       │
│  - Set up signal handlers (SIGINT, SIGTERM, SIGHUP → request_shutdown)  │
│  - Call run_loop() from line_loop package                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          loop.py (Orchestrator)                         │
│  run_loop():                                                            │
│  - Initial sync (git fetch/pull, bd sync)                               │
│  - Main loop: check ready work → run_iteration → handle outcome         │
│  - Circuit breaker & skip list management                               │
│  - Status/history file updates                                          │
│  - Epic completion detection                                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       iteration.py (Single Cycle)                       │
│  run_iteration():                                                       │
│  - Capture before snapshot (get_bead_snapshot)                          │
│  - Run phases: cook → serve → tidy (→ plate if feature complete)        │
│  - Cook retry loop on NEEDS_CHANGES                                     │
│  - Extract intent/before/after from output                              │
│  - Return IterationResult with all actions                              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        phase.py (Phase Execution)                       │
│  run_phase():                                                           │
│  - Invoke CLI with skill (e.g., /line:cook)                             │
│  - Stream stdout via select(), parse events as they arrive              │
│  - Track tool actions (extract_actions_from_event)                      │
│  - Detect signals (KITCHEN_COMPLETE, SERVE_RESULT, phase_complete)      │
│  - Idle detection (configurable timeout + action)                       │
│  - Return PhaseResult with output, signals, actions                     │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        parsing.py (Output Parsing)                      │
│  - parse_serve_result(): Extract verdict from SERVE_RESULT block        │
│  - parse_serve_feedback(): Extract issues for retry context             │
│  - parse_intent_block(): Extract INTENT and BEFORE→AFTER                │
│  - parse_stream_json_event(): Parse single line of stream-json          │
│  - extract_actions_from_event(): Get tool_use blocks from event         │
│  - update_action_from_result(): Correlate tool_result with tool_use     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Module Dependency Graph

```
┌─────────────┐
│  config.py  │  (no imports from other line_loop modules)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  models.py  │  imports: config
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ parsing.py  │  imports: config, models
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  phase.py   │  imports: config, models, parsing
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ iteration.py │ imports: config, models, parsing, phase
└──────┬───────┘
       │
       ▼
┌─────────────┐
│   loop.py   │  imports: config, models, iteration, phase
└─────────────┘
```

---

## Module Index

| Module | Responsibility | Key Exports | Used By |
|--------|----------------|-------------|---------|
| `config.py` | Named constants and default values | `DEFAULT_MAX_ITERATIONS`, `DEFAULT_PHASE_TIMEOUTS`, `BD_COMMAND_TIMEOUT`, etc. | All modules |
| `models.py` | Dataclasses for state tracking | `CircuitBreaker`, `SkipList`, `LoopError`, `LoopMetrics`, `BeadSnapshot`, `ServeResult`, `PhaseResult`, `ActionRecord`, `IterationResult`, `LoopReport`, `ProgressState` | parsing, phase, iteration, loop |
| `parsing.py` | Parse phase output | `parse_serve_result()`, `parse_serve_feedback()`, `parse_intent_block()`, `extract_actions_from_event()`, `update_action_from_result()` | phase, iteration |
| `phase.py` | Execute individual phases | `run_phase()`, `run_subprocess()`, `check_idle()`, `detect_kitchen_complete()`, `detect_kitchen_idle()` | iteration, loop |
| `iteration.py` | Run one complete task iteration | `run_iteration()`, `get_bead_snapshot()`, `check_task_completed()`, `check_feature_completion()`, `check_epic_completion_after_feature()`, `check_epic_completion()`, `get_latest_commit()`, `atomic_write()` | loop |
| `loop.py` | Main loop orchestration | `run_loop()`, `sync_at_start()`, `write_status_file()`, `generate_escalation_report()`, `request_shutdown()` | line-loop.py (CLI) |

### Module Details

#### config.py
Centralized constants following naming convention `DEFAULT_*`, `*_TIMEOUT`, `*_MAX_*`:
- **Output limits**: `OUTPUT_SUMMARY_MAX_LENGTH`, `GOAL_TEXT_MAX_LENGTH`
- **Task defaults**: `DEFAULT_MAX_ITERATIONS` (25), `DEFAULT_MAX_TASK_FAILURES` (3)
- **Timeouts**: `BD_COMMAND_TIMEOUT` (30s), `GIT_SYNC_TIMEOUT` (60s), `DEFAULT_PHASE_TIMEOUTS` (cook=1200s, serve=600s, tidy=240s, plate=600s)
- **Retry config**: `MAX_RETRY_DELAY_SECONDS` (60), `CIRCUIT_BREAKER_WINDOW_SIZE` (10)

#### models.py
Dataclasses with factory methods and computed properties:
- **CircuitBreaker**: Sliding window failure tracking with `record()`, `is_open()`, `reset()`
- **LoopError**: Structured error with `from_timeout()`, `from_json_decode()`, `from_subprocess()`, `from_io()` factory methods
- **SkipList**: Track tasks to skip after repeated failures
- **LoopMetrics**: Computed metrics (success_rate, p50/p95 duration, timeout_rate, retry_rate)
- **BeadSnapshot**: Captures ready/in_progress/closed task IDs at a point in time
- **ServeResult**: Parsed verdict, continue flag, blocking issues count
- **PhaseResult**: Phase output, signals, actions, duration, success
- **ActionRecord**: Single tool call with input/output summaries
- **IterationResult**: Full iteration outcome with before/after state
- **ProgressState**: Real-time progress for status file updates

#### parsing.py
Regex-based parsing of phase output:
- **parse_serve_result()**: Extract SERVE_RESULT block (verdict, continue, blocking_issues)
- **parse_serve_feedback()**: Extract detailed issues for retry context
- **parse_intent_block()**: Extract INTENT and BEFORE→AFTER blocks
- **Stream parsing**: `parse_stream_json_event()`, `extract_text_from_event()`, `extract_actions_from_event()`, `update_action_from_result()`

#### phase.py
Phase execution with streaming and idle detection:
- **run_phase()**: Invoke CLI, stream stdout, detect signals, track actions
- **run_subprocess()**: Wrapper with logging, timeout handling
- **check_idle()**: Check if phase has been idle beyond threshold
- **detect_kitchen_complete/idle()**: Pattern matching for cook phase signals

#### iteration.py
Single iteration lifecycle (cook→serve→tidy→plate):
- **run_iteration()**: Execute phases with retry logic on NEEDS_CHANGES
- **Bead state**: `get_bead_snapshot()`, `detect_worked_task()`, `get_task_info()`, `get_task_title()`, `get_children()`
- **Completion checks**: `check_task_completed()`, `check_feature_completion()`, `check_epic_completion_after_feature()`, `check_epic_completion()`
- **Epic reporting**: `generate_epic_closure_report()`, `get_epic_summary()`, `print_epic_completion()`
- **Git helpers**: `get_latest_commit()`, `atomic_write()`
- **Retry context**: `write_retry_context()`, `clear_retry_context()`
- **Display helpers**: `format_duration()`, `print_phase_progress()`, `print_human_iteration()`

#### loop.py
Main loop orchestration:
- **run_loop()**: Main entry point - sync, iterate, handle outcomes, write status
- **sync_at_start()**: Git fetch/pull + bd sync (runs once at startup)
- **write_status_file()**: Atomic JSON status for external monitoring
- **Escalation**: `generate_escalation_report()`, `format_escalation_report()`
- **Task selection**: `get_next_ready_task()` with skip list filtering
- **History**: `append_iteration_to_history()`, `write_history_summary()` (JSONL format)
- **Shutdown**: `request_shutdown()`, `reset_shutdown_flag()` for graceful termination

---

## Adding New Features

1. Extract magic numbers to named constants in `config.py`
2. Use `LoopError.from_*()` factory methods for error creation (in `models.py`)
3. Follow existing docstring style (Args/Returns/Notes)
4. Update status.json schema if adding new tracking fields
5. Add new parsing logic to `parsing.py`, phase logic to `phase.py`, etc.
6. Place new dataclasses in `models.py` with appropriate factory methods
7. Update `__init__.py` to re-export new public API functions

---

## Developer Debug

For contributors debugging loop internals, see the [Architecture Overview](#architecture-overview) section above.

**Key source locations:**

| Issue | Module | Key Function |
|-------|--------|--------------|
| Phase execution | `phase.py` | `run_phase()` |
| Iteration logic | `iteration.py` | `run_iteration()` |
| Circuit breaker | `models.py` | `CircuitBreaker.is_open()` |
| Skip list | `models.py` | `SkipList.is_skipped()` |
| Status updates | `loop.py` | `write_status_file()` |
| Serve parsing | `parsing.py` | `parse_serve_result()` |

**Enable verbose logging:**
```bash
# Set VERBOSE=1 to see debug output
VERBOSE=1 python3 plugins/claude-code/scripts/line-loop.py --max-iterations 1
```

**Inspect internal state:**
```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"

# Current state with all fields
jq '.' "$LOOP_DIR/status.json"

# Last iteration actions
jq -s '.[-1].actions' "$LOOP_DIR/history.jsonl"

# Circuit breaker window (from last iteration)
jq -s '.[-1] | {iteration, outcome, success}' "$LOOP_DIR/history.jsonl" | tail -10
```
