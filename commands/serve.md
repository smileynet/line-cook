---
description: Review completed work via headless Claude and file issues
allowed-tools: Bash, Read, Glob, Grep, Edit, TodoWrite
---

## Task

Review work completed by `/line:cook` via a headless Claude instance. Part of the `/line:prep` → `/line:cook` → `/line:serve` → `/line:tidy` workflow loop.

**Concept**: After cooking (doing work), you "serve" it for review before tidying up.

**Arguments:** `$ARGUMENTS` (optional) - Specific bead ID to review

## Process

### Step 1: Identify Work to Review

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

Collect changes for review:
```bash
# Get unstaged changes (work just completed)
git diff

# Or if already staged
git diff --cached

# Get list of modified files
git status --porcelain
```

If no diff is available (already committed), use:
```bash
git diff HEAD~1
```

### Step 3: Invoke Headless Claude for Review

Spawn a separate Claude instance via bash to review the changes:

```bash
git diff | claude -p "Review these changes for the task: <bead title>

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

**Note:** The headless Claude has read-only access to explore the codebase for context but cannot make changes.

### Step 4: Process Review Results

Parse the JSON output and categorize issues:

**Auto-fixable issues** (apply immediately):
- Typos in comments/strings
- Missing trailing newlines
- Simple formatting issues
- Obvious one-line fixes

For auto-fixable issues, apply the fix directly using Edit tool.

**Non-auto-fixable issues** (create beads):
- Logic errors requiring design decisions
- Security concerns needing investigation
- Missing functionality
- Architectural suggestions

For each non-auto-fixable issue:
```bash
bd create --title="Review: <issue summary>" \
  --type=bug \
  --priority=<map severity: critical→1, major→2, minor→3, nit→4> \
  --description="Found during review of <bead-id>

File: <file>:<line>
Issue: <description>
Suggestion: <fix>"
```

### Step 5: Record and Report Results

**Append review results to the bead as a comment:**
```bash
bd comments add <bead-id> "Review Results:
Verdict: <approved|needs_changes|blocked>
Summary: <summary>
Issues: <count> (<auto-fixed count> auto-fixed, <filed count> beads created)
Positive: <positive notes>"
```

**Output summary to user:**
```
Review Complete: <bead-id> - <title>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: <approved|needs_changes|blocked>

Auto-fixed (applied):
- <file>: <fix applied>

Issues filed:
- <new-bead-id>: <title> [P<priority>]

Positive notes:
- <good things>

Next: Run /line:tidy to commit, or /line:cook to continue working.
```

## Error Handling

If the headless Claude invocation fails:
1. Report the error clearly
2. Skip auto-fixes
3. Suggest manual review
4. Do not block the workflow

```
Review Error: Headless Claude invocation failed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Error: <error message>

Manual review recommended before /tidy.
```

## Example Session

```
/line:serve beads-042

Review: beads-042 - Implement prep command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gathering changes...
- 3 files modified
- 127 lines added

Invoking headless Claude for review...

Review Complete: beads-042 - Implement prep command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: approved

Auto-fixed (applied):
- prep.md: Fixed typo "retreive" → "retrieve"

Issues filed:
- (none)

Positive notes:
- Clear step-by-step process
- Good error handling section
- Follows existing command patterns

Next: Run /line:tidy to commit, or /line:cook to continue working.
```

## Example Usage

```
/line:serve              # Review most recent closed bead
/line:serve beads-042    # Review specific bead
```
