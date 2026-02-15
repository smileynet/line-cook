# Getting Started with Line Cook

A concrete walkthrough from install to first shipped task.

## Prerequisites

1. **beads** installed — `bd` command available ([install guide](https://github.com/steveyegge/beads))
2. **Line Cook** installed — see [Installation](#installation) below
3. A **git repository** to work in

### Installation

Pick your platform:
- [Claude Code](installation/claude-code.md)
- [OpenCode](installation/opencode.md)
- [Kiro](installation/kiro.md)

---

## Step 1: Initialize Beads

In your project directory:

```bash
bd init
```

This creates a `.beads/` directory for tracking work.

---

## Step 2: Plan Your Work (/mise)

Tell Claude what you want to build:

```
/line:mise
```

Mise walks you through three phases with pauses between each:

**Brainstorm** — Claude asks questions, explores approaches, recommends a direction.

```
BRAINSTORM: Reading List CLI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions:
  1. What info per book?
  2. Where should data live?

You: Title, author, finished status. Local JSON file.

BRAINSTORM COMPLETE
File: docs/planning/brainstorm-reading-cli.md

Continue to /line:scope? [Y/n]
```

**Scope** — Creates a structured plan as editable YAML.

```
MENU PLAN CREATED
File: docs/planning/menu-plan.yaml

Phases: 1 | Features: 1 | Tasks: 4

Continue to /line:finalize? [Y/n]
```

**Finalize** — Converts the plan to tracked issues with dependencies and test specs.

```
MISE COMPLETE
Beads: 1 epic, 1 feature, 4 tasks
Test Specs: 1 BDD, 4 TDD

Available tasks:
  lc-002 [P1] Implement JSON file storage
```

---

## Step 3: Clear Context

Planning is done. Clear your context (new conversation or `/compact`) so execution starts fresh.

---

## Step 4: Your First Run Cycle

### Prep — Get Oriented

```
/line:prep
```

```
SESSION: reading-cli @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date
Ready: 1 task | Blocked: 3

NEXT TASK:
  lc-002 [P1] Implement JSON file storage
```

### Cook — Execute the Task

```
/line:cook
```

Cook claims the task, writes tests first (TDD), implements code, and verifies everything passes.

```
DONE: lc-002 - Implement JSON file storage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files: A src/storage.py, A tests/test_storage.py
Verification: [✓] Tests pass (4 passed)
```

### Serve — AI Peer Review

```
/line:serve
```

A fresh Claude instance reviews your changes — no sunk cost, more objective.

```
REVIEW: lc-002
━━━━━━━━━━━━━━

Verdict: APPROVED
Summary: Clean implementation. Good test coverage.
```

### Tidy — Commit and Push

```
/line:tidy
```

```
TIDY: Session cleanup
━━━━━━━━━━━━━━━━━━━━━

Task completed: lc-002
Issues filed: 2 (discovered during cook)
Commit: a1b2c3d
Push: ✓ origin/main

Session complete.
```

Your code is pushed. Discovered issues are tracked. Dependencies are updated — previously blocked tasks are now ready.

---

## Step 5: Keep Going

Run `bd ready` to see newly unblocked tasks, then repeat the cycle:

```
/line:prep → /line:cook → /line:serve → /line:tidy
```

Or use `/line:run` to orchestrate all four phases automatically:

```
/line:run
```

---

## The Full Picture

```
Mise Cycle                    Run Cycle
┌──────────────────┐        ┌──────────────────┐
│ /brainstorm      │        │ /prep      ◄──┐  │
│      ↓           │        │    ↓          │  │
│ /scope           │        │ /cook         │  │
│      ↓           │        │    ↓          │  │
│ /finalize  ──────┼──────► │ /serve        │  │
└──────────────────┘        │    ↓          │  │
                            │ /tidy  ───────┘  │
                            │  (next task)     │
                            └──────────────────┘
```

1. **Mise** turns ideas into well-scoped tasks
2. **Run** executes tasks one at a time with quality gates
3. Repeat Run until all tasks are done
4. Run `/line:plate` when a feature's tasks are all complete

---

## Next Steps

- [Mise Cycle](cycles/mise-cycle.md) — Deep dive into planning
- [Run Cycle](cycles/run-cycle.md) — Deep dive into execution
- [FAQ](faq.md) — Common questions and troubleshooting
- [Loop Cycle](cycles/loop-cycle.md) — Autonomous multi-task execution
- [Command Reference](reference/commands.md) — All commands and options
