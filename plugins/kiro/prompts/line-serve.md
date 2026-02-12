**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Review changes for quality.** Part of prep → cook → serve → tidy.

After cooking (executing a task), you "serve" it for review before tidying up.

**Arguments:** `$ARGUMENTS` (optional) - Specific bead ID to review

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Collect Review Context

**If the user provided a bead ID:**
- Use that bead ID directly

**Otherwise:**
- Identify from the collected output below

Collect review context in one call:

#### Find Script

Locate `diff-collector.py`:

```bash
# Collect review context: bead identification, git diffs (truncated at 200 lines), file status
REVIEW=$(python3 <path-to-diff-collector.py> --json 2>/dev/null)
echo "$REVIEW"
```

The JSON output includes: `bead`, `changes`. Diffs are capped at 200 lines each to prevent context window blowout.

The bead details are in the JSON's `bead` field — use this directly for review context.

### Step 2: Polish Changes

Before review, automatically refine code for clarity. Extract modified files from the REVIEW JSON's `changes.files` array.

```
Use task tool to invoke polisher agent:
Task(description="Polish code changes", prompt="Polish the following files for clarity and consistency:

<list of modified files from REVIEW JSON changes.files>

Apply these principles:
- Preserve exact functionality (never change behavior)
- Reduce unnecessary complexity
- Improve naming clarity
- Follow project conventions from CLAUDE.md
- Remove dead code and redundancy
- Avoid nested ternaries (prefer if/else or switch)

Output: List of refinements made (file:line - change)", agent="polisher")
```

**If polisher unavailable:** Skip polishing and proceed directly to code review.

**After polisher completes:**
- If changes were made, stage them: `git add <polished files>`
- Proceed to sous-chef review

### Step 3: Code Review

Delegate to sous-chef (reviewer) agent:

```
Use task tool to invoke sous-chef agent:
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

CRITICAL: If verdict is 'blocked', explain why and what must be fixed.", agent="sous-chef")
```

**If sous-chef unavailable:** Perform inline review using the checklist above.

Wait for reviewer assessment. Address critical issues before proceeding to tidy.

### Step 4: Process Review Results

Based on sous-chef verdict:

**If verdict is ready_for_tidy:**
- Proceed to Step 5
- No changes needed

**If verdict is needs_changes:**
- Report findings to user with SERVE_RESULT showing `next_step: @line-cook`
- User will rerun `@line-cook` with the review findings
- Do NOT continue to tidy

**If verdict is blocked:**
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

If the sous-chef agent or review cannot be completed (tool failure, timeout, etc.):

```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended. Run @line-serve again after @line-tidy.

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: SKIPPED                        │
│ continue: true                          │
│ blocking_issues: 0                      │
│ retry_recommended: true                 │
└─────────────────────────────────────────┘
```

Errors are transient - workflow continues but recommends retry later.

## Example Usage

```
@line-serve              # Review most recent closed bead
@line-serve lc-042       # Review specific bead
```
