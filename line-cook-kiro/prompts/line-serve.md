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

### Step 3: Perform Code Review

Review the changes with focus on:

1. **Correctness** - Logic errors, edge cases, error handling
2. **Security** - Input validation, secrets exposure, injection risks
3. **Style** - Naming, consistency with codebase patterns
4. **Completeness** - Does it fully address the task?

For each issue found, categorize:
- **Severity**: critical | major | minor | nit
- **File/line**: Location
- **Issue**: Description
- **Suggestion**: How to fix
- **Auto-fixable**: true | false

### Step 4: Process Review Results

Based on review findings:

**If no issues found:**
- Verdict: APPROVED
- Proceed to Step 5

**If issues found but non-blocking:**
- Verdict: NEEDS_CHANGES
- Do NOT continue to tidy
- Report findings to user with SERVE_RESULT showing `next_step: @line-cook`
- The user will rerun `@line-cook` with the review findings

**If critical issues found:**
- Verdict: BLOCKED
- CRITICAL issues must be fixed before tidying
- Report blocking issues to user
- Recommend not proceeding to `@line-tidy` until fixed
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

Issues to file in /tidy (see tidy.md Finding Filing Strategy):
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
│ next_step: @line-tidy | @line-cook      │
│ blocking_issues: <count or 0>           │
└─────────────────────────────────────────┘

NEXT STEP: @line-tidy (if APPROVED) or @line-cook (if NEEDS_CHANGES)
```

**Verdict meanings:**
- **APPROVED**: No issues found, continue to tidy
- **NEEDS_CHANGES**: Issues found requiring rework. Rerun @line-cook with findings.
- **BLOCKED**: Critical issues require fixing before commit. STOP workflow.

## Error Handling

If review cannot be completed (tool failure, timeout, etc.):

```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended. Run @line-serve again after /tidy.

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: SKIPPED                        │
│ continue: true                          │
│ blocking_issues: 0                      │
│ retry_recommended: true                 │
└─────────────────────────────────────────┘
```

Errors are **transient** - workflow continues but recommends retry later.

## Example Usage

```
@line-serve              # Review most recent closed bead
@line-serve lc-042       # Review specific bead
```
