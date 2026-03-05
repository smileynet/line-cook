---
description: Commit changes, sync beads, and push to remote
---


## Summary

**File discovered issues, commit changes, and push to remote.** Part of prep → cook → serve → tidy.

This is where findings from `/line-cook` and `/line-serve` get filed as beads.

---

## Finding Filing Strategy

> **Note:** Findings marked `Auto-fixable: true` that polisher successfully applied during serve are already resolved — they appear in serve's `Auto-fixed:` section and do NOT appear here.

Findings are triaged to **three destinations** based on markers from serve (or inferred during tidy):

| Marker | Destination | Loop picks up? | Blocks feature? |
|--------|-------------|----------------|-----------------|
| `[FIX]` | Sibling under parent feature | Yes (next iteration) | Yes (must close before plate) |
| `[DEFER]` | Child of **Backlog** epic | No (excluded epic) | No (different hierarchy) |
| `[RETRO]` | Child of **Retrospective** epic | No (excluded epic) | No (different hierarchy) |

**Triage heuristic:**
- `[FIX]` — Clear defects, P0-P2, or P3 within current feature scope
- `[DEFER]` — Ambiguous suggestions, nits, P3 outside scope, P4 code items
- `[RETRO]` — Process/workflow improvements (not code findings)
- **Cook findings without serve markers** default to `[DEFER]` (safe — won't block features)

**Edge cases:**
- Task parent is an **epic** (no feature layer) → `[FIX]` files under the epic
- Task has **no parent** → `[FIX]` files as standalone with appropriate priority

**Promotion:** Users can promote deferred items back into scope:
`bd update <id> --parent=<feature-id>`

### Parking Epics (Backlog & Retrospective)

Both are auto-created if they don't exist. The loop's `EXCLUDED_EPIC_TITLES` already skips children of "Backlog" and "Retrospective" epics.

```bash
# Find-or-create pattern (run in Step 1)
BACKLOG_ID=$(bd list --type=epic --json 2>/dev/null | jq -r '.[] | select(.title=="Backlog") | .id' | head -1)
[ -z "$BACKLOG_ID" ] && BACKLOG_ID=$(bd create --title="Backlog" --type=epic --priority=4 --json 2>/dev/null | jq -r '.[0].id // .[0]')

RETRO_ID=$(bd list --type=epic --json 2>/dev/null | jq -r '.[] | select(.title=="Retrospective") | .id' | head -1)
[ -z "$RETRO_ID" ] && RETRO_ID=$(bd create --title="Retrospective" --type=epic --priority=4 --json 2>/dev/null | jq -r '.[0].id // .[0]')
```

### Bead Creation Reference

```bash
# [FIX] → sibling under parent feature (blocks feature closure)
bd create --title="..." --type=task|bug --priority=0-4 \
  --parent=<parent-feature-or-epic> \
  --notes="source_task: <id>, source_phase: <cook|serve>, location: <file:line>"

# [DEFER] → child of Backlog epic (does NOT block feature closure)
bd create --title="..." --type=task --priority=3-4 \
  --parent=$BACKLOG_ID \
  --notes="source_task: <id>, original_parent: <parent-id>, location: <file:line>"

# [RETRO] → child of Retrospective epic (process improvements)
bd create --title="..." --type=task --priority=4 \
  --parent=$RETRO_ID \
  --notes="source_task: <id>, source_phase: <cook|serve>"
```

## Process

### Step 1: Collect Tidy State

Gather filing parent, in-progress tasks, epic eligibility, and git status in one pass:

```bash
TASK_ID="<current-task-id>"

echo "=== PARENT ==="
bd show $TASK_ID --json 2>/dev/null | jq -r '.[0].parent // empty' || echo "(none)"
echo "=== PARKING EPICS ==="
echo "Backlog: $(bd list --type=epic --json 2>/dev/null | jq -r '.[] | select(.title=="Backlog") | .id' | head -1)"
echo "Retrospective: $(bd list --type=epic --json 2>/dev/null | jq -r '.[] | select(.title=="Retrospective") | .id' | head -1)"
echo "=== IN PROGRESS ==="
bd list --status=in_progress 2>/dev/null || echo "(none)"
echo "=== EPIC ELIGIBLE ==="
bd epic close-eligible --dry-run 2>/dev/null || echo "(none)"
echo "=== GIT STATUS ==="
git status --porcelain
```

Use PARENT as `--parent` for `[FIX]` findings. Use PARKING EPICS for `[DEFER]` (Backlog) and `[RETRO]` (Retrospective) — create them if not found (see find-or-create pattern in Filing Strategy above).

### Step 2: File Discovered Issues

Collect findings from cook and serve phases. Findings may be in:
1. **In-context output** (available in single-session `/run` cycles)
2. **Bead comments** (persist across sessions and `/clear`)

**Always check bead comments** for the current task to recover findings from prior sessions:
```bash
bd comments show $TASK_ID
```
Look for `PHASE: COOK` and `PHASE: SERVE` comments containing `Findings:` sections.

Create beads for all findings with full context.

**`[FIX]` findings** (sibling under parent — blocks feature closure):
```bash
bd create --title="<defect>" --type=bug|task --priority=0-3 --parent=$PARENT \
  --notes="source_task: <id>, location: <file:line>"
```

**`[DEFER]` findings** (child of Backlog — does NOT block feature closure):
```bash
bd create --title="<suggestion>" --type=task --priority=3-4 --parent=$BACKLOG_ID \
  --notes="source_task: <id>, original_parent: <parent-id>, location: <file:line>"
```

**`[RETRO]` findings** (child of Retrospective — process improvements):
```bash
bd create --title="<workflow suggestion>" --type=task --priority=4 --parent=$RETRO_ID \
  --notes="source_task: <id>, source_phase: <cook|serve>"
```

**Cook findings without serve markers** default to `[DEFER]`.

#### Research Findings (for research tasks)

When the task involved research (architecture analysis, spike, investigation), also capture findings:

**New beads for discoveries** (file under parent feature/epic):
```bash
bd create --title="Implement <finding>" --type=task --priority=2-3 --parent=$PARENT
bd create --title="Document <pattern>" --type=task --priority=3 --parent=$PARENT
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

### Step 3: Check for Epic Completion

Using the EPIC ELIGIBLE list from Step 1, check if any epics are now eligible for closure (all children complete).

If epics are eligible:

**Do NOT close epics or merge branches here.** Epic closure requires E2E validation via `/line-close-service`. Instead, note eligible epics for the session summary and suggest the next step.

```bash
# Get children for the summary
bd list --parent=<epic-id> --all --json
```

**Note:** Epic closures require the full close-service quality gate. Tidy only detects eligibility.

> **Epic Philosophy:** Epics use children (`--parent`) for grouping, not blocking dependencies.
> Dependencies between children establish order within an epic.
> See AGENTS.md for the full epic philosophy.

### Step 4: Commit Changes with Kitchen Log

Using the GIT STATUS output from Step 1, check for pending changes.

If changes exist:
1. Stage all relevant files: `git add -A`
2. Create a commit with the kitchen log format

**Kitchen log commit format:**
```bash
git commit -m "<task-id>: <Short objective>

<Detailed description of changes>

Implementation includes:
- Key feature 1
- Key feature 2
- Error handling approach

Deliverable: <What was created>
Tests: <Test summary>
Signal: KITCHEN_COMPLETE

Review findings:
- Sous-chef assessment: <verdict>
- Test quality assessment: <result>
- Issues addressed: <count>"
```

**Commit message structure:**
- Subject: `<task-id>: <Short objective>` (50 chars, imperative mood)
- Blank line
- Body: What and why (wrap at 72 chars)
- Implementation details (bullet points)
- Deliverable and test info
- Review and test quality feedback
- Signal emitted

### Step 5: Close Current Task

**CRITICAL:** Only close the bead AFTER the commit is created. This ensures beads are only closed when corresponding git commits exist.

Close the task that was just cooked (the one identified by `$TASK_ID`):

```bash
bd close $TASK_ID
```

**Other in-progress tasks** from the IN PROGRESS list should be left as-is. Do NOT attempt to infer completion of other tasks from git changes — that requires too much guesswork for a non-interactive command. They will be picked up in their own cook/serve/tidy cycles.

### Step 6: Verify Closing Kitchen

Before pushing, verify all quality gates pass:

**Kitchen closing checklist:**
- [ ] All issues filed correctly
- [ ] Commit message follows kitchen log format
- [ ] Changes staged and committed
- [ ] Beads synced with `bd sync`
- [ ] Ready to push to remote

**If any checklist item fails:**
- Create P2 bead for follow-up
- Note in commit body
- Continue with push if non-blocking issue

### Step 7: Sync and Push

```bash
bd sync                        # Commit beads changes
git pull --rebase && git push  # Push to remote (if remote exists)
```

If no remote is configured, skip the push step.

If push fails:
```bash
bd create --title="Resolve git push failure: <error>" --type=bug --priority=2
```

**CRITICAL:** Work is NOT complete until `git push` succeeds. If push fails, resolve and retry.

### Step 8: Record Session Summary

**Add final comment to the task:**
```bash
bd comments add <id> "PHASE: TIDY
Status: completed

SESSION SUMMARY
━━━━━━━━━━━━━━━
Intent: <why this change was made>
Before: <previous state/capability>
After: <new state/capability>

Problems encountered:
  - <problem>: <how resolved>

Issues filed:
  - <new-id>: <title> [P<n>]

Commit: <hash>
Push: <success|failed>"
```

### Step 9: Output Kitchen Report

**If an epic is eligible for closure**, output the epic ready banner first:

```
════════════════════════════════════════════
  EPIC READY TO CLOSE: <epic-id> - <epic-title>
════════════════════════════════════════════

All children completed (<count>):
  ✓ <id>: <title>
  ✓ <id>: <title>
  ✓ <id>: <title>
  ...

NEXT STEP: Run /line-close-service <epic-id>
  (E2E validation, critic review, acceptance docs, branch merge)

════════════════════════════════════════════
```

**Then output the kitchen report:**

```
╔══════════════════════════════════════════════════════════════╗
║  TIDY: Kitchen Closed                                        ║
╚══════════════════════════════════════════════════════════════╝

SESSION SUMMARY
━━━━━━━━━━━━━━━

Task: <id> - <title>

INTENT:
  <1-2 sentences from task description>
  Goal: <deliverable or acceptance criteria>

BEFORE → AFTER:
  <previous state> → <new state>
  <what couldn't be done> → <what can be done now>

Files changed:
  M src/foo.ts (+45, -12)
  A src/bar.ts (+78)

Problems encountered:
  - <problem description>
    Resolution: <how it was resolved>
  - (none)

Issues closed: <count>
  ✓ <id>: <title>

Epics ready to close: <count>
  ★ <epic-id>: <title> (<N> children) → run /line-close-service

Issues filed: <count>
  [FIX] Under parent (<parent-id>) — blocks feature closure:
    + <new-id>: <title> [P<n>]
  [DEFER] Under Backlog — deferred, won't block feature:
    + <new-id>: <title> [P<n>]
  [RETRO] Under Retrospective — process improvements:
    + <new-id>: <title> [P4/retro]

Commit: <hash>
  <commit message>

Push: ✓ origin/main | ⚠️ <error> | skipped (no remote)

Session complete.

```

**Information sources for summary:**
- **Intent**: Extract from task description via `bd show <id>`
- **Before**: Derive from git diff context - what existed before (files modified, previous behavior)
- **After**: Semantic summary from cook completion - what capability exists now

## Design Rationale

This command is intentionally **non-interactive** to support:

1. **Workflow velocity** - No blocking on user input
2. **Deferred decisions** - Unclear items become beads, not blockers
3. **Session end discipline** - Quick cleanup without decision fatigue
4. **Information when needed** - Bead creation reference provided where it's used

The pattern "file, don't block" means any concern that would require user judgment gets captured as a bead for later triage rather than interrupting the current flow.

## Example Usage

```
/line-tidy
```

This command takes no arguments.
