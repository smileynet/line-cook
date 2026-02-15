---
description: Learn the workflow
allowed-tools: Bash, Read
---


**Output this guide to the user.** Do not act on it - display it for reference.

---

## How Line Cook Works

Line Cook organizes AI-assisted development into two cycles: **Mise** (planning) and **Run** (execution). Think big in Mise, execute small in Run.

## The Two Cycles

```
  Mise Cycle                  Run Cycle
 ┌──────────────────┐       ┌──────────────────┐
 │                  │       │                  │
 │   /brainstorm    │       │   /prep ◄────┐   │
 │        ↓         │       │      ↓       │   │
 │     /scope       │       │   /cook      │   │
 │        ↓         │       │      ↓       │   │
 │   /finalize ─────┼─────► │   /serve     │   │
 │                  │       │      ↓       │   │
 └──────────────────┘       │   /tidy ─────┘   │
                            │    next task     │
                            └──────────────────┘
```

### Mise Cycle: Ideas → Tasks

Turn unstructured ideas into well-scoped, dependency-ordered tasks.

| Phase | Command | What it does |
|-------|---------|-------------|
| Brainstorm | `/line:brainstorm` | Explore the problem space — questions, research, risks |
| Scope | `/line:scope` | Structure into epics → features → tasks with dependencies |
| Finalize | `/line:finalize` | Create beads (tracked issues) and test specifications |

Use `/line:mise` to run all three with pauses between phases.

### Run Cycle: Tasks → Shipped Code

Execute one task at a time with TDD, AI review, and automatic commit/push.

| Phase | Command | What it does |
|-------|---------|-------------|
| Prep | `/line:prep` | Sync git/beads, show unblocked tasks |
| Cook | `/line:cook` | Claim task, write tests first, implement, close |
| Serve | `/line:serve` | AI peer review (polisher + sous-chef) |
| Tidy | `/line:tidy` | File discoveries, commit, push |

Use `/line:run` to run all four in sequence.

### Quality Gates

After the basic cycle, additional gates validate completed work:

| Gate | Command | When |
|------|---------|------|
| Feature done | `/line:plate` | All tasks under a feature are closed |
| Epic done | `/line:close-service` | All features under an epic are closed |

## Workflow Principles

1. **Sync before starting** — Always work from current state
2. **Track with beads** — Strategic tasks live in the issue tracker
3. **Note, then file** — Discoveries are noted during cook, filed during tidy
4. **Guardrails on completion** — Verify before marking done
5. **Push before stop** — Session isn't done until pushed

> **Tip:** Run `/line:plan-audit` periodically to check bead health and structure.

## What's Next?

**Ready to try it hands-on?**
Run `/line:onboarding` for an interactive walkthrough with a demo project.

**Having setup trouble?**
Run `/line:init` to verify your environment.

**Already set up?**
- Start planning: `/line:mise`
- Start executing: `/line:run`
- See all commands: `/line:help`
- Autonomous execution: `/line:loop`
