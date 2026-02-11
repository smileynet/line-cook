**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included text after the @prompt name, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Control the autonomous line-loop process.** Provides start/status/stop/tail subcommands for managing background loop execution.

**Arguments:** `$ARGUMENTS` contains the subcommand and options:
- *(no args)* - Smart default: watch if running, start if not
- `start [--max-iterations N] [--cook-timeout S] ...` - Start loop in background
- `watch` - Live progress with milestones and context
- `status` - One-shot status check
- `stop` - Gracefully stop running loop
- `tail [--lines N]` - Show recent log output
- `history [--iteration N] [--actions]` - View full iteration history with action details

---

## Quick Start

### Readiness Checklist

| Ready? | Prerequisite | Why |
|:------:|--------------|-----|
| ☐ | Run `@line-prep` → `@line-cook` → `@line-tidy` manually | Understand the workflow |
| ☐ | Run `@line-run` a few times | Practice single-task cycles |
| ☐ | Have `bd ready` tasks available | Loop needs work to do |

### First Loop

```bash
@line-loop                        # Smart default: start or watch
@line-loop start --max-iterations 3  # Test run (recommended first time)
@line-loop watch                  # Monitor progress with context
```

---

## Command Selection Guide

| Scenario | Command |
|----------|---------|
| First time / unsure | `@line-loop` (smart default) |
| Monitor with context | `@line-loop watch` |
| Quick status check | `@line-loop status` |
| Debug issues | `@line-loop tail --lines 100` |
| Review what happened | `@line-loop history --actions` |
| Stop gracefully | `@line-loop stop` |
| Custom iteration limit | `@line-loop start --max-iterations N` |
| Stop on first blocker | `@line-loop start --stop-on-blocked` |
| Focus on one epic | `@line-loop start --epic` |
| Focus on specific epic | `@line-loop start --epic lc-001` |
| Epic milestone review | `@line-loop start --break-on-epic` |
| Complex tasks (40min) | `@line-loop start --cook-timeout 2400` |

---

## Timeout Behavior

**Loop execution** manages its own subprocess timeouts, providing:
- Phase-appropriate defaults (cook needs more time than tidy)
- Full configurability via CLI flags
- Idle detection to catch hung phases
- Early termination via `<phase_complete>DONE</phase_complete>` signal

### When to Use Each

| Scenario | Recommended Mode |
|----------|------------------|
| Quick bug fix or small change | Standalone |
| Complex feature implementation | Loop with `--cook-timeout 2400` |
| Large codebase refactoring | Loop with extended timeouts |
| Learning the workflow | Standalone (see Quick Start) |
| Batch processing multiple tasks | Loop |

### Configuring Loop Timeouts

```bash
# Default timeouts (usually sufficient)
@line-loop start

# Complex tasks (40-minute cook phase)
@line-loop start --cook-timeout 2400

# Large diffs (15-minute serve phase)
@line-loop start --serve-timeout 900

# All phases extended
@line-loop start --cook-timeout 2400 --serve-timeout 900 --tidy-timeout 480
```

---

## Understanding Output

### Phase Progress Indicators

During each iteration, you'll see phase progress:
```
  ▶ COOK phase...
  ✓ COOK complete (23.5s) - 5 actions
  ▶ SERVE phase...
  ✓ SERVE complete (8.2s) - APPROVED
  ▶ TIDY phase...
  ✓ TIDY complete (4.1s) - committed a3f8b2c
```

| Symbol | Meaning |
|--------|---------|
| ▶ | Phase starting |
| ✓ | Phase completed successfully |
| ✗ | Phase encountered an error |

### Iteration Summary

After each iteration completes:
```
  [OK] lc-042: Fix timeout handling
  Intent: Increase timeout for large repos
  Before: No timeout config
  After:  Configurable timeout
  Duration: 45.2s | Verdict: APPROVED | Commit: a3f8b2c
  Actions: 12 total (Read: 4, Edit: 3, Bash: 3, Grep: 2)

  Beads: ready 5→4 | in_progress 0→0 | closed +1
```

| Status | Meaning |
|--------|---------|
| [OK] | Task completed and committed |
| [RETRY] | Task needs changes, will retry |
| [BLOCKED] | Task blocked, cannot proceed |
| [TIMEOUT] | Phase timed out |
| [DONE] | No more work items ready |

### Action Breakdown

The `Actions:` line shows tool usage during the iteration:
- **Total count** followed by breakdown by tool type
- Sorted alphabetically by tool name
- Only non-zero counts shown

---

## Help Output

If `help` is passed as an argument:

