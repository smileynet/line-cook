---
description: Manage autonomous loop execution from TUI
allowed-tools: Bash, Read, Glob
---

## Summary

**Control the autonomous line-loop process from Claude Code's TUI.** Provides start/status/stop/tail subcommands for managing background loop execution.

**Arguments:** `$ARGUMENTS` contains the subcommand and options:
- *(no args)* - Smart default: watch if running, start if not
- `start [--max-iterations N] [--timeout T]` - Start loop in background
- `watch` - Live progress with milestones and context
- `status` - One-shot status check
- `stop` - Gracefully stop running loop
- `tail [--lines N]` - Show recent log output
- `history [--iteration N] [--actions]` - View full iteration history with action details

---

## Quick Start

### Learning Path (Recommended)

Before using `/line:loop`, familiarize yourself with the individual phases:

**1. Start with individual phases:**
```
/line:prep       # Check ready tasks, sync state
/line:cook       # Execute one task interactively
/line:serve      # Review changes before commit
/line:tidy       # Commit and push changes
```
Run these manually a few times to understand the workflow.

**2. Then try the combined run:**
```
/line:run        # Runs prep → cook → serve → tidy for one task
```
This completes a single task cycle with your oversight.

**3. Finally, use loop for autonomous execution:**
```
/line:loop       # Runs multiple iterations unattended
```

### Using /line:loop

**Default (auto-detect):**
```
/line:loop
```
Starts a loop if none running, or shows watch mode if already running.

**Monitor a running loop:**
```
/line:loop watch
```
Shows live progress with milestones, action counts, and before/after context.

**Start with limited iterations (good for testing):**
```
/line:loop start --max-iterations 5
```

---

## Command Selection Guide

| Scenario | Command |
|----------|---------|
| First time / unsure | `/line:loop` (smart default) |
| Monitor with context | `/line:loop watch` |
| Quick status check | `/line:loop status` |
| Debug issues | `/line:loop tail --lines 100` |
| Review what happened | `/line:loop history --actions` |
| Stop gracefully | `/line:loop stop` |
| Custom iteration limit | `/line:loop start --max-iterations N` |

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
/line:loop - Manage autonomous loop execution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Usage:
  /line:loop                           # Smart default (watch if running, start if not)
  /line:loop watch                     # Live progress with milestones
  /line:loop start [--max-iterations N] [--timeout T]
  /line:loop status                    # One-shot status check
  /line:loop stop                      # Gracefully stop
  /line:loop tail [--lines N]          # View log output
  /line:loop history [--iteration N] [--actions]  # View iteration history

Commands:
  (none)   Smart default - watch if loop running, start if not
  watch    Live progress with milestones and before/after context
  start    Launch loop in background (default: 25 iterations, 600s timeout)
  status   One-shot status check
  stop     Gracefully stop running loop
  tail     Show recent log output (default: 50 lines)
  history  View iteration history with action details

Examples:
  /line:loop                          # Start or watch (smart default)
  /line:loop watch                    # Monitor progress with context
  /line:loop start --max-iterations 5 # Quick test run
  /line:loop status                   # One-shot status check
  /line:loop tail --lines 100         # View more log output
  /line:loop history --actions        # View all iterations with actions
  /line:loop stop                     # Stop gracefully

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

Extract the subcommand from `$ARGUMENTS`:

```
$ARGUMENTS examples:
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
    echo "Use '/line:loop status' to check progress or '/line:loop stop' to stop it."
    exit 1
  else
    # Stale or invalid PID file, clean up
    rm -f "$LOOP_DIR/loop.pid"
  fi
fi
```

### Find Script Path

Locate the line-loop.py script. Check these locations in order:

1. **Plugin installation** (most common):
   ```
   Glob(pattern="**/line-loop.py", path="~/.claude/plugins")
   ```

2. **Current project** (for development):
   ```
   Glob(pattern="**/line-loop.py")
   ```

The script is typically at `~/.claude/plugins/marketplaces/line-cook-marketplace/line/scripts/line-loop.py`.

### Launch Background Loop

Use the Bash tool with `run_in_background: true` to start the loop:

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
mkdir -p "$LOOP_DIR"
python <path-to-line-loop.py> \
  --max-iterations ${MAX_ITERATIONS:-25} \
  --timeout ${TIMEOUT:-600} \
  --json \
  --output "$LOOP_DIR/report.json" \
  --log-file "$LOOP_DIR/loop.log" \
  --pid-file "$LOOP_DIR/loop.pid" \
  --status-file "$LOOP_DIR/status.json" \
  --history-file "$LOOP_DIR/history.jsonl"
```

Replace `<path-to-line-loop.py>` with the absolute path found by Glob.

**Important:** Set `run_in_background: true` on the Bash tool call.

### Output

```
Loop started in background (task ID: <task_id>)
Project: <project-name>
Loop dir: /tmp/line-loop-<project-name>

Monitor with:
  /line:loop status    - Check progress
  /line:loop tail      - View log output
  /line:loop stop      - Stop gracefully
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

Use the Read tool to read `$LOOP_DIR/status.json` (compute the actual path first).

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
  /line:loop tail --lines 100
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
  /line:loop start
  /line:loop start --max-iterations 10
```

---

## Subcommand: watch

Watch mode provides unified progress monitoring with milestones and context from completed iterations.

### Check Running State

Same as status - verify the loop is running first.

### Read Status File

Use the Read tool to read `$LOOP_DIR/status.json`. The status file includes:

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

These enable:
- **Progress visibility**: Action count increasing = work happening
- **Stall detection**: `last_action_time` unchanged for 5+ minutes = potentially hung
- **Phase awareness**: Know which phase is executing and how long

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

Refresh: /line:loop watch | Stop: /line:loop stop
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

Start a new loop: /line:loop start
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
$ARGUMENTS examples:
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

Use the Read tool to read the history file.

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
  /line:loop start
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

When the circuit breaker trips, the loop stops with a message indicating too many consecutive failures. Check the logs (`/line:loop tail --lines 100`) to understand what's failing.

---

## Epic Completion Workflow

When the loop completes tasks that roll up into epics, it automatically detects and celebrates epic completion:

### Automatic Detection

After each successful iteration:
1. Check if the completed task's parent feature has all tasks closed
2. If feature complete, run `/line:plate` for acceptance validation
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
python line-loop.py --break-on-epic
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
- Serve phase errors (network issues, claude crashes) → `SKIPPED` verdict, iteration continues
- These allow the loop to self-heal from temporary infrastructure issues

---

## Design Notes

This skill provides TUI-friendly management of the autonomous loop:

1. **Non-blocking start** - Uses `run_in_background` for async execution
2. **Live status** - Reads status file updated after each iteration
3. **Graceful stop** - Sends SIGTERM for clean shutdown
4. **Log access** - Tail command for debugging
5. **Project isolation** - Each project gets its own loop directory in `/tmp/line-loop-<project>/`

The loop itself handles all the complex logic (circuit breakers, retries, bead tracking). This skill just provides the management interface.
