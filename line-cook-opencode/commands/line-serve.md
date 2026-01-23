---
description: Review changes via headless Claude and file issues
---

## Summary

**Review changes via headless Claude.** Part of prep → cook → serve → tidy.

After cooking (executing a task), you "serve" it for review before tidying up.

**Arguments:** `$ARGUMENTS` (optional) - Specific bead ID to review

**When run directly:** STOP after completing, show NEXT STEP, and wait for user.
**When run via `/line-work`:** Continue to the next step without stopping.

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

The sous-chef agent will:
- Review correctness (logic, edge cases, error handling)
- Check security (input validation, secrets, injection risks)
- Verify style (naming, consistency with codebase patterns)
- Assess completeness (fully addresses the task?)

**Wait for reviewer assessment. Address any critical issues before proceeding to tidy.**

**Manual fallback:** If sous-chef agent is unavailable, invoke headless Claude:
```bash
git diff | claude -p "Review these changes for task: <bead title>
...
```

### Step 4: Process Review Results

Based on sous-chef verdict:

**If verdict is ready_for_tidy:**
- Proceed to Step 5
- No changes needed

**If verdict is needs_changes:**
- Apply auto-fixable issues (typos, formatting, obvious one-line fixes)
- Note non-fixable issues for `/line-tidy`
- Categorize by priority (P1-P4)

**If verdict is blocked:**
- CRITICAL issues must be fixed before tidying
- Report blocking issues to user
- Recommend not proceeding to `/line-tidy` until fixed
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
```
╔══════════════════════════════════════════════════════════════╗
║  SERVE: Dish Presented                                       ║
╚══════════════════════════════════════════════════════════════╝

REVIEW: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: READY_FOR_TIDY | NEEDS_CHANGES | BLOCKED

Summary:
  <brief overall assessment of the changes>

Auto-fixed:
  - <file>:<line> - <fix applied>

Issues to file in /tidy:
  - [P1] "<title>" - <description>
  - [P3] "<title>" - <description>
  - [P4/retro] "<title>" - <minor suggestion>

Positive notes:
  - <good thing>
  - <good thing>

Signal: READY_FOR_TIDY

NEXT STEP: /line-tidy
```

## Error Handling

If the headless Claude invocation fails:
```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended before /line-tidy.
Workflow can continue - this is non-blocking.
```

## Example Usage

```
/line-serve              # Review most recent closed bead
/line-serve lc-042       # Review specific bead
```