```
@line-loop - Manage autonomous loop execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage:
  @line-loop                           # Smart default (watch if running, start if not)
  @line-loop watch                     # Live progress with milestones
  @line-loop start [options]           # Start loop with options
  @line-loop status                    # One-shot status check
  @line-loop stop                      # Gracefully stop
  @line-loop tail [--lines N]          # View log output
  @line-loop history [--iteration N] [--actions]  # View iteration history

Commands:
  (none)   Smart default - watch if loop running, start if not
  watch    Live progress with milestones and before/after context
  start    Launch loop in background (default: 25 iterations)
  status   One-shot status check
  stop     Gracefully stop running loop
  tail     Show recent log output (default: 50 lines)
  history  View iteration history with action details

Start Options:
  --epic [EPIC_ID]      Focus on one epic (auto-select first, or specify ID)
  --max-iterations N    Maximum iterations (default: 25)
  --cook-timeout S      Cook phase timeout in seconds (default: 1200)
  --serve-timeout S     Serve phase timeout in seconds (default: 600)
  --tidy-timeout S      Tidy phase timeout in seconds (default: 240)
  --plate-timeout S     Plate phase timeout in seconds (default: 600)
  --idle-timeout S      Seconds without tool actions before idle triggers (default: 180, 0 to disable)
  --idle-action ACTION  Action on idle: warn (log warning) or terminate (stop phase) (default: warn)
  --max-retries N       Max retries per task on NEEDS_CHANGES (default: 2)
  --max-task-failures N Skip task after this many failures (default: 3)
  --stop-on-blocked     Stop if task is BLOCKED (default: continue)
  --stop-on-crash       Stop on subprocess crash (default: continue)
  --break-on-epic       Pause loop when an epic completes (default: continue)
  --skip-initial-sync   Skip git fetch/pull and bd sync at loop start

Examples:
  @line-loop                          # Start or watch (smart default)
  @line-loop watch                    # Monitor progress with context
  @line-loop start --max-iterations 5 # Quick test run
  @line-loop start --cook-timeout 1800 # Complex tasks (30min cook timeout)
  @line-loop start --epic              # Auto-select first available epic
  @line-loop start --epic lc-001      # Focus on specific epic
  @line-loop start --break-on-epic    # Pause for review at epic completion
  @line-loop start --stop-on-blocked  # Stop immediately on blocked tasks
  @line-loop status                   # One-shot status check
  @line-loop tail --lines 100         # View more log output
  @line-loop history --actions        # View all iterations with actions
  @line-loop stop                     # Stop gracefully

Files stored in: /tmp/line-loop-<project-name>/
```

---

## File Locations

Loop artifacts are stored in a **project-specific directory** to avoid conflicts when working on multiple projects:

```
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
```

| File | Purpose |
|------|---------|
| `$LOOP_DIR/loop.pid` | Process ID for management |
| `$LOOP_DIR/loop.log` | Full log output |
| `$LOOP_DIR/status.json` | Live status (updated during phases and after iterations, includes phase progress and action counts) |
| `$LOOP_DIR/history.jsonl` | Complete history of ALL iterations with full action details (JSONL format) |
| `$LOOP_DIR/report.json` | Final report (written on completion) |

---

## Process

### Compute Loop Directory

**First, compute the project-specific loop directory:**

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
mkdir -p "$LOOP_DIR"
```

Use this `$LOOP_DIR` for all file paths in subsequent commands.

### Parse Subcommand

Extract the subcommand from the user's input:

```
Input examples:
  "start"                      -> subcommand: start
  "start --max-iterations 10"  -> subcommand: start, max_iterations: 10
  "watch"                      -> subcommand: watch
  "status"                     -> subcommand: status
  "stop"                       -> subcommand: stop
  "tail"                       -> subcommand: tail
  "tail --lines 100"           -> subcommand: tail, lines: 100
  "help"                       -> subcommand: help
  ""                           -> smart default: check if running
                                  - If running: invoke watch
                                  - If not running: invoke start with defaults
```

---

## Subcommand: start

### Acquire Start Lock

First, acquire an exclusive lock to prevent race conditions when multiple starts are attempted simultaneously:

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
mkdir -p "$LOOP_DIR"
LOCKFILE="$LOOP_DIR/loop.lock"

# Try to acquire exclusive lock (non-blocking)
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "Another loop instance is starting. Please wait and try again."
  exit 1
fi
# Lock held until script exits (fd 9 auto-closes)
```

### Check if Already Running

Then, check if a loop is already running:

```bash
if [ -f "$LOOP_DIR/loop.pid" ]; then
  PID=$(cat "$LOOP_DIR/loop.pid" 2>/dev/null)
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo "Loop already running (PID: $PID)"
    echo "Use '@line-loop status' to check progress or '@line-loop stop' to stop it."
    exit 1
  else
    # Stale or invalid PID file, clean up
    rm -f "$LOOP_DIR/loop.pid"
  fi
fi
```

### Find Script Path

Locate the `line-loop.py` CLI wrapper. The wrapper is a thin script that imports from the `line_loop/` package in the same directory.


### Launch Background Loop


```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
mkdir -p "$LOOP_DIR"
python3 <path-to-line-loop.py> \
  --max-iterations ${MAX_ITERATIONS:-25} \
  --json \
  --output "$LOOP_DIR/report.json" \
  --log-file "$LOOP_DIR/loop.log" \
  --pid-file "$LOOP_DIR/loop.pid" \
  --status-file "$LOOP_DIR/status.json" \
  --history-file "$LOOP_DIR/history.jsonl"
```

Replace `<path-to-line-loop.py>` with the absolute path located above.


### Output

```
Loop started in background (task ID: <task_id>)
Project: <project-name>
Loop dir: /tmp/line-loop-<project-name>

Monitor with:
  @line-loop status    - Check progress
  @line-loop tail      - View log output
  @line-loop stop      - Stop gracefully
```

