---
name: line-cook
description: AI-supervised development workflow. Use when running prep, cook, serve, tidy, or work commands, managing beads issues during sessions, or following prep→cook→serve→tidy cycle. Covers workflow orchestration, guardrails, and session management.
---

# Line Cook

Structured AI workflow execution: prep → cook → serve → tidy.

## When to Use

- Starting a work session with "work" or "/work"
- Running individual workflow steps: "prep", "cook", "serve", "tidy"
- Managing beads issues during execution
- Understanding workflow guardrails

## Quick Reference

| Command | Purpose |
|---------|---------|
| "work" | Full prep→cook→serve→tidy cycle |
| "prep" | Sync git, show ready tasks |
| "cook" | Claim and execute a task |
| "serve" | AI peer review of completed work |
| "tidy" | Commit, sync beads, push |

## Core Workflow

```
work              # Full cycle with auto-selected task
work <task-id>    # Full cycle with specific task
```

### Step-by-Step

1. **Prep**: Sync state, identify available work
2. **Cook**: Claim task, execute with guardrails, verify completion
3. **Serve**: Headless AI reviews changes (if supported)
4. **Tidy**: File discovered issues, commit, push

## Guardrails

Line Cook enforces these disciplines:

- **Sync before work** - Always start with current state
- **One task at a time** - Focus prevents scope creep
- **Verify before done** - Tests pass, code compiles
- **File, don't block** - Discovered issues become new beads
- **Push before stop** - Work isn't done until it's pushed

## Beads Integration

Line Cook orchestrates beads for task management:

```bash
bd ready              # Find unblocked tasks
bd update <id> --status=in_progress  # Claim task
bd close <id>         # Complete task
bd sync               # Sync with git
```

## Parking Lot Pattern

Tasks under "Retrospective" or "Backlog" epics are excluded from auto-selection. Explicit selection still works:

```
cook <parked-task-id>
```

## Error Handling

If a step fails:
- **Prep fails**: Fix sync issues, retry
- **Cook fails**: Continue to tidy to save progress
- **Serve fails**: Review skipped, continue to tidy
- **Tidy fails**: Create bead for follow-up

## Reference

For full documentation, see:
- `README.md` in project root - Philosophy and installation
- `steering/*.md` files - Workflow instructions
