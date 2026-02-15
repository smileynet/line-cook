# Mise Cycle: From Ideas to Tasks

**Think big, then break it down.**

The Mise Cycle turns unstructured ideas into well-scoped, dependency-ordered tasks ready for execution. It runs in three phases, each producing a reviewable artifact with a pause point between them.

```
Brainstorm (diverge) → Scope (converge) → Finalize (commit)
```

## Quick Reference

| Command | Purpose | Output | Skip when... |
|---------|---------|--------|--------------|
| `/line:mise` | Run all three phases with pauses | All below | Never (orchestrator) |
| `/line:brainstorm` | Explore the problem space | `docs/planning/brainstorm-<name>.md` | Requirements already clear |
| `/line:scope` | Create structured breakdown | `docs/planning/menu-plan.yaml` | Already have a menu plan |
| `/line:finalize` | Convert plan to tracked work | Beads + test specs | Already have beads |

**Skip brainstorm:** `/line:mise skip-brainstorm`
**Run phases individually** for maximum control.

---

## Phase 1: Brainstorm

**Mode:** Divergent thinking — expand possibilities before narrowing.

Brainstorm asks clarifying questions, explores approaches, identifies risks, and recommends a direction. The output is a markdown document capturing everything explored.

**What happens:**
1. Claude asks clarifying questions about the problem
2. Explores technical approaches in the codebase
3. Identifies risks and unknowns
4. Recommends direction with rationale

**Output:** `docs/planning/brainstorm-<name>.md`

**Example interaction:**

```
/line:brainstorm

BRAINSTORM: Reading List CLI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Questions:
  1. What info do you want to track per book?
  2. Where should data live?
  3. Is this just for you, or will others use it?

You: Just for me. Title, author, finished status. Local file.

BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━
File: docs/planning/brainstorm-reading-cli.md
Open questions: 0

Continue to /line:scope? [Y/n]
```

**When to skip:** Requirements are already clear, you've done your own research, or you're working from an existing spec.

---

## Phase 2: Scope

**Mode:** Convergent thinking — structure the work into a hierarchy.

Scope takes the brainstorm (or your requirements) and produces a YAML menu plan with epics, features, tasks, dependencies, and acceptance criteria.

**What happens:**
1. Loads brainstorm document (if exists)
2. Determines scope (task, feature, or epic)
3. Creates structured YAML breakdown
4. Adds tracer strategy and dependencies

**Output:** `docs/planning/menu-plan.yaml`

**Example menu plan:**

```yaml
phases:
  - id: phase-1
    title: "Phase 1: Core CLI"
    features:
      - id: feature-1.1
        title: "Basic reading list management"
        user_story: "As a reader, I want to track books so I know what I've read"
        acceptance_criteria:
          - "Can add books with title and author"
          - "Can list all books with finished status"
          - "Can mark books as finished"
        tasks:
          - title: "Implement JSON file storage"
            priority: 1
            tdd: true
          - title: "Add 'add book' command"
            priority: 2
            depends_on: ["Implement JSON file storage"]
```

**Review checklist** before proceeding:
- Are task priorities correct?
- Are dependencies right?
- Are acceptance criteria specific enough?
- Is anything missing or over-scoped?

Edit the YAML directly — it's your plan.

---

## Phase 3: Finalize

**Mode:** Execution prep — convert the plan into tracked work items.

Finalize reads the menu plan and creates beads (tracked issues) with proper hierarchy and dependencies, plus test specifications.

**What happens:**
1. Validates menu plan exists
2. Creates beads with hierarchy (epic → feature → task)
3. Sets up dependencies between tasks
4. Creates BDD test specs (`.feature` files)
5. Creates TDD test specs (`.md` files)

**Output:**

```
MISE COMPLETE
━━━━━━━━━━━━━━━━━━━

Beads Created:
  Epics: 1, Features: 1, Tasks: 4

Test Specs Created:
  BDD: 1 .feature file
  TDD: 4 .md files

Available tasks:
  lc-002 [P1] Implement JSON file storage

NEXT STEP: Clear context, then /line:prep
```

**What was created:**

```
lc-001: Core CLI (epic)
├── lc-001.1: Basic reading list management (feature)
│   ├── lc-002: Implement JSON file storage [P1]
│   ├── lc-003: Add 'add book' command [P2] (blocked by lc-002)
│   ├── lc-004: Add 'list books' command [P2] (blocked by lc-002)
│   └── lc-005: Add 'done' command [P2] (blocked by lc-002)
```

---

## Work Hierarchy

Mise creates a 3-tier hierarchy for organizing work:

| Tier | What it is | Scope | Testing |
|------|-----------|-------|---------|
| **Epic** | High-level capability area | 3+ sessions | E2E / smoke tests |
| **Feature** | User-observable outcome | 1-3 sessions | BDD acceptance tests |
| **Task** | Single implementation step | 1 session | TDD unit tests |

**The "Who" Test:** If the beneficiary is "the system" or "developers," it's a task, not a feature. Features are things a human can verify.

See [beads reference](../reference/beads.md) for hierarchy commands.

---

## Review Points

`/line:mise` pauses between each phase so you can review and adjust:

| Pause | What to check |
|-------|---------------|
| After brainstorm | Direction correct? Open questions resolved? |
| After scope | Tasks right-sized? Dependencies correct? Acceptance criteria specific? |
| After finalize | Beads look right? Ready to start execution? |

**Tip:** Edit artifacts directly between pauses. The brainstorm doc and menu plan YAML are yours to modify.

---

## After Mise

Planning is done. Before starting execution:

1. **Clear your context** — new conversation or `/compact`
2. **Start fresh** with `/line:prep`

This ensures execution gets a clean context window focused on the task at hand, not planning discussion.

**Next:** [Run Cycle](run-cycle.md) for execution.
