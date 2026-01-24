---
description: Select and execute a task with completion guardrails
---

## Summary

**Execute a task with guardrails ensuring completion.** Part of prep → cook → serve → tidy.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to execute

**When run directly:** STOP after completing, show NEXT STEP, and wait for user.
**When run via `/line-work`:** Continue to the next step without stopping.

---

## Process

### Step 1: Invoke CLI

```bash
lc cook $ARGUMENTS
```

The CLI:
- Selects task (from arg or auto-selects highest priority, filtering parking-lot epics)
- Handles epic traversal (finds first ready child if epic selected)
- Claims task (sets status to in_progress)
- Outputs task details and AI prompt

### Step 2: Execute the Task

**You must execute the task.** The CLI provides context and an AI prompt; follow its guidelines while executing.

1. **Plan with TodoWrite** - Break task into steps before starting
2. **Execute systematically** - Mark items `in_progress` when starting, `completed` when done
3. **Only one item `in_progress`** at a time
4. **Note discoveries** - Do NOT file beads during cooking; note them for `/line-tidy`

### Step 3: Verify Completion

Before marking done, verify ALL guardrails pass:

- [ ] All TodoWrite items completed
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**If any guardrail fails:**
- Do NOT close the task
- Report what's incomplete
- Keep task as `in_progress`
- Ask user how to proceed

### Step 4: Complete and Report

Only after all guardrails pass:

```bash
bd close <task-id>
```

Output completion summary:
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
  - <new tasks discovered>
  - <potential issues noted>

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
⚠️ BLOCKED: <description>
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
