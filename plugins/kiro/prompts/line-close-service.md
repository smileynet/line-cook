**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Validate completed epic and create acceptance documentation.** Final step after all features under an epic have been plated.

**Arguments:** `$ARGUMENTS` (required) - Epic bead ID to validate

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Epic to Validate

**If the user provided an epic bead ID:**
- Use that epic ID directly

**Otherwise:**
- Find recently completed epics: `bd list --status=open --type=epic --limit=5`
- Identify the epic whose children are all closed

**Validation:**

```bash
# Verify this is an epic
EPIC=$(bd show <epic-id> --json | jq -r '.[0].issue_type // empty')
if [ "$EPIC" != "epic" ]; then
  echo "Error: <epic-id> is not an epic (type: $EPIC)"
  exit 1
fi

# Verify all children are closed
TOTAL=$(bd list --parent=<epic-id> --all --json | jq 'length')
CLOSED=$(bd list --parent=<epic-id> --all --json | jq '[.[] | select(.status == "closed")] | length')

if [ "$TOTAL" -ne "$CLOSED" ]; then
  echo "Error: Epic has open children ($CLOSED/$TOTAL closed)"
  echo "Close all features first with @line-plate"
  exit 1
fi
```

**Important:** Only run close-service on epics where ALL child features are closed (plated).

### Step 2: Run E2E Validation Tests

Execute tests to verify the epic's features work together end-to-end:

```bash
# Run all tests
<test command>  # e.g., go test ./..., pytest, npm test, cargo test

# Run integration/E2E tests if available
<e2e test command>  # e.g., pytest tests/e2e/, npm run test:e2e

# Run smoke tests if available
./scripts/smoke-test.sh  # or project-specific smoke test
```

**If tests fail:**
- Investigate and fix issues
- Re-run tests
- Do NOT proceed until tests pass

### Step 3: E2E Review with Critic

Delegate E2E test quality review to critic agent:

```
Use task tool to invoke critic agent:
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
- Tests exercise real system interfaces, not mocked simulations

Report any critical issues before closing the epic.", agent="critic")
```

**If critic unavailable:** Perform inline E2E review using the checklist above.

**Wait for E2E coverage assessment.**

**If FAIL or NEEDS_WORK with critical issues:**
- Address issues
- Re-run E2E review
- Do NOT close epic until coverage is adequate

### Step 4: Create Epic Acceptance Documentation

Create epic acceptance documentation:

1. Create `docs/features/<epic-id>-acceptance.md`:
   ```bash
   mkdir -p docs/features
   ```

2. Fill in the template sections:
   - **Service Overview** - Epic capability and features included
   - **Guest Journey Validation** - E2E user journeys tested
   - **Smoke Test Results** - Critical path validation
   - **Cross-Feature Integration** - How features work together
   - **Kitchen Staff Sign-Off** - All agent approvals
   - **Guest Experience** - How users can use the capability
   - **Related Work** - Links to feature acceptance reports


### Step 5: Archive Planning Context

Archive the planning context if one exists:

```bash
EPIC_DESC=$(bd show <epic-id> --json | jq -r '.[0].description')
CONTEXT_PATH=$(echo "$EPIC_DESC" | grep -oP 'Planning context: \K.*')

if [ -n "$CONTEXT_PATH" ]; then
  # Update context README status to archived
  sed -i 's/^**Status:** .*/\*\*Status:\*\* archived/' "$CONTEXT_PATH/README.md"
  git add "$CONTEXT_PATH/README.md"
fi
```

**Graceful no-op:** If no planning context link — skip this step.

### Step 6: Update CHANGELOG.md

Add epic completion to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- <epic-title> (<epic-id>)
  - <summary of epic>
  - Features: <list of features delivered>
```

### Step 7: Close Epic Bead

Close the epic bead to mark completion:

```bash
bd close <epic-id>
```

### Step 8: Commit and Push

Commit acceptance documentation and CHANGELOG:

```bash
git add docs/features/<epic-id>-acceptance.md CHANGELOG.md
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

### Step 9: Output Summary

```
SERVICE CLOSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <epic-id> - <epic-title>
Status: Full service validated

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
  - Epic report: docs/features/<epic-id>-acceptance.md
  - CHANGELOG.md updated
  - Epic bead closed

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next epic or feature
```

## Error Handling

### Tests Fail

```
⚠️ EPIC VALIDATION FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <id> - <title>

Issue: <description of test failure>

Actions:
  1. Fix the failing tests
  2. Re-run: <test command>
  3. Retry @line-close-service <epic-id>

───────────────────────────────────────────
```

### E2E Quality Issues

```
⚠️ E2E COVERAGE ISSUES FOUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <id> - <title>

Critical Issues:
  - <Issue 1>
  - <Issue 2>

Actions:
  1. Address critical E2E issues
  2. Re-run E2E review with critic
  3. Retry @line-close-service <epic-id>

───────────────────────────────────────────
```

### Open Children

```
⚠️ EPIC NOT READY FOR CLOSE-SERVICE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <id> - <title>

Open children:
  - <feature-id> - <feature-title> (status: <status>)

Actions:
  1. Plate remaining features: @line-plate <feature-id>
  2. Retry @line-close-service <epic-id>

───────────────────────────────────────────
```

## Design Notes

The close-service phase validates epics after all features have been individually plated:

1. **E2E validation** - Cross-feature integration tests must pass
2. **E2E quality** - Tests must meet coverage bar (critic review)
3. **Documentation** - Epic acceptance report provides comprehensive record
4. **Changelog** - Track epic delivery for users
5. **Context archival** - Planning context marked as archived

**When to run:**
- After all child features for an epic are plated (closed)
- When `@line-prep` or `@line-plate` suggests it
- During `@line-run` when epic completion is detected

**Do NOT run on:**
- Epics with open features
- Features (use `@line-plate` for features)
- Tasks (only epics have cross-feature validation)

## Example Usage

```
@line-close-service lc-abc  # Validate and close epic lc-abc
```

This command takes an epic ID as argument. It will:
1. Verify all children are closed
2. Run E2E validation tests
3. Review E2E coverage (critic)
4. Create epic acceptance documentation
5. Archive planning context
6. Update CHANGELOG.md
7. Close epic bead
8. Commit and push
