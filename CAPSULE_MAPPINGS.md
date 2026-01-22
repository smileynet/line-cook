# Capsule-to-Line-Cook Methodology Mapping

## Overview

This document maps the capsule mission methodology back to line-cook's kitchen-themed workflow (prep → cook → serve → tidy), providing a more robust process while maintaining the original naming convention.

## Core Philosophies

### Line-Cook Original Theme
- **prep** → Mise en place: Sync, load context, show ready tasks
- **cook** → Execute: Do the work with guardrails
- **serve** → Review: Quality check before plating
- **tidy** → Cleanup: Commit, sync, push
- **work** → Full service: Orchestrate complete cycle

### Capsule Mission Theme (Being Mapped)
- **preflight** → Sync, show ready missions
- **execute** → TDD cycle with test quality gates
- **debrief** → Review with automatic code reviewer
- **dock** → Commit with mission log
- **mission-complete** → Feature validation (NEW)
- **mission-orchestrator** → Automated full cycle

---

## Key Methodology Improvements

### 1. Planning Phase (NEW)

**Capsule Concept:** `mission-planning.md`
**Line-Cook Theme:** **Recipe Planning**

#### Tracer Bullet Methodology

Break features into **vertical slices** through all relevant layers, building foundation first and expanding incrementally.

**Key Principles:**
- Each task is a **tracer** that proves one aspect of the feature
- Tracers touch multiple layers (not just one architectural tier)
- Production quality from the start (not throwaway prototypes)
- Build the minimal end-to-end flow first, then expand

**Example: Feature = "Authentication"**

```
Layer-by-Layer (❌ Bad - horizontal slicing):
  Task 1: Build database layer
  Task 2: Build API layer
  Task 3: Build UI layer

Tracer Sequence (✅ Good - vertical slicing):
  Task 1: Minimal auth flow (config → middleware → single API endpoint)
    → Tracer: Proves authentication pattern works end-to-end
  Task 2: Add auth to remaining endpoints
    → Expansion: Apply proven pattern
  Task 3: Add token refresh
    → Expansion: Enhance proven pattern
```

#### Task Graph First

Create a human-readable task graph before creating beads.

**Format:**
```markdown
## Phase N: Phase Name

### Feature N.M: Feature Description

**Acceptance Criteria**:
- User-observable outcome 1
- User-observable outcome 2

**Tracer Strategy**:
- Minimal end-to-end flow: [describe simplest path]
- Layers involved: [list architectural layers]
- Expansion plan: [what gets added after tracer works]

**Tasks** (ordered as tracers):

1. **Task Name** (Priority, dependencies)
   ```
   Tracer: [What layer/integration this proves]
   - Implementation detail 1
   - Implementation detail 2
   Deliverable: What gets created
   Reference: Links to examples
   ```
```

**Benefits:**
- Easy to review and edit before committing to beads
- Visual task dependencies
- Clear tracer progression through layers

#### Tracer vs Prototype vs Spike

| Approach | Use When | Task Type |
|----------|----------|-----------|
| **Tracer** | Building feature foundation | Production task |
| **Prototype** | Testing idea for stakeholders | Demo/throwaway |
| **Spike** | Learning new technology | Research task |

**Most line-cook tasks should be tracers** - production code that builds incrementally.

**Use spike only for:** "Research patterns", "Evaluate approaches"

**Avoid prototypes** - they rarely get rewritten. Build production quality from the start.

---

### 2. Prep Phase Enhancements

**Current Line-Cook:**
- Sync git/beads
- Show ready tasks

**Enhanced Prep (from preflight):**

#### Step 1: Sync Repository
```bash
cd ~/code/<project>
git pull --rebase
```

#### Step 2: Sync Kitchen Order System
```bash
bd sync
```

#### Step 3: Load Kitchen Manual
```bash
# Load work structure (if exists)
cat AGENTS.md | head -100
# Or project-specific docs
cat .claude/CLAUDE.md | head -50
```

#### Step 4: Show Ready Orders
```bash
bd ready
```

#### Step 5: Branching Strategy (NEW)

**Before selecting a task, check the branching context:**

| Task Type | Branching | Rationale |
|-----------|-----------|-----------|
| **Feature** | Create branch: `git checkout -b feature/<feature-id>` | Multi-task work, isolation |
| **Task** | Stay on main | Small, atomic changes |

