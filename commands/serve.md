---
description: Review changes via headless Claude and file issues
allowed-tools: Bash, Read, Glob, Grep, Edit, TodoWrite
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

### Step 3: Invoke Headless Claude for Review

Spawn a separate Claude instance to review:

```bash
git diff | claude -p "Review these changes for the task: <bead title>

Project context:
<summary of CLAUDE.md patterns if available>

Focus on:
- Correctness: Logic errors, edge cases, error handling
- Security: Input validation, secrets exposure, injection risks
- Style: Naming, consistency with codebase patterns
- Completeness: Does it fully address the task?

Output format (JSON):
{
  \"summary\": \"brief overall assessment\",
  \"approval\": \"approved|needs_changes|blocked\",
  \"issues\": [
    {
      \"severity\": \"critical|major|minor|nit\",
      \"file\": \"path/to/file\",
      \"line\": 42,
      \"issue\": \"description\",
      \"suggestion\": \"how to fix\",
      \"auto_fixable\": true|false
    }
  ],
  \"positive\": [\"things done well\"]
}" --output-format text --allowedTools "Read,Glob,Grep"
```

### Step 4: Process Review Results

Categorize issues:

**Auto-fixable** (apply immediately):
- Typos in comments/strings
- Missing trailing newlines
- Simple formatting issues
- Obvious one-line fixes

Apply auto-fixes directly using Edit tool.

**Non-auto-fixable** (note for `/line:tidy`):
- Logic errors requiring design decisions
- Security concerns needing investigation
- Missing functionality
- Architectural suggestions

Note these for filing in `/line:tidy`, categorized by priority.

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
REVIEW: <id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: APPROVED | NEEDS_CHANGES | BLOCKED

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

NEXT STEP: /line:tidy
```

## Error Handling

If the headless Claude invocation fails:
```
⚠️ REVIEW SKIPPED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Reason: <error message>

Manual review recommended before /line:tidy.
Workflow can continue - this is non-blocking.
```

## Example Usage

```
/line:serve              # Review most recent closed bead
/line:serve lc-042       # Review specific bead
```
