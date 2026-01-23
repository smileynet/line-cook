# Line Cook

Task-focused workflow orchestration for AI-assisted development.

## Overview

```
/mise → /prep → /cook → /serve → /tidy → /plate
  ↓       ↓       ↓        ↓        ↓        ↓
plan    sync   execute  review   commit  validate
```

Or use `/line-service` to run the full cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/line-getting-started` | Quick workflow guide for beginners |
| `/line-mise` | Create work breakdown before starting |
| `/line-prep` | Sync git, show ready tasks |
| `/line-cook` | Execute task with TDD cycle |
| `/line-serve` | Review code changes |
| `/line-tidy` | Commit and push changes |
| `/line-plate` | Validate completed feature |
| `/line-service` | Run full workflow cycle |

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Beads Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Epic Philosophy

Epics organize related work into coherent groups using a **child-based** model:

1. **Epics contain children** - Use `--parent=<epic-id>` when creating tasks
2. **Dependencies order children** - Use `bd dep add` to establish order within an epic
3. **Dependencies order epics** - Epics can depend on other epics for sequencing
4. **Cross-epic dependencies (rare)** - A child of one epic may block another epic

```bash
# Create epic structure
bd create --title="Feature X" --type=epic --priority=1
bd create --title="Design X" --type=task --parent=lc-abc
bd create --title="Implement X" --type=task --parent=lc-abc
bd dep add lc-def lc-ghi  # Implement depends on Design

# Query progress
bd epic status                    # Show all epics with child completion
bd list --parent=<epic-id> --all  # List children of an epic
```

## Session Completion (Landing the Plane)

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File issues for remaining work** - Create beads for anything needing follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** - All changes committed AND pushed

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- If push fails, resolve and retry until it succeeds
