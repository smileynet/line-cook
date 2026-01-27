Quick workflow cycle: prep → cook → serve → tidy. Streamlined version of @line-service.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on

---

## Process

This is a streamlined version of @line-service that runs through the core workflow without the plate phase.

### Step 1: Prep
Sync state and identify next task.

```bash
git fetch origin
git pull --rebase
bd sync
bd ready
```

### Step 2: Cook
Execute the task with TDD cycle.

**If `$ARGUMENTS` provided:**
- Execute that specific task

**Otherwise:**
- Select highest priority ready task

```bash
bd update <id> --status=in_progress
# ... execute task ...
bd close <id>
```

### Step 3: Serve
Quick review of changes.

```bash
git diff
git status
```

Review for:
- Correctness
- Completeness
- Obvious issues

### Step 4: Tidy
Commit and push.

```bash
git add -A
git commit -m "<task-id>: <description>"
bd sync
git push
```

### Output Summary

```
╔══════════════════════════════════════════════════════════════╗
║  WORK CYCLE COMPLETE                                          ║
╚══════════════════════════════════════════════════════════════╝

[1/4] PREP  ✓ synced
[2/4] COOK  ✓ executed
[3/4] SERVE ✓ reviewed
[4/4] TIDY  ✓ pushed

──────────────────────────────────────────

TASK: <id> - <title>

Files: <count> changed
Commit: <hash>

NEXT STEP: @line-prep (start new cycle)
```

## When to Use

Use @line-work for:
- Quick task completion
- Simple bug fixes
- Small changes

Use @line-service for:
- Feature completion (includes plate phase)
- More thorough review cycle
- Multi-task sessions

## Error Handling

```
WORK CYCLE: Incomplete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] PREP  ✓
[2/4] COOK  ✗ (error: <reason>)
[3/4] SERVE pending
[4/4] TIDY  pending

Run @line-tidy to save partial progress.
```

**NEXT STEP: @line-prep (start new cycle)**
