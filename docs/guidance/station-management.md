# Station Management

> Keep your workstation organized for efficient service.

Station management in Line Cook means keeping your AI session context clean, focused, and recoverable. Like a well-organized kitchen station, everything should have its place.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Context getting long | Run `/compact` or start new session |
| Lost after compaction | Run `lc prep` to reload context |
| Multiple tasks open | Focus on one, file others as beads |
| Session ending | Run `/tidy` to commit and push |

## The Kitchen Analogy

A line cook's station:

1. **Mise en place** - Ingredients organized and ready
2. **Clear counter** - Only current order's items out
3. **Ticket rail** - Upcoming orders visible
4. **Cleaning as you go** - Don't let mess accumulate

Your AI session works the same way.

## Context Window Management

The AI context window is like your prep counter - limited space for active work.

### Signs of Context Overload

- Responses slow down
- AI starts forgetting earlier details
- Repeated questions about things discussed before
- Long response times

### Solutions

**Compact:** Clear context while preserving summary:

```
/compact
```

After compaction, reload context:

```
/line:prep
```

**New Session:** For major context switches:

```
# End current session
/line:tidy

# Start fresh
# (open new terminal/session)
/line:prep
```

**Focus:** Work on one task at a time:

```
# Don't do this
/line:cook lc-001  # Start task 1
/line:cook lc-002  # Switch to task 2 mid-work

# Do this
/line:cook lc-001  # Complete task 1
/line:tidy         # Commit
/line:cook lc-002  # Then start task 2
```

## Session Lifecycle

### Starting a Session

Always start with prep:

```
/line:prep
```

This:
- Syncs git repository
- Syncs beads (if present)
- Shows ready tasks
- Loads project context

### During a Session

Track work with beads, not mental notes:

```bash
# Found a bug while working? Create a bead
bd create --title="Fix null check in auth" --type=bug

# Thought of an improvement? Create a bead
bd create --title="Add caching to user lookup" --type=task
```

**File, don't block** - Discoveries become beads for later, not interruptions now.

### Ending a Session

Always end with tidy:

```
/line:tidy
```

This:
- Creates descriptive commit
- Syncs beads
- Pushes to remote

**Work is not complete until pushed.**

## Context Recovery

After context is cleared (compaction, new session, crash):

### Standard Recovery

```
/line:prep
```

This reloads:
- Project structure from AGENTS.md
- Ready tasks from beads
- Git status

### If Beads Are Missing

```bash
bd sync --status  # Check sync state
bd sync           # Force sync
```

### If Git Is Diverged

```bash
git status
git pull --rebase  # Or resolve conflicts
```

## Multi-Session Work

For work spanning multiple sessions:

### Using Beads

```bash
# Session 1: Start work
bd update lc-001 --status in_progress
# ... do work ...
# Session 1 ends without completing

# Session 2: Resume
bd show lc-001  # See where you left off
# ... continue work ...
bd close lc-001
```

### Handoff Notes

When pausing work, update the bead:

```bash
bd update lc-001 --description "$(cat <<EOF
Original description...

## Progress (2024-01-15)
- Completed auth middleware
- Started on token validation
- TODO: Error handling for expired tokens
EOF
)"
```

## Task Focus

One task at a time prevents context pollution:

### Anti-pattern: Task Switching

```
/line:cook lc-001  # Start feature A
# ... partial work ...
/line:cook lc-002  # Start feature B (A incomplete)
# ... partial work ...
# Now context has two incomplete features
```

### Pattern: Sequential Focus

```
/line:cook lc-001  # Start feature A
# ... complete work ...
/line:tidy         # Commit A
/line:cook lc-002  # Start feature B with clean context
```

### If You Must Switch

File progress before switching:

```bash
# Note where you are
bd update lc-001 --description "In progress: completed X, need Y and Z"

# Commit partial work
git add .
git commit -m "wip: partial progress on lc-001"

# Now safe to switch
/line:cook lc-002
```

## Parallel Work

For truly independent work, use git worktrees:

```bash
# Create worktree for second task
git worktree add ../project-feature-b feature-b

# Work in separate directories/sessions
cd ../project-feature-b
/line:cook lc-002

# Main directory continues with lc-001
cd ../project
/line:cook lc-001
```

## Station Cleanup

Periodic cleanup keeps things manageable:

### Daily

- Close completed beads
- Push all local commits
- Clear stale branches

### Weekly

- Review in-progress beads
- Close or update stale items
- Archive completed epics

### Commands

```bash
# See what's open
bd list --status=open

# Close completed
bd close lc-001 lc-002 lc-003

# Check sync state
bd sync --status
```

## Anti-patterns

### Context Accumulation

> Building up context across many tasks without compaction.

Result: Slow responses, forgotten context, errors.

Fix: Compact or new session between major tasks.

### Untracked Work

> Starting work without beads, losing track across sessions.

Result: Forgotten work, duplicated effort.

Fix: Create beads for all strategic work.

### Uncommitted Sessions

> Ending session without committing and pushing.

Result: Lost work, diverged branches.

Fix: Always run `/line:tidy` before ending.

### Context Hoarding

> Keeping everything in context "just in case."

Result: Slower AI, worse responses.

Fix: Trust beads and git. Compact freely.

## Related

- [Workflow](./workflow.md) - Overall workflow structure
- [Kitchen Logs](./kitchen-logs.md) - Tracking what happens
- [Order Priorities](./order-priorities.md) - What to work on next
