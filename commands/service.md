---
description: Run full workflow cycle (prep→cook→serve→tidy)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, AskUserQuestion, Skill
---

## Summary

**Expeditor orchestrates full workflow: prep → cook → serve → tidy → plate.** Primary entry point for focused work sessions.

**Expeditor responsibilities:**
- Run prep checks and present ready tasks
- Delegate cooking to chef subagent
- Coordinate serving with sous-chef review
- Manage tidy phase (commit, push)
- Trigger plate phase for feature completion
- Handle failure conditions and coordinate recovery

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on (passed to cook)

---

## Process

### Step 1: Run /prep

Invoke the prep command to sync state and identify available work:

```
Skill(skill="line:prep")
```

Wait for prep to complete.

### Step 2: Run /cook

Invoke the cook command to execute work:

**If `$ARGUMENTS` provided:**
```
Skill(skill="line:cook", args="$ARGUMENTS")
```

**Otherwise:**
```
Skill(skill="line:cook")
```

Wait for cook to complete. Cook will select a task, execute the work, and output findings for tidy.

### Step 3: Run /serve

Invoke the serve command for peer review:

```
Skill(skill="line:serve")
```

Wait for review to complete. Serve will invoke sous-chef subagent for code review and categorize any issues found.

### Step 4: Run /tidy

Invoke tidy to file discovered work, commit, and push:

```
Skill(skill="line:tidy")
```

Tidy will file beads for discovered work, commit all changes, sync beads, and push to remote.

### Step 5: Check for Plate Phase (Feature Completion)

After tidying, check if the task completed a feature:

```bash
# Get task details to check parent
bd show <task-id>
```

**If task has a parent feature AND all sibling tasks are closed:**

1. Run feature validation:
   ```bash
   go test ./...
   go test ./internal/<package> -run TestFeature -v
   ```

2. Delegate to maître (BDD quality) subagent:
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

3. Wait for BDD quality assessment. Address any critical issues.

4. If BDD tests pass quality bar, proceed with plate phase:
   - Create feature acceptance documentation
   - Update CHANGELOG.md
   - Close feature bead
   - Commit and push feature report

**If no feature completed, skip plate phase and proceed to Step 6.**

### Step 6: Cycle Summary

After all steps complete, output summary derived from /tidy:

```
╔══════════════════════════════════════════════════════════════╗
║  FULL SERVICE COMPLETE                                         ║
╚══════════════════════════════════════════════════════════════╝

WORK CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] PREP    ✓ synced
[2/5] COOK    ✓ executed
[3/5] SERVE   ✓ reviewed (<verdict>)
[4/5] TIDY    ✓ committed, pushed
[5/5] PLATE ✓ (feature complete) | (not applicable)

Quality Gates:
  [✓] Test quality approved (taster)
  [✓] Code quality approved (sous-chef)
  [✓] BDD tests approved (maître, if applicable)

──────────────────────────────────────────

TASK: <id> - <title>

INTENT:
  <1-2 sentences from task description>
  Goal: <deliverable or acceptance criteria>

BEFORE → AFTER:
  <previous state> → <new state>
  <what couldn't be done> → <what can be done now>

Files: <count> changed
Commit: <hash>
Issues filed: <count>
```

## Error Handling

If any step fails:

1. **Prep fails** - Report sync error, stop workflow
2. **Cook fails** - Report what went wrong, offer to continue to tidy (to save progress)
3. **Serve fails** - Note review was skipped, continue to tidy
4. **Tidy fails** - Report push error, create bead for follow-up
5. **Plate fails** - Note feature validation incomplete, create bead for follow-up

```
WORK CYCLE: Incomplete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] PREP    ✓
[2/5] COOK    ✓
[3/5] SERVE   ✗ (error: <reason>)
[4/5] TIDY    pending
[5/5] PLATE pending

Failed at: <step>
Error: <description>

──────────────────────────────────────────

TASK: <id> - <title>

Run /line:tidy to save progress, or investigate the error.

If plate failed, feature bead will remain open for validation when issues are resolved.
```

## Design Notes

The `/line:service` command is the recommended entry point for focused work sessions. It:

1. **Ensures proper setup** - Prep runs first to sync state
2. **Maintains focus** - One task per cycle
3. **Enforces quality** - Serve reviews before commit
4. **Guarantees completion** - Tidy pushes changes

For exploratory sessions or when you need more control, use the individual commands directly.

## Example Usage

```
/line:service              # Full cycle with auto-selected task
/line:service lc-042       # Full cycle with specific task
```
