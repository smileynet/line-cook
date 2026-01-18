---
description: Load work context, sync state, review available tasks
---

## Task

Session preparation: load context, sync state, and understand available work. Part of the `/line-prep` → `/line-cook` → `/line-tidy` workflow loop.

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

### Step 2: Load Project Context

Read and summarize key project files:

1. Read `CLAUDE.md` (project instructions) if present
2. Read `AGENTS.md` if present (workflow instructions)
3. Summarize key constraints and patterns for this project

Output a brief summary of project-specific context that applies to the session.

### Step 3: Display Bead Usage Reference

If `.beads/` exists, output this reference:

```
Bead Quick Reference:
━━━━━━━━━━━━━━━━━━━━━

Creating issues:
  bd create --title="..." --type=task|bug|feature --priority=0-4

  Priority: P0=critical, P1=high, P2=medium, P3=low, P4=backlog
  Types: task (work item), bug (broken), feature (new capability)

Epics & children:
  bd create --title="Parent epic" --type=epic
  bd create --title="Child task" --type=task --parent=<epic-id>

Dependencies (B blocks A):
  bd dep add <issue-a> <depends-on-b>

  Example: Tests depend on implementation
  bd dep add beads-002 beads-001  # 002 waits for 001

Key fields:
  --assignee=<user>     Who owns this
  --description="..."   Detailed context (use for complex tasks)
  --labels=a,b,c        Categorization tags

Workflow:
  bd update <id> --status=in_progress   # Claim work
  bd comments add <id> "progress note"  # Add context
  bd close <id>                         # Mark done
```

### Step 4: Show Work Queue

Display current work state:

```bash
bd ready                      # Available tasks (no blockers)
bd list --status=in_progress  # Active work
bd blocked                    # Blocked tasks (for awareness)
```

### Step 5: Output Work Summary

Provide a concise session readiness summary:

```
Session Ready:
- Project: <name from CLAUDE.md or directory>
- Branch: <current-branch>
- Ready tasks: <count>
- In progress: <count>
- Blocked: <count>

Next recommended: <highest priority ready task with title>

Run /line-cook to start working, or /line-cook <id> for specific task.
```

## Example Output

```
/line-prep

Syncing state...
✓ git pull --rebase (up to date)
✓ bd sync (2 changes synced)

Project Context:
- meta-claude: Claude Code documentation and workflows
- Key pattern: Progressive disclosure in skills
- Constraint: Never create docs unless explicitly requested

Bead Quick Reference:
━━━━━━━━━━━━━━━━━━━━━
[reference output...]

Work Queue:
Ready (3):
  beads-042 [P1] Implement prep command
  beads-043 [P2] Add tests for cook command
  beads-044 [P3] Review documentation structure

In Progress (1):
  beads-041 [P1] Create workflow commands (assigned: sam)

Blocked (1):
  beads-045 [P2] Deploy to production (blocked by: beads-044)

Session Ready:
- Project: meta-claude
- Branch: main
- Ready tasks: 3
- In progress: 1
- Blocked: 1

Next recommended: beads-042 [P1] Implement prep command

Run /line-cook to start working, or /line-cook <id> for specific task.
```

## Example Usage

```
/line-prep
```

This command takes no arguments.
