# FAQ

Answers organized by topic. Scan the headers to find what you need.

---

## Getting Started

### What if I don't use beads?

You can still run the commands — they'll work. But you lose memory between sessions. Without beads, there's no persistent record of what was done, what's blocked, or what was discovered. Each session starts from scratch.

### How long should a task be?

A task should take roughly 5-10 minutes of AI execution time. If it's taking longer, break it down with dependencies — smaller tasks mean more checkpoints and easier recovery.

### Why clear context between tasks?

AI context windows are finite. Old planning discussions crowd out new work. Clearing between tasks ensures each session starts focused on execution. Your beads persist — only the conversation resets.

### What's the difference between `/line:run` and running phases individually?

`/line:run` orchestrates prep → cook → serve → tidy automatically. Running phases individually gives you control between each step — useful when learning the workflow or debugging issues. Start with individual phases, graduate to `/line:run` when confident.

---

## Mise Cycle

### How do I know if something is an epic, feature, or task?

Use the **"Who" Test**:

| Question | Epic | Feature | Task |
|----------|------|---------|------|
| **How long?** | 3+ sessions | 1-3 sessions | 1 session |
| **Who benefits?** | Strategic goal | End user can verify it | Developers/system |
| **Testable by?** | E2E journeys | User acceptance | Unit tests |

If the beneficiary is "the system" or "developers," it's a task, not a feature. Features are things a human can verify.

### Can I edit the menu plan YAML manually?

Yes — that's the point. The pause between Scope and Finalize exists so you can review and edit the YAML. Adjust priorities, add/remove tasks, refine acceptance criteria, change dependencies.

### What if scope changes during planning?

Edit the brainstorm doc or menu plan directly. If direction changes significantly during brainstorm, just restart brainstorm. If scope shifts during scope phase, edit the YAML before finalizing.

### What's a tracer strategy?

A tracer proves the complete path through all architectural layers with minimal scope. Instead of building database → API → UI sequentially (horizontal), build a minimal flow through all layers first (vertical), then expand.

```
Bad:  Task 1: Build database  →  Task 2: Build API  →  Task 3: Build UI
Good: Task 1: Minimal flow through all layers (tracer)  →  Task 2: Expand
```

---

## Run Cycle

### What do I do if Cook fails?

Cook changes are local and uncommitted. Options:
- **Small fix needed:** Fix the issue and continue
- **Wrong approach:** `git checkout .` to discard all changes, then retry
- **Task too big:** Split into smaller tasks with `bd create`, then start fresh

### Serve keeps rejecting my code — what now?

Rejection is normal and healthy. But repeated rejection usually means:
1. **The task is ambiguous** — update the task description with clearer requirements
2. **Edge cases missed** — address the specific issues Serve flagged
3. **Approach is wrong** — discard and retry with a different approach

If stuck, drop to individual phases: run `/line:cook` alone, review the output yourself, then `/line:serve`.

### How do I handle discoveries mid-task?

**File, don't block.** When you discover a bug, improvement, or new requirement while working:

1. Don't stop your current task
2. Don't act on the discovery
3. Note it — Cook captures findings automatically
4. Continue — Tidy will file findings as tracked issues

This prevents scope creep and keeps context clean.

### What does "headless Claude" mean?

Headless means Claude running as a background process — no interactive terminal, just a prompt in and results out. `/line:serve` uses headless Claude to get a fresh, unbiased review. The reviewer has no memory of writing the code, so it's more objective.

---

## Work Organization

### What if all my tasks are blocked?

Run `/line:plan-audit` to check your dependency graph. Common causes:
- **Circular dependencies** — break the cycle by extracting shared work
- **Missing task** — a blocker that was never created
- **Stale blocker** — a task that's done but wasn't closed (`bd close <id>`)

### How do I manage priorities?

Line Cook uses P0-P4 (numeric, not words):

| Priority | Level | When to use |
|----------|-------|-------------|
| **P0** | Critical | Production broken, security issue |
| **P1** | High | Blocks other work, time-sensitive |
| **P2** | Medium | Standard work (default) |
| **P3** | Low | Nice to have, polish |
| **P4** | Backlog | Maybe someday |

Most tasks should be P2. `/line:prep` auto-selects highest-priority unblocked task.

