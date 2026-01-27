# Menu Plan Format

Complete reference for menu plan YAML format used by `/line:mise`.

## Purpose

Menu plans are human-readable task graphs that define recipes (features) and courses (tasks) before converting to beads. They enable easy review and iteration of work structure.

## Format Structure

```yaml
phases:
  - id: phase-1
    title: "Phase 1: Foundation"
    description: "Core infrastructure description"
    duration: "Week 1 (4-6 sessions)"
    
    features:
      - id: feature-1.1
        title: "Feature 1.1: User-observable outcome"
        priority: 2
        user_story: "As a [user], I want [capability] so that [benefit]"
        acceptance_criteria:
          - "Criterion 1: User-observable outcome"
          - "Criterion 2: User-observable outcome"
          - "Criterion 3: User-observable outcome"
        tracer_strategy:
          minimal_flow: "Step 1 → Step 2 → Step 3"
          layers: "Layer 1 → Layer 2 → Layer 3"
          expansion: "Deferred items to add later"
        blocks: ["feature-2.1"]  # Optional: blocks other features
        bdd_tests:
          - test: "TestFeature_<FeatureName>"
            scenarios:
              - "Acceptance_Criterion_1_Name"
              - "Acceptance_Criterion_2_Name"
        smoke_tests:  # Required for user-facing features
          - "CLI command does X"
          - "CLI command validates Y"
        
        tasks:
          - title: "Course 1: Tracer foundation"
            priority: 1
            tracer: "What this course proves"
            description: |
              - Implementation detail 1
              - Implementation detail 2
            deliverable: "What gets created"
            reference: "~/path/to/reference"
            depends_on: ["Previous course title"]  # Optional
            tdd: true  # Required for courses
```

## Fields Reference

### Phase (Epic)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ Yes | Unique identifier (e.g., `phase-1`) |
| `title` | string | ✅ Yes | Human-readable name (e.g., "Phase 1: Foundation") |
| `description` | string | ✅ Yes | Brief description of phase scope |
| `duration` | string | ✅ Yes | Estimated time (e.g., "Week 1 (4-6 sessions)") |

### Feature

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ Yes | Unique identifier (e.g., `feature-1.1`) |
| `title` | string | ✅ Yes | User-observable outcome name |
| `priority` | number | ✅ Yes | 1 (P1), 2 (P2), or 3 (P3) |
| `user_story` | string | ✅ Yes | "As a [user], I want [capability] so that [benefit]" |
| `acceptance_criteria` | list | ✅ Yes | 3-5 testable user-observable outcomes |
| `tracer_strategy` | object | ✅ Yes | Tracer bullet methodology |
| `blocks` | list | ❌ No | IDs of features this blocks (sequential flow) |
| `bdd_tests` | list | ✅ Yes | BDD test plan mapping to acceptance criteria |
| `smoke_tests` | list | ✅ Yes | CLI smoke test scenarios |
| `tasks` | list | ✅ Yes | Courses (tasks) implementing this feature |

#### Feature: tracer_strategy

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `minimal_flow` | string | ✅ Yes | Simplest end-to-end path |
| `layers` | string | ✅ Yes | Architectural layers touched |
| `expansion` | string | ✅ Yes | Items deferred to later courses |

