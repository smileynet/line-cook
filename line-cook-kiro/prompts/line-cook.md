Execute a task with TDD cycle and completion guardrails. Part of prep → cook → serve → tidy.

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

If `issue_type` is `epic`, find first ready child and select that instead.

**Once a task is selected**, claim it:
```bash
bd show <id>                           # Display full task details
bd update <id> --status=in_progress    # Claim the task
```

### Step 2: Load Context

Load relevant context files:
1. **Project structure** - Understand codebase layout
2. **Related code** - Read files relevant to the task
3. **Dependencies** - Check what this task builds on

### Step 3: Plan the Task

Break the task into steps:
1. Read the task description carefully
2. Identify all deliverables
3. Include verification steps (test, compile, etc.)

### Step 4: Execute TDD Cycle

For code changes, follow TDD cycle:

1. **RED**: Write failing test
   ```bash
   <test command>  # Should FAIL
   ```

2. **GREEN**: Implement minimal code
   ```bash
   <implementation>
   <test command>  # Should PASS
   ```

3. **REFACTOR**: Clean up code
   ```bash
   <refactoring>
   <test command>  # All tests should PASS
   ```

**Output format during execution:**
```
COOKING: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/N] <step> ... ✓
[2/N] <step> ... ✓
[3/N] <step> ... in progress

Progress: 2/N complete

TDD Phase: RED/GREEN/REFACTOR
```

**Collecting findings:** As you execute, note (but do NOT file yet):
- New tasks discovered
- Potential issues or bugs
- Areas for improvement

These will be filed as beads in @line-tidy.

### Step 5: Verify Completion

Before marking the task done, verify ALL guardrails pass:

- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**If any guardrail fails:**
- Do NOT close the task
- Report what's incomplete
- Keep task as `in_progress`

### Step 6: Complete Task

Only after all guardrails pass:

```bash
bd close <id>
```

**Completion output format:**
```
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN COMPLETE                                             ║
╚══════════════════════════════════════════════════════════════╝

Task: <id> - <title>
Tests: ✓ All passing
Build: ✓ Successful

INTENT:
  <1-2 sentences from task description>

BEFORE → AFTER:
  <previous state> → <new state>

Files changed:
  M src/foo.ts
  A src/bar.ts

Verification:
  [✓] Code compiles
  [✓] Tests pass

Findings (to file in @line-tidy):
  New tasks:
    - "<discovered task>"
  Potential issues:
    - "<issue noted>"

NEXT STEP: @line-serve (review) or @line-tidy (commit)
```

## Guardrails

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Note, don't file** - Discovered issues are noted for @line-tidy, not filed during cook

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

Task remains in_progress. Run @line-tidy to save partial progress.
```
