File discovered issues, commit changes, and push to remote. Part of prep → cook → serve → tidy.

This is where findings from @line-cook and @line-serve get filed as beads.

**STOP after completing.** Session is complete after tidy.

---

## Finding Filing Strategy

Findings from cook and serve are filed as **siblings under the current task's parent feature**:

**Code/project findings (any priority)** → sibling tasks under parent feature
**Process improvement suggestions** → Retrospective epic

This ensures findings are addressed before the feature is plated (all children must close).

**Edge cases:**
- Task parent is an **epic** → file under the epic
- Task has **no parent** → file as standalone

### Bead Creation Reference

```bash
# Code/project findings → sibling under parent feature
bd create --title="..." --type=task|bug --priority=0-4 --parent=<parent-feature-or-epic>

# Priority: 0=critical, 1=high, 2=medium, 3=low, 4=backlog

# Process improvement suggestions → Retrospective epic
bd create --title="..." --type=task --priority=4 --parent=<retrospective-epic>
```

## Process

### Step 1: Determine Filing Parent

```bash
SOURCE_TASK="<current-task-id>"
PARENT=$(bd show $SOURCE_TASK --json | jq -r '.[0].parent // empty')
```

Use `$PARENT` as `--parent` for code/project findings. If no parent, file as standalone.

### Step 2: File Discovered Issues

Review findings from @line-cook and @line-serve and create beads.

**Code/project findings** (siblings under parent feature/epic):
```bash
bd create --title="<issue>" --type=bug|task --priority=1-3 --parent=$PARENT
```

**Lower-priority code findings** (still under parent):
```bash
bd create --title="<suggestion>" --type=task --priority=4 --parent=$PARENT
```

**Process improvement suggestions** (Retrospective epic):
```bash
bd create --title="<workflow suggestion>" --type=task --priority=4 --parent=<retro-epic>
```

### Step 2: Review In-Progress Issues

Check current task state:
```bash
bd list --status=in_progress
```

For each **in-progress** issue:
- If task appears complete based on git changes → `bd close <id>`
- If task is incomplete → leave as-is (will be picked up next session)

### Step 3: Check for Epic Closures

After closing issues, check if any epics are eligible for closure:

```bash
bd epic close-eligible --dry-run
```

If epics are eligible, close them:
```bash
bd epic close-eligible
```

### Step 4: Commit Changes

Show pending changes:
```bash
git status
```

If changes exist:
1. Stage all relevant files: `git add -A`
2. Create a commit with descriptive message

**Commit message format:**
```bash
git commit -m "<task-id>: <Short objective>

<Detailed description of changes>

Implementation includes:
- Key feature 1
- Key feature 2

Deliverable: <What was created>
Tests: <Test summary>"
```

### Step 5: Sync and Push

```bash
bd sync                        # Commit beads changes
git pull --rebase && git push  # Push to remote (if remote exists)
```

If no remote is configured, skip the push step.

**CRITICAL:** Work is NOT complete until `git push` succeeds.

### Step 6: Output Kitchen Report

```
╔══════════════════════════════════════════════════════════════╗
  ║  TIDY: Kitchen Closed                                        ║
  ╚══════════════════════════════════════════════════════════════╝

SESSION SUMMARY
━━━━━━━━━━━━━━━

Task: <id> - <title>

INTENT:
  <1-2 sentences from task description>

BEFORE → AFTER:
  <previous state> → <new state>

Files changed:
  M src/foo.ts (+45, -12)
  A src/bar.ts (+78)

Issues closed: <count>
  ✓ <id>: <title>

Epics completed: <count>
  ★ <epic-id>: <title> (<N> children)

Issues filed: <count>
  + <new-id>: <title> [P<n>]

Commit: <hash>
  <commit message>

Push: ✓ origin/main | ⚠️ <error> | skipped (no remote)

Session complete.
```

**If an epic was completed, show epic banner first:**

```
════════════════════════════════════════════
  EPIC COMPLETE: <epic-id> - <epic-title>
════════════════════════════════════════════

Children completed (<count>):
  ✓ <id>: <title>
  ✓ <id>: <title>

════════════════════════════════════════════
```

## Error Handling

If push fails:
```
⚠️ PUSH FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Error: <error message>

Changes are committed locally. Resolve and run:
  git pull --rebase && git push

Or create bead for follow-up:
  bd create --title="Resolve git push failure" --type=bug --priority=2
```

## Design Notes

This command is intentionally **non-interactive**:
- **Workflow velocity** - No blocking on user input
- **Deferred decisions** - Unclear items become beads, not blockers
- **Session end discipline** - Quick cleanup without decision fatigue

The pattern "file, don't block" means any concern that would require user judgment gets captured as a bead for later triage.

**NEXT STEP: @line-prep (start new cycle)**
