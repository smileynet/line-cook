---
description: Clear context and restart with current task only
---

## Summary

**Clear cluttered context and restart fresh with the current task.** Use when context is polluted but you want to continue the same work.

**STOP after completing.** User must manually clear context, then run `/line-cook <task-id>`.

---

## Process

### Step 1: Identify Current Task

Check for an in-progress task:

```bash
bd list --status=in_progress --json | jq -r '.[0].id // empty'
```

**If no in-progress task:**
```
NO ACTIVE TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No task is currently in_progress.

To start fresh with a specific task:
  1. Start a new OpenCode session
  2. Run /line-cook <task-id>
```

**If task found, continue.**

### Step 2: Capture Task Context

Get full task details for re-priming:

```bash
bd show <task-id>
```

Store the task ID and title for the output.

### Step 3: Output Restart Instructions

```
FRESH START: <task-id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current task captured. To restart fresh:

  1. Type `exit` to close OpenCode
  2. Start a new session: opencode
  3. Run /line-cook <task-id>

This will:
  - Clear all accumulated context
  - Reload project instructions (AGENTS.md)
  - Resume work on the same task

Your task remains in_progress and will be waiting.
```

## Design Notes

This command is intentionally minimal. It:

1. **Identifies** the current task (so you don't lose track)
2. **Instructs** the user on the manual steps needed

OpenCode does not have an equivalent to Claude Code's `/clear` command.
The only way to get a fresh context is to start a new session.

## Example Usage

```
/line-fresh
```

This command takes no arguments. It operates on the current in-progress task.
