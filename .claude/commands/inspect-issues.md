---
description: Review open PRs and standalone issues
allowed-tools: Bash, Read, Glob, Grep, Task, AskUserQuestion
---

## Summary

**Review open PRs and standalone issues.** Discovers open PRs and issues, delegates each to the appropriate review agent (inspector for PRs, issue-reviewer for standalone issues), displays reports locally, and prompts for action.

**Usage:**
- `/inspect-issues` — review all open PRs and standalone issues
- `/inspect-issues 7` — review PR #7 or issue #7

**Bot identity rule:** All comments on GitHub **issues** must be posted as `line-sous-chef[bot]` via the `respond.yml` workflow. Never use `gh issue comment` directly from local CLI — it posts as the local user. Use the `/respond` flow (dispatch `gh workflow run respond.yml ...`) for all issue comments. PR comments (`gh pr comment`) are fine as-is since they're maintainer reviews.

---

## Process

### Step 1: Discover Open PRs and Issues

```bash
gh pr list --state open --json number,title,headRefName,body,url
```

```bash
gh issue list --state open --json number,title,body,labels,author,url
```

**Cross-reference to find standalone issues:**

1. Build a set of issue numbers referenced by open PRs:
   - Branch name matches `fix/issue-<N>-*` → extract `N`
   - PR body contains `Fixes #N`, `Closes #N`, or `refs #N` → extract `N`
2. **Standalone issues** = open issues whose number is NOT in that set
3. If `$ARGUMENTS` is a number: check PRs first (match by PR number), then check standalone issues (match by issue number). If neither matches, report "No open PR or issue #N found." and stop.
4. If no open PRs AND no standalone issues are found, report "No open PRs or issues found." and stop.

### Step 2a: Fetch Context for Each PR

For each PR, extract the associated issue number:
1. If the branch name matches `fix/issue-<N>-*`, extract `N` from the branch name
2. Otherwise, look for `Fixes #N`, `Closes #N`, or `refs #N` in the PR body
3. If no issue reference is found, set `issue_number` to `null` (the PR will be evaluated on its own merits)

Fetch context for each PR (run these in parallel where possible):

**Issue body** (skip if `issue_number` is null):
```bash
gh issue view <issue-number> --json title,body,labels,author
```

**PR metadata:**
```bash
gh pr view <pr-number> --json title,body,headRefName,changedFiles,additions,deletions
```

**Code diff (capped at 300 lines):**
```bash
gh pr diff <pr-number>
```

To enforce the 300-line cap: count the lines of the raw diff output. If it exceeds 300, keep only the first 300 lines and prepend a notice: `[DIFF TRUNCATED at 300 lines — full diff is N lines]` so the inspector can factor truncation into its assessment.

**Changed files:**
```bash
gh pr view <pr-number> --json files --jq '.files[].path'
```

### Step 2b: Fetch Context for Standalone Issues

For each standalone issue, fetch full context:

```bash
gh issue view <N> --json number,title,body,labels,author,comments
```

Also prepare a condensed list of other open issues (number + title only) for duplicate detection by the issue-reviewer agent.

### Step 3: Invoke Review Agents

#### Step 3 — PRs: Invoke Inspector Agent

For each PR, delegate to the inspector agent via Task:

```
Task(description="Inspect PR #<pr-number> for issue #<issue-number>", prompt=<assembled context>, subagent_type="inspector")
```

The prompt should include:
- Issue number, title, and body
- PR number, title, and body
- The code diff
- List of changed files

The inspector returns a JSON object. Parse it with `json.loads()` or equivalent. Validate that it contains: `issue_number`, `pr_number`, `verdict`, `dimensions` (with all 8 keys), and `rationale`.

If the inspector output is not valid JSON (e.g., wrapped in markdown fences), strip fences and retry parsing. If still invalid, treat as inspection failure for that PR.

#### Step 3 — Issues: Invoke Issue Reviewer Agent

For each standalone issue, delegate to the issue-reviewer agent via Task:

```
Task(description="Triage issue #<issue-number>", prompt=<issue context + open issues list>, subagent_type="issue-reviewer")
```

The prompt should include:
- Issue number, title, body, labels, author, comments
- Condensed list of other open issues (for duplicate detection)

The issue-reviewer returns a JSON object. Validate that it contains: `type`, `issue_number`, `pr_number`, `verdict`, `dimensions` (with all 6 keys), `rationale`, and `duplicate_of`.