#### Feature: bdd_tests

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test` | string | ✅ Yes | Test function name (e.g., `TestFeature_RunMissions`) |
| `scenarios` | list | ✅ Yes | Subtest names mapping to acceptance criteria |

### Task (Course)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ Yes | Course name with tracer explanation |
| `priority` | number | ✅ Yes | 1 (P1), 2 (P2), or 3 (P3) |
| `tracer` | string | ✅ Yes | What this course proves (foundation layer) |
| `description` | string | ✅ Yes | Implementation details (multiline) |
| `deliverable` | string | ✅ Yes | What gets created |
| `reference` | string | ❌ No | Path to reference implementation |
| `depends_on` | list | ❌ No | Titles of courses this depends on |
| `tdd` | boolean | ✅ Yes | Always `true` for courses |

## Priority Levels

| Priority | Name | When to Use |
|----------|------|-------------|
| `1` | P1 (Critical Path) | Must do now, blocks other work |
| `2` | P2 (Important) | Should do soon, not blocking |
| `3` | P3 (Nice to Have) | Can defer, polish/convenience |

## Naming Conventions

### Phases (Epics)
- Pattern: `"Phase N: <Capability Area>"`
- Examples: "Phase 1: Foundation", "Phase 2: Mission Lifecycle"

### Features
- Pattern: `"Feature N.M: <User-Observable Outcome>"`
- Must be user-facing (has CLI/API/UI interface)
- Must have smoke tests
- Examples: "Feature 1.1: Execute commands in tmux sessions", "Feature 2.1: Launch missions from beads"

### Courses (Tasks)
- Pattern: `"Course: <What this proves>"` or action-oriented
- Names describe what course does, not what it is
- Examples: "Port tmux wrapper from gastown", "Implement session creation"

### Tracer Strategy
- `minimal_flow`: Simplest path through all layers
- `layers`: Architectural layers in sequence
- `expansion`: Features to add after tracer works

## Dependencies

### Task Dependencies
Use `depends_on` to enforce ordering:

```yaml
tasks:
  - title: "Implement session creation"
    depends_on: ["Port tmux wrapper from gastown"]
```

Rules:
- List previous course titles (not IDs)
- Creates directed acyclic graph (DAG)
- Converted to `bd dep add` commands

### Feature Dependencies (Sequential Flow)
Use `blocks` to enforce feature completion order:

```yaml
features:
  - id: feature-2.1
    title: "Feature 2.1: Run missions in isolated worktrees"
    blocks: ["feature-1.2"]  # This feature blocks Feature 1.2
```

Rules:
- List feature IDs (not titles)
- Ensures features complete in order
- Prevents context switching between features

## BDD Test Structure

**Every feature must have BDD tests** mapping 1:1 to acceptance criteria.

```yaml
bdd_tests:
  - test: "TestFeature_RunMissionsInIsolatedWorktrees"
    scenarios:
      - "Acceptance_Criterion_1_Create_worktree_with_unique_name"
      - "Acceptance_Criterion_2_Worktree_on_new_branch"
      - "Acceptance_Criterion_3_Changes_dont_affect_main_workspace"
      - "Acceptance_Criterion_4_Clean_removal_of_worktrees"
```

**Implementation file:** `internal/<package>/integration_test.go`

**Test structure:**
```go
func TestFeature_RunMissionsInIsolatedWorktrees(t *testing.T) {
    t.Run("Acceptance_Criterion_1_Create_worktree_with_unique_name", func(t *testing.T) {
        // Given I need to launch a new mission
        missionID := "capsule-test-001"
        
        // When I create a worktree for the mission
        worktreePath, err := wm.CreateWorktree(missionID, "main")
        
        // Then the worktree should exist with a unique name
        if _, err := os.Stat(worktreePath); os.IsNotExist(err) {
            t.Fatalf("Worktree should exist at %s", worktreePath)
        }
    })
}
```

## Smoke Tests

**Every feature must have smoke tests** (features are user-facing by definition).

```yaml
smoke_tests:
  - "capsule launch creates worktree"
  - "capsule dock removes worktree cleanly"
  - "capsule status shows running missions"
```

**Implementation file:** `scripts/smoke-test-<feature>.sh` or `cmd/smoke-test/`

**Test structure:**
```bash
#!/bin/bash
# Smoke test for Feature: Launch missions from beads

echo "Testing: capsule launch creates worktree"
worktree_path=$(capsule launch test-001 | grep -o "Worktree: .*" | cut -d' ' -f2)
if [ -d "$worktree_path" ]; then
    echo "✓ Worktree created"
else
    echo "✗ Worktree not created"
    exit 1
fi

echo "Testing: capsule dock removes worktree cleanly"
capsule dock test-001
if [ ! -d "$worktree_path" ]; then
    echo "✓ Worktree removed cleanly"
else
    echo "✗ Worktree still exists"
    exit 1
fi
```

**If you can't write smoke tests, it's not a feature** - restructure as tasks under a user-facing feature.

## Tracer Bullet Strategy

**Build vertical slices through all layers**, then expand incrementally.

### Example: Authentication Feature

```
❌ Horizontal slicing (bad):
  Task 1: Build database layer
  Task 2: Build API layer
  Task 3: Build UI layer

