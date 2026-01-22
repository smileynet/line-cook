---
description: Orchestrate full prep→cook→serve→tidy workflow cycle
---

## Summary

**Run the full prep → cook → serve → tidy cycle.** Primary entry point for focused work sessions.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on (passed to cook)

---

## Process

**IMPORTANT:** When executing sub-commands, IGNORE their "STOP after completing" instructions. Those instructions apply when running commands standalone, not when orchestrated by `/line-work`. Continue through all steps without stopping.

### Step 1: Run /line-prep

Read and execute the prep command instructions:

```
Read(~/.config/opencode/commands/line-prep.md)
```

Execute all steps from that command. Wait for prep to complete before proceeding.

### Step 2: Run /line-cook

Read and execute the cook command instructions:

```
Read(~/.config/opencode/commands/line-cook.md)
```

**If `$ARGUMENTS` provided:** Pass `$ARGUMENTS` as the task to work on.

**Otherwise:** Let cook select the highest priority ready task.

Execute all steps from that command. Wait for cook to complete before proceeding.

### Step 3: Run /line-serve

Read and execute the serve command instructions:

```
Read(~/.config/opencode/commands/line-serve.md)
```

Execute all steps from that command. Wait for review to complete before proceeding.

### Step 4: Run /line-tidy

Read and execute the tidy command instructions:

```
Read(~/.config/opencode/commands/line-tidy.md)
```

Execute all steps from that command. Tidy will file beads for discovered work, commit all changes, sync beads, and push to remote.

### Step 5: Cycle Summary

After all steps complete, output summary derived from /line-tidy:

```
WORK CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] PREP    ✓ synced
[2/4] COOK    ✓ executed
[3/4] SERVE   ✓ reviewed (<verdict>)
[4/4] TIDY    ✓ committed, pushed

Files: <count> changed
Commit: <hash>
Issues filed: <count>

───────────────────────────────────────────

TASK: <id> - <title>

SUMMARY: <what was accomplished>
```

## Error Handling

If any step fails:

1. **Prep fails** - Report sync error, stop workflow
2. **Cook fails** - Report what went wrong, offer to continue to tidy (to save progress)
3. **Serve fails** - Note review was skipped, continue to tidy
4. **Tidy fails** - Report push error, create bead for follow-up

```
WORK CYCLE: Incomplete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] PREP    ✓
[2/4] COOK    ✓
[3/4] SERVE   ✗ (error: <reason>)
[4/4] TIDY    pending

Failed at: <step>
Error: <description>

───────────────────────────────────────────

TASK: <id> - <title>

Run /line-tidy to save progress, or investigate the error.
```

## Design Notes

The `/line-work` command is the recommended entry point for focused work sessions. It:

1. **Ensures proper setup** - Prep runs first to sync state
2. **Maintains focus** - One task per cycle
3. **Enforces quality** - Serve reviews before commit
4. **Guarantees completion** - Tidy pushes changes

For exploratory sessions or when you need more control, use the individual commands directly.

## Example Usage

```
/line-work              # Full cycle with auto-selected task
/line-work lc-042       # Full cycle with specific task
```
