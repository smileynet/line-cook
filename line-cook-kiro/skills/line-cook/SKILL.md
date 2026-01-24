---
name: line-cook
description: AI-supervised development workflow. Use when running prep, cook, serve, tidy, or work commands, managing beads issues during sessions, or following prep→cook→serve→tidy cycle. Covers workflow orchestration, guardrails, and session management.
---

# Line Cook

Structured AI workflow execution with CLI tool support.

## When to Use

- Starting a work session with "work" or "/work"
- Running individual workflow steps: "mise", "prep", "cook", "serve", "tidy", "plate"
- Managing beads issues during execution
- Understanding workflow guardrails

## CLI Tool

Line Cook provides a CLI (`lc`) for mechanical operations:

```bash
lc prep              # Sync state, show ready tasks
lc cook [id]         # Claim task, output context
lc serve             # Output diff for review
lc tidy              # Commit and push
lc work [id]         # Full cycle orchestration
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| "mise" | Plan work breakdown before implementation |
| "prep" | Sync git, show ready tasks |
| "cook" | Claim and execute a task |
| "serve" | AI peer review of completed work |
| "tidy" | Commit, sync beads, push |
| "plate" | Validate completed feature |
| "service" | Full service (mise→prep→cook→serve→tidy→plate) |
| "work" | Quick cycle (prep→cook→serve→tidy) |

## Core Workflow

```bash
lc work              # Quick cycle with auto-selected task
lc work <task-id>    # Quick cycle with specific task
```

**Quick cycle (most common):**
```
prep → cook → serve → tidy
```

**Full service (feature delivery):**
```
mise → prep → cook → serve → tidy → plate
```

### Step-by-Step

1. **Mise**: Plan work breakdown (interactive)
2. **Prep**: Sync state, identify available work
3. **Cook**: Claim task, execute with guardrails, verify completion
4. **Serve**: AI reviews changes
5. **Tidy**: File discovered issues, commit, push
6. **Plate**: Validate feature completion (when applicable)

## Guardrails

Line Cook enforces these disciplines:

- **Sync before work** - Always start with current state
- **One task at a time** - Focus prevents scope creep
- **Verify before done** - Tests pass, code compiles
- **File, don't block** - Discovered issues become new beads
- **Push before stop** - Work isn't done until it's pushed

## Beads Integration

Line Cook uses beads for task management. The CLI handles most operations:

```bash
bd ready              # Find unblocked tasks
bd close <id>         # Complete task
bd sync               # Sync with git
```

## Parking Lot Pattern

Tasks under "Retrospective" or "Backlog" epics are excluded from auto-selection. Explicit selection still works:

```bash
lc cook <parked-task-id>
```

## Error Handling

If a step fails:
- **Prep fails**: Fix sync issues, retry
- **Cook fails**: Continue to tidy to save progress
- **Serve fails**: Review skipped, continue to tidy
- **Tidy fails**: Create bead for follow-up
- **Plate fails**: Note incomplete, create follow-up bead

## Reference

For full documentation, see:
- `README.md` in project root - Philosophy and installation
- `steering/*.md` files - Workflow instructions
