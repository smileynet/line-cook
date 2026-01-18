---
description: Review issues, capture new work, update docs, commit and push
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, TodoWrite, AskUserQuestion
---

## Task

Session housekeeping: review existing issues, capture discovered work, update documentation, and commit/push all changes.

## Process

### Step 1: Review Existing Issues

Check current issue state:
```bash
bd list --status=open
bd list --status=in_progress
```

For each **in-progress** issue, ask the user:
- **Complete?** → `bd close <id>`
- **Needs update?** → `bd update <id> --status=...` or add context
- **Unchanged?** → Leave as-is

For **open** issues, ask if any should be:
- Started → `bd update <id> --status=in_progress`
- Closed (no longer relevant) → `bd close <id> --reason="..."`

### Step 2: Capture New Issues

Ask the user:
> "Did you discover any issues, tasks, or items to review later during this session?"

For each new item, prompt for:
- **Title**: Brief description
- **Type**: task, bug, or feature
- **Priority**: P0 (critical) through P4 (backlog)

Create via:
```bash
bd create --title="<title>" --type=<type> --priority=<0-4>
```

**Tip**: Low-priority "review later" items should be P4 (backlog).

### Step 3: Review Documentation

Check for staleness:
- `CLAUDE.md` / `AGENTS.md` - Do they reflect current project state?
- `README.md` - Is it accurate?
- Any other docs mentioned in the session

Ask the user:
> "Are there any documentation files that need updating?"

Make requested updates using Edit or Write tools.

### Step 4: Commit Changes

Show pending changes:
```bash
git status
```

If changes exist:
1. Show what changed
2. Stage appropriate files: `git add <files>`
3. Commit with descriptive message

### Step 5: Sync and Push

```bash
bd sync                    # Commit beads changes
git pull --rebase && git push  # Push to remote
```

**Verify push succeeded.** If it fails:
- Diagnose and resolve
- Retry until successful

### Step 6: Summary

Report what was done:
```
Tidy Summary:
- Issues closed: <count>
- Issues created: <count>
- Issues updated: <count>
- Docs updated: <list>
- Commits pushed: <count>
```

## Example Session

```
/line:tidy

Checking existing issues...

In-progress issues:
- beads-042: Implement tidy command

Is beads-042 complete? [Yes/No/Update]
> Yes

Closing beads-042...

Any new issues discovered this session?
> Yes - found a bug in the hook validation

Creating new issue...
Title: Bug in hook validation
Type: bug
Priority: P2

Created beads-043

Any documentation updates needed?
> No

Committing changes...
✓ Committed: "feat: implement /line:tidy command"

Pushing to remote...
✓ Pushed to origin/main

Tidy Summary:
- Issues closed: 1
- Issues created: 1
- Issues updated: 0
- Docs updated: none
- Commits pushed: 1
```

## Example Usage

```
/line:tidy
```

This command takes no arguments.
