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

## File Locations

Loop artifacts are stored in a **project-specific directory** to avoid conflicts when working on multiple projects:

```
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
```

| File | Purpose |
|------|---------|
| `$LOOP_DIR/loop.pid` | Process ID for management |
| `$LOOP_DIR/loop.log` | Full log output |
| `$LOOP_DIR/status.json` | Live status (updated per iteration, last 5 iterations with action counts) |
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

### Check if Already Running

First, check if a loop is already running:

```bash
LOOP_DIR="/tmp/line-loop-$(basename "$PWD")"
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
Current Task: lc-042
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
  "last_verdict": "APPROVED",
  "tasks_completed": 2,
  "tasks_remaining": 5,
  "started_at": "2026-02-01T10:00:00",
  "last_update": "2026-02-01T10:15:20",
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

### Format Watch Output

```
LOOP WATCH: <project> (PID: <pid>)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: ██████░░░░░░░░░░░░░░ 3/25
Completed: 2 | Remaining: 5 | Runtime: 15m 30s

CURRENT: Iteration 3
  Task: lc-042 - Fix timeout handling
  Status: COOKING... (2m 10s)

RECENT MILESTONES
───────────────────────────────────────
[10:15] ✓ lc-041 APPROVED (3m 45s) → a1b2c3d
        Actions: 18 (8 Read, 6 Edit, 3 Bash, 1 Write)
        No timeout config → Configurable timeout
[10:11] ✓ lc-040 APPROVED (4m 12s) → e4f5g6h
        Actions: 12 (5 Read, 4 Edit, 2 Bash, 1 Glob)
        Hardcoded values → Environment variables

RECENT LOG
───────────────────────────────────────
<last 20 lines of loop.log>

Refresh: /line:loop watch | Stop: /line:loop stop
```

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
- Show action summary (total count and breakdown by type from action_types)
- Show before_state → after_state if available

**Action summary format:**
```
Actions: 18 (8 Read, 6 Edit, 3 Bash, 1 Write)
```
Only include tool types with count > 0, ordered by count descending.

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
    Actions: 12 (5 Read, 4 Edit, 2 Bash, 1 Glob)

#2  lc-041: Fix timeout handling
    ✓ APPROVED (3m 45s) → a1b2c3d
    Actions: 18 (8 Read, 6 Edit, 3 Bash, 1 Write)

#3  lc-042: Update documentation
    ✗ NEEDS_CHANGES (2m 30s)
    Actions: 8 (4 Read, 3 Edit, 1 Bash)

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
    Actions: 18 (8 Read, 6 Edit, 3 Bash, 1 Write)

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

## Error Handling

- **Start when already running:** Warn and show current status
- **Status when not running:** Show helpful message about starting
- **Stop when not running:** Handle gracefully, clean up stale PID file
- **Tail when no log:** Inform user no log exists yet

---

## Design Notes

This skill provides TUI-friendly management of the autonomous loop:

1. **Non-blocking start** - Uses `run_in_background` for async execution
2. **Live status** - Reads status file updated after each iteration
3. **Graceful stop** - Sends SIGTERM for clean shutdown
4. **Log access** - Tail command for debugging
5. **Project isolation** - Each project gets its own loop directory in `/tmp/line-loop-<project>/`

The loop itself handles all the complex logic (circuit breakers, retries, bead tracking). This skill just provides the management interface.
