Review changes before committing. Part of prep → cook → serve → tidy.

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

### Step 3: Review Changes

Review the code changes for:

**Correctness:**
- Logic errors
- Edge cases
- Error handling

**Security:**
- Input validation
- Secrets exposure
- Injection risks

**Style:**
- Naming consistency
- Code patterns
- Documentation

**Completeness:**
- Does it fully address the task?
- Any missing pieces?

### Step 4: Categorize Issues

For each issue found, categorize:

**Severity levels:**
- **critical** - Must fix before commit (blocks tidy)
- **major** - Should fix, but can file as bead
- **minor** - Nice to fix, file as P4 bead
- **nit** - Cosmetic, optional

**Auto-fixable:**
- Typos, formatting, obvious one-line fixes: Fix immediately
- Others: Note for @line-tidy to file as beads

### Step 5: Output Review Results

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

Issues to file in @line-tidy:
  - [P1] "<title>" - <description>
  - [P3] "<title>" - <description>
  - [P4/retro] "<title>" - <minor suggestion>

Positive notes:
  - <good thing>
  - <good thing>

┌─────────────────────────────────────────┐
│ SERVE_RESULT                            │
│ verdict: APPROVED | NEEDS_CHANGES | BLOCKED │
│ continue: true | false                  │
│ blocking_issues: <count or 0>           │
└─────────────────────────────────────────┘

NEXT STEP: @line-tidy
```

**Verdict meanings:**
- **APPROVED**: No issues found, continue to tidy
- **NEEDS_CHANGES**: Non-blocking issues noted, continue to tidy (issues will be filed)
- **BLOCKED**: Critical issues require fixing before commit. STOP workflow.

## Error Handling

If review cannot be completed:

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

NEXT STEP: @line-tidy
```
