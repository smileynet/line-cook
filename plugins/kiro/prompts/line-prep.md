**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. The user's message following this prompt is your input.

## Summary

**Sync state and identify ready tasks.** Part of prep → cook → serve → tidy.

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Collect State

Sync local state, load context, and gather kitchen roster in one structured call:

```bash
# Collect all state: sync, project info, roster, suggestion, hierarchy, branch
STATE=$(python3 plugins/claude-code/scripts/state-snapshot.py --json 2>/dev/null)
echo "$STATE"
```

The JSON output includes: `sync`, `project`, `roster` (ready/in_progress/blocked), `suggest_next_task` (with drill_path), `hierarchy` (epic/feature/completed_siblings), and `branch_recommendation`.

### Step 2: Branching Strategy

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

### Step 3: Identify Next Task and Gather Context

Before outputting the summary, determine the recommended next task and its hierarchy:

#### 3a: Find Next Ready Task

The `state-snapshot.py` output includes `suggest_next_task` with:
- `suggest_next_task.suggestion`: the recommended task (already drilled through epics)
- `suggest_next_task.drill_path`: list of IDs showing epic → feature → task drill-down

Use this directly. **Fallback** (if `suggestion` is null): manually check `roster.ready` and drill into epics:
1. Get the highest priority ready item
2. If it's an epic, find its first ready child via `bd list --parent=<epic-id>`

#### 3b: Gather Parent Hierarchy

The `state-snapshot.py` output already includes `hierarchy` with:
- `hierarchy.epic`: epic ID, title, goal, and progress (closed/total)
- `hierarchy.feature`: feature ID, title, goal, and progress
- `hierarchy.completed_siblings`: list of completed sibling tasks with IDs and titles

Use this data directly — no additional subprocess calls needed.

#### 3c: Extract Task Intent

Parse the task description to extract:
- **Summary**: First paragraph of description
- **Deliverables**: Lines starting with "Deliverable:", "Verify:", or bullet points under those headers

### Step 4: Output Kitchen Roster

Output a focused, scannable summary with hierarchical context:

**Standard output (task with full hierarchy):**
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
  Progress: <closed>/<total> features complete

  └── FEATURE: <feature-id> <feature-title>
      Goal: <first line of feature description>
      Progress: <closed>/<total> tasks complete

      CURRENT STATE:
        ✓ <task-id> - <completed task title>
        ✓ <task-id> - <completed task title>
        ... (list completed siblings)

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────

<task-id> [P<n>] <task-title>

INTENDED CHANGE:
  <first paragraph of task description>

  Deliverable:
    - <extracted deliverables from description>
    - <bullet points or items after "Deliverable:" header>

NEXT STEP: @line-cook <task-id>
```

**Standalone task (no parent hierarchy):**
```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: <count> tasks | In progress: <count> | Blocked: <count>

───────────────────────────────────────────
CONTEXT
───────────────────────────────────────────

(Standalone task - no parent epic or feature)

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────

<task-id> [P<n>] <task-title>

INTENDED CHANGE:
  <first paragraph of task description>

NEXT STEP: @line-cook <task-id>
```

**Feature without epic:**
```
───────────────────────────────────────────
CONTEXT
───────────────────────────────────────────

FEATURE: <feature-id> <feature-title>
  Goal: <first line of feature description>
  Progress: <closed>/<total> tasks complete

  CURRENT STATE:
    ✓ <task-id> - <completed task title>
    (or: no completed tasks yet)

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────
...
```

**No ready tasks:**
```
SESSION: <project-name> @ <branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: 0 tasks | In progress: <count> | Blocked: <count>

───────────────────────────────────────────
NO READY TASKS
───────────────────────────────────────────

In Progress:
  <id> - <title> (assigned to <assignee>)

Blocked:
  <id> - <title> (waiting on: <blocker-ids>)

OPTIONS:
  - Continue work on in-progress task
  - Unblock a blocked task
  - Create new work with: bd create --title="..." --type=task

NEXT STEP: Review options above
```

**Important:** Do NOT include bead command reference here. That information is available via `@line-getting-started` and `@line-tidy` (where it's actually needed).

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

## Example Output

**Task with full hierarchy (epic → feature → task):**
```
SESSION: line-cook @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: 4 tasks | In progress: 0 | Blocked: 2

───────────────────────────────────────────
CONTEXT
───────────────────────────────────────────

EPIC: lc-abc [P2] Phase 1: Core Workflow Enhancement
  Goal: Enhance existing commands with TDD cycle and quality gates
  Progress: 2/3 features complete

  └── FEATURE: lc-abc.1 Core Command Enhancement
      Goal: Update prep, cook, serve, tidy with TDD workflow
      Progress: 3/5 tasks complete

      CURRENT STATE:
        ✓ lc-abc.1.1 - Update prep command
        ✓ lc-abc.1.2 - Update cook command
        ✓ lc-abc.1.3 - Update serve command

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────

lc-abc.1.4 [P2] Update tidy command with commit formatting

INTENDED CHANGE:
  Add kitchen log format to commit messages and ensure
  findings from cook phase are filed as beads.

  Deliverable:
    - Commit messages use kitchen log format
    - Findings converted to beads
    - Push verification before session end

NEXT STEP: @line-cook lc-abc.1.4
```

**Standalone task:**
```
SESSION: line-cook @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date

Ready: 2 tasks | In progress: 0 | Blocked: 0

───────────────────────────────────────────
CONTEXT
───────────────────────────────────────────

(Standalone task - no parent epic or feature)

───────────────────────────────────────────
NEXT TASK
───────────────────────────────────────────

lc-042 [P1] Fix sync timeout issue

INTENDED CHANGE:
  Increase timeout for bd sync to handle large repos.

NEXT STEP: @line-cook lc-042
```

## Example Usage

```
@line-prep
```

This command takes no arguments.
