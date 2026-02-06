---
description: Validate completed feature and create acceptance documentation
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite
---

## Summary

**Validate completed features and create acceptance documentation.** Final step before feature completion.

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Feature to Validate

Select the feature to validate:

```bash
# Option 1: Use argument
/plate <feature-id>

# Option 2: Find recently completed features
bd list --status=closed --type=feature --limit=5
```

**Important:** Only run plate phase on fully completed features (all child tasks closed).

### Step 2: Run Feature Validation

Execute tests to verify feature works end-to-end:

```bash
# Run all tests
<test command>  # e.g., go test ./..., pytest, npm test, cargo test

# Run feature-specific tests
<feature test command>  # e.g., go test -run TestFeature, pytest tests/features/, npm test -- --grep "Feature"

# Run smoke tests if available
./scripts/smoke-test-<feature>.sh  # or project-specific smoke test
```

**If tests fail:**
- Investigate and fix issues
- Re-run tests
- Do NOT proceed with plate phase until tests pass

### Step 3: Review BDD Test Quality with Maître

Delegate BDD test quality review to maître subagent:

```
Use Task tool to invoke maître subagent:
Task(description="Review feature test quality", prompt="Review BDD tests for feature <feature-id>

Feature: <feature-title>
Acceptance criteria:
- <criteria 1>
- <criteria 2>
- <criteria 3>

Verify:
- All acceptance criteria have tests
- Given-When-Then structure used
- Tests map to acceptance criteria
- User perspective documented
- Error scenarios included

Report any critical issues before proceeding with plate phase.", subagent_type="maitre")
```

**Wait for BDD quality assessment.**

**If critical issues found:**
- Address issues
- Re-run BDD review
- Do NOT proceed until quality bar is met

### Step 4: Create Feature Acceptance Documentation

Create acceptance documentation using the multi-course meal template:

1. Copy the template to `docs/features/<feature-id>-acceptance.md`:
   ```bash
   mkdir -p docs/features
   cp docs/templates/feature-acceptance.md docs/features/<feature-id>-acceptance.md
   ```

2. Fill in the template sections:
   - **Chef's Selection** - User story from feature definition
   - **Tasting Notes** - Map each acceptance criterion to verification evidence
   - **Quality Checks** - Document BDD and smoke test results
   - **Kitchen Staff Sign-Off** - Record agent approvals
   - **Guest Experience** - Show users how to use the feature
   - **Kitchen Notes** - Capture limitations, ideas, deployment info
   - **Related Orders** - Link to completed tasks and related features

3. Remove the "Usage Instructions" section from the filled template

See [`docs/templates/feature-acceptance.md`](../docs/templates/feature-acceptance.md) for the full template.

### Step 5: Update CHANGELOG.md

Add feature to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- <feature-title> (<feature-id>)
  - <summary of feature>
  - <key capabilities delivered>
```

### Step 6: Close Feature Bead

Close the feature bead to mark completion:

```bash
bd close <feature-id>
```

### Step 6b: Epic Plate Phase (If Last Feature)

After closing the feature, check if all sibling features under the parent epic are now closed:

```bash
# Get parent epic
PARENT=$(bd show <feature-id> --json | jq -r '.[0].parent // empty')

if [ -n "$PARENT" ]; then
  # Check if all children are closed
  TOTAL=$(bd list --parent=$PARENT --json | jq 'length')
  CLOSED=$(bd list --parent=$PARENT --json | jq '[.[] | select(.status == "closed")] | length')

  if [ "$TOTAL" -eq "$CLOSED" ]; then
    echo "All features complete — triggering epic plate phase"
    # Continue to Step 6c for epic validation
  fi
