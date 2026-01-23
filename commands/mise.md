---
description: Create work breakdown before starting implementation
allowed-tools: Bash, Write, Read
---

## Summary

**Create human-readable work breakdown using tracer methodology.** Prep step before creating beads.

**STOP after creating menu plan.** Wait for user approval before converting to beads.

---

## Process

### Step 1: Understand the Order

Ask clarifying questions:

**What are we building?**
- What problem are we solving?
- What does success look like?
- Who is the user?

**What are the constraints?**
- Are there technical constraints?
- Time constraints (MVP vs full feature)?
- Dependencies on other work?

**What's the scope?**
- MVP (minimum viable product)
- Full feature
- Multi-session epic

**Ask questions if unclear.** Don't assume.

### Step 2: Create Menu Plan (Task Graph)

Build a structured breakdown in YAML format for easy conversion to beads.

**Why YAML?**
- Human-readable and easy to edit
- Machine-parseable for automated bead creation
- Version controlled and reviewable
- Can iterate quickly before creating beads

**Create `docs/planning/menu-plan.yaml`:**

```yaml
phases:
  - id: phase-1
    title: "Phase 1: Foundation"
    description: "Core infrastructure for tmux integration and worktrees"
    duration: "Week 1 (4-6 sessions)"
    
    features:
      - id: feature-1.1
        title: "Feature 1.1: Execute commands in tmux sessions"
        priority: 2
        user_story: "As a capsule orchestrator, I want to execute commands in tmux sessions so that I can programmatic control OpenCode TUI"
        acceptance_criteria:
          - "Can create/destroy tmux sessions"
          - "Can send commands with proper debouncing"
          - "Can capture session output"
        tracer_strategy:
          minimal_flow: "Create session → Send command → Capture output → Destroy"
          layers: "Tmux wrapper → Command execution → Output capture"
          expansion: "Window management, pane splitting (deferred)"
        
        tasks:
          - title: "Port tmux wrapper from gastown"
            priority: 1
            tracer: "Foundation layer - proves tmux integration works"
            description: |
              - Copy internal/tmux/tmux.go structure
              - Adapt for Capsule needs
            deliverable: "internal/tmux/tmux.go skeleton"
            reference: "~/code/gastown/internal/tmux/tmux.go"
            tdd: true
          
          - title: "Implement session creation/destruction"
            priority: 1
            depends_on: ["Port tmux wrapper from gastown"]
            tracer: "Session lifecycle - proves basic management works"
            description: |
              - NewSession(name, workDir) function
              - KillSession(name) function
              - SessionExists(name) check
            deliverable: "Session management with tests"
            tdd: true
          
          - title: "Implement command execution"
            priority: 1
            depends_on: ["Implement session creation/destruction"]
            tracer: "Command execution - proves sending commands works"
            description: |
              - SendCommand(session, command) function
              - Wait for completion with timeout
              - Capture stdout/stderr
            deliverable: "Command execution with tests"
            tdd: true
```

**See `docs/planning/menu-plan-format.md` for complete format reference.**

### Step 3: Add Feature Dependencies (Sequential Features)

Add `blocks` field to enforce sequential feature completion:

```yaml
features:
  - id: feature-2.1
    title: "Feature 2.1: Run missions in isolated worktrees"
    blocks: ["feature-1.2"]  # This feature blocks Feature 1.2
    # ...
  
  - id: feature-1.2
    title: "Feature 1.2: Basic CLI structure"
    blocks: ["feature-3.1"]  # This feature blocks Feature 3.1
    # ...
```

**Why sequential?**
- Maintains focus on one feature at a time
- Prevents context switching
- Ensures features are fully complete before moving on

### Step 4: Plan BDD Tests for Features

**Every feature must include BDD tests** that validate acceptance criteria from the user's perspective.

**Define BDD test plan:**

