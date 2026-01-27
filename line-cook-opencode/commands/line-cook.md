---
description: Select and execute a task with completion guardrails
---

## Summary

**Execute a task with guardrails ensuring completion.** Part of prep → cook → serve → tidy.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to execute

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Select Task

**If `$ARGUMENTS` provided:**
- Use that task ID directly

**Otherwise:**
- Run `bd ready` to get available tasks
- Select the highest priority task (lowest P number)

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

### Step 2: Load Recipe

Load the task details (the recipe):

```bash
bd show <id>
```

Review the task description, acceptance criteria, and any dependencies. This is the recipe for what will be cooked.

### Step 3: Load Ingredients

Load relevant context files and documentation (the ingredients):

1. **Project structure** - Understand codebase layout
2. **Kitchen manual** - Review AGENTS.md for conventions
3. **Related code** - Read files relevant to the task
4. **Dependencies** - Check what this task builds on

Use Read, Glob, and Grep tools to gather necessary context before starting implementation.

### Step 4: Plan the Task

Break the task into steps using a checklist:

1. Read the task description carefully
2. Identify all deliverables
3. List steps before starting
4. Include verification steps (test, compile, etc.)

For complex tasks, use explore-plan-code workflow or ask clarifying questions.

### Step 5: Execute TDD Cycle

Process checklist items systematically with TDD guardrails:

- Work through items one at a time
- Track progress as you go

**For code changes, follow TDD cycle:**

1. **RED**: Write failing test
    ```bash
    <test command>  # e.g., pytest, go test, npm test
    # Should FAIL
    ```

2. **GREEN**: Implement minimal code
   ```bash
   <implementation>
   <test command>
   # Should PASS
   ```

3. **REFACTOR**: Clean up code
   ```bash
   <refactoring>
   <test command>
   # All tests should PASS
   ```

**Output format during execution:**
```
COOKING: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/N] <todo item> ... ✓
[2/N] <todo item> ... ✓
[3/N] <todo item> ... in progress

Progress: 2/N complete

TDD Phase: RED/GREEN/REFACTOR
```

**Collecting findings:** As you execute, note (but do NOT file yet):
- New tasks discovered
- Potential issues or bugs
- Areas for improvement

These will be filed as beads in `/line-tidy`.

### Step 6: Verify Kitchen Equipment

Before marking the task done, verify ALL guardrails pass:

- [ ] All checklist items completed
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**Kitchen equipment checklist** (MANDATORY):

- [ ] All tests pass: `<test command>` (e.g., `go test ./...`, `pytest`, `npm test`)
- [ ] Code builds: `<build command>` (e.g., `go build ./...`, `npm run build`)
- [ ] Lint passes: `<lint command>` (if applicable, e.g., `npm run lint`)
- [ ] Task deliverable complete
- [ ] Code follows kitchen manual conventions

**If any guardrail fails:**
- Do NOT close the task
- Report what's incomplete
- Keep task as `in_progress`
- Ask user how to proceed

### Step 7: Complete Task

Only after all guardrails pass:

```bash
bd close <id>
bd comments add <id> "PHASE: COOK
Status: completed

SEMANTIC CONTEXT (for tidy summary):
Intent: <why this change was made, from task description>
Before: <previous state - what existed/didn't work>
After: <new state - what's now possible/fixed>

Files: <count> changed
Findings: <issues/improvements noted for tidy>"
```

**Completion output format:**
```
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN COMPLETE                                            ║
╚══════════════════════════════════════════════════════════════╝

Task: <id> - <title>
Tests: ✓ All passing
Build: ✓ Successful

Signal: KITCHEN_COMPLETE

INTENT:
  <1-2 sentences from task description>
  Goal: <deliverable or acceptance criteria>

BEFORE → AFTER:
  <previous state> → <new state>
  <what couldn't be done> → <what can be done now>

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

NEXT STEP: /line-serve (review) or /line-tidy (commit)
```

## Guardrails (Critical)

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Note, don't file** - Discovered issues are noted for `/line-tidy`, not filed during cook

## Error Handling

If execution is blocked:
```
⚠️ KITCHEN BLOCKED: <description>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <why it failed>
Progress: <what was completed>

Options:
  1. <recovery option>
  2. <alternative>

Task remains in_progress. Run /line-tidy to save partial progress.
```

## Example Usage

```
/line-cook              # Pick highest priority ready task
/line-cook lc-042       # Execute specific task
```
