> **INSTRUCTIONS**: Execute this workflow now. Follow each step below. Do not display, summarize, or recreate this content as a file.

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

```bash
if [ ! -f docs/planning/menu-plan.yaml ]; then
    echo "Error: Menu plan not found. Run @line-scope first."
    exit 1
fi
```

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
- Generate test specification files

### Step 3: Create BDD Test Specifications

For each feature with acceptance criteria, create a Gherkin `.feature` file:

**File:** `tests/features/<feature-id>-<feature-name>.feature`

```gherkin
Feature: Execute commands in tmux sessions
  As a capsule orchestrator
  I want to execute commands in tmux sessions
  So that I can programmatic control OpenCode TUI

  Scenario: Create and destroy tmux sessions
    Given no tmux session named "test-session" exists
    When I create a tmux session named "test-session"
    Then the session "test-session" should exist
```

### Step 4: Create TDD Test Specifications

For each task with `tdd: true`, create a test specification:

**File:** `tests/specs/<task-title-slugified>.md`

```markdown
# Test Specification: Port tmux wrapper from gastown

## Tracer
Foundation layer - proves tmux integration works

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| NewTmux() | Returns Tmux instance | Constructor works |

## Edge Cases
- [ ] Empty session name
- [ ] Invalid characters in session name

## Implementation Notes
These specs will be translated to language-specific tests during /cook.
```

### Step 5: Verify Beads and Dependencies

```bash
bd list              # See all beads
bd ready             # See available work
bd show <epic-id>    # View epic with child features
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

TDD specs created:
- <task-1>.md"
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

Commit: <hash>

Available tasks:
  <id> - <title>
```

Then ask the user how they'd like to proceed:

- **Start working -- @line-prep** — Begin the execution cycle
- **Done for now** — End the session

Wait for the user's response before continuing. If user chooses to start working, run `@line-prep`.

---

## Example Usage

```
@line-finalize
```

