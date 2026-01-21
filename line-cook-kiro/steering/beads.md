# Beads Quick Reference

Git-native issue tracking for multi-session work.

## Creating Issues

```bash
bd create --title="..." --type=task|bug|feature|epic --priority=0-4

# Priority: 0=critical, 1=high, 2=medium, 3=low, 4=backlog
# Types: task (work item), bug (broken), feature (new capability), epic (container)
```

## Finding Work

```bash
bd ready                      # Unblocked tasks
bd list --status=open         # All open
bd list --status=in_progress  # Active work
bd blocked                    # Tasks with blockers
bd show <id>                  # Full details
```

## Managing Tasks

```bash
bd update <id> --status=in_progress  # Claim task
bd comments add <id> "note"          # Add context
bd close <id>                        # Mark done
bd close <id1> <id2> ...             # Close multiple
```

## Epics and Children

```bash
bd create --title="Epic" --type=epic --priority=2
bd create --title="Task" --type=task --parent=<epic-id>
bd list --parent=<epic-id>           # View children
```

## Dependencies

```bash
bd dep add <issue> <depends-on>      # A depends on B
bd blocked                           # View blocked tasks
```

## Sync

```bash
bd sync                              # Push/pull with remote
bd sync --status                     # Check without syncing
```

## Stats

```bash
bd stats                             # Project statistics
bd doctor                            # Check for issues
```

## Retrospective Pattern

For minor suggestions, file under a retrospective epic:

```bash
bd create --title="Consider X" --type=task --priority=4 --parent=<retro-epic-id>
```

Tasks under "Retrospective" or "Backlog" epics are excluded from auto-selection.

## Context Recovery

```bash
bd prime                             # Reload context after session clear
```
