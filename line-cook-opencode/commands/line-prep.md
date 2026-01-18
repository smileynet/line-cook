---
description: Sync state, load context, show ready tasks
---

## Task

Session preparation: sync state and identify available work. Part of the `/line-prep` → `/line-cook` → `/line-serve` → `/line-tidy` workflow loop.

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

### Step 2: Gather Work Queue

Get project and branch info:
```bash
pwd                           # Project directory
git branch --show-current     # Current branch
```

Display current work state:
```bash
bd ready                      # Available tasks (no blockers)
bd list --status=in_progress  # Active work
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

New to line-cook? Run /line-getting-started for workflow guide.
Run /line-cook to start, or /line-cook <id> for specific task.
```

**Important:** Do NOT include bead command reference here. That information is available via `/line-getting-started` and `/line-tidy` (where it's actually needed).

## Error Handling

If sync fails:
```
⚠️ SYNC FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Options:
  1. Resolve manually and run /line-prep again
  2. Run /line-cook to work offline (will sync later)
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

New to line-cook? Run /line-getting-started for workflow guide.
Run /line-cook to start, or /line-cook lc-042 for this task.
```

## Example Usage

```
/line-prep
```

This command takes no arguments.
