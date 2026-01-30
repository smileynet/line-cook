Convert plan to beads and create test specifications (execution). Third and final phase of mise en place.

**Input:** `docs/planning/menu-plan.yaml` (approved by user)
**Output:**
- Beads in `.beads/`
- BDD specs: `tests/features/<feature-name>.feature`
- TDD specs: `tests/specs/<task-name>.md`

---

## Process

### Step 1: Validate Menu Plan Exists

```bash
if [ ! -f docs/planning/menu-plan.yaml ]; then
    echo "Error: Menu plan not found. Run @line-plan first."
    exit 1
fi
```

### Step 2: Convert Menu Plan to Beads

```bash
./scripts/menu-plan-to-beads.sh docs/planning/menu-plan.yaml
```

Creates epics, features, tasks with dependencies.

### Step 3: Create BDD Specs

For each feature, create `tests/features/<feature-id>.feature`:

```gherkin
Feature: <title>
  As a <role>
  I want to <action>
  So that <benefit>

  Scenario: <acceptance criterion>
    Given the preconditions are met
    When the action is performed
    Then <expected outcome>
```

### Step 4: Create TDD Specs

For tasks with `tdd: true`, create `tests/specs/<task-slug>.md`:

```markdown
# Test Specification: <title>

## Tracer
<tracer explanation>

## Test Cases
| Input | Expected Output | Notes |
|-------|-----------------|-------|
| TODO | TODO | Based on tracer |
```

### Step 5: Verify Beads

```bash
bd list
bd ready
bd show <epic-id>
```

### Step 6: Sync and Commit

```bash
bd sync
git add docs/planning/menu-plan.yaml .beads/ tests/
git commit -m "plan: Create menu plan"
git push
```

### Step 7: Output Summary

```
MISE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Beads Created:
  Epics: <N>
  Features: <M>
  Tasks: <L>

Test Specs Created:
  BDD: <N> .feature files
  TDD: <M> .md files

NEXT STEP: Run @line-prep to start working on tasks
```