**Check task type:**
```bash
bd show <task-id>
# If issue_type is "feature", create branch
# If issue_type is "task", stay on main
```

#### Step 6: Completion Output

```
╔══════════════════════════════════════════════════════════════╗
║  PREP COMPLETE                                                ║
╚══════════════════════════════════════════════════════════════╝

Repository: ✓ Up to date with origin/main
Kitchen Order System: ✓ Synced (42 orders)

Ready Orders: 10 P1 items available

Kitchen Roster:
  lc-1bt.1 [P1] Port tmux wrapper from gastown
  lc-520.1 [P1] Set up cobra CLI framework

NEXT STEP: /line:cook to execute a task
```

---

### 3. Cook Phase Enhancements

**Current Line-Cook:**
- Select task
- Plan with TodoWrite
- Execute
- Verify completion

**Enhanced Cook (from execute):**

#### Step 1: Select Task (with branching)

```bash
# Show task details
bd show <task-id>

# Claim the task
bd update <task-id> --status=in_progress

# Add phase comment
bd comments add <task-id> "PHASE: COOK
Status: started"
```

#### Step 2: Load Recipe

```bash
# View mission details
bd show <task-id>
```

#### Step 3: Load Ingredients (Required Context)

Based on task type, load relevant documentation:

**For specific work:**
```bash
cat <reference-file>
```

**For all tasks:**
```bash
cat AGENTS.md | head -50
```

#### Step 4: Execute TDD Cycle (NEW & CRITICAL)

Follow **Red-Green-Refactor** with **automatic test quality review**:

##### RED: Write failing test
```bash
# Write test
go test ./internal/<package> -run <TestName>
# Should FAIL
```

**VERIFY TEST QUALITY (automatic):**
```
Use the test-quality subagent to review tests for <package>
```

The test-quality agent will check:
- Tests are isolated, fast, repeatable
- Clear test names and error messages
- Proper structure (Setup-Execute-Validate-Cleanup)
- No anti-patterns

**Address critical issues before implementing.**

If test-quality agent reports ❌ critical issues, fix tests before GREEN phase.

##### GREEN: Implement minimal code
```bash
# Write implementation
go test ./internal/<package> -run <TestName>
# Should PASS
```

##### REFACTOR: Clean up code
```bash
go test ./internal/<package>
# All tests should PASS
```

#### Step 5: Verify Kitchen Equipment

**MANDATORY before marking complete:**

```bash
# All tests must pass
go test ./...

# Code must build
go build ./...
```

#### Step 6: Completion Output

```
╔══════════════════════════════════════════════════════════════╗
║  COOK COMPLETE                                                 ║
╚══════════════════════════════════════════════════════════════╝

Task: lc-1bt - Port tmux wrapper from gastown
Tests: ✓ All passing
Build: ✓ Successful

Signal: KITCHEN_COMPLETE

NEXT STEP: /line:serve to review the dish
```

#### Kitchen Equipment Checklist

**MANDATORY before emitting KITCHEN_COMPLETE:**

- [ ] All tests pass: `go test ./...`
- [ ] Code builds: `go build ./...`
- [ ] Task deliverable complete
- [ ] Code follows kitchen manual conventions

If any equipment fails, continue cooking until all pass.

---

### 4. Serve Phase Enhancements

**Current Line-Cook:**
- Show changes
- Invoke headless Claude for review
- Process review results

**Enhanced Serve (from debrief):**

#### Step 1: Show the Dish (Telemetry)

```bash
git status
git diff
```

#### Step 2: Review Against Recipe

Load task details and verify deliverables:

```bash
bd show <task-id>
```

Check:
- [ ] Deliverable matches task objective
- [ ] All acceptance criteria met (for features)
- [ ] Tests cover the implementation
- [ ] Code follows kitchen manual conventions

#### Step 3: Verify Kitchen Equipment

```bash
# Run all tests
go test ./...

# Check test coverage (optional)
go test -cover ./internal/<package>
```

#### Step 4: Verify Build Systems

```bash
go build ./...
```

#### Step 5: Code Quality Review

Check for:
- [ ] Clear function/variable names
- [ ] Appropriate comments
- [ ] No TODO/FIXME left behind
- [ ] Error handling present
- [ ] No debug code left in

#### Step 6: Automatic Code Review (NEW)

