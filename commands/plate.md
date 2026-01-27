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
go test ./...

# Run feature-specific BDD tests
go test ./internal/<package> -run TestFeature -v

# Run smoke tests if available
./scripts/smoke-test-<feature>.sh
```

**If tests fail:**
- Investigate and fix issues
- Re-run tests
- Do NOT proceed with plate phase until tests pass

### Step 3: Review BDD Test Quality with Sommelier

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

### Step 7: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- BDD tests approved by maître
- Smoke tests passing

Acceptance report: docs/features/<feature-id>-acceptance.md"

bd sync
git push
```

### Step 8: Output Summary

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