```yaml
features:
  - id: feature-2.1
    title: "Feature 2.1: Run missions in isolated worktrees"
    user_story: "As a capsule orchestrator, I want to run missions in isolated git worktrees so that I can execute multiple missions in parallel without workspace conflicts"
    acceptance_criteria:
      - "Can create worktree with unique name"
      - "Worktree on new branch"
      - "Changes don't affect main workspace"
      - "Clean removal of worktrees"
    bdd_tests:
      - test: "TestFeature_RunMissionsInIsolatedWorktrees"
        scenarios:
          - "Acceptance_Criterion_1_Create_worktree_with_unique_name"
          - "Acceptance_Criterion_2_Worktree_on_new_branch"
          - "Acceptance_Criterion_3_Changes_dont_affect_main_workspace"
          - "Acceptance_Criterion_4_Clean_removal_of_worktrees"
      - test: "TestFeature_ParallelMissionIsolation"
        scenarios:
          - "Multiple missions run independently"
    smoke_tests:  # CLI validation - REQUIRED for user-facing features
      - "capsule launch creates worktree"
      - "capsule dock removes worktree cleanly"
```

**BDD Test Structure:**
- File: `internal/<package>/integration_test.go`
- Format: Given-When-Then comments
- Naming: `TestFeature_<FeatureName>`
- Subtests: Map to acceptance criteria
- Real operations: Use actual git/tmux/system calls

**Smoke Test Structure:**
- File: `scripts/smoke-test-<feature>.sh` or `cmd/smoke-test/`
- Tests: Real CLI commands with expected outputs
- **Every feature must have smoke tests** (features are user-facing by definition)
- Validates: End-to-end user experience

**If you can't write smoke tests, it's not a feature** - it's infrastructure that should be tasks under a user-facing feature.

### Step 5: Output Menu Plan Summary

After creating the menu plan, output:

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

Phases: <N>
Features: <M>
Courses (tasks): <L>

Breakdown:
  Phase 1: <title> (<X> sessions)
    - Feature 1.1: <title>
      - <N> courses
    - Feature 1.2: <title>
      - <N> courses
  ...

Tracer Strategy:
  Feature 1.1:
    Minimal flow: <flow description>
    Layers: <layers>
    Expansion: <deferred items>

REVIEW THE PLAN:
  1. Check hierarchy makes sense
  2. Verify each feature has:
     ✓ User story
     ✓ Acceptance criteria (3-5)
     ✓ BDD test plan
     ✓ Smoke test plan (CLI)
  3. Verify each course has:
     ✓ Tracer explanation
     ✓ Clear deliverable
     ✓ Dependencies listed

NEXT STEP: Run /line:cook to convert menu plan to beads
  (Review plan first, modify if needed, then convert)
```

### Step 6: Convert Menu Plan to Beads

**ONLY convert after user approves the menu plan.**

Run the conversion script:

```bash
./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml
```

**Script will:**
- Create epics (phases)
- Create features with acceptance criteria
- Create tasks with descriptions and deliverables
- Add task dependencies (depends_on)
- Add feature dependencies (blocks)

**Or create beads manually:**
```bash
bd create --title="Phase 1: Foundation" --type=epic --priority=2
bd create --title="Feature 1.1: Execute commands in tmux sessions" --type=feature --parent=lc-abc --priority=3
bd create --title="Port tmux wrapper from gastown" --parent=lc-abc.1 --priority=1
bd dep add <new-task-id> <dependency-task-id>
```

### Step 7: Verify Beads and Dependencies

Check that beads were created correctly and dependencies are enforced:

```bash
bd list              # See all beads
bd list -t epic      # See only epics
bd list -t feature   # See only features
bd ready             # See available work (should be focused on one feature)
bd blocked           # See blocked features
bd show <epic-id>    # View epic with child features
bd show <feature-id> # View feature with child tasks
```

**Verify hierarchy:**
```bash
# Check epic structure
bd show <epic-id>
# Should show:
#   Epic: Phase 1: Foundation
#   Children:
#     - Feature 1.1: Execute commands in tmux sessions
#     - Feature 1.2: Manage git worktrees

# Check feature structure  
bd show <feature-id>
# Should show:
#   Feature: 1.1: Execute commands in tmux sessions
#   Parent: Phase 1: Foundation
#   Children:
#     - Course: Port tmux wrapper from gastown
#     - Course: Implement session creation/destruction
```

**Verify dependencies:**
```bash
bd ready
# Should only show courses from the current feature (not blocked)

