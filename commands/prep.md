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

### Step 2: Load Kitchen Manual

Load the work structure documentation:

```bash
cat AGENTS.md | head -100
```

This loads kitchen terminology, agent definitions, and workflow principles.

### Step 3: Gather Kitchen Roster

Get project and branch info:
```bash
pwd                           # Project directory
git branch --show-current     # Current branch
```

Display current task state:
```bash
bd ready                      # Available orders (no blockers)
bd list --status=in_progress  # Active orders
bd blocked                    # Blocked orders (for awareness)
```

### Step 4: Branching Strategy

Before selecting a task, check branching context:

| Task Type | Branching | Rationale |
|-----------|-----------|-----------|
| **Feature** | Create branch: `git checkout -b feature/<feature-id>` | Multi-task work, isolation |
| **Task** | Stay on main | Small, atomic changes |

If preparing to work on a feature (has `--type=feature`), create a feature branch first:
```bash
bd show <feature-id>  # Confirm it's a feature
git checkout -b feature/<feature-id>
```

### Step 5: Identify Next Order

Before outputting the summary, determine the recommended next task:

1. Get the highest priority ready item from `bd ready`
2. Check if it's an epic: `bd show <id> --json` and check `issue_type`

**If the top item is an epic:**
- Epics themselves don't contain work - their children do
- Find the first ready child task: `bd list --parent=<epic-id>` filtered by ready (open + unblocked)
- Recommend that child task instead, noting it's part of the epic

**If no ready tasks but epics have unstarted children:**
- Check epic children that are open but not blocked
- Recommend starting with those

### Step 6: Output Kitchen Roster

Output a focused, scannable summary:

**Standard output (task is ready):**
```
╔══════════════════════════════════════════════════════════════╗
║  PREP: Kitchen Ready                                          ║
╚══════════════════════════════════════════════════════════════╝

SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date | ⚠️ <issue>

Kitchen Roster:
  Ready: <count> orders
  In progress: <count> orders
  Blocked: <count> orders

NEXT ORDER:
  <id> [P<n>] <title>
  <first line of description if available>

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook (or /line:cook <id> for specific order)
```

**Epic-aware output (when top priority is an epic):**
```
╔══════════════════════════════════════════════════════════════╗
║  PREP: Kitchen Ready                                          ║
╚══════════════════════════════════════════════════════════════╝

SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date | ⚠️ <issue>

Kitchen Roster:
  Ready: <count> orders
  In progress: <count> orders
  Blocked: <count> orders

EPIC IN FOCUS:
  <epic-id> [P<n>] <epic-title>
  Progress: <closed>/<total> children complete

NEXT ORDER (part of epic):
  <task-id> [P<n>] <task-title>
  <first line of description if available>

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook <task-id>
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

**Standard task:**
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

**Epic with child tasks:**
```
SESSION: line-cook @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: 5 tasks
In progress: 0
Blocked: 2

EPIC IN FOCUS:
  lc-45k [P1] Reimagine line-cook as Go CLI tool
  Progress: 0/5 children complete

NEXT TASK (part of epic):
  lc-cvo [P2] Research beads Go CLI architecture
  Study how beads implements its Go CLI tool

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook lc-cvo
```

## Example Usage

```
/line:prep
```

This command takes no arguments.