**Delegate to reviewer subagent:**
```
Use the reviewer agent to review task <task-id>
```

The reviewer agent will:
- Review correctness (logic, edge cases, error handling)
- Check security (input validation, secrets, injection risks)
- Verify style (naming, consistency with codebase patterns)
- Assess completeness (fully addresses the task?)

**Wait for reviewer assessment. Address any critical issues before proceeding to tidy.**

#### Step 7: Completion Output

```
╔══════════════════════════════════════════════════════════════╗
║  SERVE COMPLETE                                                ║
╚══════════════════════════════════════════════════════════════╝

Task: lc-1bt - Port tmux wrapper from gastown
Review: ✓ Passed all checks
Tests: ✓ All passing
Build: ✓ Successful

Telemetry:
  M internal/tmux/tmux.go (+150 lines)
  A internal/tmux/tmux_test.go (+80 lines)

Verdict: READY_FOR_TIDY

Reviewer Feedback:
  ✅ Clear separation of concerns
  ✅ Comprehensive test coverage
  ✅ Proper error handling

Test Quality: <Assessment or "Not assessed">

NEXT STEP: /line:tidy to close kitchen
```

---

### 5. Tidy Phase Enhancements

**Current Line-Cook:**
- File discovered issues as beads
- Review in-progress issues
- Commit changes
- Sync and push
- Record session summary

**Enhanced Tidy (from dock):**

#### Step 1: Close Task Order

```bash
bd close <task-id>
```

#### Step 2: Stage the Dish

```bash
git add -A
git status
```

#### Step 3: Commit with Kitchen Log (NEW)

```bash
git commit -m "<task-id>: <Short objective>

<Detailed description of changes>

Implementation includes:
- Key feature 1
- Key feature 2
- Error handling approach

Deliverable: <What was created>
Tests: <Test summary>
Signal: KITCHEN_COMPLETE"
```

**Commit message format:**
- Subject: `<task-id>: <Short objective>` (50 chars, imperative mood)
- Blank line
- Body: What and why (wrap at 72 chars)
- Implementation details (bullet points)
- Deliverable and test info
- Signal emitted

#### Step 4: Sync Kitchen Order System

```bash
bd sync
```

#### Step 5: Push to Kitchen Ledger

```bash
git pull --rebase
git push
```

#### Step 6: Verify Closing Kitchen

```bash
git status
# Should show: "Your branch is up to date with 'origin/main'"
```

#### Step 7: Completion Output

**MANDATORY: Task is NOT complete until `git push` succeeds.**

```
╔══════════════════════════════════════════════════════════════╗
║  KITCHEN CLOSED                                                ║
╚══════════════════════════════════════════════════════════════╝

Task: lc-1bt - Port tmux wrapper from gastown
Status: ✓ Closed
Commit: ✓ Created (<commit-hash>)
Push: ✓ Successful

Changes:
  M internal/tmux/tmux.go (+150 lines)
  A internal/tmux/tmux_test.go (+80 lines)

Deliverable: internal/tmux/tmux.go skeleton
Tests: 4 tests passing (85% coverage)
Build: Successful

Reviewer Feedback:
  ✅ Clear separation of concerns
  ✅ Comprehensive test coverage
  ✅ Proper error handling

Test Quality: <Assessment or "Not assessed">

Kitchen closed! Ready for next order.
```

**Note:** Reviewer and test quality feedback appear in tidy report only, not in commit message.

#### Closing Checklist

**MANDATORY before considering task complete:**

- [ ] All tests pass: `go test ./...`
- [ ] Code builds: `go build ./...`
- [ ] Task closed: `bd close <task-id>`
- [ ] Changes committed: `git commit`
- [ ] Kitchen Order System synced: `bd sync`
- [ ] Changes pushed: `git push`
- [ ] Status clean: `git status` shows "up to date"

**Task is NOT complete until ALL checkboxes are checked.**

---

### 6. NEW: Feature Complete Phase (Dessert Service)

**Capsule Concept:** `mission-complete.md`
**Line-Cook Theme:** **Dessert Service** - Feature validation

Run this when **all tasks for a feature are complete**.

#### When to Use

After completing all tasks under a feature bead:
- All child tasks are closed
- Feature is ready for validation and documentation

#### Process

##### Step 1: Verify All Tasks Complete

```bash
bd show <feature-id>
```

