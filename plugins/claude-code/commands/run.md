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

### Step 1: Run /line:prep

Invoke the prep command to sync state and identify available work:

```
Skill(skill="line:prep")
```

Wait for prep to complete.

### Step 2: Run /line:cook

Invoke the cook command to execute work:

**If the user provided a task ID:**
```
Skill(skill="line:cook", args="$ARGUMENTS")
```

**Otherwise:**
```
Skill(skill="line:cook")
```

Wait for cook to complete. Cook will select a task, execute the work, and output findings for tidy.

### Step 3: Run /line:serve

Invoke the serve command for peer review:

```
Skill(skill="line:serve")
```

Wait for review to complete. Serve will invoke sous-chef subagent for code review and output a SERVE_RESULT block.

**Check the SERVE_RESULT verdict from serve output:**

- **APPROVED** (`continue: true`) → proceed to Step 4
- **NEEDS_CHANGES** (`continue: true`, `next_step: /line:cook`) → loop back to Step 2 (rework)
- **SKIPPED** (`continue: true`, `retry_recommended: true`) → proceed to Step 4 with retry note
- **BLOCKED** (`continue: false`) → STOP and wait for user decision (see Error Handling)

**On NEEDS_CHANGES verdict (Rework Loop):**
1. Reopen the task: `bd update <id> --status=in_progress`
2. Re-invoke cook (task will detect rework mode via serve comments):
   ```
   Skill(skill="line:cook", args="<task-id>")
   ```
3. Re-invoke serve
4. Repeat until APPROVED or BLOCKED
5. Maximum 3 rework attempts before requiring user decision

### Step 4: Run /line:tidy

Invoke tidy to file discovered work, commit, and push:

```
Skill(skill="line:tidy")
```

Tidy will file beads for discovered work, commit all changes, sync beads, and push to remote.

### Step 5: Check for Feature/Epic Completion

After tidying, check if the task completed a feature:

```bash
# Get task details to check parent
bd show <task-id>
```

**If task has a parent feature AND all sibling tasks are closed:**

1. Run plate phase for the feature:
   ```
   Skill(skill="line:plate", args="<feature-id>")
   ```

2. Wait for plate to complete. Plate handles maître review, acceptance docs, and CHANGELOG.

3. If plate output shows "EPIC READY TO CLOSE", run close-service:
   ```
   Skill(skill="line:close-service", args="<epic-id>")
   ```

**If no feature completed, skip plate phase and proceed to Step 6.**

### Step 6: Cycle Summary

After all steps complete, output summary derived from /tidy:

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

───────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────
Ready: <count> tasks | Blocked: <count>

  /clear       Clear context before next cycle (recommended)
  /line:run    Continue with next task
  /line:prep   Review state first
  /line:help   See all commands

Tip: Clear context between tasks to prevent accumulation.
```

## Error Handling

If any step fails:

1. **Prep fails** - Report sync error, stop workflow
2. **Cook fails** - Report what went wrong, offer to continue to tidy (to save progress)
3. **Serve verdict** - Check SERVE_RESULT (see below)
4. **Tidy fails** - Report push error, create bead for follow-up
5. **Plate fails** - Note feature validation incomplete, create bead for follow-up

### Serve Verdict Handling

After serve completes, check the SERVE_RESULT block:

| Verdict | continue | Action |
|---------|----------|--------|
| `APPROVED` | true | Continue to tidy |
| `NEEDS_CHANGES` | true | Loop back to cook (rework) |
| `SKIPPED` | true | Continue to tidy with retry recommendation |
| `BLOCKED` | false | **STOP workflow** - require user decision |

**On NEEDS_CHANGES verdict (Rework Loop):**
1. Reopen the task: `bd update <id> --status=in_progress`
2. Re-invoke cook with the task ID (task will detect rework mode via serve comments)
3. Re-invoke serve
4. Repeat until APPROVED or BLOCKED
5. Maximum 3 rework attempts before requiring user decision

```
REWORK REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Review found issues that should be addressed:

<list issues from SERVE_RESULT>

Looping back to /line:cook for rework (attempt <n>/3)...
```

**On BLOCKED verdict:**
```
WORKFLOW STOPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Review found blocking issues that must be addressed:

<list blocking issues from SERVE_RESULT>

Options:
1. Fix the issues, then run /line:run again
2. Override: run /line:tidy directly (skips review gate)
3. Abandon: leave changes uncommitted for manual handling

Waiting for user decision...
```

**On SKIPPED verdict (API error):**
```
Review skipped due to API error. Continuing to tidy.
Recommendation: Run /line:serve manually after tidy completes.
```

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

The `/line:run` command is the recommended entry point for focused work sessions. It:

1. **Ensures proper setup** - Prep runs first to sync state
2. **Maintains focus** - One task per cycle
3. **Enforces quality** - Serve reviews before commit
4. **Guarantees completion** - Tidy pushes changes

For exploratory sessions or when you need more control, use the individual commands directly.

## Example Usage

```
/line:run              # Full cycle with auto-selected task
/line:run lc-042       # Full cycle with specific task
```
