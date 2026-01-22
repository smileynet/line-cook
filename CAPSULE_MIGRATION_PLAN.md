# Capsule to Line-Cook Migration Plan

## Overview

Comprehensive plan for ingesting all capsule prompts, guidance docs, and methodology into line-cook using kitchen theming.

## Phase 1: Core Command Updates (Existing Commands)

### 1.1 Update `/line:prep` (commands/prep.md)

**Source:** capsule/prompts/preflight.md

**Changes:**
- Add "Load Kitchen Manual" step (from capsule's preflight)
- Add branching strategy check (feature vs task)
- Update output format with phase completion banner
- Add kitchen roster terminology

**Translation Mapping:**
- `preflight` → `prep` (kitchen preparation)
- `mission` → `order` (work item)
- `mission roster` → `kitchen roster` (ready orders)

**Implementation:**
```markdown
### Step 3: Load Kitchen Manual
```bash
# Load work structure
cat AGENTS.md | head -50
```

### Step 5: Branching Strategy
**Before selecting a task, check the branching context:**

| Task Type | Branching | Rationale |
|-----------|-----------|-----------|
| **Feature** | Create branch: `git checkout -b feature/<feature-id>` | Multi-task work, isolation |
| **Task** | Stay on main | Small, atomic changes |
```

### 1.2 Update `/line:cook` (commands/cook.md)

**Source:** capsule/prompts/execute.md

**Changes:**
- Add "Load Recipe" step (from capsule's execute)
- Add "Load Ingredients" step (load context docs)
- **CRITICAL:** Add TDD cycle with automatic test-quality review
- Add kitchen equipment verification checklist
- Update output format with phase completion banner

**Translation Mapping:**
- `execute` → `cook` (cooking phase)
- `mission brief` → `recipe` (task details)
- `mission objective` → `dish` (what's being cooked)
- `telemetry` → `ingredients` (context/docs)
- `flight systems` → `kitchen equipment` (tests, build)
- `MISSION_COMPLETE` → `KITCHEN_COMPLETE`

**New TDD Cycle Section:**
```markdown
### Step 4: Execute TDD Cycle (NEW & CRITICAL)

Follow **Red-Green-Refactor** with **automatic test quality review**:

##### RED: Write failing test
```bash
# Write test
go test ./internal/<package> -run <TestName>
# Should FAIL
```

**VERIFY TEST QUALITY (automatic):**
```
Use the quality-control subagent to review tests for <package>
```

The quality-control agent will check:
- Tests are isolated, fast, repeatable
- Clear test names and error messages
- Proper structure (Setup-Execute-Validate-Cleanup)
- No anti-patterns

**Address critical issues before implementing.**

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
```

### 1.3 Update `/line:serve` (commands/serve.md)

**Source:** capsule/prompts/debrief.md

**Changes:**
- Keep headless Claude invocation (already implemented)
- Add automatic reviewer subagent delegation (NEW)
- Add review checklist (from debrief)
- Include reviewer feedback in report
- Update output format

**Translation Mapping:**
- `debrief` → `serve` (presenting the dish)
- `telemetry` → `dish` (changes to review)
- `mission brief` → `recipe` (task requirements)
- `flight systems` → `kitchen equipment` (tests, build)
- `READY_FOR_DOCK` → `READY_FOR_TIDY`

**New Automatic Review:**
```markdown
### Step 6: Automatic Code Review (NEW)

**Delegate to sous-chef (reviewer) subagent:**
```
Use the sous-chef agent to review task <task-id>
```

The sous-chef agent will:
- Review correctness (logic, edge cases, error handling)
- Check security (input validation, secrets, injection risks)
- Verify style (naming, consistency with codebase patterns)
- Assess completeness (fully addresses the task?)

**Wait for reviewer assessment. Address any critical issues before proceeding to tidy.**
```

### 1.4 Update `/line:tidy` (commands/tidy.md)

**Source:** capsule/prompts/dock.md

**Changes:**
- Update commit message format (from dock's kitchen log)
- Include reviewer and test quality feedback in report
- Update closing checklist
- Add "Verify Closing Kitchen" step

**Translation Mapping:**
- `dock` → `tidy` (cleanup phase)
- `mission log` → `kitchen log` (commit message format)
- `capsule docked` → `kitchen closed`
- `mission report` → `kitchen report`

**New Commit Format:**
```markdown
### Step 3: Commit with Kitchen Log (NEW)

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
```

### 1.5 Update `/line:work` (commands/work.md)

**Source:** capsule/prompts/mission-orchestrator.md

**Changes:**
- Update as "Kitchen Manager" orchestrator
- Add automatic feature completion check (NEW)
- Add quality gates and failure conditions
- Update agent delegation terminology

**Translation Mapping:**
- `mission-orchestrator` → `kitchen-manager`
- `pilot` → `chef` (task execution)
- `reviewer` → `sous-chef` (code review)
- `test-quality` → `quality-control` (test quality)
- `bdd-quality` → `sommelier` (feature test quality)

**New Feature Completion Check:**
```markdown
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
   Use the sommelier agent to review feature tests for <package>
   ```

3. Wait for BDD quality assessment. Address any critical issues.

4. If BDD tests pass quality bar, proceed with dessert service:
   - Create feature acceptance documentation
   - Update CHANGELOG.md
   - Close feature bead
   - Commit and push feature report
```

---

## Phase 2: New Commands

### 2.1 Create `/line:plan` (commands/plan.md)

**Source:** capsule/prompts/mission-planning.md

**Purpose:** Recipe planning with tracer bullet methodology

**Translation Mapping:**
- `mission planning` → `recipe planning`
- `mission` → `dish` (feature)
- `task` → `course` (implementation step)
- `tracer bullet` → `tracer dish` (vertical slice)
- `task graph` → `menu plan`

**Key Features:**
- Task graph first (human-readable planning)
- Tracer bullet methodology
- Convert menu plan to beads script
- Feature→Course hierarchy (already exists in line-cook)
- Epic→Feature→Task hierarchy (keep existing)

**Structure:**
```markdown
# Recipe Planning Prompt

Use this prompt to plan dishes before cooking.

## Process

### Step 1: Understand the Order
Ask clarifying questions:
- What problem are we solving?
- What does success look like?
- Are there any constraints or requirements?
- What's the scope (MVP vs full feature)?

### Step 2: Create Menu Plan
Build a structured breakdown using **tracer dish methodology**.

### Step 3: Convert Menu Plan to Beads
Once the menu plan is approved, convert it to beads.

### Tracer Dish Approach
Build vertical slices that touch all relevant layers, building foundation first and expanding incrementally.
```

### 2.2 Create `/line:dessert` (commands/dessert.md)

**Source:** capsule/prompts/mission-complete.md

**Purpose:** Feature validation and documentation when all tasks complete

**Translation Mapping:**
- `mission complete` → `dessert service` (feature completion)
- `feature` → `multi-course meal` (feature)
- `BDD tests` → `tasting menu` (feature tests)
- `CLI smoke tests` → `restaurant inspection` (end-to-end validation)

**Key Features:**
- Verify all tasks complete
- Run all tests (unit + BDD + CLI)
- BDD quality review (sommelier agent)
- Update CHANGELOG.md
- Create feature acceptance documentation
- Close feature bead

**Structure:**
```markdown
# Dessert Service - Feature Completion

Run this when all courses (tasks) for a feature are complete.

## Process

### Step 1: Verify All Courses Complete
Check:
- [ ] All child tasks are closed
- [ ] All acceptance criteria defined
- [ ] Feature is ready for validation

### Step 2: Run All Tests
```bash
# Unit tests (TDD)
go test ./...

# Feature tests (BDD)
go test ./internal/<package> -run TestFeature -v

# Build verification
go build ./...
```

### Step 3: Verify BDD Test Quality (NEW)
**Check BDD tests meet quality bar (automatic):**
```
Use the sommelier agent to review feature tests for <package>
```

### Step 4: Run Restaurant Inspection (if applicable)
CLI smoke tests for user-facing features

### Step 5: Update Menu Changelog
Update CHANGELOG.md with feature

### Step 6: Create Feature Report
Document feature acceptance results

### Step 7: Close Feature Bead
After documentation is committed
```

---

## Phase 3: Guidance Documentation

### 3.1 Create `docs/guidance/tracer-dishes.md`

**Source:** capsule/docs/guidance/tracer-bullets.md

**Purpose:** Guidelines for using tracer dish development effectively

**Translation Mapping:**
- `tracer bullets` → `tracer dishes`
- `tracer bullet` → `tracer dish`
- `prototype` → `tasting plate` (demo/throwaway)
- `spike` → `kitchen experiment` (research)
- `feature` → `multi-course meal`
- `task` → `course`

**Structure:**
```markdown
# Tracer Dish Development

Guidelines for using tracer dish development in line-cook.

## What Are Tracer Dishes?

**Tracer dishes** are development approach where you build a minimal, end-to-end implementation that touches all layers of your system. Like a tasting menu that reveals the chef's path through the meal, tracer code illuminates path through your architecture.

**Key principle**: Build a complete vertical slice through all system layers, then expand functionality incrementally.

## Core Characteristics

1. **Not disposable** - Written for production, not throwaway
2. **Production quality** - Includes error handling, follows conventions
3. **Not fully functional** - Minimal feature set, expanded later
4. **End-to-end** - Touches all architectural layers
5. **Foundation for growth** - Base for final menu item

### Tracer Dish vs Tasting Plate vs Kitchen Experiment

| Aspect | Tracer Dish | Tasting Plate | Kitchen Experiment |
|--------|-------------|---------------|-------------------|
| Purpose | Build foundation | Demo idea | Research/learn |
| Lifespan | Production code | Disposable | Disposable |
| Quality | Production standards | Quick & dirty | Minimal code |
| Scope | End-to-end slice | Focused demo | Investigation |
| Error handling | Full | Minimal/none | None |
| Tests | Yes | Optional | No |
| Architecture | Follows standards | Shortcuts OK | Any approach |
```

### 3.2 Create `docs/guidance/test-prep.md`

**Source:** capsule/docs/guidance/test-writing/README.md

**Purpose:** Core principles for writing quality tests

**Translation Mapping:**
- `test writing` → `test prep`
- `unit tests` → `individual prep` (TDD)
- `feature tests` → `course tasting` (BDD)
- `CLI smoke tests` → `restaurant inspection`
- `test quality` → `prep quality`

**Structure:**
```markdown
# Test Prep Guidelines

Core principles for writing quality tests in line-cook.

## Test Quality Criteria

### ✅ Good Individual Prep (TDD) Are:
1. **Isolated** - Each test runs independently
2. **Fast** - Completes in milliseconds (< 100ms)
3. **Repeatable** - Same result every time
4. **Self-contained** - All setup within test
5. **Focused** - Tests one thing
6. **Clear** - Intent obvious from reading

### ✅ Good Course Tastings (BDD) Are:
1. **Acceptance-Driven** - Maps to feature acceptance criteria
2. **User-Centric** - Tests from user perspective
3. **Scenario-Based** - Uses Given-When-Then structure
4. **Real-World** - Tests actual usage patterns
5. **Comprehensive** - Includes error scenarios
6. **Self-Documenting** - Test names explain what's validated
```

### 3.3 Create `docs/guidance/tdd-bdd.md`

**Source:** capsule/docs/guidance/work-structure/tdd-bdd.md

**Purpose:** How TDD and BDD integrate with Feature→Task hierarchy

**Translation Mapping:**
- `TDD` → `Individual Prep` (task-level)
- `BDD` → `Course Tasting` (feature-level)
- `feature` → `multi-course meal`
- `task` → `course`
- `unit tests` → `individual prep tests`
- `feature tests` → `course tasting tests`

**Structure:**
```markdown
# TDD/BDD Integration

How TDD and BDD integrate with Feature→Task hierarchy.

## Core Principles

**TDD (Test-Driven Development)** = Course-level implementation
**BDD (Behavior-Driven Development)** = Multi-course meal validation

```
Epic: Meal Theme (Mission Lifecycle)
├── Feature: Appetizer Course (Execute commands in tmux sessions) (BDD)
│   ├── Course: Port tmux wrapper (TDD)
│   ├── Course: Implement session creation (TDD)
│   └── Course: Implement command injection (TDD)
└── Feature: Main Course (Run missions in worktrees) (BDD)
    └── ...
```
```

### 3.4 Create `docs/guidance/kitchen-logs.md`

**Source:** capsule/docs/guidance/commit-messages.md

**Purpose:** Guidelines for writing clear, consistent commit messages

**Translation Mapping:**
- `commit messages` → `kitchen logs`
- `mission commits` → `order completion logs`
- `mission ID` → `order ID`

**Structure:**
```markdown
# Kitchen Log Guide

Guidelines for writing clear, consistent kitchen logs (commit messages).

## Format

```
<type>: <description>

[optional body]

[optional footer]
```

## Order Completion Logs

For course/feature completion, use order ID as prefix:

```
<order-id>: <Short objective>

<Detailed description of changes>

Implementation includes:
- Key feature 1
- Key feature 2
- Error handling approach

Deliverable: <What was created>
Tests: <Test summary>
Signal: KITCHEN_COMPLETE
```
```

### 3.5 Create `docs/guidance/station-management.md`

**Source:** capsule/docs/guidance/git-branching.md

**Purpose:** Git branching strategy based on work type

**Translation Mapping:**
- `git branching` → `station management`
- `feature` → `multi-course meal`
- `task` → `course`
- `branch` → `station`
- `feature branch` → `course station`

**Structure:**
```markdown
# Station Management

## Overview

Line-cook uses different git workflows based on work type:

- **Multi-course meals (features)**: Work on dedicated stations, merge via PR
- **Courses (tasks)**: Work on `main` directly (or current course station)

## Station Management Rules

### Multi-Course Meals (Features)

**When to create station:**
- Starting work on a feature bead
- Feature has multiple courses
- Feature needs review before merging

**Station naming:**
```bash
feature/<feature-id>
```

### Courses (Tasks)

**When to work on main:**
- Standalone course (not part of feature)
- Small, atomic change
- No review needed

**When to work on feature station:**
- Course belongs to a feature
- Feature station already exists
```

### 3.6 Create `docs/guidance/menu-changes.md`

**Source:** capsule/docs/guidance/changelog.md

**Purpose:** Changelog maintenance and format

**Translation Mapping:**
- `changelog` → `menu changes`
- `feature` → `new menu item`
- `bug fix` → `recipe correction`
- `unreleased` → `today's specials`

**Structure:**
```markdown
# Menu Changes Guide

Guidelines for maintaining the menu (changelog).

## Format

```markdown
## [Today's Specials / X.Y.Z - YYYY-MM-DD]

### New Menu Items
- Feature description. User benefit.
  - Key capability 1
  - Key capability 2

### Recipe Corrections
- Bug fix description
```
```

### 3.7 Create `docs/guidance/order-priorities.md`

**Source:** capsule/docs/guidance/work-structure/priorities.md

**Purpose:** Priority system guidelines

**Translation Mapping:**
- `priorities` → `order priorities`
- `P1` → `Critical path`
- `P2` → `Important`
- `P3` → `Nice to have`

**Structure:**
```markdown
# Order Priorities

## Priority System

**P1: Critical Path** - Must do now, blocks other work
**P2: Important** - Should do soon, not blocking
**P3: Nice to Have** - Can defer, polish/convenience
```

### 3.8 Create `docs/guidance/workflow.md`

**Source:** capsule/docs/guidance/work-structure/README.md

**Purpose:** Core concepts for structuring and ordering work

**Translation Mapping:**
- `work structure` → `workflow`
- `feature→task hierarchy` → `multi-course→course hierarchy`
- `epic` → `meal theme`
- `feature` → `multi-course meal`
- `task` → `course`

**Structure:**
```markdown
# Kitchen Workflow

Core concepts for structuring and ordering work in line-cook.

## Multi-Course→Course Hierarchy

Line-cook uses a **3-tier hierarchy**:

1. **Meal Themes (Epics)** - High-level capability areas (3+ sessions)
2. **Multi-Course Meals (Features)** - User-observable, acceptance-testable outcomes
3. **Courses (Tasks)** - Single-session preparation steps

**Example:**
```
Meal Theme: Mission Lifecycle
├── Multi-Course Meal: Launch missions from beads
│   ├── Course: Read bead details
│   ├── Course: Create worktree
│   └── Course: Update bead status
└── Multi-Course Meal: Monitor mission progress
    ├── Course: Capture output
    └── Course: Detect signals
```
```

---

## Phase 4: Testing Documentation

### 4.1 Create `docs/testing/feature-completion-template.md`

**Source:** capsule/docs/testing/feature-acceptance-template.md

**Purpose:** Template for documenting feature completion

**Translation Mapping:**
- `feature acceptance` → `feature completion`
- `acceptance criteria` → `dining criteria`
- `feature description` → `menu item description`
- `test results` → `tasting results`

**Structure:**
```markdown
# Feature Completion Template

**Copy this template when documenting multi-course meal (feature) completion.**

---

# Feature X.Y: [Menu Item Name]

**Status**: ✅ All Dining Criteria Met

## Menu Item Description

As a [diner type], I want to [capability] so that I can [benefit].

## Dining Criteria

### ✅ 1. [First criterion]
**Test**: `TestFeature_[Name]/Dining_Criterion_1`
- [What it validates]
- [Expected behavior]

## Tasting Results

```
[N] tests passing
- [X] individual prep tests (TDD)
- [Y] course tasting tests (BDD)

Coverage: [%]
Duration: [time]
```

## Restaurant Inspection (CLI Smoke Tests)

```
[N] inspections passing
- Bash inspection ([X] scenarios)
- Go inspection ([Y] scenarios)

Duration: [time]
```

## Feature Sign-Off

**Menu Item**: [feature-id] ✅ COMPLETE
**Courses**: [X]/[X] closed
**Dining Tests**: [Y]/[Y] passing
**Restaurant Inspections**: [Z]/[Z] passing (if applicable)
**Ready for**: [Next integration step]
```

---

## Phase 5: Agent/Subagent Definitions

### 5.1 Create Quality-Control Agent (test-quality)

**Source:** capsule's test-quality subagent

**Purpose:** Review unit tests (TDD) for quality

**Kitchen Name:** Quality-Control Inspector

**Responsibilities:**
- Verify tests are isolated, fast, repeatable
- Check test names and error messages
- Validate structure (Setup-Execute-Validate-Cleanup)
- Identify anti-patterns

**When to Use:**
- RED phase of TDD cycle in `/line:cook`
- Before implementing code after writing failing tests

**Critical Issues (block GREEN phase):**
- Tests not isolated (shared state)
- Tests too slow (> 100ms)
- Missing error cases
- Unclear test names

**Structure:**
```
# Quality Control Inspector

You review individual prep tests (TDD) to ensure they meet quality standards.

## Review Process

### Check Test Isolation
- Does each test run independently?
- Are there shared state issues?
- Can tests run in any order?

### Check Test Performance
- Is test fast (< 100ms)?
- Are there unnecessary sleeps or waits?
- Is test efficient?

### Check Test Structure
- Follows Setup-Execute-Validate-Cleanup?
- Proper cleanup with defer?
- Clear test names?

## Output Format

If critical issues found:
```
❌ TEST QUALITY ISSUES

Critical:
- [description]
- [description]

Address these before GREEN phase.
```

If no critical issues:
```
✅ TEST QUALITY APPROVED

Ready to proceed to GREEN phase.
```
```

### 5.2 Create Sous-Chef Agent (reviewer)

**Source:** capsule's reviewer subagent

**Purpose:** Review code changes for correctness, security, style

**Kitchen Name:** Sous-Chef

**Responsibilities:**
- Review correctness (logic, edge cases, error handling)
- Check security (input validation, secrets, injection risks)
- Verify style (naming, consistency with codebase patterns)
- Assess completeness

**When to Use:**
- SERVE phase after completing work
- Before proceeding to TIDY

**Critical Issues (block TIDY):**
- Logic errors that would break functionality
- Security vulnerabilities
- Missing error handling

**Output Format:**
```
# Sous-Chef Code Review

## Review for Task: <task-id>

## Verdict
[✅ Ready for TIDY | ⚠️ Needs Changes | ❌ Blocked]

## Strengths
- [strength 1]
- [strength 2]

## Issues

### Critical (Must fix)
- [issue] - [file]:[line] - [suggestion]

### Major (Should fix)
- [issue] - [file]:[line] - [suggestion]

### Minor (Nice to have)
- [issue] - [file]:[line] - [suggestion]
```

### 5.3 Create Sommelier Agent (bdd-quality)

**Source:** capsule's bdd-quality subagent

**Purpose:** Review feature tests (BDD) for quality

**Kitchen Name:** Sommelier (Course Tasting Inspector)

**Responsibilities:**
- Verify all acceptance criteria have tests
- Check Given-When-Then structure
- Validate user perspective
- Check error scenarios

**When to Use:**
- DESSERT service when all tasks complete
- Before closing feature bead

**Critical Issues (block feature completion):**
- Missing acceptance criteria tests
- Not using Given-When-Then structure
- Testing implementation details instead of behavior

**Output Format:**
```
# Sommelier Feature Test Review

## Review for Feature: <feature-id>

## Verdict
[✅ Feature Complete | ⚠️ Needs Improvements | ❌ Critical Issues]

## Strengths
- [strength 1]
- [strength 2]

## Issues

### Critical (Must fix)
- Missing test for acceptance criterion: [criterion]
- Not using Given-When-Then structure

### Major (Should fix)
- Missing error scenario: [scenario]

### Minor (Nice to have)
- Test could be clearer

## Feature Readiness
- [✅] All acceptance criteria have tests
- [✅] Tests use Given-When-Then structure
- [✅] User perspective documented
- [✅] Error scenarios included
- [✅] CLI smoke tests added (if applicable)
```

### 5.4 Create Chef Agent (pilot/task execution)

**Source:** capsule's pilot subagent

**Purpose:** Execute tasks with TDD cycle

**Kitchen Name:** Chef

**Responsibilities:**
- Execute RED-GREEN-REFACTOR cycle
- Implement task deliverables
- Run quality gates (tests, build)

**When to Use:**
- COOK phase delegated by kitchen-manager

**Output Signal:** `KITCHEN_COMPLETE`

---

## Phase 6: Documentation Updates

### 6.1 Update AGENTS.md

**Changes:**
- Add kitchen terminology throughout
- Add TDD cycle with automatic quality-control review
- Add feature completion (dessert service)
- Add agent definitions (chef, sous-chef, quality-control, sommelier)
- Update workflow to include automatic quality gates

**New Sections to Add:**
```markdown
## Kitchen Workflow (Enhanced)

```
/line:plan  →  /line:prep  →  /line:cook  →  /line:serve  →  /line:tidy  →  /line:dessert
     ↓             ↓              ↓              ↓              ↓              ↓
  menu plan     sync           TDD cycle      review        commit        feature validation
```

Or use `/line:work` to run full cycle with kitchen-manager orchestration.

### /line:plan (NEW)
- Create menu plan with tracer dish methodology
- Convert to beads after approval
- Define multi-course→course hierarchy

### /line:prep (Enhanced)
- Load kitchen manual (work structure docs)
- Check branching strategy (feature vs task)
- Show ready orders with kitchen roster

### /line:cook (Enhanced)
- Execute TDD cycle (RED-GREEN-REFACTOR)
- Automatic quality-control review in RED phase
- Verify kitchen equipment (tests, build)

### /line:serve (Enhanced)
- Automatic sous-chef (reviewer) subagent
- Code quality checklist
- Reviewer feedback in report

### /line:tidy (Enhanced)
- Commit with kitchen log format
- Include reviewer and test quality feedback

### /line:dessert (NEW)
- Feature validation when all courses complete
- BDD quality review (sommelier)
- CLI smoke tests (restaurant inspection)
- Update menu changes (changelog)
- Create feature completion documentation

### /line:work (Enhanced)
- Kitchen-manager orchestration
- Automatic feature completion check
- Quality gates and failure conditions
```

### 6.2 Update README.md

**Changes:**
- Update workflow diagram to include plan and dessert
- Add new commands to quick start
- Update command descriptions with TDD, quality gates
- Add kitchen terminology glossary

**Updated Quick Start:**
```markdown
## Quick Start

1. Run `/line:plan` to plan multi-course meals (features)
2. Run `/line:prep` to see ready courses (tasks)
3. Run `/line:cook` to execute with TDD cycle
4. Run `/line:serve` for sous-chef review
5. Run `/line:tidy` to commit and push
6. Run `/line:dessert` when all courses complete (feature validation)

Or just run `/line:work` for full cycle with kitchen-manager.
```

**Add Glossary:**
```markdown
## Kitchen Terminology

| Kitchen Term | Technical Term | Description |
|--------------|----------------|-------------|
| Order | Bead | Work item tracked in beads |
| Multi-Course Meal | Feature | User-observable outcome with acceptance criteria |
| Course | Task | Single-session implementation step |
| Meal Theme | Epic | High-level capability area |
| Menu Plan | Task Graph | Human-readable planning before bead creation |
| Tracer Dish | Tracer Bullet | Vertical slice through all layers |
| Tasting Plate | Prototype | Demo/throwaway code |
| Kitchen Experiment | Spike | Research/learning code |
| Chef | Pilot Agent | Executes tasks |
| Sous-Chef | Reviewer Agent | Reviews code changes |
| Quality Control | Test-Quality Agent | Reviews test quality |
| Sommelier | BDD-Quality Agent | Reviews feature tests |
| Individual Prep | TDD | Task-level test-driven development |
| Course Tasting | BDD | Feature-level behavior-driven development |
| Restaurant Inspection | CLI Smoke Tests | End-to-end CLI validation |
| Kitchen Log | Commit Message | Commit message with kitchen log format |
| Station | Git Branch | Feature or main branch |
| Kitchen Equipment | Tests + Build | Verification systems |
| Dining Criteria | Acceptance Criteria | User-observable requirements |
| Feature Completion | Dessert Service | Feature validation and documentation |
```

### 6.3 Update CHANGELOG.md

**Add Unreleased section with planned features:**
```markdown
## [Unreleased]

### Added
- Enhanced workflow with TDD cycle and automatic quality gates
- New `/line:plan` command for recipe planning with tracer dish methodology
- New `/line:dessert` command for feature validation and documentation
- Automatic quality-control agent (test-quality review)
- Automatic sous-chef agent (code review)
- Automatic sommelier agent (BDD test quality review)
- Kitchen-manager orchestration in `/line:work`
- Enhanced branching strategy (feature stations vs main)
- Kitchen log commit message format

### Changed
- `/line:prep` now loads kitchen manual and checks branching strategy
- `/line:cook` now includes TDD cycle with quality gates
- `/line:serve` now includes automatic sous-chef review
- `/line:tidy` now uses kitchen log format and includes reviewer feedback
- `/line:work` now orchestrates full cycle with feature completion check

### Documentation
- Added comprehensive guidance docs (tracer-dishes, test-prep, tdd-bdd, etc.)
- Added feature completion template
- Updated AGENTS.md with enhanced workflow
- Added kitchen terminology glossary
```

---

## Phase 7: OpenCode Plugin Commands

### 7.1 Update OpenCode Commands

Update all OpenCode commands (`line-cook-opencode/commands/*.md`) to match Claude Code commands:

- `line-prep.md` → Match updated `commands/prep.md`
- `line-cook.md` → Match updated `commands/cook.md`
- `line-serve.md` → Match updated `commands/serve.md`
- `line-tidy.md` → Match updated `commands/tidy.md`
- `line-work.md` → Match updated `commands/work.md`
- `line-plan.md` → Create new (from `commands/plan.md`)
- `line-dessert.md` → Create new (from `commands/dessert.md`)

**Note:** OpenCode uses `line-command` naming (e.g., `line-prep`), Claude Code uses `line:command` (e.g., `line:prep`).

---

## Phase 8: Kiro Agent Updates

### 8.1 Update Kiro Skills

Update `line-cook-kiro/skills/line-cook/SKILL.md` to include new commands and methodology.

**Add:**
- `/plan` command
- `/dessert` command
- TDD cycle with quality gates
- Agent definitions

### 8.2 Update Kiro Steering Docs

Update steering docs to reflect enhanced workflow:
- `line-cook-kiro/steering/line-cook.md`
- `line-cook-kiro/steering/session.md`

---

## Phase 9: Testing and Validation

### 9.1 Create Test Scenarios

Create test scenarios to validate new functionality:

1. **Recipe Planning Test**
   - Create menu plan for feature
   - Convert to beads
   - Verify hierarchy

2. **TDD Cycle Test**
   - Write failing test
   - Run quality-control review
   - Fix issues
   - Implement code
   - Verify GREEN phase

3. **Feature Completion Test**
   - Complete all courses for feature
   - Run dessert service
   - Verify BDD quality review
   - Check documentation

4. **Automatic Review Test**
   - Complete work
   - Verify sous-chef review runs
   - Check reviewer feedback in report

### 9.2 Update Fixtures

Update test fixtures in `tests/fixtures/sample-project/` to use enhanced workflow.

---

## Phase 10: Migration Checklist

### Pre-Migration

- [ ] Read all capsule prompts and guidance docs
- [ ] Create CAPSULE_MAPPINGS.md methodology document ✓
- [ ] Create this comprehensive migration plan
- [ ] Review plan with stakeholders

### Implementation

**Phase 1: Core Command Updates**
- [ ] Update `/line:prep` (commands/prep.md)
- [ ] Update `/line:cook` (commands/cook.md)
- [ ] Update `/line:serve` (commands/serve.md)
- [ ] Update `/line:tidy` (commands/tidy.md)
- [ ] Update `/line:work` (commands/work.md)

**Phase 2: New Commands**
- [ ] Create `/line:plan` (commands/plan.md)
- [ ] Create `/line:dessert` (commands/dessert.md)

**Phase 3: Guidance Documentation**
- [ ] Create `docs/guidance/tracer-dishes.md`
- [ ] Create `docs/guidance/test-prep.md`
- [ ] Create `docs/guidance/tdd-bdd.md`
- [ ] Create `docs/guidance/kitchen-logs.md`
- [ ] Create `docs/guidance/station-management.md`
- [ ] Create `docs/guidance/menu-changes.md`
- [ ] Create `docs/guidance/order-priorities.md`
- [ ] Create `docs/guidance/workflow.md`

**Phase 4: Testing Documentation**
- [ ] Create `docs/testing/feature-completion-template.md`

**Phase 5: Agent/Subagent Definitions**
- [ ] Define quality-control agent
- [ ] Define sous-chef agent
- [ ] Define sommelier agent
- [ ] Define chef agent
- [ ] Define kitchen-manager agent

**Phase 6: Documentation Updates**
- [ ] Update AGENTS.md
- [ ] Update README.md
- [ ] Update CHANGELOG.md

**Phase 7: OpenCode Plugin Commands**
- [ ] Update line-prep.md
- [ ] Update line-cook.md
- [ ] Update line-serve.md
- [ ] Update line-tidy.md
- [ ] Update line-work.md
- [ ] Create line-plan.md
- [ ] Create line-dessert.md

**Phase 8: Kiro Agent Updates**
- [ ] Update SKILL.md
- [ ] Update steering docs

**Phase 9: Testing and Validation**
- [ ] Create test scenarios
- [ ] Update test fixtures
- [ ] Run integration tests
- [ ] Fix issues

### Post-Migration

- [ ] Review all translated content
- [ ] Verify kitchen theming consistency
- [ ] Test all commands
- [ ] Update tutorials if needed
- [ ] Create release notes
- [ ] Tag release

---

## Phase 11: Rollback Plan

If issues arise after migration:

1. **Revert commands**
   ```bash
   git checkout HEAD~1 commands/
   ```

2. **Revert documentation**
   ```bash
   git checkout HEAD~1 AGENTS.md README.md CHANGELOG.md
   ```

3. **Revert OpenCode commands**
   ```bash
   git checkout HEAD~1 line-cook-opencode/commands/
   ```

4. **Fix issues and redeploy**

---

## Summary

This migration plan comprehensively maps all capsule methodology to line-cook's kitchen theming:

**Command Updates:** 5 existing commands enhanced
**New Commands:** 2 new commands (plan, dessert)
**Guidance Docs:** 8 new guidance documents
**Testing Docs:** 1 new template
**Agents:** 5 agent definitions
**Documentation Updates:** 3 major docs
**OpenCode Updates:** 7 commands
**Kiro Updates:** 3 docs

**Total:** ~30 files to create or update

**Key Enhancements:**
- TDD cycle with automatic quality gates
- Automatic code review (sous-chef)
- Feature validation (dessert service)
- Comprehensive guidance documentation
- Consistent kitchen theming throughout

**Timeline Estimate:** 3-5 days for full implementation and testing.