---

## Subcommand: status

### Check Running State

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
# Check if PID file exists and process is running
if [ -f "$LOOP_DIR/loop.pid" ]; then
  PID=$(cat "$LOOP_DIR/loop.pid")
  if kill -0 "$PID" 2>/dev/null; then
    RUNNING=true
  else
    RUNNING=false
  fi
else
  RUNNING=false
fi
```

### Read Status File

Read `$LOOP_DIR/status.json` (compute the actual path first).

### Format Output

**Cross-check status file with PID:** If status file shows `running: true` but no process is running (PID file missing or process dead), the loop terminated unexpectedly. Report this to the user.

**If running:**
```
Loop Status: RUNNING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: <project-name>
Iteration: 3/25
Current Task: lc-042 - Fix timeout handling
Last Verdict: APPROVED

Progress:
  Completed: 2
  Remaining: 5

Running since: 5m 30s ago
Last update: 10s ago
```

**If status shows running but process is dead (stale status):**
```
Loop Status: TERMINATED UNEXPECTEDLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The loop process is no longer running but did not exit cleanly.
This may indicate it was killed or crashed.

Last known state:
  Iteration: 3/25
  Current Task: lc-042
  Last update: 5m ago

Check logs for details:
  @line-loop tail --lines 100
```

**If not running but status file exists (clean exit):**
```
Loop Status: STOPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stop reason: no_tasks
Final iteration: 8/25

Summary:
  Completed: 6
  Remaining: 0

Last update: 2m ago
```

**If no status file:**
```
Loop Status: NOT RUNNING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No loop is currently running and no previous status found.

Start a loop with:
  @line-loop start
  @line-loop start --max-iterations 10
```

---

## Subcommand: watch

Watch mode provides unified progress monitoring with milestones and context from completed iterations.

### Check Running State

Same as status - verify the loop is running first.

### Read Status File

Read `$LOOP_DIR/status.json`. The status file includes:

```json
{
  "running": true,
  "iteration": 3,
  "max_iterations": 25,
  "current_task": "lc-042",
  "current_task_title": "Fix timeout handling",
  "last_verdict": "APPROVED",
  "tasks_completed": 2,
  "tasks_remaining": 5,
  "started_at": "2026-02-01T10:00:00",
  "last_update": "2026-02-01T10:15:20",
  "current_phase": "cook",
  "phase_start_time": "2026-02-01T10:15:00",
  "current_action_count": 12,
  "last_action_time": "2026-02-01T10:17:45",
  "recent_iterations": [
    {
      "iteration": 2,
      "task_id": "lc-041",
      "task_title": "Fix timeout handling",
      "outcome": "completed",
      "serve_verdict": "APPROVED",
      "commit_hash": "a1b2c3d",
      "duration_seconds": 225,
      "intent": "Increase timeout for large repos",
      "before_state": "No timeout config",
      "after_state": "Configurable timeout",
      "completed_at": "2026-02-01T10:15:20",
      "action_count": 18,
      "action_types": {"Read": 8, "Edit": 6, "Bash": 3, "Write": 1}
    }
  ]
}
```

### Intra-Iteration Progress Fields

The following fields provide real-time visibility during long-running phases:

| Field | Description |
|-------|-------------|
| `current_phase` | Currently executing phase (cook, serve, tidy, plate) |
| `phase_start_time` | When the current phase started |
| `current_action_count` | Number of tool actions in current phase |
| `last_action_time` | Timestamp of most recent tool action |
| `epic_mode` | Epic filter mode if active (`auto` or epic ID) |
| `current_epic` | Currently focused epic ID (in epic mode) |

These enable:
- **Progress visibility**: Action count increasing = work happening
- **Stall detection**: `last_action_time` unchanged for 5+ minutes = potentially hung
- **Phase awareness**: Know which phase is executing and how long

**Note:** Status writes are throttled to max 1 per 5 seconds to avoid I/O overhead. Phase transitions always trigger an immediate write.

### Failure Tracking Fields

When tasks fail repeatedly, additional fields are included:

| Field | Description |
|-------|-------------|
| `skipped_tasks` | List of tasks skipped due to repeated failures |
| `escalation` | Escalation report with failure details and suggested actions |

**skipped_tasks format:**
```json
{
  "skipped_tasks": [
    {"id": "lc-123", "failure_count": 3},
    {"id": "lc-456", "failure_count": 3}
  ]
}
```

**escalation format (on circuit breaker or all_tasks_skipped):**
```json
{
  "escalation": {
    "stop_reason": "all_tasks_skipped",
    "recent_failures": [
      {"iteration": 5, "task_id": "lc-123", "outcome": "needs_retry", ...}
    ],
    "skipped_tasks": [{"id": "lc-123", "failure_count": 3}],
    "suggested_actions": [
      "Review the skipped tasks to understand failure patterns",
      "Check if tasks have missing dependencies or unclear requirements"
    ],
    "generated_at": "2026-02-01T10:30:00"
  }
}
```

### Format Watch Output

```
LOOP WATCH: <project> (PID: <pid>)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: ██████░░░░░░░░░░░░░░ 3/25
Completed: 2 | Remaining: 5 | Runtime: 15m 30s

