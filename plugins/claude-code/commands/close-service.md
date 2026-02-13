---
description: Validate completed epic and create acceptance documentation
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite
---


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
  echo "Close all features first with /line:plate"
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

Delegate E2E test quality review to critic subagent:

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
- Tests exercise real system interfaces, not mocked simulations

Report any critical issues before closing the epic.", subagent_type="critic")
```

**Wait for E2E coverage assessment.**

**If FAIL or NEEDS_WORK with critical issues:**
- Address issues
- Re-run E2E review
- Do NOT close epic until coverage is adequate

### Step 4: Create Epic Acceptance Documentation

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

See [`docs/templates/epic-acceptance.md`](../../../docs/templates/epic-acceptance.md) for the full template.

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

### Step 8: Commit Acceptance Documentation

Commit acceptance documentation and CHANGELOG on the epic branch:

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
```

### Step 8.5: Merge Epic Branch to Main

After validation passes and documentation is committed, merge the epic branch:

```bash
EPIC_BRANCH="epic/<epic-id>"
CURRENT=$(git branch --show-current)

if [ "$CURRENT" = "$EPIC_BRANCH" ]; then
  EPIC_TITLE=$(bd show <epic-id> --json | jq -r '.[0].title')

  # Checkout main and merge
  git checkout main
  git pull --rebase

  if git merge --no-ff $EPIC_BRANCH -m "Merge epic <epic-id>: $EPIC_TITLE"; then
    # Success - delete branch and push
    git branch -d $EPIC_BRANCH
    git push origin main
    git push origin --delete $EPIC_BRANCH 2>/dev/null || true
  else
    # Merge conflict - abort and return to epic branch
    git merge --abort
    git checkout $EPIC_BRANCH

    bd create --title="Resolve merge conflict for epic <epic-id>" \
      --type=bug --priority=1 \
      --description="Epic <epic-id> ($EPIC_TITLE) completed but merge to main failed due to conflicts."

    echo "⚠️ MERGE CONFLICT - manual resolution required"
  fi
fi
```

**If not on an epic branch** (e.g., working directly on main), skip the merge step and just push:
```bash
git push
```

### Step 9: Output Summary

```
SERVICE CLOSED
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
  - Epic report: docs/features/<epic-id>-acceptance.md
  - CHANGELOG.md updated
  - Epic bead closed
  - Branch: epic/<epic-id> merged to main

Commit: <hash>
───────────────────────────────────────────

NEXT STEP: Continue with next epic or feature
```

**If merge failed (conflict):**

```
SERVICE CLOSED (with merge conflict)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Epic: <epic-id> - <epic-title>
Status: ✅ Validated but merge failed

⚠️ MERGE CONFLICT
Epic branch could not be merged to main.

Conflicts require manual resolution:
  1. Resolve conflicts manually
  2. git add <resolved-files>
  3. git commit
  4. git push origin main
  5. git branch -d epic/<epic-id>

Bug bead created: <new-bead-id>
───────────────────────────────────────────
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
  3. Retry /line:close-service <epic-id>

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
  3. Retry /line:close-service <epic-id>

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
  1. Plate remaining features: /line:plate <feature-id>
  2. Retry /line:close-service <epic-id>

───────────────────────────────────────────
```

## Design Notes

The close-service phase validates epics after all features have been individually plated:

1. **E2E validation** - Cross-feature integration tests must pass
2. **E2E quality** - Tests must meet coverage bar (critic review)
3. **Documentation** - Epic acceptance report provides comprehensive record
4. **Changelog** - Track epic delivery for users
5. **Context archival** - Planning context marked as archived
6. **Branch merge** - Epic branch merged to main (Claude Code only)

**When to run:**
- After all child features for an epic are plated (closed)
- When `/line:prep` or `/line:plate` suggests it
- During `/line:run` when epic completion is detected

**Do NOT run on:**
- Epics with open features
- Features (use `/line:plate` for features)
- Tasks (only epics have cross-feature validation)

## Example Usage

```
/line:close-service lc-abc  # Validate and close epic lc-abc
```

This command takes an epic ID as argument. It will:
1. Verify all children are closed
2. Run E2E validation tests
3. Review E2E coverage (critic)
4. Create epic acceptance documentation
5. Archive planning context
6. Update CHANGELOG.md
7. Close epic bead
8. Commit acceptance docs
9. Merge epic branch to main (Claude Code only)
