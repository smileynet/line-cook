Validate completed feature and create acceptance documentation. Final step before feature completion.

**Arguments:** `$ARGUMENTS` - Feature ID to validate (required)

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Feature to Validate

Select the feature to validate:

```bash
# Use argument
@line-plate <feature-id>

# Or find recently completed features
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
- Do NOT proceed until tests pass

### Step 3: Create Acceptance Documentation

Create acceptance documentation:

1. Create file `docs/features/<feature-id>-acceptance.md`
2. Fill in sections:
   - **Summary** - What was built
   - **Acceptance Criteria** - Map each criterion to verification
   - **Test Results** - Document test outcomes
   - **Usage** - Show users how to use the feature

### Step 4: Update CHANGELOG.md

Add feature to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- <feature-title> (<feature-id>)
  - <summary of feature>
  - <key capabilities delivered>
```

### Step 5: Close Feature Bead

Close the feature bead to mark completion:

```bash
bd close <feature-id>
```

### Step 6: Commit and Push

```bash
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- Tests passing

Acceptance report: docs/features/<feature-id>-acceptance.md"

bd sync
git push
```

### Step 7: Output Summary

```
PLATE PHASE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature: <id> - <title>
Status: ✓ Validated and complete

Acceptance Criteria:
  [✓] <Criterion 1>
  [✓] <Criterion 2>
  [✓] <Criterion 3>

Quality Assurance:
  [✓] Tests passing
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
  2. Re-run tests
  3. Retry @line-plate <feature-id>

───────────────────────────────────────────
```

## When to Run

- After all child tasks for a feature are closed
- Before closing the feature bead
- During @line-run when feature completion is detected

**Do NOT run on:**
- Partially completed features (tasks still open)
- Epics (use plate on individual features)
- Tasks (only features have acceptance criteria)

**NEXT STEP: @line-prep (start new cycle)**