bd blocked
# Should show features blocked by dependencies
```

### Step 8: Sync and Commit

```bash
bd sync
git add docs/planning/menu-plan.yaml .beads/
git commit -m "plan: Create menu plan for <phase>

- <N> phases planned
- <M> features with acceptance criteria
- <L> courses (tasks) with tracer strategy

Key features:
- Feature 1.1: <title>
- Feature 1.2: <title>

Tracer approach:
- Each course builds foundation for next
- Vertical slices through all layers
- Production quality from start"
git push
```

---

## Hierarchy Structure

**Three-tier hierarchy:**

```
Epic (Phase)
├── Feature 1 (User-observable outcome)
│   ├── Course 1.1 (Implementation step)
│   ├── Course 1.2 (Implementation step)
│   └── Course 1.3 (Implementation step)
└── Feature 2 (User-observable outcome)
    ├── Course 2.1 (Implementation step)
    └── Course 2.2 (Implementation step)
```

**Mapping:**
- **Epic** = Phase (3+ sessions, multiple features)
- **Feature** = User-observable capability (1-3 sessions, multiple courses)
- **Course (Task)** = Single implementation unit (< 2 hours, one tracer)

---

## CRITICAL: Features Must Be User-Facing

A feature MUST have a user interface (CLI, API, or UI) that allows users to exercise the capability. If there's no way for users to interact with it, it's not a feature - it's infrastructure that belongs as courses under a real feature.

**❌ Wrong - "Internal feature" with no user interface:**
```
Epic: Phase 1: Foundation
├── Feature 1.1: Execute commands in tmux sessions
│   ├── Course: Implement session creation
│   ├── Course: Implement command execution
│   └── Course: Add smoke tests ✅ (CLI testable)
└── Feature 1.2: Manage git worktrees ❌ (No CLI - not a feature!)
    ├── Course: Implement worktree creation
    ├── Course: Implement worktree cleanup
    └── Course: ??? (No smoke tests - nothing to test!)
```

**✅ Correct - Infrastructure as courses under user-facing feature:**
```
Epic: Phase 1: Foundation
└── Feature 1.1: Launch missions in isolated environments
    ├── Course: Implement tmux session wrapper
    ├── Course: Implement worktree manager
    ├── Course: Implement launch command
    ├── Course: Add bead integration
    └── Course: Add smoke tests (validates entire flow)
```

**✅ Also correct - Split if features are independently useful:**
```
Epic: Phase 1: Foundation
├── Feature 1.1: Execute commands in tmux sessions
│   ├── Course: Implement session management
│   ├── Course: Implement command execution
│   ├── Course: Add tmux CLI wrapper
│   └── Course: Add smoke tests (capsule tmux create/send/capture)
└── Feature 1.2: Launch missions in isolated worktrees
    ├── Course: Implement worktree manager
    ├── Course: Implement launch command
    ├── Course: Integrate tmux + worktrees
    └── Course: Add smoke tests (capsule launch/status/dock)
```

**Test for valid feature:**
- ✅ Can a user invoke this via CLI/API/UI?
- ✅ Can you write smoke tests that exercise it?
- ✅ Would a user understand what this does?
- ❌ Is this just infrastructure for another feature?

**Examples:**

| Description | Valid Feature? | Why |
|-------------|----------------|-----|
| "Launch missions from beads" | ✅ Yes | User runs `capsule launch <id>` |
| "Manage git worktrees" | ❌ No | No CLI - just infrastructure |
| "Monitor mission progress" | ✅ Yes | User runs `capsule status <id>` |
| "Implement state machine" | ❌ No | Internal detail of a feature |
| "Add authentication" | ✅ Yes | User provides API key, gets auth'd |
| "Port tmux wrapper" | ❌ No | Infrastructure unless exposed via CLI |

---

## Tracer Dish Approach

**Build vertical slices through all system layers, then expand incrementally.**

**Key principle**: Each course is a mini-tracer that:
- Implements one focused capability end-to-end
- Touches relevant architectural layers
- Provides foundation for next course
- Is production-quality (not throwaway)

**Example - Feature broken into tracer courses:**

```markdown
Feature 3.1: Launch missions from beads

