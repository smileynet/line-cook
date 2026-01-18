---
description: Select and execute a task with completion guardrails
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, AskUserQuestion
---

## Task

Execute work on a task with guardrails ensuring completion. Part of the `/line:prep` → `/line:cook` → `/line:serve` → `/line:tidy` workflow loop.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on

## Process

### Step 1: Select Task

**If `$ARGUMENTS` provided:**
- Use that task ID directly

**Otherwise:**
- Run `bd ready` to get available tasks
- Select the highest priority task (lowest P number)

Once selected, claim the work:
```bash
bd show <id>                           # Display full task details
bd update <id> --status=in_progress    # Claim the work
bd comments add <id> "PHASE: COOK
Status: started"
```

### Step 2: Plan the Work

Break the task into steps using TodoWrite:

1. Read the task description carefully
2. Identify all deliverables
3. Add steps to TodoWrite before starting work
4. Include verification steps (test, compile, etc.)

For complex tasks, use explore-plan-code workflow or ask clarifying questions.

### Step 3: Execute Work

Work through TodoWrite items systematically:

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

**Collecting findings:** As you work, note (but do NOT file yet):
- New work discovered
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
  New work:
    - "Add support for edge case X"
  Potential issues:
    - "Error handling in Y could be improved"
  Improvements:
    - "Consider refactoring Z for clarity"

Run /line:serve for review, or /line:tidy to commit.
```

## Guardrails (Critical)

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Note, don't file** - Discovered work is noted for `/line:tidy`, not filed during cook

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
/line:cook lc-042       # Work on specific task
```
