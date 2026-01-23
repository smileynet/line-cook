---
description: Feature validation and BDD test review
---

## Summary

**Validate completed features and create acceptance documentation.** Final step before feature completion.

**When run directly:** STOP after completing, show NEXT STEP, and wait for user.
**When run via `/line-work`:** Continue to the next step without stopping.

---

## Process

### Step 1: Identify Feature to Validate

Select the feature to validate:

```bash
# Option 1: Use argument
/line-dessert <feature-id>

# Option 2: Find recently completed features
bd list --status=closed --type=feature --limit=5
```

**Important:** Only run dessert service on fully completed features (all child tasks closed).

### Step 2: Run Feature Validation

Execute tests to verify feature works end-to-end:

```bash
# Run all tests
go test ./...

# Run feature-specific BDD tests
go test ./internal/<package> -run TestFeature -v

# Run smoke tests if available
./scripts/smoke-test-<feature>.sh
```

**If tests fail:**
- Investigate and fix issues
- Re-run tests
- Do NOT proceed with dessert service until tests pass

### Step 3: Review BDD Test Quality with Sommelier

Delegate BDD test quality review to sommelier subagent:

```
Use Task tool to invoke sommelier subagent:
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

Report any critical issues before proceeding with dessert service.", subagent_type="sommelier")
```

**Wait for BDD quality assessment.**

**If critical issues found:**
- Address issues
- Re-run BDD review
- Do NOT proceed until quality bar is met

### Step 4: Create Feature Acceptance Documentation

Create a comprehensive acceptance report documenting feature completion:

Create `docs/features/<feature-id>-acceptance.md`:

```markdown
# Feature Acceptance Report

**Feature:** <feature-title>
**ID:** <feature-id>
**Completed:** YYYY-MM-DD
**Parent Epic:** <epic-id> - <epic-title>

## Acceptance Criteria

- [x] <Criterion 1>
  - **Verification:** <how verified>
  - **Evidence:** <test or demonstration>

- [x] <Criterion 2>
  - **Verification:** <how verified>
  - **Evidence:** <test or demonstration>

- [x] <Criterion 3>
  - **Verification:** <how verified>
  - **Evidence:** <test or demonstration>

## BDD Tests

### Test: <TestName>

**Purpose:** Validate <aspect>

**Scenarios:**
- ✅ <Scenario 1> - <description>
- ✅ <Scenario 2> - <description>
- ✅ <Scenario 3> - <description>

**Results:** All scenarios passing

### Smoke Tests

- ✅ <Smoke test 1>
- ✅ <Smoke test 2>

**Results:** All smoke tests passing

## User Experience

**User Story:** As a <user>, I want <capability> so that <benefit>

**Verification:** <how user can verify feature works>

## Quality Assurance

**Code Review:** Approved by sous-chef
**Test Quality:** Approved by quality-control
**BDD Quality:** Approved by sommelier

## Known Limitations

- <Any known limitations or future work>

## Migration Notes

- <Any migration or deployment notes>

## Related Work

- **Tasks Completed:**
  - <task-id> - <task-title>
  - <task-id> - <task-title>

- **Related Features:**
  - <feature-id> - <feature-title>

---

**Status:** ✅ Feature Complete and Validated
```

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

### Step 7: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- BDD tests approved by sommelier
- Smoke tests passing

Acceptance report: docs/features/<feature-id>-acceptance.md"

bd sync
git push
```

### Step 8: Output Summary

```
DESSERT SERVICE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: <id> - <title>
Status: ✅ Validated and complete

Acceptance Criteria:
  [✓] <Criterion 1>
  [✓] <Criterion 2>
  [✓] <Criterion 3>

Quality Assurance:
  [✓] Tests passing
  [✓] BDD tests approved (sommelier)
  [✓] Code review complete (sous-chef)

Deliverables:
  - Acceptance report: docs/features/<feature-id>-acceptance.md
  - CHANGELOG.md updated
  - Feature bead closed

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next feature or task
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
  2. Re-run: go test ./...
  3. Retry /line-dessert <feature-id>

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
  2. Re-run BDD review with sommelier
  3. Retry /line-dessert <feature-id>

───────────────────────────────────────────
```

## Design Notes

The dessert service ensures features are production-ready before completion:

1. **End-to-end validation** - All tests must pass
2. **BDD quality** - Tests must meet quality bar (sommelier review)
3. **Documentation** - Acceptance report provides comprehensive record
4. **Changelog** - Track feature delivery for users

**When to run:**
- After all child tasks for a feature are closed
- Before closing the feature bead
- During `/line-work` when feature completion is detected

**Do NOT run on:**
- Partially completed features (tasks still open)
- Epics (use dessert on individual features)
- Tasks (only features have BDD tests)

## Example Usage

```
/line-dessert lc-abc.1  # Validate feature lc-abc.1
```

This command takes a feature ID as argument. It will:
1. Run tests to validate feature
2. Review BDD test quality
3. Create acceptance documentation
4. Update CHANGELOG.md
5. Close feature bead
6. Commit and push
