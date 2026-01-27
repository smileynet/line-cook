**Output this guide to the user.** Do not act on it - display it for reference.

---

## Line Cook - Workflow Guide

Line Cook provides structured workflow cycles for AI-assisted development.

### The Workflow Loop

```
@line-prep  →  @line-cook  →  @line-serve  →  @line-tidy
    ↓              ↓              ↓              ↓
  sync          execute        review         commit
```

Or use `@line-run` to run the full cycle.

### Commands

| Command | Purpose |
|---------|---------|
| `@line-prep` | Sync git and beads, show ready tasks |
| `@line-cook` | Claim and execute a task with TDD |
| `@line-serve` | Review changes before commit |
| `@line-tidy` | File issues, commit, push |
| `@line-mise` | Plan work breakdown |
| `@line-plate` | Validate completed feature |
| `@line-run` | Full cycle (prep→cook→serve→tidy) |
| `@line-getting-started` | Show this guide |

### Bead Reference

```bash
bd ready                      # Tasks with no blockers
bd list --status=open         # All open issues
bd show <id>                  # View details
bd update <id> --status=in_progress  # Claim task
bd close <id>                 # Mark done
bd sync                       # Push/pull with remote
```

### Quick Start

1. `@line-prep` - See what's ready
2. `@line-cook` - Execute the top task
3. `@line-tidy` - Commit and push

Or just run `@line-run` for the full cycle.
