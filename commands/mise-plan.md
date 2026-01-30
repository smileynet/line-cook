---
description: Create structured work breakdown (convergent thinking)
allowed-tools: Bash, Read, Write, Glob, Grep, Task, AskUserQuestion
---

## Summary

**Convergent thinking phase: structure, scope, decompose.** Second phase of mise en place.

This phase transforms exploration into a structured, reviewable plan. Output is a YAML menu plan that can be converted to beads.

**Input:** Brainstorm document (optional) or direct requirements
**Output:** `docs/planning/menu-plan.yaml`

**STOP after creating menu plan.** Wait for user approval before committing.

---

## Process

### Step 1: Load Context

Check for existing brainstorm document:

```bash
ls docs/planning/brainstorm-*.md 2>/dev/null
```

**If brainstorm exists:**
- Read the brainstorm document
- Use it as input for planning
- Verify open questions are resolved

**If no brainstorm:**
- Ask user for requirements directly
- Consider if brainstorm phase would be valuable first

### Step 2: Determine Scope

Based on the problem, determine the right scope:

| Scope | Sessions | When to use |
|-------|----------|-------------|
| **Task** | <1 | Simple, clear deliverable |
| **Feature** | 1-3 | User-observable capability |
| **Epic** | 3+ | Multiple features, large effort |

**For tasks:** Skip menu plan, create bead directly
**For features:** Create single-feature menu plan
**For epics:** Create multi-phase menu plan

### Step 3: Create Menu Plan

Build a structured breakdown in YAML format:

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
          minimal_flow: "Create session -> Send command -> Capture output -> Destroy"
          layers: "Tmux wrapper -> Command execution -> Output capture"
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
```

**See `docs/planning/menu-plan-format.md` for complete format reference.**

### Step 4: Add Feature Dependencies

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

### Step 5: Validate Feature Quality

Every feature MUST be user-facing. Validate:

| Check | Requirement |
|-------|-------------|
| **User interface** | Has CLI/API/UI for users to invoke |
| **User story** | Clear "As a... I want... So that..." |
| **Acceptance criteria** | 3-5 testable outcomes |
| **Smoke testable** | Can write end-to-end CLI tests |

**If you can't write smoke tests, it's not a feature** - it's infrastructure that should be tasks under a real feature.

### Step 6: Output Menu Plan Summary

After creating the menu plan, output:

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

Phases: <N>
Features: <M>
Tasks: <L>

Breakdown:
  Phase 1: <title> (<X> sessions)
    - Feature 1.1: <title>
      - <N> tasks
    - Feature 1.2: <title>
      - <N> tasks
  ...

Tracer Strategy:
  Feature 1.1:
    Minimal flow: <flow description>
    Layers: <layers>
    Expansion: <deferred items>

REVIEW THE PLAN:
  1. Check hierarchy makes sense
  2. Verify each feature has:
     [ ] User story
     [ ] Acceptance criteria (3-5)
     [ ] Tracer strategy
  3. Verify each task has:
     [ ] Tracer explanation
     [ ] Clear deliverable
     [ ] Dependencies listed
     [ ] TDD flag if applicable

NEXT STEP: Run /line:mise:commit to convert to beads and create test specs
  (or /line:mise to continue with full orchestration)
```

---

## Hierarchy Structure

**Three-tier hierarchy:**

```
Epic (Phase)
├── Feature 1 (User-observable outcome)
│   ├── Task 1.1 (Implementation step)
│   ├── Task 1.2 (Implementation step)
│   └── Task 1.3 (Implementation step)
└── Feature 2 (User-observable outcome)
    ├── Task 2.1 (Implementation step)
    └── Task 2.2 (Implementation step)
```

**Mapping:**
- **Epic** = Phase (3+ sessions, multiple features)
- **Feature** = User-observable capability (1-3 sessions, multiple tasks)
- **Task** = Single implementation unit (< 2 hours, one tracer)

---

## Task Sizing Guidelines

**Use tracer bullet thinking** - each task should be a vertical slice through relevant layers.

**Too Small** (combine into one tracer):
- "Add import statement"
- "Create empty file"
- "Update comment"

**Just Right** (single tracer, one session):
- "Define mission struct and state machine" (data layer)
- "Implement bead integration" (external interface layer)
- "Implement launch command" (orchestration layer)

**Too Large** (break into multiple tracers):
- "Implement entire mission lifecycle" -> Break into: state machine, launch, monitor, dock
- "Add all monitoring features" -> Break into: capture, detect, log, report
- "Complete Phase 1" -> Break into individual features

---

## Common Mistakes to Avoid

- Creating beads directly: Hard to review, edit, and discuss
- Too vague: "Implement monitoring"
- Too large: "Complete Phase 1"
- No deliverable: "Research tmux"
- Horizontal slicing: "Build entire UI layer"
- No tracer strategy: Tasks in random order
- "Internal features" with no CLI: "Feature: Manage worktrees" (no user interface)
- Features without smoke tests: If you can't smoke test it, it's not a feature

---

## Example Usage

```
/line:mise:plan
```

This command will:
1. Check for existing brainstorm document
2. Determine scope (task/feature/epic)
3. Create YAML menu plan
4. Output summary for review
5. Wait for user approval before committing
