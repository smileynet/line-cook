# Workflow

> The complete prep → cook → serve → tidy cycle.

Line Cook's workflow provides structure for AI-assisted development. Each phase has a clear purpose, and the cycle ensures work is tracked, reviewed, and persisted.

## Progressive Disclosure

**Load only what you need:**

```bash
# Core concepts (this file)
cat docs/guidance/workflow.md

# Specific topics
cat docs/guidance/tdd-bdd.md           # Testing workflow details
cat docs/guidance/priorities.md        # P0-P4 priority system
cat docs/guidance/scope-management.md  # Handling scope changes
cat docs/guidance/context-management.md # Managing AI context
```

---

## Quick Reference

```
/mise → /prep → /cook → /serve → /tidy → /plate
   ↓       ↓       ↓       ↓        ↓        ↓
 plan    sync   execute  review   commit  validate

Hygiene: /audit (run periodically)
```

Or run the full cycle:

```
/line:run
```

## Work Hierarchy

Line Cook uses a **3-tier hierarchy** for organizing work:

```
Epic (Meal Theme)
├── Feature (Multi-course Meal)
│   ├── Task (Course)
│   └── Task (Course)
└── Feature (Multi-course Meal)
    └── Task (Course)
```

### The Tiers

| Tier | Kitchen Term | Description | Scope |
|------|--------------|-------------|-------|
| **Epic** | Meal Theme | High-level capability area | 3+ sessions |
| **Feature** | Multi-course Meal | User-observable outcome | 1-3 sessions |
| **Task** | Course | Single implementation step | 1 session |

### What Makes a Feature

**A feature is user-observable when a human can verify it works.**

| Criterion | Feature | Task |
|-----------|---------|------|
| **Value** | Delivers visible benefit to user | Supports features, no standalone value |
| **Testable** | User can verify "it works" | Only devs can verify |
| **Perspective** | Human user's viewpoint | System/developer viewpoint |
| **Scope** | End-to-end (vertical slice) | Single layer/component |

**The "Who" Test:** If the beneficiary is "the system" or "developers," it's a task, not a feature.

### Example

```
Epic: User Authentication (Meal Theme: "Italian Night")
├── Feature: Users can log in (Course: Antipasti)
│   ├── Task: Implement login form
│   ├── Task: Add password validation
│   └── Task: Create session management
└── Feature: Users can reset password (Course: Primo)
    ├── Task: Create reset email template
    └── Task: Implement token validation
```

### Creating Hierarchy

```bash
# Create epic
bd create --title="User Authentication" --type=epic --priority=2

# Create features under epic
bd create --title="Users can log in" --type=feature --parent=lc-abc --priority=2

# Create tasks under feature
bd create --title="Implement login form" --type=task --parent=lc-abc.1
```

## The Kitchen Analogy

Restaurant service flow:

1. **Mise** - Plan the menu, prep ingredients
2. **Prep** - Set up station for service
3. **Cook** - Execute orders with TDD
4. **Serve** - Quality check before plating
5. **Tidy** - Clean station, file orders
6. **Plate** - Final presentation check

## Phase: Mise (Planning)

**Command:** `/line:mise`

**Purpose:** Create work breakdown before starting implementation.

Mise en place separates planning into three cognitive phases, each with a natural pause point for review:

```
/brainstorm → /scope → /finalize
(divergent)   (convergent)   (execution prep)
```

### Why Three Phases?

Each phase has a distinct cognitive mode:

| Phase | Mode | Purpose | Output |
|-------|------|---------|--------|
| **Brainstorm** | Divergent | Explore, question, research | `docs/planning/brainstorm-<name>.md` |
| **Scope** | Convergent | Structure, scope, decompose | `docs/planning/menu-plan.yaml` |
| **Finalize** | Execution | Create beads, write test specs | `.beads/` + `tests/features/` + `tests/specs/` |

This prevents premature commitment. Brainstorm expands possibilities before plan narrows to structure. Plan creates a reviewable artifact before finalize commits to tracked work.

### The Sub-Phases

**`/line:brainstorm`** - Divergent thinking
- Asks clarifying questions about the problem
- Explores technical approaches in the codebase
- Identifies risks and unknowns
- Recommends direction with rationale
- Output: `docs/planning/brainstorm-<name>.md`

**`/line:scope`** - Convergent thinking
- Loads brainstorm document (if exists)
- Determines scope (task/feature/epic)
- Creates structured YAML breakdown
- Adds tracer strategy and dependencies
- Output: `docs/planning/menu-plan.yaml`

**`/line:finalize`** - Execution prep
- Validates menu plan exists
- Converts plan to beads with hierarchy
- Creates BDD test specs (`.feature` files)
- Creates TDD test specs (`.md` files)
- Output: Beads + test specifications

### Pause Points

Between each phase, `/mise` pauses for user review:

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━━━
File: docs/planning/brainstorm-reading-cli.md

