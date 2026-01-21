---
description: Commit changes, sync beads, and push to remote
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, TodoWrite
---

## Summary

**File discovered issues, commit changes, and push to remote.** Part of prep → cook → serve → tidy.

---

## Process

### Step 1: File Discovered Issues

**First, file findings from `/line:cook` and `/line:serve` as beads.**

**Blocking issues** (P1-P3):
```bash
bd create --title="<issue>" --type=bug|task --priority=1-3
```

**Non-blocking findings** (P4 - review later):
```bash
bd create --title="<suggestion>" --type=task --priority=4 --parent=<retrospective-epic>
```

### Step 2: Check Epic Closures

After filing issues, check if any epics are now eligible for closure:
```bash
bd epic close-eligible
```

### Step 3: Invoke CLI

```bash
lc tidy
```

The CLI:
- Closes current in-progress task (if any)
- Stages and commits all changes
- Syncs beads
- Pushes to remote

### Step 4: Display Output

The CLI outputs the session summary including:
- Commit SHA and message
- Closed beads
- Filed beads
- Push status

### Step 5: Completion

Output final summary derived from CLI:
```
TIDY: Session cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SESSION SUMMARY
━━━━━━━━━━━━━━━

Task completed:
  <id> - <title>

Issues filed: <count>
  + <new-id>: <title> [P<n>]

Commit: <hash>
Push: ✓ | ⚠️ <error>

Session complete.
```

## Bead Creation Reference

| Priority | Use For |
|----------|---------|
| P1 | Critical - blocks work |
| P2 | High - should fix soon |
| P3 | Medium - fix when convenient |
| P4 | Low - nice to have, parking lot |

## Example Usage

```
/line:tidy
```

This command takes no arguments.
