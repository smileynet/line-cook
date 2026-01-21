---
description: Sync state, load context, show ready tasks
---

## Summary

**Sync state and identify ready tasks.** Part of prep → cook → serve → tidy.

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Invoke CLI

```bash
lc prep
```

### Step 2: Display Output

The CLI syncs git, syncs beads (if present), filters ready tasks, and outputs the session summary.

Display the output directly to the user.

### Step 3: Completion

The CLI output includes the NEXT STEP guidance.

If sync failed, inform user of the error and suggest:
- Resolve manually and run `/line-prep` again
- Run `/line-cook` to proceed offline (will sync later)

## Example Usage

```
/line-prep
```

This command takes no arguments.
