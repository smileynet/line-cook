---
description: Select and execute a task with completion guardrails
---


## Summary

**Execute a task with guardrails ensuring completion.** Part of prep → cook → serve → tidy.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to execute

**When run directly:** STOP after completing, show NEXT STEP, and wait for user.
**When run via `/line-run`:** Continue to the next step without stopping.

---

## Process

### Step 1: Select Task

**If the user provided a task ID:**
- Use that task ID directly

**Otherwise:**
- Call kitchen-equipment.py without a task ID to fetch ready task list
- Select the highest priority task (lowest P number)
- Call kitchen-equipment.py again with the selected task ID

**Gather task context (epic check, prior context, tools):**

#### Find Script

Locate `kitchen-equipment.py`:

```bash
# Without <id>: returns ready_list for task selection
# With <id>: returns full task context (epic check, prior context, tools)
CONTEXT=$(python3 <path-to-kitchen-equipment.py> <id> --json 2>/dev/null)
echo "$CONTEXT"
```

The JSON output includes: `task`, `is_epic`, `epic_children`, `prior_context`, `tools`, and `planning_context`.

If `is_epic` is true, the epic itself has no work to execute. Instead:

1. Use `epic_children` from the kitchen-equipment.py output (already fetched)

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
```

**Once a regular task is selected**, claim it:
```bash
# Claim the task and display details
bd show <id>
bd update <id> --status=in_progress
bd comments add <id> "PHASE: COOK
Status: started"
```

### Step 2: Load Ingredients

Load relevant context files and documentation (the ingredients):

1. **Project structure** - Understand codebase layout
2. **Kitchen manual** - Review AGENTS.md for conventions
3. **Related code** - Read files relevant to the task
4. **Dependencies** - Check what this task builds on
5. **Planning context** - Check for design rationale:
   - Use `planning_context` from the kitchen-equipment.py output (already fetched in Step 1)
   - If a context folder is referenced, read `README.md` (always) and `architecture.md` (for patterns/constraints)
   - Graceful no-op if no context folder exists

Use Read, Glob, and Grep tools to gather necessary context before starting implementation.

### Step 3: Plan the Task

Break the task into a checklist of steps:

1. Read the task description carefully
2. Identify all deliverables
3. List steps before starting implementation
4. Include verification steps (test, compile, etc.)

For complex tasks, use explore-plan-code workflow or ask clarifying questions.

### Step 4: Execute TDD Cycle

Process checklist items systematically with TDD guardrails:

- Mark items `in_progress` when starting
- Mark items `completed` immediately when done
- Only one item should be `in_progress` at a time

**For code changes, follow TDD cycle:**

1. **RED**: Write failing test
    ```bash
    <test command>  # e.g., pytest, go test, npm test
    # Should FAIL
    ```

   **Automatic test quality review:**

   Before proceeding to GREEN, review your test code for quality:
   - Tests are isolated, fast, repeatable
   - Clear test names and error messages
   - Proper structure (Setup-Execute-Validate-Cleanup)
   - No anti-patterns (shared mutable state, flaky assertions, implementation coupling)

   **Address critical issues before GREEN phase.**

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

These will be filed as beads in tidy phase (see tidy.md Finding Filing Strategy).

### Step 5: Verify Kitchen Equipment

Before marking the task done, verify ALL guardrails pass:

- [ ] All checklist items completed
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**Kitchen equipment checklist:**

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

### Step 6: Complete Task

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
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN COMPLETE                                            ║
╚══════════════════════════════════════════════════════════════╝

Task: <id> - <title>
Parent: <parent-id> - <parent-title> (or "none")
Tests: ✓ All passing
Build: ✓ Successful

Signal: KITCHEN_COMPLETE

Summary:
  <1-2 sentence description of what was accomplished>

Files changed:
  M src/foo.ts
  A src/bar.ts

Verification:
  [✓] All todos complete
  [✓] Code compiles
  [✓] Tests pass

Findings (to file in tidy):
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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
