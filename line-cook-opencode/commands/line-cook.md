---
description: Select and execute a task with completion guardrails
---

## Task

Execute work on a task with guardrails ensuring completion. Part of the `/line-prep` → `/line-cook` → `/line-tidy` workflow loop.

**Arguments:** `$ARGUMENTS` (optional) - Specific task ID to work on

## Process

### Step 1: Select Task

**If `$ARGUMENTS` provided:**
- Use that task ID directly

**Otherwise:**
- Run `bd ready` to get available tasks
- Select the highest priority task (lowest P number)

Once selected:
```bash
bd show <id>                           # Display full task details
bd update <id> --status=in_progress    # Claim the work
```

### Step 2: Plan the Work

**CRITICAL:** Break the task into granular, atomic steps using TodoWrite.

1. Read the task description carefully
2. Identify all deliverables and sub-tasks
3. Decompose each deliverable into small, concrete actions
4. Add ALL steps to TodoWrite before starting work

**Granularity guidelines:**
- Each todo should be completable in ~1-5 minutes
- Prefer too many small steps over too few large ones
- Include verification steps (e.g., "Test X works", "Verify Y compiles")
- Include file operations explicitly (e.g., "Create foo.md", "Update bar.json")

**Example decomposition:**
```
Task: "Add new command"

BAD (too coarse):
- [ ] Implement the command

GOOD (granular):
- [ ] Create command file with frontmatter
- [ ] Write command process steps
- [ ] Add example usage section
- [ ] Add entry to plugin.json
- [ ] Copy to .claude/commands/
- [ ] Test command loads correctly
```

For complex tasks:
- Consider using explore-plan-code workflow
- Ask clarifying questions via AskUserQuestion before starting
- For non-trivial tasks, confirm approach with user

### Step 3: Execute Work

Work through TodoWrite items systematically:

- Mark items `in_progress` when starting
- Mark items `completed` immediately when done
- Only one item should be `in_progress` at a time

Add progress comments to the bead for significant milestones:
```bash
bd comments add <id> "Implemented core logic, moving to tests"
```

### Step 4: Verify Completion

**CRITICAL:** Before marking the task done, verify ALL guardrails pass:

- [ ] All TodoWrite items completed
- [ ] Code compiles/runs without errors
- [ ] Tests pass (if applicable)
- [ ] Changes match task description

**If any guardrail fails:**
- Do NOT close the task
- Report what's incomplete
- Keep task as `in_progress`
- Ask user how to proceed

### Step 5: Complete Task

Only after all guardrails pass:

```bash
bd close <id>
```

**Automatically invoke /serve for peer review:**

Use the Skill tool to review the completed work:
```
Skill(skill="serve", args="<bead-id>")
```

The serve command will review changes and report results.

Output summary:
```
Task <id> completed: <title>

Changes made:
- <summary of changes>

Review: <approved|needs_changes|blocked>

Run /line-tidy to commit and push, or /line-cook for next task.
```

## Guardrails (Critical)

This command enforces strict rules:

1. **No silent failures** - If something breaks, report it clearly
2. **No premature completion** - Task stays open until verification passes
3. **No scope creep** - Stay focused on the specific task
4. **Discovered work → beads** - New issues found during work get created as beads (P3/P4)

When discovering new work during execution:
```bash
bd create --title="<discovered issue>" --type=task --priority=3
```

Do NOT work on discovered issues in the current task. Create the bead and stay focused.

## Example Session

```
/line-cook beads-042

Selecting task: beads-042
━━━━━━━━━━━━━━━━━━━━━━━━━

beads-042 [P1] Implement prep command
Type: task
Status: open → in_progress
Description: Create /prep command for session setup...

Planning work...
━━━━━━━━━━━━━━━

TodoWrite items:
1. [ ] Create claude-plugin/commands/prep.md
2. [ ] Add command to plugin.json
3. [ ] Create .claude/commands/prep.md copy
4. [ ] Test command execution

Executing...
━━━━━━━━━━━

[1/4] Creating claude-plugin/commands/prep.md...
✓ Created with frontmatter and 5-step process

[2/4] Adding to plugin.json...
✓ Added command entry

[3/4] Creating local copy...
✓ Copied to .claude/commands/prep.md

[4/4] Testing...
✓ Command loads and displays expected output

Verification:
━━━━━━━━━━━━

[✓] All TodoWrite items completed
[✓] No syntax errors
[✓] Changes match task description

Invoking /serve for peer review...

Review Complete: beads-042 - Implement prep command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: approved
Issues: 0 (0 auto-fixed, 0 beads created)

Task beads-042 completed: Implement prep command

Changes made:
- Created prep.md command in claude-plugin/commands/
- Added entry to plugin.json
- Created local copy in .claude/commands/

Review: approved

Run /line-tidy to commit and push, or /line-cook for next task.
```

## Example Usage

```
/line-cook              # Pick highest priority ready task
/line-cook beads-042    # Work on specific task
```