Check:
- [ ] All child tasks are closed
- [ ] All acceptance criteria defined
- [ ] Feature is ready for validation

##### Step 2: Run All Tests

```bash
# Unit tests (TDD)
go test ./...

# Feature tests (BDD)
go test ./internal/<package> -run TestFeature -v

# Build verification
go build ./...
```

**All tests must pass before proceeding.**

##### Step 3: Verify BDD Test Quality (NEW)

**Check BDD tests meet quality bar (automatic):**
```
Use the bdd-quality subagent to review feature tests for <package>
```

The BDD quality agent will check:
- All acceptance criteria have tests
- Tests use Given-When-Then structure
- Tests map to acceptance criteria
- User perspective documented
- Error scenarios included

**Address critical issues before proceeding.**

If BDD quality agent reports ❌ critical issues, fix tests before continuing.

##### Step 4: Run CLI Smoke Tests (if applicable)

```bash
# If feature has CLI smoke tests
make smoke-test

# Or run individually
./scripts/smoke-test-<feature>.sh
```

**Skip this step if feature has no CLI interface.**

##### Step 5: Update Changelog

```bash
# Edit CHANGELOG.md
# Add feature to Unreleased section
```

**Format:**
```markdown
## [Unreleased]

### Added
- <Feature description>. <User benefit explanation>.
  - Key capability 1
  - Key capability 2
  - Key capability 3
```

##### Step 6: Create Feature Report (NEW)

```bash
# Create feature acceptance document
vim docs/features/feature-<feature-id>-acceptance.md
```

**Document:**
- Feature description
- Each acceptance criterion with test mapping
- Test results (unit, BDD, CLI)
- Quality assessment
- Feature sign-off checklist

##### Step 7: Commit Documentation

```bash
git add CHANGELOG.md
git add docs/features/feature-<feature-id>-acceptance.md
git commit -m "docs: Feature <feature-id> acceptance report

Complete acceptance report for Feature <feature-id>:
- All acceptance criteria validated
- BDD tests: <N> passing
- CLI smoke tests: <N> passing (if applicable)
- Coverage: <X>%

Updated CHANGELOG.md with feature details.

Feature complete. Ready for integration."

git push
```

##### Step 8: Close Feature Bead

**IMPORTANT: Close feature bead AFTER pushing documentation.**

```bash
bd close <feature-id>
bd sync
git add .beads/issues.jsonl
git commit -m "chore: close feature <feature-id>

Feature <feature-id> complete and documented."
git push
```

This ensures:
- Documentation is committed before bead closure
- Bead closure is committed and synced to remote
- No orphaned closed beads without documentation

##### Step 9: Completion Output

```
╔══════════════════════════════════════════════════════════════╗
║  DESSERT SERVICE COMPLETE                                       ║
╚══════════════════════════════════════════════════════════════╝

Feature: <feature-id> - <name>
Status: ✓ Closed and documented

Tests:
  Unit: <N> passing
  BDD: <N> passing
  CLI: <N> passing (if applicable)
  Coverage: <X>%

Feature Report: docs/features/feature-<feature-id>-acceptance.md

Ready for: <Next integration step>

Next Feature: <next-feature-id>
```

---

### 7. NEW: Kitchen Orchestrator (Full Service)

**Capsule Concept:** `mission-orchestrator.md`
**Line-Cook Theme:** **Full Service** - Automated workflow

You are the Kitchen Manager orchestrating complete service cycles: prep → cook → serve → tidy → dessert (feature-complete).

#### Your Role

Coordinate the full kitchen lifecycle:
1. Running prep checks
2. Delegating cooking to chef subagent
3. Reviewing dishes in serve phase
4. Tidying the kitchen
5. Serving dessert when features complete

**CRITICAL: Always proceed through all phases to closing unless a failure condition is encountered.**

#### Failure Conditions (STOP execution)

- Tests fail (`go test ./...` returns non-zero)
- Build fails (`go build ./...` returns non-zero)
- Reviewer blocks with ❌ Not ready
- BDD quality blocks with ❌ Critical issues
- Git operations fail (conflicts, push failures)

**If a failure condition occurs:**
```
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  SERVICE ABORTED                                           ║
╚══════════════════════════════════════════════════════════════╝

Phase: <phase where failure occurred>
Failure: <specific failure condition>

Details:
<error output or reviewer feedback>

Next Steps:
1. <specific action to resolve>
2. <specific action to resolve>
3. Re-run service after fixes

Task Status: OPEN (not closed, not committed)
```

