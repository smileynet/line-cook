# Workflow

> The complete prep → cook → serve → tidy cycle.

Line Cook's workflow provides structure for AI-assisted development. Each phase has a clear purpose, and the cycle ensures work is tracked, reviewed, and persisted.

## Quick Reference

```
/mise → /prep → /cook → /serve → /tidy → /plate
   ↓       ↓       ↓       ↓        ↓        ↓
 plan    sync   execute  review   commit  validate
```

Or run the full cycle:

```
/line:service
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

**Purpose:** Create work breakdown before starting.

**When to use:**
- Starting a new feature or project
- Breaking down complex work
- Planning multiple sessions

**What happens:**
1. Analyze requirements
2. Create menu plan (YAML)
3. Convert to beads
4. Set up dependencies

**Output:** Beads ready for execution

See [Menu Plan Format](../planning/menu-plan-format.md) for details.

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

Assessment: GOOD_TO_GO

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

**Command:** `/line:service`

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
bd update lc-042 --status=pending  # Reset task
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

## Related

- [TDD/BDD Workflow](./tdd-bdd.md) - Testing cycle in cook phase
- [Context Management](./context-management.md) - Managing context
- [Priority and Dependencies](./priorities.md) - What to work on next
- [Scope Management](./scope-management.md) - Handling scope changes