**Escalate:** `bd update <id> --priority=1`
**Park it:** Move to a Backlog epic — parked tasks are excluded from auto-selection.

### How do I handle scope creep?

Create a bead for the additional work instead of doing it now:

```bash
bd create --title="Also add caching" --type=task --priority=3
# Continue with your current task
```

If scope creep is coming from the task itself being too big, split it:

```bash
bd create --title="Part A" --type=task --parent=<feature-id>
bd create --title="Part B" --type=task --parent=<feature-id>
bd dep add <part-b-id> <part-a-id>
```

### When should I split a task?

Split when:
- It'll take more than one session
- You realize it has multiple independent parts
- You're mid-task and already have shippable progress

Don't split trivially small work — overhead isn't worth it.

---

## Testing

### What's the TDD cycle in Cook?

Cook follows Red-Green-Refactor:

1. **Red** — Write a failing test that describes desired behavior. Taster agent reviews test quality.
2. **Green** — Write minimal code to make the test pass.
3. **Refactor** — Improve code structure while keeping tests green.

Tests must fail before implementation (Red) and pass after (Green). Cook won't close a task with failing tests.

### How do I write good acceptance criteria?

Acceptance criteria should be specific, testable statements from a user perspective:

```
Good: "User can add a book with title and author"
Bad:  "Book adding works"

Good: "Invalid email shows error message"
Bad:  "Error handling"
```

Each criterion maps to one BDD test scenario. Aim for 2-4 criteria per feature.

### What's the difference between TDD and BDD specs?

| | TDD (tasks) | BDD (features) |
|---|---|---|
| **Level** | Unit/function | User scenario |
| **Perspective** | Developer | End user |
| **Format** | Test code | Given-When-Then |
| **Created by** | Finalize | Finalize |
| **Validated by** | Taster agent | Maitre agent |

TDD specs drive implementation. BDD specs validate that the feature works from a user's perspective.

---

## Context & Sessions

### When should I clear context?

- **After planning** — before starting execution
- **After each task** — especially if context is getting long
- **When responses slow down** or Claude forgets earlier details
- **At natural boundaries** — after Tidy pushes work

Trust beads and git. Clearing context costs nothing when your state is persisted.

### What does /compact do?

`/compact` clears the conversation history while preserving a summary. After compacting, run `/line:prep` to reload project state.

### How do I recover after compaction?

Run `/line:prep`. It reloads:
- Project structure from AGENTS.md
- Ready tasks from beads
- Git status

If beads seem missing: `bd sync` to pull from remote.

---

## Advanced

### How do I use /plan-audit?

`/line:plan-audit` checks your bead structure for quality issues:
- **Structural** — orphans, circular dependencies, hierarchy depth
- **Quality** — missing acceptance criteria, priorities, types
- **Health** — stale items, nearly complete features

```bash
/line:plan-audit           # Check open items
/line:plan-audit full      # Include closed items and work verification
/line:plan-audit lc-001    # Check a specific epic and its children
/line:plan-audit --fix     # Auto-fix safe issues (missing priority, etc.)
```

Run periodically — it's cheap and catches drift early.

### When should I use /architecture-audit?

`/line:architecture-audit` analyzes code structure (not beads). Use it:
- Before major refactoring
- At project milestones
- When onboarding to a new codebase
- Quarterly for health checks

It checks coupling, complexity, code smells, and documentation health.

### How do I validate an epic?

When all features of an epic are complete:
1. Run `/line:plate` on each feature first (validates acceptance criteria)
2. Epic-level validation triggers automatically when the last feature closes
3. Critic agent reviews E2E test coverage across features
4. Acceptance report is generated

### What are spices?

Domain-specific addons that enhance Mise planning. Spices load automatically during `/line:mise` when Claude detects relevant project context.

Example: [game-spice](https://github.com/smileynet/game-spice) adds MLP scoping, core loop design, and game planning anti-patterns.

```bash
/plugin install game-spice@line-cook
```

### When should I use Loop vs Run?

| Use `/line:run` | Use `/line:loop` |
|-----------------|------------------|
| Learning the workflow | Comfortable with the workflow |
| Complex or ambiguous tasks | Well-defined, independent tasks |
| Want to review between tasks | Want hands-free batch execution |
| First time with a codebase | Trusted codebase with good tests |

See [Loop Cycle](cycles/loop-cycle.md) for details.
