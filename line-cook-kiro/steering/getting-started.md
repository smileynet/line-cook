# Getting Started

When the user says "getting started", "tutorial", "help with line cook", or similar:

**Read and display the full Line Cook tutorial to the user.**

Use the Read tool to read the tutorial file at `docs/tutorial-kiro.md` (in the line-cook repository root).

After reading, output the entire contents to the user so they can follow along. Do not summarize or act on it - display it for reference.

If the file cannot be found, display this fallback quick reference:

---

## Line Cook Quick Reference

### The Workflow Loop

```
prep  →  cook  →  serve  →  tidy
  ↓        ↓        ↓        ↓
sync    execute  review   commit
```

Or say `work` to run the full cycle.

### Commands

| Say | What happens |
|-----|--------------|
| `prep` | Sync and show ready work |
| `cook` | Execute a task with guardrails |
| `serve` | AI peer review |
| `tidy` | Commit, file findings, push |
| `work` | Full cycle (all four) |

### Beads Commands

```bash
bd create --title="..." --type=task --priority=2  # Create a task
bd dep add <task> <depends-on>                     # Add dependency
bd ready                                           # Show unblocked tasks
bd blocked                                         # Show blocked tasks
bd stats                                           # Project overview
bd sync                                            # Sync with remote
```

### Guardrails

1. **Sync before work** - Always start current
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles
4. **File, don't block** - Discoveries become beads
5. **Push before stop** - Work isn't done until pushed

---

For the full tutorial, see `docs/tutorial-kiro.md` in the line-cook repository.