Ready to proceed to planning phase?
Continue to /line:scope? [Y/n]
```

This allows you to:
- Review the brainstorm document
- Resolve open questions
- Make edits before proceeding
- Abandon if direction is wrong

### When to Use What

| Situation | Command |
|-----------|---------|
| Full planning with review pauses | `/line:mise` |
| Requirements are crystal clear | `/line:mise skip-brainstorm` |
| Just want to explore first | `/line:brainstorm` alone |
| Already have brainstorm, need structure | `/line:scope` alone |
| Already have menu plan, need beads | `/line:finalize` alone |

### Example Flow

```bash
# Full orchestrated flow with pauses
/line:mise

# Skip brainstorm when requirements are clear
/line:mise skip-brainstorm

# Maximum control - run each phase separately
/line:brainstorm
# ... review and refine brainstorm document ...
/line:scope
# ... review and refine menu plan ...
/line:finalize
```

See [Menu Plan Format](../planning/menu-plan-format.md) for YAML structure details.

## Phase: Audit

**Command:** `/line:audit [scope] [--fix]`

**Purpose:** Optional hygiene check for bead structure and quality.

**When to use:**
- Periodically for project health checks
- After major scope changes
- Before milestones or releases

**Scopes:**
- `active` (default) - Check open/in_progress beads
- `full` - All beads including work verification
- `<id>` - Specific bead and hierarchy

**What it checks:**
- Structural: hierarchy depth, orphans, type consistency
- Quality: acceptance criteria, priority, issue_type
- Health: stale items, nearly complete features
- Work verification (full): acceptance docs for closed features

**Output:**

```
AUDIT: Bead Health Check
━━━━━━━━━━━━━━━━━━━━━━━━

Issues: 0 critical, 2 warnings, 3 info
Auto-fixable: 2 (run with --fix)

NEXT STEP: Address findings, or continue with /line:prep
```

## Phase: Prep

**Command:** `/line:prep`

**Purpose:** Sync state and identify ready tasks.

**When to use:**
- Starting a work session
- After context compaction
- Checking what's available

**What happens:**
1. Sync git repository
2. Sync beads with remote
3. Filter for ready tasks (not blocked)
4. Show session summary

**Output:**

```
SESSION: project @ branch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Sync: up to date

Ready: 5 tasks
In progress: 0
Blocked: 2

NEXT TASK:
  lc-042 [P2] Add email verification
```

## Phase: Cook

**Command:** `/line:cook [task-id]`

**Purpose:** Execute task with TDD cycle.

**When to use:**
- After prep shows ready tasks
- When ready to do implementation work

**What happens:**
1. Select task (from arg or auto-select)
2. Claim task (status → in_progress)
3. Break into TodoWrite steps
4. Execute RED-GREEN-REFACTOR cycle
5. Verify all steps complete
6. Close task

**TDD Cycle:**

```
RED      → Write failing test
         → Taster reviews test quality

GREEN    → Implement minimal code
         → Verify tests pass

REFACTOR → Improve code structure
         → Verify tests still pass
```

**Output:**

```
DONE: lc-042 - Add email verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Added email verification with token-based flow

Files changed:
  M internal/auth/verification.go
  A internal/auth/verification_test.go
  M cmd/api/handlers.go

Verification:
  [✓] All todos complete
  [✓] Code compiles
  [✓] Tests pass

NEXT STEP: /line:serve
```

See [TDD/BDD Workflow](./tdd-bdd.md) for details.

## Phase: Serve

**Command:** `/line:serve`

**Purpose:** Review code changes before committing.

**When to use:**
- After cook phase completes
- Before committing work

**What happens:**
1. Show diff of changes
2. Sous-chef agent reviews:
   - Correctness (logic, edge cases)
   - Security (input validation, injection)
   - Style (naming, consistency)
   - Completeness (fully addresses task)
3. Report findings

**Output:**

```
SERVE: Code Review
━━━━━━━━━━━━━━━━━━

Files changed: 3
Lines: +124, -15

SOUS-CHEF REVIEW:
  [✓] Correctness: Logic is sound
  [✓] Security: Input validated
  [✓] Style: Follows project patterns
  [✓] Completeness: Task fully addressed

Assessment: APPROVED

NEXT STEP: /line:tidy
```

## Phase: Tidy

**Command:** `/line:tidy`

**Purpose:** Commit changes and push to remote.

**When to use:**
- After serve phase approves changes
- Before ending session

**What happens:**
1. Create descriptive commit
2. Sync beads
3. Push to remote
4. Verify push success

**Output:**

```
TIDY: Commit and Push
━━━━━━━━━━━━━━━━━━━━━

Commit: feat(auth): add email verification flow
Files: 3 changed, 124 insertions(+), 15 deletions(-)
Beads: synced

✓ Pushed to origin/main

NEXT STEP: /line:prep (for next task) or session complete
```

**Critical:** Work is not complete until pushed.

## Phase: Plate

**Command:** `/line:plate [feature-id]`

**Purpose:** Validate completed feature against acceptance criteria.

**When to use:**
- All tasks for a feature are complete
- Ready for feature sign-off

**What happens:**
1. Load feature acceptance criteria
2. Maître agent reviews:
   - All criteria have tests
   - BDD structure is correct
   - Smoke tests pass
3. Create acceptance report

**Output:**

```
PLATE: Feature Validation
━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: User Authentication
Criteria: 4/4 verified

