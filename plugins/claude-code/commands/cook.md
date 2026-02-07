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

**If no actionable tasks available** (e.g., only P4 parking lot items or research tasks):

Output the idle signal and stop:
```
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN IDLE                                                ║
╚══════════════════════════════════════════════════════════════╝

No actionable tasks available.

Available: <count> items (all P4 parking lot or research)

Signal: KITCHEN_IDLE

<phase_complete>DONE</phase_complete>
```

**Once a regular task is selected**, claim it:
```bash
bd show <id>                           # Display full task details
bd update <id> --status=in_progress    # Claim the task
bd comments add <id> "PHASE: COOK
Status: started"
```

### Step 1.5: Check for Review Findings (Rework Mode)

Check if this task has previous review findings:

```bash
bd comments list <id> | grep -A 20 "PHASE: SERVE"
```

**If review findings exist (NEEDS_CHANGES):**
1. Load the findings from the serve comment
2. Add findings to TodoWrite as items to address
3. Prioritize fixing these before new work

**Output in rework mode:**
```
REWORK MODE: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Previous review found issues to address:
  - [major] <issue 1>
  - [minor] <issue 2>

Addressing review findings first.
```

**If no review findings:** Continue normally with Step 2.

### Step 1.6: Check for Retry Context (Loop Mode)

When running in line-loop, check for structured retry context:

```bash
cat .line-cook/retry-context.json 2>/dev/null
```

**If retry-context.json exists:**
This file contains structured feedback from the previous serve review, including:
- `verdict`: The serve verdict (NEEDS_CHANGES)
- `summary`: Brief assessment of the changes
- `issues`: Array of issues with severity, location, problem, and suggestion
- `attempt`: Which retry attempt this is

**Prioritize issues from the context file over bead comments**, as they're more structured and reliable.

**Output in retry mode:**
```
╔══════════════════════════════════════════════════════════════╗
║  RETRY MODE - Attempt <N>                                    ║
╚══════════════════════════════════════════════════════════════╝

Task: <id> - <title>
Previous verdict: NEEDS_CHANGES

Issues to address:
  [critical] <location>: <problem>
    → <suggestion>
  [major] <location>: <problem>
    → <suggestion>
  [minor] <location>: <problem>

Summary: <assessment from serve>

Addressing issues in priority order (critical → major → minor).
```

**Add issues to TodoWrite** in severity order:
1. Critical issues first (blocking)
2. Major issues second
3. Minor issues last

**If no retry context exists:** Continue normally with Step 2.

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
5. **Planning context** - Check for design rationale:
   - Get task's parent chain: `bd show <id> --json` -> parent -> epic
   - Read epic description, look for `Planning context:` line
   - If found, read `README.md` (always) and `architecture.md` (for patterns/constraints)
   - Graceful no-op if no context folder exists

Use Read, Glob, and Grep tools to gather necessary context before starting implementation.

### Step 4: Plan the Task

Break the task into steps using TodoWrite:

1. Read the task description carefully
2. Identify all deliverables
3. Add steps to TodoWrite before starting
4. Include verification steps (test, compile, etc.)

For complex tasks, use explore-plan-code workflow or ask clarifying questions.

### Step 5: Execute TDD Cycle

Process TodoWrite items systematically with TDD guardrails:

- Mark items `in_progress` when starting
- Mark items `completed` immediately when done
- Only one item should be `in_progress` at a time

**For code changes, follow TDD cycle:**

1. **RED**: Write failing test
    ```bash
    <test command>  # e.g., pytest, go test, npm test
    # Should FAIL
    ```

    **Automatic test quality review (CRITICAL):**
    ```
    Use Task tool to invoke taster subagent:
    Task(description="Review test code for quality", prompt="Review test code for <package> for quality, checking:
    - Tests are isolated, fast, repeatable
    - Clear test names and error messages
    - Proper structure (Setup-Execute-Validate-Cleanup)
    - No anti-patterns

    Report any critical issues that must be addressed before proceeding.", subagent_type="taster")
    ```

    **Address critical issues before GREEN phase.** The taster agent will:
    - Verify tests are isolated, fast, repeatable
    - Check for clear test names and error messages
    - Ensure proper structure (Setup-Execute-Validate-Cleanup)
    - Identify anti-patterns
    - Provide critical issue blocking if needed

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

These will be filed as beads in `/line:tidy` (see tidy.md Finding Filing Strategy).

### Step 6: Verify Kitchen Equipment

Before marking the task done, verify ALL guardrails pass:

- [ ] All TodoWrite items completed
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
Parent: <parent-id> - <parent-title> (or "none")
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

NEXT STEP: /line:serve

<phase_complete>DONE</phase_complete>
```

**Phase completion signal:** The `<phase_complete>DONE</phase_complete>` tag signals to the line-loop orchestrator that this phase has completed its work and can be terminated early. This avoids waiting for natural exit or timeout. Always emit this signal at the very end of successful completion output.

## Guardrails (Critical)

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Note, don't file** - Discovered issues are noted for `/line:tidy`, not filed during cook

## Error Handling

If execution is blocked:
```
⚠️ KITCHEN BLOCKED: <description>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
