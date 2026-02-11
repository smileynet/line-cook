---
description: Workflow guide with full bead reference
allowed-tools: Bash, Read
---


**Output this guide to the user.** Do not act on it - display it for reference.

---

## line-cook Workflow Guide

This guide explains the line-cook workflow and provides a complete reference for beads (issue tracking).

## The Workflow Loop

```
/line:prep  →  /line:cook  →  /line:serve  →  /line:tidy
    ↓              ↓              ↓              ↓
  sync          execute        review         commit
```

Or use `/line:run` to run the full cycle.

For autonomous execution of multiple tasks, use the `/line:loop` command (see [Autonomous Loop](#autonomous-loop) below).

### /line:prep - "What's ready?"
- Syncs git and beads
- Shows available tasks
- Identifies the next recommended task

### /line:cook - "Execute the task"
- Claims a task
- Plans and executes the task
- Notes discovered issues for later (doesn't file beads yet)
- Closes the task when done

### /line:serve - "Review changes"
- Invokes headless Claude for peer review
- Auto-fixes minor issues
- Categorizes findings for /tidy

### /line:tidy - "Commit and capture"
- Files discovered issues as beads
- Commits changes
- Pushes to remote
- Records session summary

## Workflow Principles

1. **Sync before starting** - Always start with current state
2. **Track with beads** - Strategic tasks live in issue tracker
3. **Note, then file** - Discovered issues are noted in /cook, filed in /tidy
4. **Guardrails on completion** - Verify before marking done
5. **Push before stop** - Session isn't done until pushed

> **Tip:** Run `/line:plan-audit` periodically to check bead health and structure.

---

## Bead Reference

Beads is the git-native issue tracker. Here's the complete reference.

### Creating Issues

```bash
bd create --title="..." --type=task|bug|feature --priority=0-4

# Priority levels:
#   0 = P0 = critical (production down)
#   1 = P1 = high (blocking)
#   2 = P2 = medium (normal priority)
#   3 = P3 = low (when time permits)
#   4 = P4 = backlog (someday/maybe)

# Types:
#   task    = work item
#   bug     = broken behavior
#   feature = new capability
#   epic    = container for related tasks
```

### Epics and Children

```bash
# Create an epic
bd create --title="Parent epic" --type=epic --priority=2

# Create child tasks
bd create --title="Child task" --type=task --parent=<epic-id>
```

### Dependencies

Dependencies express "A depends on B" (B blocks A):

```bash
bd dep add <issue-a> <depends-on-b>

# Example: Tests depend on implementation
bd dep add beads-002 beads-001  # 002 waits for 001 to complete
```

### Key Fields

```bash
--assignee=<user>     # Who owns this
--description="..."   # Detailed context
--labels=a,b,c        # Categorization tags
```

### Workflow Commands

```bash
# Finding tasks
bd ready                      # Tasks with no blockers
bd list --status=open         # All open issues
bd list --status=in_progress  # Active tasks
bd blocked                    # Tasks with unmet dependencies

# Managing issues
bd show <id>                           # View details
bd update <id> --status=in_progress    # Claim task
bd comments add <id> "progress note"   # Add context
bd close <id>                          # Mark done

# Sync and collaboration
bd sync                # Push/pull with remote
bd stats               # Project statistics
```

### Finding Filing Strategy

Code/project findings from serve and other reviewers are filed as **siblings under the current task's parent feature** (any priority). This ensures findings are addressed before the feature is plated.

**Process improvement suggestions** (ways to improve cook, serve, tidy, etc.) go to a Retrospective epic:

```bash
# One-time setup
bd create --title="Retrospective" --type=epic --priority=4

# File process improvements as children
bd create --title="Consider adding lint step to serve" --type=task --priority=4 --parent=<retro-epic-id>
```

See `commands/tidy.md` Finding Filing Strategy for full details.

---

## Quick Start

1. Run `/line:prep` to see ready tasks
2. Run `/line:cook` to execute the top task
3. Run `/line:tidy` when done to commit and push

Or just run `/line:run` for the full cycle.

---

## Autonomous Loop

For batch processing multiple tasks, use the external script wrapper instead of running `/line:run` manually each time:

```bash
# Run with default 25 iterations
/line:loop

# Or invoke the script directly
python3 plugins/claude-code/scripts/line-loop.py

# Run with custom limit
python3 plugins/claude-code/scripts/line-loop.py --max-iterations 10

# JSON output for automation
python3 plugins/claude-code/scripts/line-loop.py --json --output report.json

# Control behavior
python3 plugins/claude-code/scripts/line-loop.py --stop-on-blocked --max-retries 1
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-n, --max-iterations` | 25 | Max iterations before stopping |
| `-t, --timeout` | 600 | Per-iteration timeout in seconds |
| `--json` | false | Output JSON instead of human-readable |
| `-o, --output` | - | Write final report to file |
| `--stop-on-blocked` | false | Stop if task is BLOCKED |
| `--stop-on-crash` | false | Stop on claude crash |
| `--max-retries` | 2 | Max retries per task on NEEDS_CHANGES |

### Why External Script?

The script runs **outside** Claude Code, which provides:
- **Fresh context per task** - No context accumulation across iterations
- **Session independence** - Runs without active Claude Code session
- **Better recovery** - Script survives Claude crashes, can restart
- **Robust feedback** - Tracks bead state changes and parses SERVE_RESULT

The script:
1. Captures bead state (ready/in_progress/closed)
2. Runs `claude --skill line:run` for each task
3. Parses SERVE_RESULT verdict and INTENT block
4. Handles retries on NEEDS_CHANGES (up to max-retries)
5. Reports progress with before/after bead state diffs
6. Stops when no tasks remain or limit reached
