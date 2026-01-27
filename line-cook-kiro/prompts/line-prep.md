Sync state and identify ready tasks. Part of prep → cook → serve → tidy.

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

### Step 2: Gather State

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

### Step 3: Identify Next Task

1. Get the highest priority ready item from `bd ready`
2. Check if it's an epic: `bd show <id> --json` and check `issue_type`

**If the top item is an epic:**
- Find the first ready child task: `bd list --parent=<epic-id>`
- Recommend that child task instead

### Step 4: Gather Context

Once you have identified the next task, gather its parent chain:

```bash
# Get task details
bd show <task-id>

# Check for parent feature/epic
bd show <parent-id>  # if task has parent
```

### Step 5: Output Summary

Use this exact format:

```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date | ⚠️ <issue>

Ready: <count> tasks | In progress: <count> | Blocked: <count>

───────────────────────────────────────────
CONTEXT
───────────────────────────────────────────

EPIC: <epic-id> [P<n>] <epic-title>
  Goal: <first line of epic description>

  └── FEATURE: <feature-id> <feature-title>
      Progress: <closed>/<total> tasks complete

      CURRENT STATE:
        ✓ <task-id> - <completed task title>
        ○ <task-id> - <pending task title>

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────

<task-id> [P<n>] <task-title>

INTENDED CHANGE:
  <first paragraph of task description>

NEXT STEP: @line-cook <task-id>
```

**No ready tasks:**
```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready: 0 tasks | In progress: <count> | Blocked: <count>

───────────────────────────────────────────
NO READY TASKS
───────────────────────────────────────────

In Progress:
  <id> - <title>

Blocked:
  <id> - <title> (waiting on: <blocker-ids>)

OPTIONS:
  - Continue work on in-progress task
  - Unblock a blocked task
  - Create new work with: bd create --title="..." --type=task

NEXT STEP: Review options above
```

## Error Handling

If sync fails:
```
⚠️ SYNC FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Options:
  1. Resolve manually and run @line-prep again
  2. Run @line-cook to proceed offline (will sync later)
```