MAÎTRE REVIEW:
  [✓] Criterion 1: Can log in with valid credentials
  [✓] Criterion 2: Invalid credentials show error
  [✓] Criterion 3: Session persists across requests
  [✓] Criterion 4: Can log out

Assessment: FEATURE_COMPLETE
```

## Complete Cycle

**Command:** `/line:run`

Runs the full cycle: prep → cook → serve → tidy

**When to use:**
- For automated execution
- When workflow is familiar
- For batch processing

**Output:**

```
SERVICE: Full Cycle
━━━━━━━━━━━━━━━━━━━

[1/4] PREP    ✓ synced
[2/4] COOK    ✓ executed
[3/4] SERVE   ✓ reviewed
[4/4] TIDY    ✓ committed

TASK: lc-042 - Add email verification
SUMMARY: Implemented email verification with token flow
```

## Guardrails

Line Cook enforces discipline:

| Guardrail | Enforcement |
|-----------|-------------|
| Sync before work | Prep phase syncs git and beads |
| One task at a time | Cook claims exclusive task |
| Verify before done | Tests must pass |
| File, don't block | Discoveries become beads |
| Push before stop | Tidy pushes to remote |

## Session Boundaries

After `/line:tidy` completes a cycle, decide:

**Continue working:**
```
/line:prep  # Start next task
```

**End session:**
```
# Session is complete (work is pushed)
```

**Clear context:**
```
/compact          # Clear and summarize
/line:prep        # Reload context
```

## Error Recovery

### Prep Fails

```
# Check git status
git status

# Resolve conflicts
git pull --rebase

# Retry
/line:prep
```

### Cook Fails

```
# Task stays in_progress
# Fix the issue, then continue

# Or abandon
git checkout .  # Discard changes
bd update lc-042 --status=open  # Reset task
```

### Serve Fails (Issues Found)

```
# Fix issues identified by sous-chef
# Then retry serve
/line:serve
```

### Tidy Fails

```
# Check push failure
git status
git push

# If remote diverged
git pull --rebase
git push
```

## Workflow Patterns

### Standard Flow

```
/line:prep     # See what's ready
/line:cook     # Execute task
/line:serve    # Review changes
/line:tidy     # Commit and push
```

### Planning Session

```
/line:mise     # Create work breakdown
bd ready       # See created tasks
```

### Feature Completion

```
# After all tasks for feature complete
/line:plate lc-feature
```

### Quick Fix

```
/line:prep     # Sync
/line:cook lc-urgent  # Specific task
/line:serve    # Review
/line:tidy     # Push
```

## TDD/BDD Integration

Testing integrates with the work hierarchy:

| Tier | Testing Style | Purpose |
|------|---------------|---------|
| **Task** | TDD (Red-Green-Refactor) | Unit-level implementation |
| **Feature** | BDD (Given-When-Then) | Acceptance validation |
| **Epic** | Integration validation | End-to-end verification |

### The Kitchen Analogy

**Task = TDD = Individual Prep**
- Each ingredient prepped to specification
- Red: Define what "properly diced" means
- Green: Dice until it matches spec
- Refactor: Improve technique, same result

**Feature = BDD = Course Tasting**
- All prepped items combine into a dish
- Validate the complete dish works together
- Guest perspective: does the course deliver?

**Epic = Multi-course Meal (Full Service)**
- Multiple courses (features) compose the meal
- Each course validated independently
- Full meal validated at service (E2E/smoke tests)
- Critic agent reviews cross-feature integration

### Epic Validation

When the last feature of an epic completes, epic-level validation triggers:

1. **Run smoke tests** - Critical paths work end-to-end
2. **Invoke critic agent** - Reviews E2E test coverage
3. **Generate acceptance report** - `docs/features/<epic-id>-acceptance.md`
4. **Close epic** - After validation passes

See [Epic-Level Testing](./epic-testing.md) for project-type-specific guidance.

### Quality Gates

| Phase | Agent | Checks |
|-------|-------|--------|
| **RED** | Taster | Test isolation, naming, structure |
| **GREEN** | Automatic | Tests pass, builds, no lint errors |
| **REFACTOR** | Sous-chef | Correctness, security, style, completeness |
| **PLATE (Feature)** | Maître | Acceptance criteria, BDD structure |
| **PLATE (Epic)** | Critic | User journeys, E2E coverage, integration |

See [TDD/BDD Workflow](./tdd-bdd.md) for detailed testing guidance.

## Related

- [TDD/BDD Workflow](./tdd-bdd.md) - Testing cycle in cook phase
- [Epic-Level Testing](./epic-testing.md) - E2E and smoke test guidance
- [Context Management](./context-management.md) - Managing context
- [Priority and Dependencies](./priorities.md) - What to work on next
- [Scope Management](./scope-management.md) - Handling scope changes