✅ Tracer sequence (good):
  Task 1: Minimal auth flow (config → middleware → single endpoint)
    → Tracer: Proves authentication pattern works end-to-end
  Task 2: Add auth to remaining endpoints
    → Expansion: Apply proven pattern
  Task 3: Add token refresh
    → Expansion: Enhance proven pattern
```

### When to Use Tracer vs Prototype vs Spike

| Approach | Use When | Task Type |
|----------|----------|-----------|
| **Tracer** | Building feature foundation | Production task |
| **Prototype** | Testing idea for stakeholders | Demo/throwaway |
| **Spike** | Learning new technology | Research task |

**Most line-cook tasks should be tracers** - production code that builds incrementally.

**Use spike only for:** "Research patterns", "Evaluate approaches"

**Avoid prototypes** - they rarely get rewritten. Build production quality from the start.

## Validation Checklist

Before converting to beads, verify:

### Phase Level
- [ ] Title follows `"Phase N: <Capability Area>"` pattern
- [ ] Duration is realistic (e.g., "Week 1 (4-6 sessions)")
- [ ] Features are logically grouped

### Feature Level
- [ ] Title describes user-observable outcome
- [ ] User story follows "As a [user], I want [capability] so that [benefit]"
- [ ] Acceptance criteria (3-5) are user-observable
- [ ] Feature has CLI/API/UI interface (smoke-testable)
- [ ] Tracer strategy defined
- [ ] BDD tests map 1:1 to acceptance criteria
- [ ] Smoke tests defined

### Task (Course) Level
- [ ] Title describes what course does (tracer explanation)
- [ ] Tracer field explains what this proves
- [ ] Deliverable is clear and specific
- [ ] `tdd: true` for all courses
- [ ] Dependencies listed (if any)

## Conversion to Beads

After validation, convert to beads using:

```bash
./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml
```

The script will:
1. Create epics (phases)
2. Create features with acceptance criteria
3. Create tasks with descriptions and deliverables
4. Add task dependencies (`bd dep add`)
5. Add feature dependencies (`blocks`)

**Verification:**
```bash
bd ready    # Should show first available courses
bd blocked  # Should show blocked features
bd show <epic-id>    # Check hierarchy
bd show <feature-id>  # Check children
```

## Example Complete Menu Plan

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
        user_story: "As a capsule orchestrator, I want to execute commands in tmux sessions so that I can programmatically control OpenCode TUI"
        acceptance_criteria:
          - "Can create/destroy tmux sessions"
          - "Can send commands with proper debouncing"
          - "Can capture session output"
        tracer_strategy:
          minimal_flow: "Create session → Send command → Capture output → Destroy"
          layers: "Tmux wrapper → Command execution → Output capture"
          expansion: "Window management, pane splitting (deferred)"
        blocks: ["feature-1.2"]
        bdd_tests:
          - test: "TestFeature_ExecuteCommandsInTmuxSessions"
            scenarios:
              - "Acceptance_Criterion_1_Create_destroy_tmux_sessions"
              - "Acceptance_Criterion_2_Send_commands_with_debouncing"
              - "Acceptance_Criterion_3_Capture_session_output"
        smoke_tests:
          - "capsule tmux create creates session"
          - "capsule tmux send executes command"
          - "capsule tmux capture retrieves output"
          - "capsule tmux destroy removes session"
        
        tasks:
          - title: "Port tmux wrapper from gastown"
            priority: 1
            tracer: "Foundation layer - proves tmux integration works"
            description: |
              - Copy internal/tmux/tmux.go structure
              - Adapt for Capsule needs
              - Add session lifecycle functions
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

## Tips

- **Use tracer bullet methodology**: Break features into vertical slices through layers
- **Start with menu plan**: Human-readable planning before bead creation
- **Define tracer strategy**: Identify minimal flow, layers, and expansion plan
- **Plan BDD tests upfront**: Define acceptance criteria and test structure during planning
- **Order tasks as tracers**: Foundation first, orchestration last
- **Review before converting**: Easier to edit YAML than beads
- **Be specific**: Include deliverables and references
- **Think dependencies**: What must be done first?
- **Defer complexity**: Advanced features come after basic flow works

See [Vertical Slicing](../guidance/vertical-slicing.md) for complete methodology.