If the output is not valid JSON, strip fences and retry parsing. If still invalid, treat as triage failure for that issue.

**Launch all inspector and issue-reviewer agents in parallel** when reviewing multiple items.

### Step 3a: Write Feedback Files

#### PR Feedback

After the inspector returns valid JSON, augment it and write to `.beads/inspect-feedback/issue-<number>.json`.

If `issue_number` is null, skip writing the feedback file — feedback is only consumed by the issue-agent, which looks up by issue number.

```bash
mkdir -p .beads/inspect-feedback
```

**Read existing feedback to track polish attempts:**

```bash
if [ -f .beads/inspect-feedback/issue-<number>.json ]; then
  EXISTING_FEEDBACK=$(cat .beads/inspect-feedback/issue-<number>.json)
  PREVIOUS_ATTEMPTS=$(echo "$EXISTING_FEEDBACK" | jq -r '.polish_attempts // 0')
else
  PREVIOUS_ATTEMPTS=0
fi
```

**Calculate new attempt count:**
- If verdict is POLISH: increment `PREVIOUS_ATTEMPTS` by 1
- Otherwise: set to 0

**Check for escalation:**
- If `polish_attempts >= 3` and verdict is POLISH, override verdict to FEEDBACK and add escalation note to rationale

**Augment the inspector's JSON** with `type`, `polish_attempts`, and `reviewed_at`, then write:

```python
# Inspector already provides: issue_number, pr_number, verdict, dimensions, rationale
# Augment with operational metadata:
feedback = inspector_output  # The parsed JSON from inspector
feedback["type"] = "pr_review"
feedback["polish_attempts"] = new_attempt_count
feedback["reviewed_at"] = datetime.now(timezone.utc).isoformat()
```

Write atomically using a temp file:
```bash
cat > .beads/inspect-feedback/issue-<number>.json.tmp << 'EOF'
<augmented json>
EOF
mv .beads/inspect-feedback/issue-<number>.json.tmp .beads/inspect-feedback/issue-<number>.json
```

#### Issue Feedback

After the issue-reviewer returns valid JSON, augment it and write to `.beads/inspect-feedback/issue-<number>.json`.

```bash
mkdir -p .beads/inspect-feedback
```

**Augment the issue-reviewer's JSON** with `reviewed_at`, then write:

```python
# Issue-reviewer already provides: type, issue_number, pr_number, verdict, dimensions, rationale, duplicate_of
# Augment with operational metadata:
feedback = issue_reviewer_output  # The parsed JSON from issue-reviewer
feedback["reviewed_at"] = datetime.now(timezone.utc).isoformat()
```

Write atomically using a temp file (same pattern as PR feedback).

Issue feedback does NOT track `polish_attempts` (not applicable to standalone issues).

**Note:** Both PR reviews and issue reviews write to the same path pattern (`.beads/inspect-feedback/issue-<number>.json`). The cross-referencing in Step 1 prevents simultaneous collisions (a PR-linked issue is never treated as standalone). However, if a PR is later closed and the issue becomes standalone, re-running `/inspect-issues` will overwrite the old PR review with an issue review. Consumers must check the `type` field to determine the feedback shape.

### Step 4: Display Reports

#### PR Reports

For each PR, render the inspector's JSON as a readable markdown report in the terminal. Do NOT write to temp files. Do NOT post to GitHub.

```
## Inspection: PR #<pr_number> / Issue #<issue_number>

### What Changed
<dimensions.what_changed>

### Project Value
<dimensions.project_value>

### Issue Validity
<dimensions.issue_validity>

### Intent Alignment
<dimensions.intent_alignment>

### Scope
<dimensions.scope>

### Security
<dimensions.security>

### Code Quality
<dimensions.code_quality>

### Root Cause Depth
<dimensions.root_cause_depth>

---

**Verdict: <verdict>** [(attempt N/3) if POLISH with polish_attempts > 0]

<rationale>
```

Lead with **What Changed** and **Project Value** — these help the maintainer understand the change before seeing the safety checklist.

#### Issue Reports

For each standalone issue, render the issue-reviewer's JSON as a readable markdown report:

```
## Triage: Issue #<issue_number> — <title>

### Issue Validity
<dimensions.issue_validity>

### Actionability
<dimensions.actionability>

### Project Relevance
<dimensions.project_relevance>

### Priority Signal
<dimensions.priority_signal>

### Duplicate Check
<dimensions.duplicate_check>

### Proposed Direction
<dimensions.proposed_direction>

---

**Verdict: <verdict>** [Duplicate of #<duplicate_of> if applicable]

<rationale>
```

### Step 5: Prompt User for Action

#### PR Actions

Use AskUserQuestion to present options based on the verdict:

| Verdict | Options |
|---------|---------|
| **MERGE** | "Merge" (post concise comment + squash-merge the PR), "Skip" (no action) |
| **POLISH** | "Polish" (run polisher agent on PR branch, then re-prompt with updated verdict), "Skip" |
| **FEEDBACK** | "Comment" (post concise verdict comment only), "Skip" |
| **REWORK** | "Comment" (post concise verdict comment only), "Skip" |
| **REJECT** | "Comment" (post concise verdict comment only), "Skip" |

**Actions by choice:**

**"Merge"** (MERGE verdict only):
1. Post a concise comment to the PR (see format below)
2. Squash-merge the PR: `gh pr merge <pr-number> --squash`

**"Polish"** (POLISH verdict only):
1. **Check attempt limit:** If `polish_attempts >= 3`, skip polish action and display warning:
   ```
   ⚠️ POLISH limit reached (3/3 attempts)

   This PR has been polished 3 times without reaching MERGE.
   Consider manual review or REWORK verdict.

   Options: "Comment" (post feedback), "Skip"
   ```
   Then skip to "Comment" or "Skip" options (do not offer "Polish" again).

2. Note the current branch: `git branch --show-current`
3. Fetch and checkout the PR branch: `gh pr checkout <pr-number>`
4. Get the list of changed files: `git diff --name-only main...HEAD`
5. Launch the polisher: `Task(description="Polish bot fix for issue #<issue-number>", prompt="Polish these files: <file list>", subagent_type="polisher")`
6. If the polisher made changes, stage, commit, and push:
   ```bash
   git add <changed-files>
   ```
   ```bash
   git commit -m "style: polish bot fix (refs #<issue-number>)"
   ```
   ```bash
   git push
   ```
7. Return to the original branch: `git checkout <original-branch>`
8. Re-run the inspector (Step 3) on the polished PR and re-prompt with the new verdict

**"Comment"** (FEEDBACK/REWORK/REJECT verdicts):
1. Post a concise comment to the PR (see format below)

**"Skip":** No action taken for this PR.

**PR comment format (follow VOICE.md — warm, conversational, specific):**
```
<!-- line:inspect-issues verdict -->
**Verdict: <VERDICT>**
<1-2 sentence warm rationale — acknowledge the work, explain the verdict conversationally>
---
*Reviewed by `/inspect-issues`.*

Example (MERGE): "Nice work — clean fix that matches existing patterns. Ready to ship."
Example (POLISH): "Good direction! A few style nits to tidy up before this is ready."
Example (REWORK): "Appreciate the effort — the approach needs some rethinking though. See the dimensions above for specifics."
```

Post using:
```bash
gh pr comment <pr-number> --body "<comment>"
```

#### Issue Actions

Use AskUserQuestion to present options based on the verdict:

| Verdict | Options |
|---------|---------|
| **VALID** | "Auto-fix" (trigger issue-agent to file a candidate fix PR — recommended), "Respond" (post templated response via `/respond`), "Label" (apply triage label), "Skip" |
| **NEEDS_INFO** | "Respond" (post templated response via `/respond`), "Skip" |
| **DUPLICATE** | "Respond & Close" (post templated response via `/respond`, then close), "Skip" |
| **REJECT** | "Respond & Close" (post templated response via `/respond`, then close), "Skip" |

**Actions by choice:**

**"Auto-fix"** (VALID verdict only):
1. Close then reopen the issue to trigger the `issues: [reopened]` event in `.github/workflows/issue-agent.yml`:
   ```bash
   gh issue close <issue-number>
   gh issue reopen <issue-number>
   ```
   The issue-agent workflow will post its own comment as `line-sous-chef[bot]` — do not post a separate comment here.

**"Label"** (VALID verdict only):
1. Apply a triage label to the issue:
   ```bash
   gh issue edit <issue-number> --add-label "triaged"
   ```