**Otherwise: ALWAYS continue through all phases to completion.**

#### Full Service Cycle

##### Phase 1: Prep

```bash
git pull --rebase
bd sync
bd ready
```

Present kitchen roster and ask which task to execute.

**Branching Strategy:**
- **Tasks**: Work on `main` directly (small, atomic changes)
- **Features**: Create git branch first (multi-task work)

```bash
# For feature beads, create branch:
git checkout -b feature/<feature-id>

# For task beads, stay on main:
# (no branch needed)
```

##### Phase 2: Cook

Delegate to chef subagent:

```
Use the chef agent to execute task <task-id>
```

Wait for chef to emit KITCHEN_COMPLETE signal.

##### Phase 3: Serve

Review the dish:

```bash
git status
git diff
bd show <task-id>
go test ./...
go build ./...
```

Delegate to sous-chef (reviewer) subagent:

```
Use the reviewer agent to review task <task-id>
```

Wait for reviewer assessment. Address any critical issues before proceeding to tidy.

Check against recipe:
- [ ] Deliverable matches objective
- [ ] All tests pass
- [ ] Code builds
- [ ] No debug code left behind
- [ ] Reviewer approved (✅ Ready to tidy)

##### Phase 4: Tidy

```bash
bd close <task-id>
git add -A
git commit -m "<task-id>: <objective>

<details>

Deliverable: <what was created>
Tests: <test summary>
Signal: KITCHEN_COMPLETE"

bd sync
git pull --rebase
git push
```

Verify tidy:
```bash
git status
# Should show: "Your branch is up to date with 'origin/main'"
```

##### Phase 5: Dessert Service (NEW - Feature Completion Check)

After tidying, check if this task completed a feature:

```bash
bd show <task-id>
```

**If task has a parent feature AND all sibling tasks are closed:**

1. Run feature validation:
   ```bash
   go test ./...
   go test ./internal/<package> -run TestFeature -v
   ```

2. Delegate to sommelier (BDD quality) subagent:
   ```
   Use the bdd-quality agent to review feature tests for <package>
   ```

3. Wait for BDD quality assessment. Address any critical issues.

4. If BDD tests pass quality bar, proceed with dessert service:
   - Create feature acceptance documentation
   - Update CHANGELOG.md
   - Close feature bead
   - Commit and push feature report

**If task is standalone task or feature has remaining tasks:**
- Skip to Kitchen Report below

#### Kitchen Report

After successful tidy, file a kitchen report:

```markdown
# Kitchen Report: <task-id>

## Objective
<task objective>

## Service Summary
- Phase 1 (Prep): ✓ Complete
- Phase 2 (Cook): ✓ Complete - <N> files changed
- Phase 3 (Serve): ✓ Passed all checks
- Phase 4 (Tidy): ✓ Successfully closed

## Deliverables
<list files created/modified>

## Test Results
- Tests: <N> passing
- Coverage: <percentage if available>
- Build: Successful

## Review
Reviewer: <approved|needs_changes>
Test Quality: <assessment>

## Signal
KITCHEN_COMPLETE

## Next Service
Ready for next order. <N> P1 items available.
```

---

## Quality Gates Summary

### Automatic Quality Checks

| Phase | Quality Gate | Automatic? |
|-------|--------------|------------|
| **Cook (RED)** | Test quality review | ✅ Yes (test-quality agent) |
| **Serve** | Code review | ✅ Yes (reviewer agent) |
| **Dessert** | BDD test quality | ✅ Yes (bdd-quality agent) |

### Manual Quality Gates

| Phase | Quality Gate | Manual Check |
|-------|--------------|--------------|
| **Cook** | Tests pass | `go test ./...` |
| **Cook** | Build succeeds | `go build ./...` |
| **Serve** | Code quality checklist | Manual review |
| **Tidy** | Push succeeds | `git push` |
| **Dessert** | CLI smoke tests | `make smoke-test` |

---

## Output Formats Summary

### Phase Completion Signals

```
╔══════════════════════════════════════════════════════════════╗
║  <PHASE> COMPLETE                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Abort Signal

```
╔══════════════════════════════════════════════════════════════╗
║  ⚠️  SERVICE ABORTED                                           ║
╚══════════════════════════════════════════════════════════════╝
```

### Epic/Feature Completion Banner

```
═════════════════════════════════════════════
  FEATURE COMPLETE: <feature-id> - <feature-title>
