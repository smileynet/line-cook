---
description: Execute multiple tasks in a loop until done or failure
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, AskUserQuestion, Skill
---

## Summary

**Loop orchestrates multiple /line:run cycles autonomously.** Continues executing ready tasks until none remain or a failure occurs.

**Loop responsibilities:**
- Parse iteration limits from arguments
- Check for ready tasks via `bd ready`
- Delegate each task to `/line:run`
- Track progress across iterations
- Stop on failure or empty ready queue
- Report final summary with all completed work

**Arguments:** `$ARGUMENTS` (optional) - `--max-iterations N` or `-n N` to limit iterations (default: 25)

---

## Process

### Step 1: Parse Arguments

Check `$ARGUMENTS` for iteration limit:

**If `--max-iterations N` or `-n N` provided:**
- Extract N as the maximum number of iterations

**Otherwise:**
- Default to 25 iterations (safety limit)

Initialize counters:
- `iteration = 0`
- `completed_tasks = []`
- `failed = false`

### Step 2: Check Ready Tasks

Query for available work:

```bash
bd ready
```

**If no tasks ready:**
- Proceed to Step 6 (Final Summary)

**If tasks available:**
- Continue to Step 3

### Step 3: Check Iteration Limit

**If `iteration >= max_iterations`:**
- Output warning: "Reached iteration limit (N). Stopping loop."
- Proceed to Step 6 (Final Summary)

**Otherwise:**
- Increment `iteration`
- Continue to Step 4

### Step 4: Execute /line:run

Invoke the run command for one complete cycle:

```
Skill(skill="line:run")
```

Wait for run to complete. Run will execute prep → cook → serve → tidy for one task.

**On success:**
- Record completed task in `completed_tasks`
- Continue to Step 5

**On failure:**
- Set `failed = true`
- Record which task failed and why
- Proceed to Step 6 (Final Summary)

### Step 5: Loop Continuation

Output progress indicator:

```
Loop iteration N complete. Task <id> finished.
Checking for more work...
```

Return to Step 2.

### Step 6: Final Summary

Output comprehensive summary:

```
╔══════════════════════════════════════════════════════════════╗
║  LOOP COMPLETE                                               ║
╚══════════════════════════════════════════════════════════════╝

STATUS: <Success | Failed | Iteration Limit Reached>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Iterations: N / max
Tasks completed: M

COMPLETED TASKS:
  [✓] <task-1-id> - <title>
  [✓] <task-2-id> - <title>
  [✓] <task-3-id> - <title>

<If failed:>
FAILED TASK:
  [✗] <task-id> - <title>
  Error: <description>

──────────────────────────────────────────

Remaining ready tasks: <count>
Run /line:loop to continue processing.
```

## Error Handling

Loop stops on first failure:

1. **Run fails** - Stop loop, report failed task and all previously completed tasks
2. **No ready tasks** - Normal completion, report all completed tasks
3. **Iteration limit** - Stop with warning, report completed tasks and remaining count

The loop is designed to fail fast. Any failure in a `/line:run` cycle stops the entire loop to allow investigation before continuing.

After a failure, the user can:
- Investigate and fix the issue
- Run `/line:run <task-id>` to retry the specific task
- Run `/line:loop` again to continue from where it stopped

## Design Notes

The `/line:loop` command enables autonomous multi-task execution:

1. **Safety limits** - Default 25 iterations prevents runaway execution
2. **Fail-fast** - Stops on first error for investigation
3. **Progress tracking** - Clear output of what was accomplished
4. **Resumable** - After fixing issues, simply run again to continue

Use `/line:loop` when you want to process multiple ready tasks without manual intervention. For single-task execution, use `/line:run` directly.

## Example Usage

```
/line:loop                    # Process up to 25 ready tasks
/line:loop --max-iterations 5 # Process up to 5 tasks
/line:loop -n 10              # Process up to 10 tasks
```
