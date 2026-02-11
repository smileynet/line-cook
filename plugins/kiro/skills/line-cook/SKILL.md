---
name: line-cook
description: AI-supervised development workflow. Use when running prep, cook, serve, tidy, or work commands, managing beads issues during sessions, or following prep→cook→serve→tidy cycle. Covers workflow orchestration, guardrails, and session management.
---

# Line Cook

Structured AI workflow execution for disciplined development.

## When to Use

- Starting a work session with "work"
- Running individual workflow steps: "mise", "prep", "cook", "serve", "tidy", "plate"
- Planning phases: "brainstorm", "scope", "finalize"
- Managing beads issues during execution
- Architecture decisions, audits, and quality checks
- Understanding workflow guardrails

## Quick Reference

| Command | Purpose |
|---------|---------|
| "brainstorm" | Explore problem space (divergent thinking) |
| "scope" | Structure work breakdown (convergent thinking) |
| "finalize" | Convert plan to beads and test specs |
| "mise" or "plan" | Full planning (brainstorm→scope→finalize) |
| "prep" | Sync git, show ready tasks |
| "cook" | Claim and execute a task with TDD cycle |
| "serve" | AI peer review of completed work |
| "tidy" | Commit, sync beads, push |
| "plate" | Validate completed feature |
| "run" or "work" | Full execution cycle |
| "decision" | Manage architecture decisions (ADRs) |
| "architecture-audit" | Audit codebase architecture |
| "plan-audit" | Audit planning quality |
| "help" | Show available commands |
| "loop" | Manage autonomous loop |
| "getting started" | Show workflow guide |

Use `@line-<command>` syntax for explicit invocation (e.g., `@line-brainstorm`, `@line-cook`).

## Core Workflow

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

## TDD Cycle with Quality Gates

Cook phase follows Red-Green-Refactor with automatic quality checks:

**RED**: Write failing test
- Write test for the feature
- Verify test fails
- Taster agent reviews test quality
- Address critical issues before proceeding

**GREEN**: Implement minimal code
- Write simplest code to make test pass
- Verify tests pass
- No refactoring yet

**REFACTOR**: Clean up code
- Improve structure while tests pass
- Ensure tests still pass after refactoring

**Quality Gates** (must pass before completion):
- Tests pass (project-specific test command)
- Code builds (project-specific build command)
- Test quality approved by taster agent
- Code quality approved by sous-chef agent (serve phase)

## Beads Integration

Line Cook uses beads for task management:

```bash
bd ready                              # Find unblocked tasks
bd update <id> --status in_progress   # Claim task
bd show <id>                          # Get task context
bd close <id>                         # Complete task
bd sync                               # Sync with git
```

## Parking Lot Pattern

Tasks under "Retrospective" or "Backlog" epics are excluded from auto-selection. Explicit selection still works:

```bash
bd update <parked-task-id> --status in_progress
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
