---
description: Select and execute a task with completion guardrails
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, AskUserQuestion
---

## Summary

**Execute a task with guardrails ensuring completion.** Part of prep → cook → serve → tidy.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to execute

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Select Task

**If `$ARGUMENTS` provided:**
- Use that task ID directly (explicit selection bypasses filtering)

**Otherwise (auto-selection with filtering):**

Exclude children of parking-lot epics ("Retrospective", "Backlog") from auto-selection:

```bash
# Find parking-lot epic IDs
EXCLUDE_EPICS=$(bd list --type=epic --json | jq '[.[] | select(.title == "Retrospective" or .title == "Backlog") | .id]')

# Get next task from filtered ready list
NEXT_TASK=$(bd ready --json | jq -r --argjson exclude "$EXCLUDE_EPICS" \
  'map(select(.parent == null or (.parent | IN($exclude[]) | not))) | .[0].id')
```

**Important:** This exclusion ONLY applies to auto-selection. If `$ARGUMENTS` is provided, execute that task regardless of parent epic. This allows explicit work on parked items.

**If no tasks after filtering:**
```
No actionable tasks ready.
All ready tasks are in Retrospective or Backlog epics.

To work on parked items: /line:cook <specific-task-id>
To see parked work: bd list --parent=<epic-id>
```

**Check if selected item is an epic:**
```bash
bd show <id> --json
```

If `issue_type` is `epic`, the epic itself has no work to execute. Instead:

1. Show the epic and its children:
   ```bash
   bd list --parent=<epic-id> --all
   ```

2. Find the first ready (unblocked, open) child and select that instead

3. Output epic context:
   ```
   EPIC SELECTED: <epic-id> - <epic-title>
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Epics contain no direct work. Selecting first ready child:

   Children (<open>/<total>):
     ○ <id>: <title> [P<n>] ← selected
     ○ <id>: <title> [P<n>] (blocked by above)
     ✓ <id>: <title> (closed)

   Proceeding with: <selected-task-id>
   ```

4. Continue with the selected child task

**Once a regular task is selected**, claim it:
```bash
bd show <id>                           # Display full task details
bd update <id> --status=in_progress    # Claim the task
bd comments add <id> "PHASE: COOK
Status: started"
```

### Step 2: Plan the Task

Break the task into steps using TodoWrite:

1. Read the task description carefully
2. Identify all deliverables
3. Add steps to TodoWrite before starting
4. Include verification steps (test, compile, etc.)

For complex tasks, use explore-plan-code workflow or ask clarifying questions.

### Step 3: Execute Task

Process TodoWrite items systematically:

- Mark items `in_progress` when starting
- Mark items `completed` immediately when done
- Only one item should be `in_progress` at a time

**Output format during execution:**
```
COOKING: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/N] <todo item> ... ✓
[2/N] <todo item> ... ✓
[3/N] <todo item> ... in progress

Progress: 2/N complete
```

**Collecting findings:** As you execute, note (but do NOT file yet):
- New tasks discovered
- Potential issues or bugs
- Areas for improvement

These will be filed as beads in `/line:tidy`.

### Step 4: Verify Completion

Before marking the task done, verify ALL guardrails pass:

- [ ] All TodoWrite items completed
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**If any guardrail fails:**
- Do NOT close the task
- Report what's incomplete
- Keep task as `in_progress`
- Ask user how to proceed

### Step 5: Complete Task

Only after all guardrails pass:

```bash
bd close <id>
bd comments add <id> "PHASE: COOK
Status: completed
Summary: <what was done>
Files: <count> changed
Findings: <issues/improvements noted for tidy>"
```

**Completion output format:**
```
DONE: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  <1-2 sentence description of what was accomplished>

Files changed:
  M src/foo.ts
  A src/bar.ts

Verification:
  [✓] All todos complete
  [✓] Code compiles
  [✓] Tests pass

Findings (to file in /tidy):
  New tasks:
    - "Add support for edge case X"
  Potential issues:
    - "Error handling in Y could be improved"
  Improvements:
    - "Consider refactoring Z for clarity"

NEXT STEP: /line:serve (review) or /line:tidy (commit)
```

## Guardrails (Critical)

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Note, don't file** - Discovered issues are noted for `/line:tidy`, not filed during cook

## Error Handling

If execution is blocked:
```
⚠️ BLOCKED: <description>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <why it failed>
Progress: <what was completed>

Options:
  1. <recovery option>
  2. <alternative>

Task remains in_progress. Run /line:tidy to save partial progress.
```

## Example Usage

```
/line:cook              # Pick highest priority ready task
/line:cook lc-042       # Execute specific task
```
