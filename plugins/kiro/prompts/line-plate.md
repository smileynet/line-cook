**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Validate completed features and create acceptance documentation.** Final step before feature completion.

**Arguments:** `$ARGUMENTS` (optional) - Feature bead ID to validate

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Feature to Validate

**If the user provided a feature bead ID:**
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

### Step 3: Review BDD Test Quality with Maitre

Delegate BDD test quality review to maitre agent:

```
Use task tool to invoke maitre agent:
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
- Tests exercise real system operations, not mocked simulations

Report any critical issues before proceeding with plate phase.", agent="maitre")
```

**If maitre unavailable:** Review BDD tests manually using the checklist above.

**Wait for BDD quality assessment.**

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

### Step 7: Check for Epic Completion

After closing the feature, check if all sibling features under the parent epic are now closed:

```bash
# Get parent epic
PARENT=$(bd show <feature-id> --json | jq -r '.[0].parent // empty')

if [ -n "$PARENT" ]; then
  # Check parent is an epic
  PARENT_TYPE=$(bd show $PARENT --json | jq -r '.[0].issue_type // empty')

  if [ "$PARENT_TYPE" = "epic" ]; then
    TOTAL=$(bd list --parent=$PARENT --all --json | jq 'length')
    CLOSED=$(bd list --parent=$PARENT --all --json | jq '[.[] | select(.status == "closed")] | length')

    if [ "$TOTAL" -eq "$CLOSED" ]; then
      EPIC_READY=true
    fi
  fi
fi
```

**If epic is ready:** Include the suggestion in the output summary (Step 9).
**Otherwise:** No action needed.

### Step 8: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
git add docs/features/<feature-id>-acceptance.md CHANGELOG.md
git commit -m "feat: complete <feature-title> (<feature-id>)

Feature validation complete:
- All acceptance criteria verified
- BDD tests approved by maitre
- Smoke tests passing

Acceptance report: docs/features/<feature-id>-acceptance.md"

bd sync
git push
```

### Step 9: Output Summary

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
  [✓] BDD tests approved (maitre)
  [✓] Code review complete (sous-chef)

Deliverables:
  - Acceptance report: docs/features/<feature-id>-acceptance.md
  - CHANGELOG.md updated
  - Feature bead closed

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next feature or task
```

**If parent epic is now fully closed (all features plated):**

Append to the output:

```
───────────────────────────────────────────
EPIC READY TO CLOSE
───────────────────────────────────────────

All features under <epic-id> (<epic-title>) are now plated.

NEXT STEP: Run @line-close-service <epic-id>
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
  3. Retry @line-plate <feature-id>

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
  2. Re-run BDD review with maitre
  3. Retry @line-plate <feature-id>

───────────────────────────────────────────
```

## Design Notes

The plate phase ensures features are production-ready before completion:

1. **End-to-end validation** - All tests must pass
2. **BDD quality** - Tests must meet quality bar (maitre review)
3. **Documentation** - Acceptance report provides comprehensive record
4. **Changelog** - Track feature delivery for users

**When to run:**
- After all child tasks for a feature are closed
- Before closing the feature bead
- During `@line-run` when feature completion is detected

**Do NOT run on:**
- Partially completed features (tasks still open)
- Epics (use `@line-close-service` for epics)
- Tasks (only features have BDD tests)

## Example Usage

```
@line-plate lc-abc.1  # Validate feature lc-abc.1
```

This command takes a feature ID as argument. It will:
1. Run tests to validate feature
2. Review BDD test quality
3. Create acceptance documentation
4. Update CHANGELOG.md
5. Close feature bead
6. Check for epic completion (suggest close-service if ready)
7. Commit and push