═════════════════════════════════════════════

Tasks completed (<count>):
  ✓ <id>: <title>
  ✓ <id>: <title>
  ✓ <id>: <title>
  ...

Impact:
  <1-2 sentence description of what capability/improvement is now complete>

═════════════════════════════════════════════
```

---

## Commit Message Format

### Task Completion

```
<task-id>: <Short objective> (50 chars, imperative)

<Detailed description of changes>

Implementation includes:
- Key feature 1
- Key feature 2
- Error handling approach

Deliverable: <What was created>
Tests: <Test summary>
Signal: KITCHEN_COMPLETE
```

### Feature Documentation

```
docs: Feature <feature-id> acceptance report

Complete acceptance report for Feature <feature-id>:
- All acceptance criteria validated
- BDD tests: <N> passing
- CLI smoke tests: <N> passing (if applicable)
- Coverage: <X>%

Updated CHANGELOG.md with feature details.

Feature complete. Ready for integration.
```

### Bead Closure

```
chore: close feature <feature-id>

Feature <feature-id> complete and documented.
```

---

## Branching Strategy

| Task Type | Branch | Workflow |
|-----------|--------|----------|
| **Task** | `main` | Small, atomic changes directly to main |
| **Feature** | `feature/<feature-id>` | Multi-task work on feature branch |

**Feature Branch Workflow:**
1. Create branch before starting first task
2. Complete all tasks on branch
3. Run dessert service (feature-complete) on branch
4. Create PR or merge to main (manual step - review required)

---

## Agent Naming (Kitchen Theme)

| Capsule Agent | Line-Cook Agent | Role |
|---------------|------------------|------|
| pilot | chef | Executes the task |
| reviewer | sous-chef | Reviews code changes |
| test-quality | quality-control | Reviews test quality |
| bdd-quality | sommelier | Reviews feature test quality |
| mission-orchestrator | kitchen-manager | Orchestrates full service |

---

## Implementation Checklist

To implement these improvements in line-cook:

### Phase 1: Core Workflow Updates

- [ ] Update `prep.md` with branching strategy and kitchen manual loading
- [ ] Update `cook.md` with TDD cycle and automatic test-quality review
- [ ] Update `serve.md` with automatic reviewer subagent
- [ ] Update `tidy.md` with kitchen log commit format

### Phase 2: New Commands

- [ ] Create `plan.md` for recipe planning (tracer bullet methodology)
- [ ] Create `dessert.md` for feature completion and validation
- [ ] Update `work.md` as kitchen-manager orchestrator

### Phase 3: Subagents

- [ ] Define test-quality agent (quality-control)
- [ ] Define reviewer agent (sous-chef)
- [ ] Define bdd-quality agent (sommelier)
- [ ] Define chef agent (task execution)
- [ ] Define kitchen-manager agent (full orchestration)

### Phase 4: Documentation

- [ ] Update AGENTS.md with new terminology
- [ ] Update README.md with new workflow
- [ ] Create feature acceptance template

---

## Comparison Summary

| Aspect | Line-Cook Original | Line-Cook Enhanced (from Capsule) |
|--------|-------------------|-----------------------------------|
| **Planning** | Direct to beads | Task graph first, tracer methodology |
| **Prep** | Sync, show tasks | + Branching strategy, load kitchen manual |
| **Cook** | TodoWrite execution | + TDD cycle, automatic test-quality review |
| **Serve** | Headless Claude review | + Automatic reviewer subagent, checklist |
| **Tidy** | File beads, commit, push | + Kitchen log format, include review feedback |
| **Feature Completion** | Epic closure in tidy | + Dessert phase: BDD quality, docs, changelog |
| **Orchestration** | Manual work command | + Kitchen-manager with automatic error handling |
| **Quality Gates** | Manual only | + Automatic agents for test quality, code review, BDD quality |

---

## Notes

- Maintain line-cook's kitchen theming throughout
- All phases use kitchen terminology (prep, cook, serve, tidy, dessert)
- Agents use kitchen role names (chef, sous-chef, sommelier, quality-control, kitchen-manager)
- Keep the "file, don't block" philosophy from original line-cook
- Enhanced methodology adds quality gates without losing velocity
