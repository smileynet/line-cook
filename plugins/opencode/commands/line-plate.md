---
description: Validate completed feature and create acceptance documentation
---


## Summary

**Validate completed features and create acceptance documentation.** Final step before feature completion.

**Arguments:** `$ARGUMENTS` (optional) - Feature bead ID to validate

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Feature to Validate

**If `$ARGUMENTS` provided:**
- Use that feature ID directly

**Otherwise:**
- Find recently completed features: `bd list --status=closed --type=feature --limit=5`

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

### Step 3: Review BDD Test Quality

Review BDD tests for quality:

**Verify:**
- All acceptance criteria have tests
- Given-When-Then structure used
- Tests map to acceptance criteria
- User perspective documented
- Error scenarios included
- Tests exercise real system operations, not mocked simulations

**If critical issues found:**
- Address issues
- Re-run BDD review
- Do NOT proceed until quality bar is met

### Step 4: Create Feature Acceptance Documentation

Create acceptance documentation using the multi-course meal format:

1. Create `docs/features/<feature-id>-acceptance.md` with the sections below:
   ```bash
   mkdir -p docs/features
   ```

2. Fill in the template sections:
   - **Chef's Selection** - User story from feature definition
   - **Tasting Notes** - Map each acceptance criterion to verification evidence
   - **Quality Checks** - Document BDD and smoke test results
   - **Kitchen Staff Sign-Off** - Record agent approvals
   - **Guest Experience** - Show users how to use the feature
   - **Kitchen Notes** - Capture limitations, ideas, deployment info
   - **Related Orders** - Link to completed tasks and related features


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

### Step 6b: Archive Planning Context (If Epic Complete)

After closing the feature, check if all sibling features under the parent epic are now closed:

```bash
PARENT=$(bd show <feature-id> --json | jq -r '.[0].parent // empty')
```

If parent exists and all children are closed:
1. Read epic description, find `Planning context:` path
2. Update context README status to `archived`
3. Include in commit

Graceful no-op if no parent epic, no context link, or siblings still open.

### Step 7: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- BDD tests approved
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
Status: Validated and complete

Acceptance Criteria:
  [✓] <Criterion 1>
  [✓] <Criterion 2>
  [✓] <Criterion 3>

Quality Assurance:
  [✓] Tests passing
  [✓] BDD tests reviewed
  [✓] Code review complete

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
  2. Re-run: <test command>
  3. Retry /line-plate <feature-id>

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
  2. Re-run BDD review
  3. Retry /line-plate <feature-id>

───────────────────────────────────────────
```

## Design Notes

The plate phase ensures features are production-ready before completion:

1. **End-to-end validation** - All tests must pass
2. **BDD quality** - Tests must meet quality bar
3. **Documentation** - Acceptance report provides comprehensive record
4. **Changelog** - Track feature delivery for users

**When to run:**
- After all child tasks for a feature are closed
- Before closing the feature bead
- During `/line-run` when feature completion is detected

**Do NOT run on:**
- Partially completed features (tasks still open)
- Epics (use plate on individual features)
- Tasks (only features have BDD tests)

## Example Usage

```
/line-plate lc-abc.1  # Validate feature lc-abc.1
```

This command takes a feature ID as argument. It will:
1. Run tests to validate feature
2. Review BDD test quality
3. Create acceptance documentation
4. Update CHANGELOG.md
5. Close feature bead
6. Commit and push
