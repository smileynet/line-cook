---
description: Review changes via headless Claude and file issues
allowed-tools: Bash, Read, Glob, Grep, Edit, TodoWrite, Task
---

## Summary

**Review changes via headless Claude.** Part of prep → cook → serve → tidy.

After cooking (executing a task), you "serve" it for review before tidying up.

**Arguments:** `$ARGUMENTS` (optional) - Specific bead ID to review

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Identify Changes to Review

**If `$ARGUMENTS` provided:**
- Use that bead ID directly

**Otherwise:**
- Find most recently closed bead: `bd list --status=closed --limit=1`
- Or find current in-progress bead if cook didn't close it yet

Show the bead being reviewed:
```bash
bd show <id>
```

### Step 2: Gather Review Context

Collect changes and project context:
```bash
# Get changes
git diff                    # Unstaged changes
git diff --cached           # Or staged changes
git status --porcelain      # File list

# If already committed
git diff HEAD~1
```

**Load project context for context-aware review:**
```bash
# Check for CLAUDE.md
cat CLAUDE.md 2>/dev/null | head -50
```

This gives the reviewer awareness of project patterns and conventions.

### Step 2.5: Polish Changes (Automatic)

Before review, automatically refine code for clarity. Extract the list of modified files from git status.

```
Use Task tool to invoke polisher subagent:
Task(description="Polish code changes", prompt="Polish the following files for clarity and consistency:

<list of modified files from git status --porcelain>

Apply these principles:
- Preserve exact functionality (never change behavior)
- Reduce unnecessary complexity
- Improve naming clarity
- Follow project conventions from CLAUDE.md
- Remove dead code and redundancy
- Avoid nested ternaries (prefer if/else or switch)

Output: List of refinements made (file:line - change)", subagent_type="polisher")
```

**After polisher completes:**
- If changes were made, stage them: `git add <polished files>`
- Proceed to sous-chef review (reviewer sees polished code)

### Step 3: Automatic Code Review

Delegate to sous-chef (reviewer) subagent:

```
Use Task tool to invoke sous-chef subagent:
Task(description="Review code changes for task <id>", prompt="Review the following changes for task: <bead title>

Task ID: <id>
Task description: <brief description>

Changes to review:
<git diff output or diff HEAD~1>

Project context:
<CLAUDE.md summary if available>

Review checklist:
- Correctness: Logic errors, edge cases, error handling
- Security: Input validation, secrets exposure, injection risks
- Style: Naming, consistency with codebase patterns
- Completeness: Does it fully address the task?

Output format:
1. Summary: Brief overall assessment
2. Verdict: ready_for_tidy | needs_changes | blocked
3. Issues found:
   - Severity: critical | major | minor | nit
   - File/line: Location
   - Issue: Description
   - Suggestion: How to fix
   - Auto-fixable: true | false
4. Positive notes: What was done well

CRITICAL: If verdict is 'blocked', explain why and what must be fixed.", subagent_type="sous-chef")
```

Wait for reviewer assessment. Address any critical issues before proceeding to tidy.

**Manual fallback (if sous-chef agent unavailable):**
```bash
git diff | claude \
  --max-turns 1 \
  -p "Review these changes for the task: <bead title>
  ..." \
  --output-format text \
  --allowedTools "Read,Glob,Grep"
```

### Step 4: Process Review Results

Based on sous-chef verdict:

**If verdict is ready_for_tidy:**
- Proceed to Step 5
- No changes needed

**If verdict is needs_changes:**
- Do NOT continue to tidy
- Report findings to user with SERVE_RESULT showing `next_step: /line:cook`
- The user will rerun `/line:cook` with the review findings

**If verdict is blocked:**
- CRITICAL issues must be fixed before tidying
- Report blocking issues to user
- Recommend not proceeding to `/line:tidy` until fixed
- Keep task as in_progress

### Step 5: Record and Report Results

**Record via comment:**
```bash
bd comments add <bead-id> "PHASE: SERVE
Status: completed
Verdict: <approved|needs_changes|blocked>
Issues: <count> found (<auto-fixed>, <to-file>)
Summary: <brief assessment>"
```

**Output format:**

CRITICAL: The SERVE_RESULT block must be present and parseable by orchestrators.

```
╔══════════════════════════════════════════════════════════════╗
║  SERVE: Dish Presented                                       ║
╚══════════════════════════════════════════════════════════════╝

REVIEW: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  <brief overall assessment of the changes>

Auto-fixed:
  - <file>:<line> - <fix applied>

Issues to file in tidy (see tidy.md Finding Filing Strategy):
  Code/project findings (siblings under parent):
  - [P1] "<title>" - <description>
  - [P3] "<title>" - <description>
  - [P4] "<title>" - <minor code finding>
  Process improvements (under Retrospective epic):
  - [P4] "<title>" - <workflow suggestion>

Positive notes:
  - <good thing>
  - <good thing>

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: APPROVED | NEEDS_CHANGES | BLOCKED │
│ continue: true | false                  │
│ next_step: /line:tidy | /line:cook      │
│ blocking_issues: <count or 0>           │
└─────────────────────────────────────────┘

NEXT STEP: /line:tidy (if APPROVED) or /line:cook (if NEEDS_CHANGES)
```

**Verdict meanings:**
- **APPROVED**: No issues found, continue to tidy
- **NEEDS_CHANGES**: Issues found requiring rework. Rerun /line:cook with findings.
- **BLOCKED**: Critical issues require fixing before commit. STOP workflow.

**Phase completion signal:** After outputting the SERVE_RESULT block, emit the phase completion signal:
```
<phase_complete>DONE</phase_complete>
```
This signals to the line-loop orchestrator that the serve phase has completed its work and can be terminated early, avoiding unnecessary wait for timeout.

## Error Handling

If the sous-chef agent or headless Claude invocation fails (API error, timeout, etc.):

```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended. Run /line:serve again after /line:tidy.

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: SKIPPED                        │
│ continue: true                          │
│ blocking_issues: 0                      │
│ retry_recommended: true                 │
└─────────────────────────────────────────┘
```

API errors are transient - workflow continues but recommends retry later.

## Example Usage

```
/line:serve              # Review most recent closed bead
/line:serve lc-042       # Review specific bead
```