CURRENT: Iteration 3
  Task: lc-042 - Fix timeout handling
  Phase: COOK (2m 45s) | Actions: 12 | Last: 5s ago

RECENT MILESTONES
───────────────────────────────────────
[10:15] ✓ lc-041 APPROVED (3m 45s) → a1b2c3d
        Intent: Increase timeout for large repos
        No timeout config → Configurable timeout
        Actions: 18 (Bash: 3, Edit: 6, Read: 8, Write: 1)
[10:11] ✓ lc-040 APPROVED (4m 12s) → e4f5g6h
        Intent: Support environment-based configuration
        Hardcoded values → Environment variables
        Actions: 12 (Bash: 2, Edit: 4, Glob: 1, Read: 5)

RECENT LOG
───────────────────────────────────────
<last 20 lines of loop.log>

Refresh: @line-loop watch | Stop: @line-loop stop
```

The `Phase:` line shows:
- Current phase name (COOK, SERVE, TIDY, PLATE)
- Time elapsed in current phase
- Number of tool actions in current phase
- Time since last action (for stall detection)

### Progress Bar Calculation

```python
filled = int((iteration / max_iterations) * 20)
bar = "█" * filled + "░" * (20 - filled)
```

### Milestones from recent_iterations

For each entry in `recent_iterations` (from status.json):
- Show timestamp (completed_at formatted as HH:MM)
- Show verdict symbol: ✓ for APPROVED, ✗ for NEEDS_CHANGES, ⚠ for BLOCKED
- Show task_id and verdict
- Show duration and commit hash
- Show intent (why the change was made)
- Show before_state → after_state (the transformation)
- Show action summary (total count and breakdown by type from action_types)

**Action summary format:**
```
Actions: 18 (Bash: 3, Edit: 6, Read: 8, Write: 1)
```
Only include tool types with count > 0, sorted alphabetically by tool name.

### Runtime Calculation

Calculate runtime from `started_at` in status.json:
```bash
START_TIME=$(jq -r '.started_at' "$LOOP_DIR/status.json")
RUNTIME=$(( $(date +%s) - $(date -d "$START_TIME" +%s) ))
```

Format as human-readable (e.g., "15m 30s").

### Log Tail

Include last 20 lines of `$LOOP_DIR/loop.log` at the bottom.

### If Not Running

If the loop is not running, show the final status instead:
```
LOOP WATCH: <project> (STOPPED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Final: ████████████████████ 8/25
Completed: 6 | Failed: 2 | Stop reason: no_tasks

FINAL MILESTONES
───────────────────────────────────────
<last 5 completed iterations>

Start a new loop: @line-loop start
```

---

## Subcommand: stop

### Check if Running

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
if [ ! -f "$LOOP_DIR/loop.pid" ]; then
  echo "No loop is running (no PID file found)"
  exit 0
fi

PID=$(cat "$LOOP_DIR/loop.pid")
if ! kill -0 "$PID" 2>/dev/null; then
  echo "Loop is not running (stale PID file)"
  rm -f "$LOOP_DIR/loop.pid"
  exit 0
fi
```

### Send SIGTERM

```bash
echo "Stopping loop (PID: $PID)..."
kill -TERM "$PID"
```

### Wait for Graceful Shutdown

```bash
# Wait up to 30 seconds for graceful shutdown
for i in {1..30}; do
  if ! kill -0 "$PID" 2>/dev/null; then
    echo "Loop stopped gracefully"
    exit 0
  fi
  sleep 1
done

echo "Warning: Loop did not stop within 30s"
echo "You may need to kill it manually: kill -9 $PID"
```

### Output

```
Stopping loop (PID: 12345)...
Loop stopped gracefully.

Final status:
  Iterations: 5/25
  Completed: 4
  Stop reason: shutdown
```

---

## Subcommand: tail

### Parse Lines Argument

Default to 50 lines if not specified.

### Read Log File

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
if [ ! -f "$LOOP_DIR/loop.log" ]; then
  echo "No log file found. Is a loop running?"
  exit 1
fi

tail -n "${LINES:-50}" "$LOOP_DIR/loop.log"
```

### Output

Display the raw log output.

---

## Subcommand: history

View detailed history of loop iterations including all tool actions captured during execution.

### Parse Arguments

```
Input examples:
  "history"                    -> Show summary of all iterations
  "history --iteration 3"      -> Show details for iteration 3 only
  "history --actions"          -> Include full action list for each iteration
  "history --iteration 3 --actions"  -> Show iteration 3 with all actions
```

### Read History File

The history is stored in JSONL format (one JSON object per line). Each line is either:
1. An iteration record with full details and actions
2. A loop_summary record marking the end of a run

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
HISTORY_FILE="$LOOP_DIR/history.jsonl"
```

Read the history file.

### JSONL Record Format

**Iteration record:**
```json
{
  "iteration": 2,
  "task_id": "lc-041",
  "task_title": "Fix timeout handling",
  "outcome": "completed",
  "serve_verdict": "APPROVED",
  "commit_hash": "a1b2c3d",
  "duration_seconds": 225,
  "success": true,
  "intent": "Increase timeout for large repos",
  "before_state": "No timeout config",
  "after_state": "Configurable timeout",
  "beads_before": {"ready": 5, "in_progress": 0},
  "beads_after": {"ready": 4, "in_progress": 0},
  "action_count": 18,
  "action_types": {"Read": 8, "Edit": 6, "Bash": 3, "Write": 1},
  "actions": [
    {
      "tool_name": "Read",
      "tool_use_id": "toolu_abc123",
      "input_summary": "/path/to/file.py",
      "output_summary": "File contents...",
      "success": true,
      "timestamp": "2026-02-01T10:12:30"
    }
  ],
  "project": "line-cook",
  "recorded_at": "2026-02-01T10:15:20"
}
```

**Loop summary record:**
```json
{
  "type": "loop_summary",
  "project": "line-cook",
  "started_at": "2026-02-01T10:00:00",
  "ended_at": "2026-02-01T11:30:00",
  "iteration_count": 8,
  "total_actions": 142,
  "stop_reason": "no_tasks"
}
```

### Format Output

**Default (summary):**
```
LOOP HISTORY: <project>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ITERATIONS
───────────────────────────────────────
#1  lc-040: Add config validation
    ✓ APPROVED (4m 12s) → e4f5g6h
    Actions: 12 (Bash: 2, Edit: 4, Glob: 1, Read: 5)

#2  lc-041: Fix timeout handling
    ✓ APPROVED (3m 45s) → a1b2c3d
    Actions: 18 (Bash: 3, Edit: 6, Read: 8, Write: 1)

#3  lc-042: Update documentation
    ✗ NEEDS_CHANGES (2m 30s)
    Actions: 8 (Bash: 1, Edit: 3, Read: 4)

SUMMARY
───────────────────────────────────────
Total iterations: 3
Total actions: 38
Duration: 10m 27s
```

**With --actions flag:**
Include the full list of actions for each iteration:
```
#2  lc-041: Fix timeout handling
    ✓ APPROVED (3m 45s) → a1b2c3d
    Actions: 18 (Bash: 3, Edit: 6, Read: 8, Write: 1)

    ACTIONS:
    [10:12:30] Read /src/config.py ✓
    [10:12:32] Read /src/timeout.py ✓
    [10:12:45] Edit /src/config.py ✓
    [10:13:01] Bash: pytest tests/ ✓
    ...
```

**With --iteration N:**
Show only the specified iteration in detail (implies --actions).

### No History File

```
LOOP HISTORY: <project>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No history file found.

Start a loop to begin recording:
  @line-loop start
```

---

## Error Handling

- **Start when already running:** Warn and show current status
- **Status when not running:** Show helpful message about starting
- **Stop when not running:** Handle gracefully, clean up stale PID file
- **Tail when no log:** Inform user no log exists yet

---

## Circuit Breaker Behavior

The loop includes a circuit breaker to prevent runaway failures:

- **Threshold:** 5 consecutive failures within a 10-iteration window
- **Triggers on:** Any non-success outcome (timeout, blocked, needs_retry after max retries)
- **Reset on success:** After any successful iteration, the failure window resets
- **Exit code:** 3 when circuit breaker trips

When the circuit breaker trips, the loop stops with a message indicating too many consecutive failures. Check the logs (`@line-loop tail --lines 100`) to understand what's failing.

### Circuit Breaker Flow

```
        ┌────────────────────┐
        │ Iteration Complete │
        └────────┬───────────┘
                 ▼
           ┌───────────┐
           │ Success?  │
           └─────┬─────┘
           Yes   │   No
        ┌────────┼────────┐
        ▼                 ▼
  ┌───────────┐   ┌──────────────┐
  │  Reset    │   │Record failure│
  │  window   │   │in sliding    │
  │  (clear   │   │window        │
  │  all)     │   │(size 10)     │
  └─────┬─────┘   └──────┬───────┘
        │                 ▼
        │         ┌──────────────┐
        │         │Last 5 entries│
        │         │all failures? │
        │         └──────┬───────┘
        │          No    │   Yes
        │       ┌────────┼────────┐
        ▼       ▼                 ▼
     Continue  Continue    ┌────────────┐
     loop      loop        │ STOP loop  │
                           │ + escalate │
                           └────────────┘
```

---

## Skip List Behavior

The loop tracks tasks that fail repeatedly and adds them to a skip list:

- **Threshold:** 3 failures for the same task
- **Triggers on:** Any failed outcome (needs_retry after max retries, blocked, crashed, timeout)
- **Effect:** Skipped tasks won't be selected for execution until the loop restarts
- **Reset:** A fresh loop run clears the skip list; successful completion clears a task's failure count

### Skip List Flow

```
       ┌──────────────────┐
       │ Get ready tasks  │
       │ (bd ready)       │
       └────────┬─────────┘
                ▼
       ┌──────────────────┐
       │ Filter out:      │
       │  - epics         │
       │  - skipped IDs   │
       │  - retro/backlog │
       └────────┬─────────┘
                ▼
         ┌────────────┐
         │ Any left?  │
         └──────┬─────┘
          Yes   │   No
       ┌────────┼──────────────┐
       ▼                       ▼
 Select highest       ┌──────────────────┐
 priority task        │ all_tasks_skipped │
       │              │ ► STOP + escalate │
       ▼              └──────────────────┘
  Run iteration
```

### Stop Reason: all_tasks_skipped

When all remaining ready tasks are in the skip list:
- The loop stops with `stop_reason: "all_tasks_skipped"`
- Exit code: 3 (same as circuit breaker)
- An escalation report is generated with suggested actions

This prevents retry spirals where the same failing tasks burn through all iterations.

---

## Escalation Reports

When the loop stops due to repeated failures (circuit breaker or all_tasks_skipped), an escalation report is generated:

```
============================================================
ESCALATION REPORT
============================================================
Stop reason: all_tasks_skipped

SKIPPED TASKS (too many failures):
  - lc-123: 3 failures
  - lc-456: 3 failures

RECENT FAILURES:
  - #5: lc-123 (needs_retry)
  - #4: lc-456 (timeout)

SUGGESTED ACTIONS:
  • Review the skipped tasks to understand failure patterns
  • Check if tasks have missing dependencies or unclear requirements
  • Consider breaking down complex tasks into smaller pieces
  • Use 'bd show <task_id>' to see full task details
  • Restart loop after fixing blocking issues: '@line-loop start'

============================================================
```

The escalation report is:
- Printed to console on loop stop
- Written to `status.json` in the `escalation` field
- Includes actionable suggestions for human intervention

---

## Epic Completion Workflow

When the loop completes tasks that roll up into epics, it automatically detects and celebrates epic completion:

### Automatic Detection

After each successful iteration:
1. Check if the completed task's parent feature has all tasks closed
2. If feature complete, run `@line-plate` for acceptance validation
3. Check if the completed feature's parent epic has all features closed
4. If epic complete, display an epic closure report

### Epic Closure Report

```
╔══════════════════════════════════════════════════════════════╗
║  EPIC COMPLETE: beads-001 - Implement User Authentication    ║
╚══════════════════════════════════════════════════════════════╝

Intent: Add secure user authentication to the application

Features delivered (3):
  [x] beads-010: Login flow
  [x] beads-011: Session management
  [x] beads-012: Password reset

Summary: Completed 3 features under this epic.

══════════════════════════════════════════════════════════════
```

### Break on Epic

Use `--break-on-epic` flag to pause the loop when an epic completes:

```bash
@line-loop start --break-on-epic
```

This gives you a natural checkpoint to review progress before continuing.

---

## Retry Mechanism

### Cook Phase Retries

When the serve phase returns `NEEDS_CHANGES`:
1. The cook phase is retried (up to `--max-retries`, default 2)
2. Each retry reads any rework comments from the previous serve
3. Exponential backoff applies between retries (2s, 4s, 8s... capped at 60s)

### Serve Parse Failure

If the serve output cannot be parsed to extract a verdict:
1. The full cook→serve cycle is retried (using the same attempt counter)
2. This ensures we don't incorrectly assume success or failure
3. If max retries exhausted without a verdict, the iteration fails conservatively

### Transient Errors

Some errors are treated as transient and don't count toward retries:
- Serve phase errors (network issues, subprocess crashes) → `SKIPPED` verdict, iteration continues
- These allow the loop to self-heal from temporary infrastructure issues

### Retry Flow

```
┌─────────────────────────────────────────────────┐
│ WITHIN ITERATION (iteration.py)                 │
│                                                 │
│          ┌──────────────┐                       │
│     ┌───►│  Cook Phase  │                       │
│     │    └──────┬───────┘                       │
│     │           ▼                               │
│     │    ┌──────────────┐                       │
│     │    │ Serve Phase  │                       │
│     │    └──────┬───────┘                       │
│     │           ▼                               │
│     │     ┌──────────┐                          │
│     │     │ Verdict? │                          │
│     │     └────┬─────┘                          │
│     │          ├── APPROVED ──► Done (success)  │
│     │          ├── BLOCKED ───► Done (blocked)  │
│     │          ├── SKIPPED ───► Done (success)  │
│     │          │                                │
│     │     NEEDS_CHANGES                         │
│     │          ▼                                │
│     │    ┌──────────────┐                       │
│     │    │ Attempts     │                       │
│     │    │ ≤ max? (2)   │── No ──► needs_retry  │
│     │    └──────┬───────┘             │         │
│     │       Yes │                     │         │
│     │           ▼                     │         │
│     │     Write retry                 │         │
│     │     context                     │         │
│     │           │                     │         │
│     └───────────┘                     │         │
│                                       │         │
└───────────────────────────────────────┼─────────┘
                                        ▼
┌─────────────────────────────────────────────────┐
│ ACROSS ITERATIONS (loop.py)                     │
│                                                 │
│     ┌────────────────┐                          │
│     │ Same task as   │                          │
│     │ last attempt?  │── No ──► counter = 1     │
│     └───────┬────────┘              │           │
│         Yes │                       │           │
│             ▼                       │           │
│       counter += 1                  │           │
│             │                       │           │
│             ▼                       ▼           │
│     ┌────────────────┐                          │
│     │ counter ≥      │                          │
│     │ max_retries?   │── No ──► Backoff         │
│     │ (default 2)    │         (4s,8s,16s...    │
│     └───────┬────────┘          cap 60s)        │
│         Yes │                   then retry      │
│             ▼                                   │
│     Record task failure                         │
│     in skip list                                │
│             │                                   │
│             ▼                                   │
│     Move to next task                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Idle Detection

The loop monitors tool action activity during phases to detect hung or stalled executions:

- **Default threshold:** 180 seconds (3 minutes) without tool actions
- **Measurement:** Time since last tool_use event in the stream
- **Actions:**
  - `warn` (default): Logs a warning but allows the phase to continue
  - `terminate`: Stops the phase gracefully with an idle timeout error

### Configuration

```bash
# Disable idle detection
@line-loop start --idle-timeout 0

# More aggressive idle detection (60s) with termination
@line-loop start --idle-timeout 60 --idle-action terminate

# Relaxed idle detection for complex tasks
@line-loop start --idle-timeout 300
```

### When Idle Detection Triggers

Idle detection is useful for catching:
- Phases that are waiting for user input (which won't come in headless mode)
- Infinite loops or stuck processes within the AI agent
- Network issues preventing tool execution

**Note:** Idle detection only triggers after at least one tool action has occurred. A phase that hasn't started any tool calls yet won't be considered idle.

### Idle Detection Flow

```
       ┌───────────────────┐
       │ Phase running     │
       │ (cook/serve/tidy) │
       └─────────┬─────────┘
                 ▼
       ┌───────────────────┐
       │ Any tool actions  │
       │ yet?              │
       └─────────┬─────────┘
          Yes    │    No
       ┌─────────┼──────────┐
       ▼                    ▼
 ┌───────────────┐   Not idle (skip
 │Time since last│   detection until
 │action >= idle │   first action)
 │timeout (180s)?│
 └───────┬───────┘
   No    │   Yes
 ┌───────┼────────────┐
 ▼                    ▼
Continue       ┌────────────┐
               │idle_action?│
               └──────┬─────┘
              warn    │  terminate
            ┌─────────┼─────────┐
            ▼                   ▼
      Log warning          Stop phase
      + continue           (error)
```

---

## Phase Completion Signal

Phases can emit `<phase_complete>DONE</phase_complete>` to signal early completion:

- Detected during streaming
- Triggers graceful termination of the phase
- Avoids waiting for natural exit or timeout
- Useful when the phase is confident it has completed all work

This signal should be emitted at the end of successful completion output in cook, serve, and tidy phases.

---

## Troubleshooting

### Quick Scan

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Loop already running" but nothing happening | Stale PID file | `rm -f /tmp/line-loop-$(basename "$PWD")/loop.pid` |
| "Another loop instance is starting" | Race condition | Wait a few seconds, or `rm -f $LOOP_DIR/loop.lock` |
| `stop_reason: circuit_breaker` | 5+ consecutive failures | Review logs, fix failing tasks, restart |
| `stop_reason: all_tasks_skipped` | All tasks failed 3+ times | `bd show <task-id>` for each, fix issues, restart |
| `stop_reason: no_tasks` | Work complete | Not an error - all tasks done |
| Cook phase times out | Task too complex | `--cook-timeout 2400` (40 min) |
| Serve phase times out | Large diff | `--serve-timeout 900` (15 min) |
| "Idle timeout after Ns" | Phase waiting/stuck | `--idle-timeout 0` to disable |
| Status shows "running" but process dead | Unclean shutdown | `rm -f $LOOP_DIR/loop.pid && @line-loop start` |
| Same task keeps retrying | Unclear requirements | Review task, clarify, restart |
| Loop exits immediately | No ready work | `bd create` tasks first |

---

### Loop Won't Start

**Symptom:** `@line-loop start` reports "Loop already running" but nothing is happening.

**Cause:** Stale PID file from a previous run that crashed or was killed.

**Fix:**
```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
rm -f "$LOOP_DIR/loop.pid"
@line-loop start
```

---

**Symptom:** "Another loop instance is starting. Please wait and try again."

**Cause:** Race condition - multiple start attempts simultaneously.

**Fix:** Wait a few seconds and try again. If it persists:
```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
rm -f "$LOOP_DIR/loop.lock"
```

---

### Loop Stops Unexpectedly

Use this decision tree to diagnose why the loop stopped:

```
Loop stops unexpectedly
├── Check stop_reason in status.json
│   │   jq '.stop_reason' /tmp/line-loop-$(basename "$PWD")/status.json
│   │
│   ├── "circuit_breaker" → 5+ consecutive failures
│   │   └── See "Circuit Breaker" section below
│   │
│   ├── "all_tasks_skipped" → All tasks failed 3+ times
│   │   └── See "All Tasks Skipped" section below
│   │
│   ├── "no_tasks" → Work complete (not an error)
│   │   └── All ready tasks completed successfully
│   │
│   ├── "max_iterations" → Reached iteration limit
│   │   └── Restart with `@line-loop start` to continue
│   │
│   └── "shutdown" → Graceful stop requested
│       └── User or signal requested stop
│
└── No status file or stop_reason
    └── Process crashed - check logs:
        @line-loop tail --lines 100
```

---

**Symptom:** Loop stops with `stop_reason: circuit_breaker`.

**Cause:** 5+ consecutive failures within 10 iterations tripped the circuit breaker.

**Diagnose:**
```bash
@line-loop tail --lines 100
@line-loop history --actions
```

**Common causes:**
- Tasks with unclear requirements (agent gets stuck in loops)
- Missing dependencies or environment issues
- Flaky tests causing serve rejections

**Fix:** Review the escalation report in status.json, fix the underlying issues, then restart.

---

**Symptom:** Loop stops with `stop_reason: all_tasks_skipped`.

**Cause:** Every ready task has failed 3+ times and been added to the skip list.

**Diagnose:**
```bash
cat /tmp/line-loop-$(basename "$PWD")/status.json | jq '.skipped_tasks'
```

**Fix:**
1. Review skipped tasks: `bd show <task-id>` for each
2. Fix issues (clarify requirements, fix dependencies)
3. Restart loop (clears skip list): `@line-loop start`

---

### Phases Timing Out

**Symptom:** Cook phase times out on complex tasks.

**Cause:** Default 20-minute cook timeout too short for large changes.

**Fix:** Increase timeout:
```bash
@line-loop start --cook-timeout 2400  # 40 minutes
```

---

**Symptom:** Serve phase times out.

**Cause:** Large diffs take longer to review.

**Fix:**
```bash
@line-loop start --serve-timeout 900  # 15 minutes
```

---

### Idle Detection Issues

**Symptom:** Loop terminates with "Idle timeout after Ns without tool actions".

**Cause:** Phase went too long without tool calls (possibly waiting for something).

**Fix options:**
```bash
# Disable idle detection
@line-loop start --idle-timeout 0

# Use warning instead of termination
@line-loop start --idle-action warn

# Increase threshold
@line-loop start --idle-timeout 300
```

---

**Symptom:** Phase appears stuck but idle detection doesn't trigger.

**Cause:** Idle detection only triggers AFTER at least one tool action. If a phase never makes a tool call, it won't trigger.

**Diagnose:**
```bash
@line-loop watch  # Check "Actions:" count and "Last: Ns ago"
```

**Fix:** If phase is truly stuck, use `@line-loop stop` to terminate gracefully.

---

### Status File Issues

**Symptom:** `@line-loop watch` shows stale data.

**Cause:** Status file updates are throttled to 1 write per 5 seconds during phases.

**Fix:** This is expected behavior. For real-time logs:
```bash
@line-loop tail --lines 50
```

---

**Symptom:** Status shows "running: true" but process is dead.

**Cause:** Loop crashed or was killed without cleaning up.

**Diagnose:**
```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
cat "$LOOP_DIR/loop.pid"  # Get PID
ps -p <PID>               # Check if alive
```

**Fix:**
```bash
rm -f "$LOOP_DIR/loop.pid"
@line-loop start
```

---

### Retry Spiral

**Symptom:** Same task keeps retrying with NEEDS_CHANGES.

**Cause:** Task has issues that can't be fixed automatically (unclear requirements, architectural problems).

**Diagnose:**
```bash
@line-loop history --iteration N --actions  # See what happened
```

**How the loop handles this:**
- Max 2 retries per iteration (configurable via `--max-retries`)
- After 3 total failures, task is added to skip list
- After all tasks skipped, loop stops with escalation report

**Fix:** Manually review the task, clarify requirements, then restart.

---

### Log Files

**Where to look:**

| Issue | File |
|-------|------|
| Full execution log | `$LOOP_DIR/loop.log` |
| Current status | `$LOOP_DIR/status.json` |
| All iterations | `$LOOP_DIR/history.jsonl` |
| Final report | `$LOOP_DIR/report.json` |

Where `LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"`.

**Quick debug:**
```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
tail -100 "$LOOP_DIR/loop.log"           # Recent logs
jq '.' "$LOOP_DIR/status.json"           # Current state
jq -s '.[-3:]' "$LOOP_DIR/history.jsonl" # Last 3 iterations
```

---

### Common Antipatterns

| Antipattern | Problem | Solution |
|-------------|---------|----------|
| Running without `bd ready` work | Loop exits immediately | Create tasks first with `bd create` |
| Tasks with vague descriptions | Agent gets stuck, timeouts | Write clear acceptance criteria |
| Dependencies not declared | Tasks attempted out of order | Use `bd dep add` |
| Complex tasks as single beads | Timeouts, partial completion | Break into smaller tasks |
| Skipping `@line-run` practice | Don't understand failure modes | Run manual cycles first |

---

### Recovery Checklist

When things go wrong:

1. **Stop the loop** (if running):
   ```bash
   @line-loop stop
   ```

2. **Check what happened**:
   ```bash
   @line-loop tail --lines 100
   @line-loop history --actions
   ```

3. **Check task status**:
   ```bash
   bd ready
   bd list --status=in_progress
   ```

4. **Clean up if needed**:
   ```bash
   # Reset stuck in_progress tasks
   bd update <id> --status=open

   # Clear stale loop files
   rm -rf /tmp/line-loop-$(basename "$PWD")
   ```

5. **Fix underlying issues** (unclear tasks, missing deps)

6. **Restart**:
   ```bash
   @line-loop start
   ```

---

