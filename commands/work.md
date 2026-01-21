---
description: Orchestrate full prep→cook→serve→tidy workflow cycle
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, AskUserQuestion, Skill
---

## Summary

**Run the full prep → cook → serve → tidy cycle.** Primary entry point for focused work sessions.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on (passed to cook)

---

## Process

Execute all steps in sequence without stopping between commands.

### Step 1: Run /prep

```
Skill(skill="line:prep")
```

Wait for prep to complete.

### Step 2: Run /cook

**If `$ARGUMENTS` provided:**
```
Skill(skill="line:cook", args="$ARGUMENTS")
```

**Otherwise:**
```
Skill(skill="line:cook")
```

Wait for cook to complete.

### Step 3: Run /serve

```
Skill(skill="line:serve")
```

Wait for review to complete.

### Step 4: Run /tidy

```
Skill(skill="line:tidy")
```

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
- **Serve fails**: Note review skipped, continue to tidy
- **Tidy fails**: Report push error, create bead for follow-up

## Example Usage

```
/line:work              # Full cycle with auto-selected task
/line:work lc-042       # Full cycle with specific task
```
