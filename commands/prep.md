---
description: Sync state, load context, show ready tasks
allowed-tools: Bash, Read, Glob
---

## Summary

**Sync state and identify ready tasks.** Part of prep → cook → serve → tidy.

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Sync State

Ensure local state is current:

```bash
git fetch origin
git pull --rebase
```

If `.beads/` directory exists:
```bash
bd sync
```

### Step 2: Gather Task Queue

Get project and branch info:
```bash
pwd                           # Project directory
git branch --show-current     # Current branch
```

Display current task state:
```bash
bd ready                      # Available tasks (no blockers)
bd list --status=in_progress  # Active tasks
bd blocked                    # Blocked tasks (for awareness)
```

### Step 3: Output Session Summary

Output a focused, scannable summary:

```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date | ⚠️ <issue>

Ready: <count> tasks
In progress: <count>
Blocked: <count>

NEXT TASK:
  <id> [P<n>] <title>
  <first line of description if available>

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook (or /line:cook <id> for specific task)
```

**Important:** Do NOT include bead command reference here. That information is available via `/line:getting-started` and `/line:tidy` (where it's actually needed).

## Error Handling

If sync fails:
```
⚠️ SYNC FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Options:
  1. Resolve manually and run /line:prep again
  2. Run /line:cook to proceed offline (will sync later)
```

## Example Output

```
SESSION: line-cook @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: 3 tasks
In progress: 1
Blocked: 1

NEXT TASK:
  lc-042 [P1] Implement prep command
  Create /prep command for session setup with minimal context

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook (or /line:cook lc-042 for this task)
```

## Example Usage

```
/line:prep
```

This command takes no arguments.
