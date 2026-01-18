---
description: Commit changes, sync beads, and push to remote
---

## Task

Session housekeeping: commit all changes and push to remote. Operates non-interactively; any concerns are filed as beads.

## Process

### Step 1: Review In-Progress Issues

Check current work state:
```bash
bd list --status=in_progress
```

For each **in-progress** issue:
- If work appears complete based on git changes → `bd close <id>`
- If work is incomplete → leave as-is (will be picked up next session)
- If status is unclear → create a P4 bead to review later:
  ```bash
  bd create --title="Review status of <id>: <title>" --type=task --priority=4
  ```

**Do NOT ask the user** - make a reasonable judgment or file a bead.

### Step 2: Capture Discovered Work

During the session, the `/cook` command should have created beads for any discovered work. This step verifies that pattern was followed.

If you notice uncommitted work that isn't tracked:
```bash
bd create --title="<discovered issue>" --type=task --priority=3
```

**Do NOT ask the user** - file it as a bead for later triage.

### Step 3: Check Documentation Staleness

Quick automated check:
```bash
# Check if key docs were modified
git diff --name-only HEAD~5 | grep -E "(CLAUDE|AGENTS|README)\.md" || echo "No recent doc changes"
```

If documentation appears stale or inconsistent with code changes:
```bash
bd create --title="Review <file> for staleness" --type=task --priority=4
```

**Do NOT ask the user** - file it as a bead for later review.

### Step 4: Commit Changes

Show pending changes:
```bash
git status
```

If changes exist:
1. Stage all relevant files: `git add -A`
2. Create a commit with a descriptive message summarizing the session's work
3. Use conventional commit format (feat:, fix:, docs:, etc.)

### Step 5: Sync and Push

```bash
bd sync                    # Commit beads changes
git pull --rebase && git push  # Push to remote (if remote exists)
```

If no remote is configured, skip the push step.

If push fails:
- Attempt to diagnose and resolve automatically
- If unresolvable, create a P2 bead:
  ```bash
  bd create --title="Resolve git push failure: <error>" --type=bug --priority=2
  ```

### Step 6: Summary

Report what was done:
```
Tidy Summary:
━━━━━━━━━━━━━
- Issues closed: <count>
- Issues created: <count> (for later review)
- Commits made: <count>
- Push status: <success|skipped|failed>

Beads created during tidy:
- <id>: <title>
```

## Example Session

```
/tidy

Reviewing in-progress issues...
  lc-k6i: Appears complete based on git changes
  → Closing lc-k6i

Checking for untracked work...
  → No orphaned work detected

Checking documentation...
  → No staleness detected

Committing changes...
  → Staged 2 files
  → Committed: "fix: make tidy command non-interactive"

Syncing beads...
  → bd sync complete

Pushing to remote...
  → No remote configured, skipping push

Tidy Summary:
━━━━━━━━━━━━━
- Issues closed: 1
- Issues created: 0
- Commits made: 1
- Push status: skipped (no remote)
```

## Design Rationale

This command is intentionally **non-interactive** to support:

1. **Workflow velocity** - No blocking on user input
2. **Automated pipelines** - Can run in CI/headless mode
3. **Deferred decisions** - Unclear items become beads, not blockers
4. **Session end discipline** - Quick cleanup without decision fatigue

The pattern "file, don't block" means any concern that would require user judgment gets captured as a bead for later triage rather than interrupting the current flow.

## Example Usage

```
/tidy
```

This command takes no arguments.
