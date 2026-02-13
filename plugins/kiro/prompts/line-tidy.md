**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**File discovered issues, commit changes, and push to remote.** Part of prep → cook → serve → tidy.

This is where findings from `@line-cook` and `@line-serve` get filed as beads.

---

## Finding Filing Strategy

Findings from cook and serve are filed as **siblings under the current task's parent feature**:

**Code/project findings (any priority)** → sibling tasks under parent feature
**Process improvement suggestions** → Retrospective epic

This ensures:
- Findings are addressed before the feature is plated (all children must close)
- The loop picks them up next (highest priority first)
- Context is maintained (findings cluster with related work)

**Edge cases:**
- Task parent is an **epic** (no feature layer) → file under the epic
- Task has **no parent** → file as standalone with appropriate priority

### Bead Creation Reference

```bash
# Code/project findings → sibling under parent feature
bd create --title="..." --type=task|bug --priority=0-4 --parent=<parent-feature-or-epic>

# Priority: 0=critical, 1=high, 2=medium, 3=low, 4=backlog
# Types: task, bug (broken), feature (new capability)

# Process improvement suggestions → Retrospective epic
# (Ways to improve cook, serve, tidy, plate, or other workflow phases)
bd create --title="..." --type=task --priority=4 --parent=<retrospective-epic>
```

**Retrospective epic:**

Reserved for **process improvement suggestions** (not code findings):
- Workflow phase improvements (cook, serve, tidy, etc.)
- Tooling or automation suggestions
- Process observations

```bash
# One-time setup (if not exists)
bd create --title="Retrospective" --type=epic --priority=4

# File process improvements as children
bd create --title="Consider adding lint step to serve" --type=task --priority=4 --parent=<retro-epic-id>
```

## Process

### Step 1: Collect Tidy State

Gather filing parent, in-progress tasks, epic eligibility, and git status in one pass:

```bash
TASK_ID="<current-task-id>"

echo "=== PARENT ==="
bd show $TASK_ID --json 2>/dev/null | jq -r '.[0].parent // empty' || echo "(none)"
echo "=== IN PROGRESS ==="
bd list --status=in_progress 2>/dev/null || echo "(none)"
echo "=== EPIC ELIGIBLE ==="
bd epic close-eligible --dry-run 2>/dev/null || echo "(none)"
echo "=== GIT STATUS ==="
git status --porcelain
```

Use the PARENT value from output as `--parent` for all code/project findings. If no parent exists, file as standalone beads.

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

**Code/project findings** (file as siblings under parent feature/epic):
```bash
bd create --title="<issue>" --type=bug|task --priority=1-3 --parent=$PARENT
```

**Lower-priority code findings** (still under parent, not retro):
```bash
bd create --title="<suggestion>" --type=task --priority=4 --parent=$PARENT
```

**Process improvement suggestions** (file under Retrospective epic):
```bash
bd create --title="<workflow suggestion>" --type=task --priority=4 --parent=<retro-epic>
```

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

### Step 3: Close Current Task

Close the task that was just cooked (the one identified by `$TASK_ID`):

```bash
bd close $TASK_ID
```

**Other in-progress tasks** from the IN PROGRESS list should be left as-is. Do NOT attempt to infer completion of other tasks from git changes — that requires too much guesswork for a non-interactive command. They will be picked up in their own cook/serve/tidy cycles.

### Step 4: Check for Epic Completion

Using the EPIC ELIGIBLE list from Step 1, check if any epics are now eligible for closure (all children complete).

If epics are eligible:

**Do NOT close epics or merge branches here.** Epic closure requires E2E validation via `@line-close-service`. Instead, note eligible epics for the session summary and suggest the next step.

```bash
# Get children for the summary
bd list --parent=<epic-id> --all --json
```

**Note:** Epic closures require the full close-service quality gate. Tidy only detects eligibility.

> **Epic Philosophy:** Epics use children (`--parent`) for grouping, not blocking dependencies.
> Dependencies between children establish order within an epic.
> See AGENTS.md for the full epic philosophy.

### Step 5: Commit Changes with Kitchen Log

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

NEXT STEP: Run @line-close-service <epic-id>
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
  ★ <epic-id>: <title> (<N> children) → run @line-close-service

Issues filed: <count>
  Under parent (<parent-id>):
    + <new-id>: <title> [P<n>]
  Under Retrospective:
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
@line-tidy
```

This command takes no arguments.
