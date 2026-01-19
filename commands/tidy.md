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

**Parking Lot Epics (Retrospective & Backlog):**

For minor suggestions, improvements, and "nice-to-haves" discovered during execution, file them to a parking lot epic. This keeps the main backlog focused on actionable work.

- **Retrospective** - Minor suggestions discovered during work (nits, "consider this", style preferences)
- **Backlog** - Low-priority someday/maybe items (ideas, nice-to-haves, future enhancements)

```bash
# One-time setup (if not exists)
bd create --title="Retrospective" --type=epic --priority=4
bd create --title="Backlog" --type=epic --priority=4

# File minor items as children
bd create --title="Consider refactoring X" --type=task --priority=4 --parent=<retro-epic-id>
bd create --title="Someday add feature Y" --type=task --priority=4 --parent=<backlog-epic-id>
```

**Important:** Items filed under Retrospective or Backlog epics are automatically excluded from `/line:prep` and `/line:cook` auto-selection. They're parked until explicitly requested via `/line:cook <task-id>`.

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

#### Research Findings (for research tasks)

When the task involved research (architecture analysis, spike, investigation), also capture findings:

**New beads for discoveries:**
```bash
bd create --title="Implement <finding>" --type=task --priority=2-3
bd create --title="Document <pattern>" --type=task --priority=3
```

**Update existing beads:**
```bash
bd comments add <id> "RESEARCH FINDINGS:
- <key insight 1>
- <key insight 2>
- Recommendation: <action>"
```

**Research output patterns:**
- Actionable improvement → Create task bead
- Architectural insight → Comment on epic or create doc task
- Blocker discovered → Create bug/task as dependency
- Option evaluated → Comment on research task
- Decision made → Update task description

**Tip:** Research tasks often yield multiple follow-up beads. This is expected.

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

### Step 3: Check for Epic Closures

After closing issues, check if any epics are now eligible for closure (all children complete):

```bash
bd epic close-eligible --dry-run
```

If epics are eligible:
1. Close them: `bd epic close-eligible`
2. For each closed epic, get its children for the summary:
   ```bash
   bd list --parent=<epic-id> --all --json
   ```

**Note:** Epic closures are significant milestones. They will be highlighted prominently in the session summary.

> **Epic Philosophy:** Epics use children (`--parent`) for grouping, not blocking dependencies.
> Dependencies between children establish order within an epic.
> See AGENTS.md for the full epic philosophy.

### Step 4: Commit Changes

Show pending changes:
```bash
git status
```

If changes exist:
1. Stage all relevant files: `git add -A`
2. Create a commit with a descriptive message summarizing the session
3. Use conventional commit format (feat:, fix:, docs:, etc.)

### Step 5: Sync and Push

```bash
bd sync                        # Commit beads changes
git pull --rebase && git push  # Push to remote (if remote exists)
```

If no remote is configured, skip the push step.

If push fails:
```bash
bd create --title="Resolve git push failure: <error>" --type=bug --priority=2
```

### Step 6: Record Session Summary

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

### Step 7: Output Summary

**If an epic was closed**, output the epic completion banner first:

```
════════════════════════════════════════════
  EPIC COMPLETE: <epic-id> - <epic-title>
════════════════════════════════════════════

Children completed (<count>):
  ✓ <id>: <title>
  ✓ <id>: <title>
  ✓ <id>: <title>
  ...

Impact:
  <1-2 sentence description of what capability/improvement is now complete,
   derived from the epic description>

════════════════════════════════════════════
```

**Then output the standard session summary:**

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

Epics completed: <count>
  ★ <epic-id>: <title> (<N> children)

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
