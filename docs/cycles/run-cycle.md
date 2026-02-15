# Run Cycle: From Tasks to Shipped Code

**Execute small, ship often.**

The Run Cycle takes a single task from ready to pushed. Strong guardrails — small context windows, TDD, AI peer review, and acceptance criteria — keep execution disciplined. Each phase is a checkpoint you can return to if something goes wrong.

```
Prep (sync) → Cook (execute) → Serve (review) → Tidy (commit)
```

## Quick Reference

| Command | Purpose | Safe to re-run? |
|---------|---------|----------------|
| `/line:run` | Run all four phases | Yes |
| `/line:prep` | Sync git, show ready tasks | Yes (read-only) |
| `/line:cook [id]` | Execute task with TDD | Yes (discard with `git checkout .`) |
| `/line:serve` | AI peer review of changes | Yes |
| `/line:tidy` | Commit, file discoveries, push | Irreversible after push |
| `/line:plate [id]` | Validate completed feature | Yes |
| `/line:close-service [id]` | Validate completed epic | Yes |

---

## Phase 1: Prep

**Purpose:** Get oriented. Sync state and identify what to work on.

```
/line:prep
```

**What happens:**
1. Syncs git repository with remote
2. Syncs beads (issue tracking)
3. Filters for ready tasks (no blockers)
4. Shows session summary with recommended next task

**Example output:**

```
SESSION: reading-cli @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date
Ready: 3 tasks
In progress: 0
Blocked: 1

NEXT TASK:
  lc-003 [P2] Add 'add book' command

NEXT STEP: /line:cook lc-003
```

Prep is read-only — it never changes your code. Safe to run anytime.

---

## Phase 2: Cook

**Purpose:** Execute the task using TDD (Red-Green-Refactor).

```
/line:cook           # auto-selects highest-priority unblocked task
/line:cook lc-003    # work on a specific task
```

**What happens:**
1. Claims the task (status → in_progress)
2. Breaks work into steps
3. Executes the TDD cycle for each step:
   - **Red** — Write failing test (taster agent reviews test quality)
   - **Green** — Write minimal code to pass
   - **Refactor** — Improve while keeping tests green
4. Verifies all steps complete, tests pass, code compiles
5. Closes the task

**Discoveries during execution** are noted but not acted on — the "file, don't block" principle. They become tracked issues during Tidy.

```
Findings (to file in /tidy):
  New tasks:
    - "Add validation for book titles"
  Improvements:
    - "Consider adding timestamps to entries"
```

Cook won't mark a task complete if tests fail or code doesn't compile.

---

## Phase 3: Serve

**Purpose:** AI peer review before committing.

```
/line:serve
```

**What happens:**
1. Collects the diff of changes
2. Polisher agent refines code for clarity and consistency
3. Sous-chef agent reviews (fresh context, no sunk cost):
   - Correctness (logic, edge cases)
   - Security (input validation, injection)
   - Style (naming, consistency)
   - Completeness (task fully addressed)
4. Reports verdict

**Why a separate reviewer matters:** The Claude that wrote the code has sunk cost — it made decisions and might rationalize them. A fresh instance is more objective.

**Verdicts:**

| Verdict | What happens next |
|---------|-------------------|
| **APPROVED** | Proceed to Tidy |
| **NEEDS_CHANGES** | Returns to Cook to fix issues, then re-runs Serve |
| **BLOCKED** | Critical problems — must fix before proceeding |

Rejection is normal and healthy. The Cook → Serve → Cook cycle continues until code is approved.

---

## Phase 4: Tidy

**Purpose:** Commit, file discoveries, push. Nothing is lost.

```
/line:tidy
```

**What happens:**
1. Files discoveries from Cook/Serve as tracked issues
2. Checks if any epics/features are now complete
3. Creates a conventional commit
4. Syncs beads with remote
5. Pushes code to remote

**Work is not complete until pushed.**

```
SESSION SUMMARY
━━━━━━━━━━━━━━━

Task completed:
  lc-003 - Add 'add book' command

Issues filed: 2
  + lc-006: Add validation for book titles [P3]
  + lc-007: Consider dataclass for Book type [P4]

Commit: a1b2c3d
Push: ✓ origin/main
```

---

## Quality Gates

Each phase has built-in quality checks:

| Phase | Agent | What it checks |
|-------|-------|----------------|
| **Cook (Red)** | Taster | Test isolation, naming, structure |
| **Cook (Green)** | Automatic | Tests pass, code compiles, no lint errors |
| **Serve (pre-review)** | Polisher | Code clarity, consistency, maintainability |
| **Serve (review)** | Sous-chef | Correctness, security, style, completeness |
| **Plate (Feature)** | Maitre | Acceptance criteria coverage, BDD structure |
| **Close-service (Epic)** | Critic | User journeys, E2E coverage, integration |

---

## Recovery Points

Each phase is a checkpoint. Nothing is irreversible until push.

| Problem | Recovery |
|---------|----------|
| Prep shows wrong state | `bd sync` to refresh, re-run prep |
| Cook made bad changes | `git checkout .` to discard, retry |
| Task too big | Split into smaller tasks, start fresh |
| Serve rejected code | Fix issues, re-run serve |
| Serve keeps rejecting | Drop to individual phases, debug the issue |
| Tidy commit failed | Check error, fix, retry |
| Tidy push failed | Resolve conflicts, retry push |
| Lost track of where you are | `bd show <id>` for task details, `bd ready` for overview |
| Context too long | Clear context, `/line:prep` to resume |

**The nuclear option:** `git checkout . && git pull && bd sync` — discards local changes but beads survive. You haven't lost your place, just uncommitted work.

---

## Session Boundaries

After Tidy pushes your work, you're at a natural session boundary. Options:

| Option | When |
|--------|------|
| `/line:prep` | Continue with next task |
| `/compact` then `/line:prep` | Context getting long |
| End session | Done for now (work is pushed and safe) |

---

## Feature Completion (/plate)

When all tasks for a feature are complete, validate the feature as a whole:

```
/line:plate              # auto-detect close-eligible features
/line:plate lc-001.1     # validate a specific feature
```

**What Plate does:**
1. Validates acceptance criteria with BDD tests
2. Verifies all child tasks are closed
3. Creates acceptance documentation
4. Closes the feature
5. Checks if parent epic is now complete

Not every task needs Plate. Run it when a feature's tasks are all done and you're ready to close the feature.

---

## Epic Completion (/close-service)

When all features of an epic are plated, validate the epic as a whole:

```
/line:close-service lc-001     # validate a specific epic
```

The Critic agent reviews E2E coverage across features, creates epic acceptance documentation, and merges the epic branch to main.

---

## After Run

- **Next task:** `/line:prep` (or just `/line:run` again)
- **Autonomous execution:** See [Loop Cycle](loop-cycle.md) for hands-free multi-task execution
- **Feature done:** `/line:plate` to validate and close the feature
