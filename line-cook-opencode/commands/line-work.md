---
description: Run full workflow cycle (prep→cook→serve→tidy)
---

## Summary

**Run the full prep → cook → serve → tidy cycle.** Primary entry point for focused work sessions.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on (passed to cook)

---

## Process

Execute all steps in sequence without stopping between commands.

### Step 1: Run /line-prep

Read and follow `line-prep.md` to sync state and identify available work.

Wait for prep to complete.

### Step 2: Run /line-cook

Read and follow `line-cook.md` to execute work.

**If `$ARGUMENTS` provided:** Pass the task ID to cook for explicit task selection.

**Otherwise:** Cook will auto-select the highest priority ready task.

Wait for cook to complete.

### Step 3: Run /line-serve

Read and follow `line-serve.md` for peer review.

Wait for review to complete. **Check SERVE_RESULT verdict:**

- If `continue: true` → proceed to Step 4
- If `continue: false` (BLOCKED) → STOP and wait for user decision (see Error Handling)

### Step 4: Run /line-tidy

Read and follow `line-tidy.md` to file discovered work, commit, and push.

Tidy files discovered work, commits, syncs, and pushes.

### Step 5: Cycle Summary

```
WORK CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] PREP    ✓ synced
[2/4] COOK    ✓ executed
[3/4] SERVE   ✓ reviewed
[4/4] TIDY    ✓ committed, pushed

TASK: <id> - <title>
SUMMARY: <what was accomplished>
```

## Error Handling

If any step fails:
- **Prep fails**: Report sync error, stop workflow
- **Cook fails**: Report error, offer to continue to tidy (to save progress)
- **Serve fails**: Check SERVE_RESULT verdict (see below)
- **Tidy fails**: Report push error, create bead for follow-up

### Serve Verdict Handling

After serve completes, check the SERVE_RESULT block:

| Verdict | continue | Action |
|---------|----------|--------|
| `APPROVED` | true | Continue to tidy |
| `NEEDS_CHANGES` | true | Continue to tidy (issues will be filed) |
| `SKIPPED` | true | Continue to tidy with retry recommendation |
| `BLOCKED` | false | **STOP workflow** - require user decision |

**On BLOCKED verdict:**
```
⛔ WORKFLOW STOPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Review found blocking issues that must be addressed:

<list blocking issues from SERVE_RESULT>

Options:
1. Fix the issues, then run /line-work again
2. Override: run /line-tidy directly (skips review gate)
3. Abandon: leave changes uncommitted for manual handling

Waiting for user decision...
```

**On SKIPPED verdict (API error):**
```
⚠️ Review skipped due to API error. Continuing to tidy.
Recommendation: Run /line-serve manually after tidy completes.
```

## Example Usage

```
/line-work              # Full cycle with auto-selected task
/line-work lc-042       # Full cycle with specific task
```
