Run full workflow cycle: prep → cook → serve → tidy. Primary entry point for focused work sessions.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on (passed to cook)

---

## Process

### Step 1: Run @line-prep

Sync state and identify available work.

Execute the prep workflow to:
- Sync with remote
- Display ready tasks
- Identify next task

### Step 2: Run @line-cook

Execute work with TDD cycle.

**If `$ARGUMENTS` provided:**
- Execute that specific task

**Otherwise:**
- Select highest priority ready task

Execute the task through:
- Claim task
- Load context
- TDD cycle (red → green → refactor)
- Verify completion
- Close task

### Step 3: Run @line-serve

Review changes before commit.

Review the code changes for:
- Correctness
- Security
- Style
- Completeness

Categorize any issues found.

### Step 4: Run @line-tidy

File discovered work, commit, and push.

- File beads for discovered issues
- Commit all changes
- Sync beads
- Push to remote

### Step 5: Check for Feature Completion

After tidying, check if the task completed a feature:

```bash
bd show <task-id>
```

**If task has a parent feature AND all sibling tasks are closed:**
- Run @line-plate to validate the feature
- Create acceptance documentation
- Close feature bead

### Step 6: Output Cycle Summary

```
╔══════════════════════════════════════════════════════════════╗
  ║  FULL SERVICE COMPLETE                                       ║
  ╚══════════════════════════════════════════════════════════════╝

WORK CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] PREP    ✓ synced
[2/5] COOK    ✓ executed
[3/5] SERVE   ✓ reviewed (<verdict>)
[4/5] TIDY    ✓ committed, pushed
[5/5] PLATE   ✓ (feature complete) | ○ (not applicable)

──────────────────────────────────────────

TASK: <id> - <title>

INTENT:
  <1-2 sentences from task description>

BEFORE → AFTER:
  <previous state> → <new state>

Files: <count> changed
Commit: <hash>
Issues filed: <count>

NEXT STEP: @line-prep (start new cycle)
```

## Error Handling

If any step fails:

1. **Prep fails** - Report sync error, stop workflow
2. **Cook fails** - Report what went wrong, offer to continue to tidy
3. **Serve fails** - Note review was skipped, continue to tidy
4. **Tidy fails** - Report push error, create bead for follow-up
5. **Plate fails** - Note feature validation incomplete, create bead

```
WORK CYCLE: Incomplete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] PREP    ✓
[2/5] COOK    ✓
[3/5] SERVE   ✗ (error: <reason>)
[4/5] TIDY    pending
[5/5] PLATE   pending

Failed at: <step>
Error: <description>

──────────────────────────────────────────

TASK: <id> - <title>

Run @line-tidy to save progress, or investigate the error.
```

## Design Notes

The @line-service command is the recommended entry point for focused work sessions:

1. **Ensures proper setup** - Prep runs first to sync state
2. **Maintains focus** - One task per cycle
3. **Enforces quality** - Serve reviews before commit
4. **Guarantees completion** - Tidy pushes changes

For exploratory sessions or when you need more control, use individual commands.

**NEXT STEP: @line-prep (start new cycle)**