Course 1: Define mission struct and state machine
  → Tracer: Data layer foundation
  → Proves: State management approach works

Course 2: Implement bead integration  
  → Tracer: External interface layer
  → Proves: Can read/update bead status

Course 3: Implement launch command
  → Tracer: Orchestration layer
  → Proves: End-to-end flow works (CLI → Mission → Worktree → Tmux → Bead)
```

Each course builds on the previous, creating a complete vertical slice.

---

## Course Sizing Guidelines

**Use tracer bullet thinking** - each course should be a vertical slice through relevant layers.

**Too Small** (combine into one tracer):
- "Add import statement"
- "Create empty file"  
- "Update comment"

**Just Right** (single tracer, one session):
- "Define mission struct and state machine" (data layer)
- "Implement bead integration" (external interface layer)
- "Implement launch command" (orchestration layer)

**Too Large** (break into multiple tracers):
- "Implement entire mission lifecycle" → Break into: state machine, launch, monitor, dock
- "Add all monitoring features" → Break into: capture, detect, log, report
- "Complete Phase 1" → Break into individual features

---

## Common Mistakes to Avoid

❌ **Creating beads directly**: Hard to review, edit, and discuss
✅ **Menu plan first**: Easy to review and iterate

❌ **Too vague**: "Implement monitoring"  
✅ **Specific tracer**: "Implement output capture loop with 5s interval"

❌ **Too large**: "Complete Phase 1"
✅ **Sized right**: "Define mission struct and state machine"

❌ **No deliverable**: "Research tmux"
✅ **Clear outcome**: "Document tmux patterns in RESEARCH.md"

❌ **Horizontal slicing**: "Build entire UI layer"
✅ **Vertical slicing**: "Implement launch command (CLI → Mission → Tmux)"

❌ **No tracer strategy**: Courses in random order
✅ **Tracer sequence**: Foundation → Integration → Orchestration

❌ **Prototype thinking**: "Quick and dirty, we'll rewrite later"
✅ **Tracer thinking**: "Production quality, minimal scope, expand incrementally"

❌ **"Internal features" with no CLI**: "Feature: Manage worktrees" (no user interface)
✅ **User-facing features only**: "Feature: Launch missions in isolated worktrees" (has `capsule launch`)

❌ **Features without smoke tests**: If you can't smoke test it, it's not a feature
✅ **Every feature has smoke tests**: Validates end-to-end user experience

---

## Example Output

**Menu plan created:**

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

Phases: 1
Features: 2
Courses: 5

Breakdown:
  Phase 1: Foundation (4-6 sessions)
    - Feature 1.1: Execute commands in tmux sessions
      - 3 courses
    - Feature 1.2: Launch missions in isolated worktrees
      - 2 courses

Tracer Strategy:
  Feature 1.1:
    Minimal flow: Create session → Send command → Capture output → Destroy
    Layers: Tmux wrapper → Command execution → Output capture
    Expansion: Window management, pane splitting (deferred)

  Feature 1.2:
    Minimal flow: Read bead → Create worktree → Launch Tmux → Update status
    Layers: Bead API → Worktree manager → Tmux integration
    Expansion: Parallel missions, monitoring (deferred)

REVIEW THE PLAN:
  1. Check hierarchy makes sense ✓
  2. Verify each feature has:
     ✓ User story
     ✓ Acceptance criteria (3-5)
     ✓ BDD test plan
     ✓ Smoke test plan (CLI)
  3. Verify each course has:
     ✓ Tracer explanation
     ✓ Clear deliverable
     ✓ Dependencies listed

NEXT STEP: Run /line:prep to convert menu plan to beads
  (Review plan first, modify if needed, then convert)
```

---

## Example Usage

```
/line:mise
```

This command takes no arguments. It will:
1. Ask clarifying questions about what you're building
2. Create a YAML menu plan in `docs/planning/menu-plan.yaml`
3. Output summary for review
4. Wait for user to convert to beads

To convert plan to beads:
```bash
./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml
```
