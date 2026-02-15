# Beads Quick Reference

Beads is the git-native issue tracker that gives Line Cook memory between sessions. This is a quick reference — see the [beads repo](https://github.com/steveyegge/beads) for full documentation.

## Essential Commands

```bash
bd init                                    # Initialize in project
bd ready                                   # Find available work (no blockers)
bd show <id>                               # View issue details
bd update <id> --status=in_progress        # Claim work
bd close <id>                              # Complete work
bd close <id1> <id2> ...                   # Close multiple at once
bd sync                                    # Sync with git remote
bd stats                                   # Project statistics
bd blocked                                 # Show blocked issues
```

## Work Hierarchy

Line Cook uses a 3-tier hierarchy:

```
Epic (capability area)
├── Feature (user-verifiable outcome)
│   ├── Task (implementation step)
│   └── Task (implementation step)
└── Feature (user-verifiable outcome)
    └── Task (depends on another task)
```

| Tier | Scope | Testing | Created by |
|------|-------|---------|------------|
| **Epic** | 3+ sessions | E2E / smoke | `/line:finalize` |
| **Feature** | 1-3 sessions | BDD acceptance | `/line:finalize` |
| **Task** | 1 session | TDD unit | `/line:finalize` |

**Exception:** Research and Backlog epics have tasks as direct children (no feature layer).

## Creating Hierarchy

```bash
# Create epic
bd create --title="User Authentication" --type=epic --priority=2

# Create features under epic
bd create --title="Users can log in" --type=feature --parent=lc-abc --priority=2

# Create tasks under feature
bd create --title="Implement login form" --type=task --parent=lc-abc.1

# Add dependency (task B depends on task A)
bd dep add lc-B lc-A
```

## Priority Levels

| Priority | Level | Usage |
|----------|-------|-------|
| P0 | Critical | Production broken |
| P1 | High | Blocks other work |
| P2 | Medium | Standard (default) |
| P3 | Low | Nice to have |
| P4 | Backlog | Maybe someday |

```bash
bd update <id> --priority=1    # Escalate
bd update <id> --priority=4    # Park it
```

## Querying Progress

```bash
bd epic status                    # All epics with child completion
bd epic status --eligible-only    # Epics ready to close
bd list --parent=<epic-id>        # Children of an epic
bd list --status=open             # All open issues
bd list --status=in_progress      # Active work
```
