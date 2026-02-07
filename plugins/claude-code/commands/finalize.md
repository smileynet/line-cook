---
description: Convert plan to beads and create test specifications (execution)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill
---

## Summary

**Execution phase: create beads, write test specs, persist.** Third and final phase of mise en place.

This phase transforms the approved menu plan into actionable beads and creates language-agnostic test specifications.

**Input:** `docs/planning/menu-plan.yaml` (approved by user)
**Output:**
- Beads in `.beads/`
- BDD specs: `tests/features/<feature-name>.feature` (Gherkin)
- TDD specs: `tests/specs/<task-name>.md` (for tasks with `tdd: true`)

---

## Process

### Step 1: Validate Menu Plan Exists

Check that the menu plan exists and is ready for conversion:

```bash
if [ ! -f docs/planning/menu-plan.yaml ]; then
    echo "Error: Menu plan not found. Run /line:scope first."
    exit 1
fi
```

**If no menu plan exists:** Stop and instruct user to run `/line:scope`.

### Step 2: Convert Menu Plan to Beads

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
- Generate test specification files

**Or create beads manually:**
```bash
bd create --title="Phase 1: Foundation" --type=epic --priority=2
bd create --title="Feature 1.1: Execute commands in tmux sessions" --type=feature --parent=lc-abc --priority=3
bd create --title="Port tmux wrapper from gastown" --parent=lc-abc.1 --priority=1
bd dep add <new-task-id> <dependency-task-id>
```

### Step 3: Create BDD Test Specifications

For each feature with acceptance criteria, create a Gherkin `.feature` file:

**File:** `tests/features/<feature-id>-<feature-name>.feature`

```gherkin
# tests/features/feature-1.1-execute-commands-in-tmux-sessions.feature
Feature: Execute commands in tmux sessions
  As a capsule orchestrator
  I want to execute commands in tmux sessions
  So that I can programmatic control OpenCode TUI

  Background:
    Given a clean tmux environment

  Scenario: Create and destroy tmux sessions
    Given no tmux session named "test-session" exists
    When I create a tmux session named "test-session"
    Then the session "test-session" should exist
    When I destroy the session "test-session"
    Then the session "test-session" should not exist

  Scenario: Send commands with proper debouncing
    Given a tmux session named "test-session"
    When I send the command "echo hello"
    And I wait for debounce period
    Then the command should have executed
    And the output should contain "hello"

  Scenario: Capture session output
    Given a tmux session running "echo test-output"
    When I capture the session output
    Then the captured output should contain "test-output"
```

**Naming convention:** Map acceptance criteria to scenarios.

### Step 4: Create TDD Test Specifications

For each task with `tdd: true`, create a test specification:

**File:** `tests/specs/<task-title-slugified>.md`

```markdown
# Test Specification: Port tmux wrapper from gastown

## Tracer
Foundation layer - proves tmux integration works

## Context
- Copy internal/tmux/tmux.go structure
- Adapt for Capsule needs
- Deliverable: internal/tmux/tmux.go skeleton

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| NewTmux() | Returns Tmux instance | Constructor works |
| tmux.SessionExists("nonexistent") | false | Non-existent session check |
| tmux.SessionExists("existing") | true | Existing session check |

## Edge Cases
- [ ] Empty session name
- [ ] Invalid characters in session name
- [ ] Session name already exists

## Implementation Notes
These specs will be translated to language-specific tests during /cook.
```

### Step 5: Verify Beads and Dependencies

Check that beads were created correctly:

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
#     - Task: Port tmux wrapper from gastown
#     - Task: Implement session creation/destruction
```

### Step 5b: Update Planning Context

If a planning context folder exists (`docs/planning/context-<name>/`):

1. **Update README.md:**
   - Set status to `finalized`
   - Add epic bead ID
   - Add finalize summary (beads created, test specs)

2. **Link context from epic bead description:**
   ```bash
   DESC=$(bd show <epic-id> --json | jq -r '.[0].description')
   bd update <epic-id> --body-file=- <<EOF
   $DESC

   Planning context: docs/planning/context-<name>/
   EOF
   ```

### Step 6: Sync and Commit

```bash
bd sync
git add docs/planning/menu-plan.yaml .beads/ tests/features/ tests/specs/ docs/planning/context-*/
git commit -m "plan: Create menu plan for <phase>

- <N> phases planned
- <M> features with acceptance criteria
- <L> tasks with tracer strategy

BDD specs created:
- <feature-1>.feature
- <feature-2>.feature

TDD specs created:
- <task-1>.md
- <task-2>.md

Key features:
- Feature 1.1: <title>
- Feature 1.2: <title>

Tracer approach:
- Each task builds foundation for next
- Vertical slices through all layers
- Production quality from start"
git push
```

### Step 7: Handoff

Output the commit summary:

```
FINALIZE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Menu plan committed to beads and test specs created.

Beads Created:
  Epics: <N>
  Features: <M>
  Tasks: <L>

Test Specs Created:
  BDD (features/): <N> .feature files
  TDD (specs/): <M> .md files

Files committed:
  - docs/planning/menu-plan.yaml
  - .beads/ (N files)
  - tests/features/ (N files)
  - tests/specs/ (N files)

Commit: <hash>

Available tasks:
  <id> - <title>
  <id> - <title>
```

Then **use AskUserQuestion** to ask:

**Question:** "Planning complete. Beads and test specs committed. How would you like to proceed?"
**Options:**
  - "Start working -- /line:prep" — Begin the execution cycle
  - "Done for now" — End the session

If user chooses "Start working", invoke `Skill(skill="line:prep")`.
Otherwise, stop and output the summary.

---

## Test Specification Workflow

Test specs are **language-agnostic** templates that guide implementation:

1. **During /finalize** - Generate `.feature` and `.md` specs from menu plan
2. **During /cook RED phase** - Translate specs to actual test code
3. **During /cook GREEN phase** - Implement to pass the tests

This separates **what to test** (specs) from **how to test** (implementation).

---

## Directory Structure

After commit, the test structure should be:

```
tests/
├── features/
│   ├── feature-1.1-execute-commands-in-tmux.feature
│   └── feature-1.2-manage-worktrees.feature
└── specs/
    ├── port-tmux-wrapper.md
    ├── implement-session-creation.md
    └── implement-command-execution.md
```

---

## Example Usage

```
/line:finalize
```

This command will:
1. Validate menu plan exists
2. Convert menu plan to beads
3. Create BDD test specifications (.feature files)
4. Create TDD test specifications (.md files)
5. Verify bead hierarchy and dependencies
6. Commit all artifacts
7. Output summary with ready tasks
