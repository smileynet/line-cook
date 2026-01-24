---
description: Sync state, load context, show ready tasks
---

## Summary

**Sync state and identify ready tasks.** Part of prep → cook → serve → tidy.

**When run directly:** STOP after completing, show NEXT STEP, and wait for user.
**When run via `/line-work`:** Continue to the next step without stopping.

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

### Step 3: Identify Next Task (Filtered)

Before outputting the summary, determine the recommended next task.

**Exclude parking-lot epics from auto-selection:**

Certain epics ("Retrospective", "Backlog") are parking lots for deferred work. Their children should NOT be auto-selected.

1. Find parking-lot epic IDs:
```bash
EXCLUDE_EPICS=$(bd list --type=epic --json | jq '[.[] | select(.title == "Retrospective" or .title == "Backlog") | .id]')
```

2. Get filtered ready list (excluding children of parking-lot epics):
```bash
bd ready --json | jq --argjson exclude "$EXCLUDE_EPICS" \
  'map(select(.parent == null or (.parent | IN($exclude[]) | not)))'
```

3. Get the highest priority item from the filtered list
4. Check if it's an epic: `bd show <id> --json` and check `issue_type`

**If the top item is an epic:**
- Epics themselves don't contain work - their children do
- Find the first ready child task: `bd list --parent=<epic-id>` filtered by ready (open + unblocked)
- Recommend that child task instead, noting it's part of the epic

**If no ready tasks but epics have unstarted children:**
- Check epic children that are open but not blocked
- Recommend starting with those

**If no actionable tasks remain after filtering:**
```
No actionable tasks ready.
All ready tasks are in Retrospective or Backlog epics.

To work on parked items: /line-cook <specific-task-id>
To see parked work: bd list --parent=<epic-id>
```

### Step 4: Output Session Summary

Output a focused, scannable summary:

**Standard output (task is ready):**
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

NEXT STEP: /line-cook (or /line-cook <id> for specific task)
```

**Epic-aware output (when top priority is an epic):**
```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date | ⚠️ <issue>

Ready: <count> tasks
In progress: <count>
Blocked: <count>

EPIC IN FOCUS:
  <epic-id> [P<n>] <epic-title>
  Progress: <closed>/<total> children complete

NEXT TASK (part of epic):
  <task-id> [P<n>] <task-title>
  <first line of description if available>

NEXT STEP: /line-cook <task-id>
```

## Error Handling

If sync fails:
```
⚠️ SYNC FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Options:
  1. Resolve manually and run /line-prep again
  2. Run /line-cook to proceed offline (will sync later)
```

## Example Usage

```
/line-prep
```

This command takes no arguments.