fi
```

**Graceful no-op:** If no parent epic or siblings still open — skip epic plate steps.

### Step 6c: Epic E2E Review with Critic (If Epic Complete)

When all features of an epic are closed, invoke the critic agent for E2E review:

```
Use Task tool to invoke critic subagent:
Task(description="Review epic E2E coverage", prompt="Review E2E test coverage for epic <epic-id>

Epic: <epic-title>
Features completed:
- <feature-1>
- <feature-2>
- <feature-3>

Verify:
- Critical user journeys are tested end-to-end
- Cross-feature integration points are validated
- Smoke tests exist for critical paths
- Testing approach fits project type
- No major antipatterns

Report any critical issues before closing the epic.", subagent_type="critic")
```

**Wait for E2E coverage assessment.**

**If FAIL or NEEDS_WORK with critical issues:**
- Address issues
- Re-run E2E review
- Do NOT close epic until coverage is adequate

### Step 6d: Create Epic Acceptance Documentation (If Epic Complete)

Create epic acceptance documentation using the full service template:

1. Copy the template to `docs/features/<epic-id>-acceptance.md`:
   ```bash
   mkdir -p docs/features
   cp docs/templates/epic-acceptance.md docs/features/<epic-id>-acceptance.md
   ```

2. Fill in the template sections:
   - **Service Overview** - Epic capability and features included
   - **Guest Journey Validation** - E2E user journeys tested
   - **Smoke Test Results** - Critical path validation
   - **Cross-Feature Integration** - How features work together
   - **Kitchen Staff Sign-Off** - All agent approvals
   - **Guest Experience** - How users can use the capability
   - **Related Work** - Links to feature acceptance reports

3. Remove the "Usage Instructions" section from the filled template

See [`docs/templates/epic-acceptance.md`](../docs/templates/epic-acceptance.md) for the full template.

### Step 6e: Archive Planning Context (If Epic Complete)

Archive the planning context if one exists:

```bash
EPIC_DESC=$(bd show $PARENT --json | jq -r '.[0].description')
CONTEXT_PATH=$(echo "$EPIC_DESC" | grep -oP 'Planning context: \K.*')

if [ -n "$CONTEXT_PATH" ]; then
  # Update context README status to archived
  sed -i 's/^**Status:** .*/\*\*Status:\*\* archived/' "$CONTEXT_PATH/README.md"
  git add "$CONTEXT_PATH/README.md"
fi
```

**Graceful no-op:** If no planning context link — skip this step.

### Step 6f: Close Epic (If Epic Complete)

Close the parent epic bead:

```bash
bd close $PARENT
```

### Step 7: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
# For feature-only plate:
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- BDD tests approved by maître
- Smoke tests passing

Acceptance report: docs/features/<feature-id>-acceptance.md"

# For epic plate (include epic artifacts):
git add docs/features/<feature-id>-acceptance.md docs/features/<epic-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <epic-title> (<epic-id>)

Epic validation complete:
- All features plated and accepted
- Critical user journeys validated by critic
- E2E and smoke tests passing
- Cross-feature integration verified

Epic report: docs/features/<epic-id>-acceptance.md"

bd sync
git push
```

### Step 8: Output Summary

**For feature-only plate:**

```
PLATE PHASE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: <id> - <title>
Status: ✅ Validated and complete

Acceptance Criteria:
  [✓] <Criterion 1>
  [✓] <Criterion 2>
  [✓] <Criterion 3>

Quality Assurance:
  [✓] Tests passing
  [✓] BDD tests approved (maître)
  [✓] Code review complete (sous-chef)

Deliverables:
  - Acceptance report: docs/features/<feature-id>-acceptance.md
  - CHANGELOG.md updated
  - Feature bead closed

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next feature or task
```

**For epic plate (last feature triggers epic completion):**

```
EPIC PLATE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <epic-id> - <epic-title>
Status: ✅ Full service validated

Features Plated:
  [✓] <feature-1>
  [✓] <feature-2>
  [✓] <feature-3>

User Journey Validation:
  [✓] <Journey 1> - tested end-to-end
  [✓] <Journey 2> - tested end-to-end

Quality Assurance:
  [✓] All smoke tests passing
  [✓] E2E coverage approved (critic)
  [✓] Cross-feature integration verified

Deliverables:
  - Feature report: docs/features/<feature-id>-acceptance.md
  - Epic report: docs/features/<epic-id>-acceptance.md
  - CHANGELOG.md updated
  - Feature and epic beads closed

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next epic or feature
```

## Error Handling

### Tests Fail

```
⚠️ FEATURE VALIDATION FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: <id> - <title>

Issue: <description of test failure>

Actions:
  1. Fix the failing tests
  2. Re-run: <test command>
  3. Retry /line:plate <feature-id>

───────────────────────────────────────────
```

### BDD Quality Issues

```
⚠️ BDD QUALITY ISSUES FOUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: <id> - <title>

Critical Issues:
  - <Issue 1>
  - <Issue 2>

Actions:
  1. Address critical BDD issues
  2. Re-run BDD review with maître
  3. Retry /line:plate <feature-id>

───────────────────────────────────────────
```

## Design Notes

The plate phase ensures features are production-ready before completion:

1. **End-to-end validation** - All tests must pass
2. **BDD quality** - Tests must meet quality bar (maître review)
3. **Documentation** - Acceptance report provides comprehensive record
4. **Changelog** - Track feature delivery for users

**When to run:**
- After all child tasks for a feature are closed
- Before closing the feature bead
- During `/line:run` when feature completion is detected

**Do NOT run on:**
- Partially completed features (tasks still open)
- Epics (use plate on individual features)
- Tasks (only features have BDD tests)

## Example Usage

```
/line:plate lc-abc.1  # Validate feature lc-abc.1
```

This command takes a feature ID as argument. It will:
1. Run tests to validate feature
2. Review BDD test quality
3. Create acceptance documentation
4. Update CHANGELOG.md
5. Close feature bead
6. Commit and push
