---
description: Commit changes, sync beads, and push to remote
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, TodoWrite
---

## Summary

**File discovered issues, commit changes, and push to remote.** Part of prep → cook → serve → tidy.

This is where findings from `/line:cook` and `/line:serve` get filed as beads.

---

## Bead Creation Reference

Use this when filing discovered issues:

```bash
# Standard issues (blocking tasks)
bd create --title="..." --type=task|bug|feature --priority=0-4

# Priority: 0=critical, 1=high, 2=medium, 3=low, 4=backlog
# Types: task, bug (broken), feature (new capability)

# Minor improvements (review later)
bd create --title="..." --type=task --priority=4 --parent=<retrospective-epic>
```

**Retrospective Epic Pattern:**

For minor suggestions, improvements, and "nice-to-haves" discovered during execution, file them to a retrospective epic. This keeps the main backlog focused on real issues.

```bash
# One-time setup (if not exists)
bd create --title="Retrospective" --type=epic --priority=4

# Then file minor items as children
bd create --title="Consider refactoring X" --type=task --priority=4 --parent=<retro-epic-id>
```

## Process

### Step 1: File Discovered Issues

Review findings from `/line:cook` and `/line:serve` and create beads:

**Blocking issues** (needs attention):
```bash
bd create --title="<issue>" --type=bug|task --priority=1-3
```

**Non-blocking findings** (review later):
```bash
bd create --title="<suggestion>" --type=task --priority=4 --parent=<retro-epic>
```

### Step 2: Review In-Progress Issues

Check current task state:
```bash
bd list --status=in_progress
```

For each **in-progress** issue:
- If task appears complete based on git changes → `bd close <id>`
- If task is incomplete → leave as-is (will be picked up next session)
- If status is unclear → create a P4 bead to review later

**Do NOT ask the user** - make a reasonable judgment or file a bead.

### Step 3: Commit Changes

Show pending changes:
```bash
git status
```

If changes exist:
1. Stage all relevant files: `git add -A`
2. Create a commit with a descriptive message summarizing the session
3. Use conventional commit format (feat:, fix:, docs:, etc.)

### Step 4: Sync and Push

```bash
bd sync                        # Commit beads changes
git pull --rebase && git push  # Push to remote (if remote exists)
```

If no remote is configured, skip the push step.

If push fails:
```bash
bd create --title="Resolve git push failure: <error>" --type=bug --priority=2
```

### Step 5: Record Session Summary

**Add final comment to the task:**
```bash
bd comments add <id> "PHASE: TIDY
Status: completed

SESSION SUMMARY
━━━━━━━━━━━━━━━
Task completed:
  <summary of what was accomplished>

Problems encountered:
  - <problem>: <how resolved>

Issues filed:
  - <new-id>: <title> [P<n>]

Commit: <hash>
Push: <success|failed>"
```

### Step 6: Output Summary

```
TIDY: Session cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SESSION SUMMARY
━━━━━━━━━━━━━━━

Task completed:
  Task: <id> - <title>
  <1-2 sentence summary of what was accomplished>

Files changed:
  M src/foo.ts (+45, -12)
  A src/bar.ts (+78)

Problems encountered:
  - <problem description>
    Resolution: <how it was resolved>
  - (none)

Issues closed: <count>
  ✓ <id>: <title>

Issues filed: <count>
  + <new-id>: <title> [P<n>]
  + <new-id>: <title> [P4/retro]

Commit: <hash>
  <commit message>

Push: ✓ origin/main | ⚠️ <error> | skipped (no remote)

Session complete.
```

## Design Rationale

This command is intentionally **non-interactive** to support:

1. **Workflow velocity** - No blocking on user input
2. **Deferred decisions** - Unclear items become beads, not blockers
3. **Session end discipline** - Quick cleanup without decision fatigue
4. **Information when needed** - Bead creation reference provided here, where it's actually used

The pattern "file, don't block" means any concern that would require user judgment gets captured as a bead for later triage rather than interrupting the current flow.

## Example Usage

```
/line:tidy
```

This command takes no arguments.
