---
description: Review changes via headless Claude and file issues
allowed-tools: Bash, Read, Glob, Grep, Edit, TodoWrite
---

## Summary

**Review changes via headless Claude.** Part of prep → cook → serve → tidy.

**Arguments:** `$ARGUMENTS` (optional) - Specific bead ID to review

**STOP after completing.** Show NEXT STEP and wait for user.

---

## Process

### Step 1: Invoke CLI

```bash
lc serve $ARGUMENTS
```

The CLI:
- Gets the task (from arg, session state, or most recently closed)
- Generates git diff of changes
- Outputs task details, diff, and review prompt

### Step 2: Run Headless Review

**You must invoke headless Claude for peer review.**

Use a 10-minute timeout (600000ms) - reviews often exceed 2-minute default:

```bash
git diff | claude -p "<review_prompt> + Output JSON: {summary, approval: approved|needs_changes|blocked, issues: [{severity, file, line, issue, suggestion, auto_fixable}], positive: []}" --output-format text --allowedTools "Read,Glob,Grep"
```

Use the review prompt from CLI output, adding the JSON output format specification shown above.

If headless invocation fails:
- Note review was skipped
- Continue to `/line:tidy` (non-blocking)

### Step 3: Process Results

**Auto-fixable issues** (apply immediately):
- Typos in comments/strings
- Missing trailing newlines
- Simple formatting issues

Use Edit tool to apply auto-fixes directly.

**Non-auto-fixable issues** (note for `/line:tidy`):
- Logic errors requiring design decisions
- Security concerns needing investigation
- Missing functionality

Categorize by priority:
- **P1-P3**: Blocking issues → filed as standalone beads in tidy
- **P4/nits**: Minor suggestions → filed under Retrospective epic in tidy

### Step 4: Report Results

Output review summary:
```
REVIEW: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: APPROVED | NEEDS_CHANGES | BLOCKED

Summary:
  <brief overall assessment>

Auto-fixed:
  - <file>:<line> - <fix applied>

Issues to file in /tidy:
  - [P1] "<title>" - <description>
  - [P4/retro] "<title>" - <minor suggestion>

Positive notes:
  - <good things noted>

NEXT STEP: /line:tidy
```

## Error Handling

If headless Claude fails:
```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended before /line:tidy.
Workflow can continue - this is non-blocking.
```

## Example Usage

```
/line:serve              # Review most recent task
/line:serve lc-042       # Review specific bead
```