**"Respond & Close"** (DUPLICATE or REJECT verdict):
1. Follow the "Respond" flow below to post a templated comment as `line-sous-chef[bot]` (use `duplicate` or `wont-fix` template)
2. After the respond workflow succeeds, close the issue:
   For DUPLICATE:
   ```bash
   gh issue close <issue-number> --reason "not planned"
   ```
   For REJECT:
   ```bash
   gh issue close <issue-number> --reason "not planned"
   ```

**"Respond"** (all verdicts — posts as `line-sous-chef[bot]` via the respond workflow):

Map the verdict to a suggested template:
- **VALID** → `acknowledged` (always include a proposed solution focused on user value — a candidate fix PR should follow), `fix-shipped` (if a fix has shipped), `workaround-available` (if a workaround exists but fix is pending), or skip template suggestion
- **NEEDS_INFO** → `needs-info`
- **DUPLICATE** → `duplicate`
- **REJECT** → `wont-fix`

Then follow the `/respond` command flow:
1. Read the suggested template from `core/templates/responses/<template>.md`
2. Collect required variables from the user (use AskUserQuestion to ask for each required variable listed in the template's frontmatter)
3. Render the template with variable substitution and show preview
4. On confirmation, dispatch the workflow:
   ```bash
   gh workflow run respond.yml -f issue_number=<N> -f template=<template_name> -f variables='<json>' -f close=<from_frontmatter> -f close_reason=<from_frontmatter>
   ```
5. Write response record to `.beads/inspect-feedback/issue-<N>.json` (append to `responses` array if file exists, or create minimal file with `type: "response_only"`)

**"Skip":** No action taken for this issue.

**Issue comments — bot identity rule:**
All issue comments must be posted as `line-sous-chef[bot]` via the respond workflow. Never call `gh issue comment` directly for issues — it posts as the local user. Use the "Respond" flow above, which dispatches `gh workflow run respond.yml ...` to post as the bot. Available templates: `acknowledged`, `needs-info`, `fix-shipped`, `workaround-available`, `duplicate`, `wont-fix`.

### Step 6: Output Summary

Display a summary report with two sections (PRs, Issues). Only show sections that have entries.

```
╔══════════════════════════════════════════════════════════════╗
║  INSPECT: Review Complete                                     ║
╚══════════════════════════════════════════════════════════════╝

┌─── PRs ─────────────────────────────────────────────────────┐
│ PR #7   MERGE    Issue #6: <title>          → merged         │
│ PR #12  REJECT   Issue #11: <title>         → commented      │
│ PR #15  POLISH   Issue #14: <title>         → skipped        │
└─────────────────────────────────────────────────────────────┘

┌─── Issues ──────────────────────────────────────────────────┐
│ Issue #3   VALID       <title>              → auto-fix       │
│ Issue #9   DUPLICATE   <title>              → closed         │
│ Issue #18  NEEDS_INFO  <title>              → commented      │
└─────────────────────────────────────────────────────────────┘

  PRs:
    MERGE:    1 — ready to merge
    REJECT:   1 — close issue and PR
    POLISH:   1 — polished and ready

  Issues:
    VALID:      1 — ready for work
    DUPLICATE:  1 — closed as duplicate
    NEEDS_INFO: 1 — needs clarification
```

Group the tally by verdict type within each section. Only show lines for verdicts that have a count > 0. Annotate each line with the action taken (→ merged / → commented / → polished / → skipped / → auto-fix / → closed / → labeled).

## Error Handling

- **gh CLI not authenticated:** Report the error and stop.
- **PR has no issue reference:** Proceed normally with `issue_number` as null (per Step 2a). The PR is evaluated on its own merits.
- **Issue reference found but inaccessible:** Log a warning but still inspect the PR using only the PR metadata and diff.
- **Issue has no body:** Proceed with title only. The issue-reviewer will note the lack of detail in the actionability dimension.
- **Inspector fails:** Skip that PR, note it in the summary as "SKIPPED — inspection failed".
- **Issue-reviewer fails:** Skip that issue, note it in the summary as "SKIPPED — triage failed".
- **Feedback file write fails:** Log warning but continue (feedback is supplementary, not critical).
- **Polisher fails on POLISH verdict:** Display the verdict anyway. Note in the summary that polish was attempted but failed.
- **Merge fails:** Note in the summary. The verdict was still computed.
- **Cross-reference mismatch** (PR closed but issue still open): Treat the issue as standalone.
