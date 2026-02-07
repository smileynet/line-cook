---
name: line-cook
description: AI-supervised development workflow. Use when running /line-run, /line-prep, /line-cook, /line-serve, /line-tidy commands, managing beads issues during sessions, or following prep→cook→serve→tidy cycle. Covers workflow orchestration, guardrails, and session management.
---

# Line Cook

Structured AI workflow execution: prep → cook → serve → tidy.

## When to Use

- Starting a work session with `/line-run`
- Running individual workflow steps: `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`
- Managing beads issues during execution
- Understanding workflow guardrails

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/line-run` | Full prep→cook→serve→tidy cycle |
| `/line-prep` | Sync git, show ready tasks |
| `/line-cook` | Claim and execute a task |
| `/line-serve` | AI peer review of completed work |
| `/line-tidy` | Commit, sync beads, push |

## Core Workflow

```
/line-run              # Full cycle with auto-selected task
/line-run <task-id>    # Full cycle with specific task
```

### Step-by-Step

1. **Prep**: Sync state, identify available work
2. **Cook**: Claim task, execute with guardrails, verify completion
3. **Serve**: Headless AI reviews changes
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

```bash
/line-cook <parked-task-id>
```

## Error Handling

If a step fails:
- **Prep fails**: Fix sync issues, retry
- **Cook fails**: Continue to tidy to save progress
- **Serve fails**: Review skipped, continue to tidy
- **Tidy fails**: Create bead for follow-up

## Reference

- [README](../../../../README.md) - Philosophy and installation
- [Commands](../../commands/) - Detailed command documentation
