---
description: Commit changes, sync beads, and push to remote
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, TodoWrite
---

## Summary

**File discovered issues, commit changes, and push to remote.** Part of prep → cook → serve → tidy.

This is where findings from `/line:cook` and `/line:serve` get filed as beads.

---

## Bead Creation Reference

Use this when filing discovered issues. **Always include a description** that explains the discovery context:

```bash
# Standard issues (blocking tasks)
bd create --title="..." --type=task|bug|feature --priority=0-4 \
  --description="$(cat <<'EOF'
Discovery Source: <source-task-id> - <source-task-title>
Discovered During: <cook|serve> phase

Impact:
<why this matters - user impact, technical debt, or risk>

Context:
<before/after state if relevant, file/component involved>
EOF
)"

# Priority: 0=critical, 1=high, 2=medium, 3=low, 4=backlog
# Types: task, bug (broken), feature (new capability)

# Minor improvements (review later)
bd create --title="..." --type=task --priority=4 --parent=<retrospective-epic> \
  --description="$(cat <<'EOF'
Discovery Source: <source-task-id> - <source-task-title>
Discovered During: <cook|serve> phase

Impact:
<why this is worth considering later>

Context:
<observation that triggered this suggestion>
EOF
)"
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

Review findings from `/line:cook` and `/line:serve` and create beads with full context:

**Blocking issues** (needs attention):
```bash
bd create --title="Fix race condition in session cleanup" \
  --type=bug --priority=2 \
  --description="$(cat <<'EOF'
Discovery Source: lc-abc - Implement session timeout
Discovered During: cook phase

Impact:
Sessions may not be cleaned up under load, causing resource leaks.
This affects production reliability under concurrent requests.

Context:
Test for timeout cleanup failed intermittently.
Related: internal/session/manager.go:145
EOF
)"
```

**Non-blocking findings** (review later):
```bash
bd create --title="Consider caching session lookups" \
  --type=task --priority=4 --parent=<retro-epic> \
  --description="$(cat <<'EOF'
Discovery Source: lc-abc - Implement session timeout
Discovered During: cook phase (profiling)

Impact:
Performance optimization opportunity, not blocking.
Could reduce latency by ~20ms per request in hot path.

Context:
Session.Get() called 10+ times per request in hot path.
Related: internal/session/store.go
EOF
)"
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

### Step 3: Check for Epic Closures and Branch Merges

After closing issues, check if any epics are now eligible for closure (all children complete):

```bash
bd epic close-eligible --dry-run
```

If epics are eligible:
1. Close them: `bd epic close-eligible`
2. For each closed epic, **merge the epic branch to main**:
   ```bash
   for EPIC_ID in $(bd epic close-eligible --dry-run --json 2>/dev/null | jq -r '.[].id' || true); do
     EPIC_BRANCH="epic/$EPIC_ID"
     CURRENT=$(git branch --show-current)

     if [ "$CURRENT" = "$EPIC_BRANCH" ]; then
       EPIC_TITLE=$(bd show $EPIC_ID --json | jq -r '.[0].title')

       # Checkout main and merge
       git checkout main
       git pull --rebase

       if git merge --no-ff $EPIC_BRANCH -m "Merge epic $EPIC_ID: $EPIC_TITLE"; then
         # Success - delete branch and push
         git branch -d $EPIC_BRANCH
         git push origin main
         git push origin --delete $EPIC_BRANCH 2>/dev/null || true
       else
         # Merge conflict - abort and create bug bead
         git merge --abort
         git checkout $EPIC_BRANCH

         bd create --title="Resolve merge conflict for epic $EPIC_ID" \
           --type=bug --priority=1 \
           --description="Epic $EPIC_ID ($EPIC_TITLE) completed but merge to main failed due to conflicts."

         echo "⚠️ MERGE CONFLICT - manual resolution required"
       fi
     fi
   done
   ```

3. Get children for the summary:
   ```bash
   bd list --parent=<epic-id> --all --json
   ```

**Note:** Epic closures are significant milestones. They will be highlighted prominently in the session summary.

> **Epic Philosophy:** Epics use children (`--parent`) for grouping, not blocking dependencies.
> Dependencies between children establish order within an epic.
> See AGENTS.md for the full epic philosophy.

### Step 4: Commit Changes with Kitchen Log

Show pending changes:
```bash
git status
```

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

### Step 5: Verify Closing Kitchen

Before pushing, verify all quality gates pass:

**Kitchen closing checklist (MANDATORY):**
- [ ] All issues filed correctly
- [ ] Commit message follows kitchen log format
- [ ] Changes staged and committed
- [ ] Beads synced with `bd sync`
- [ ] Ready to push to remote

**If any checklist item fails:**
- Create P2 bead for follow-up
- Note in commit body
- Continue with push if non-blocking

### Step 6: Sync and Push

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

### Step 7: Record Session Summary

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

### Step 8: Output Kitchen Report

**If an epic was closed**, output the epic completion banner first:

```
════════════════════════════════════════════
  EPIC COMPLETE: <epic-id> - <epic-title>
  Branch: epic/<epic-id> merged to main
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

**If merge failed (conflict):**

```
════════════════════════════════════════════
  EPIC COMPLETE: <epic-id> - <epic-title>
════════════════════════════════════════════

⚠️ MERGE CONFLICT
Epic branch could not be merged to main.

Conflicts require manual resolution:
  1. Resolve conflicts manually
  2. git add <resolved-files>
  3. git commit
  4. git push origin main
  5. git branch -d epic/<epic-id>

Bug bead created: <new-bead-id>

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

Epics completed: <count>
  ★ <epic-id>: <title> (<N> children)

Issues filed: <count>
  + <new-id>: <title> [P<n>]
    Source: <source-task-id> (<cook|serve> phase)
  + <new-id>: <title> [P4/retro]
    Source: <source-task-id> (<cook|serve> phase)

Commit: <hash>
  <commit message>

Push: ✓ origin/main | ⚠️ <error> | skipped (no remote)

Session complete.

───────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────
Ready tasks remaining: <count>

  /clear       Clear context before next cycle (recommended)
  /line:prep   Start fresh cycle
  /line:run    Continue automatically
  /line:help   See all commands

Tip: Clear context between tasks to prevent accumulation.

<phase_complete>DONE</phase_complete>
```

**Phase completion signal:** The `<phase_complete>DONE</phase_complete>` tag signals to the line-loop orchestrator that this phase has completed its work and can be terminated early. Always emit this signal at the very end of successful completion output.

**Information sources for summary:**
- **Intent**: Extract from task description via `bd show <id>`
- **Before**: Derive from git diff context - what existed before (files modified, previous behavior)
- **After**: Semantic summary from cook completion - what capability exists now

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
