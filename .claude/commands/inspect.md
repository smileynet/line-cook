---
description: Review bot-created issue/PR pairs before merging
allowed-tools: Bash, Read, Glob, Grep, Task, AskUserQuestion
---

## Summary

**Review all open bot-created PRs and produce a verdict for each.** Discovers PRs from `fix/issue-*` branches, delegates each to the inspector agent, displays the full report locally, and prompts for action.

**Usage:**
- `/inspect` — review all open bot PRs
- `/inspect 7` — review only PR #7

---

## Process

### Step 1: Discover Open Bot PRs

```bash
gh pr list --state open --json number,title,headRefName,body,url
```

Filter to PRs whose `headRefName` starts with `fix/issue-`. If `$ARGUMENTS` is a number, filter to that single PR.

If no matching PRs are found, report "No open bot PRs found." and stop.

### Step 2: Fetch Context for Each PR

For each bot PR, extract the issue number from the branch name (`fix/issue-42-desc` → `42`).

Fetch context for each PR (run these in parallel where possible):

**Issue body:**
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

### Step 3: Invoke Inspector Agent

For each PR, delegate to the inspector agent via Task:

```
Task(subagent_type="inspector", prompt=<assembled context>)
```

The prompt should include:
- Issue number, title, and body
- PR number, title, and body
- The code diff
- List of changed files

If reviewing multiple PRs, launch inspector agents in parallel.

Parse the inspector's response to extract the verdict line (`**Verdict: <VERDICT>**`).

### Step 4: Display Report Locally

For each PR, display the inspector's full analysis (all 8 dimensions + verdict) directly in the terminal as markdown. Do NOT write to temp files. Do NOT post to GitHub.

Lead with **What Changed** and **Project Value** — these help the maintainer understand the change before seeing the safety checklist. The remaining 6 dimensions (validity, alignment, scope, security, quality, root cause) follow as due diligence.

### Step 5: Prompt User for Action

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
1. Note the current branch: `git branch --show-current`
2. Fetch and checkout the PR branch: `gh pr checkout <pr-number>`
3. Get the list of changed files: `git diff --name-only main...HEAD`
4. Launch the polisher: `Task(subagent_type="polisher", prompt="Polish these files: <file list>")`
5. If the polisher made changes, stage, commit, and push:
   ```bash
   git add <changed-files>
   ```
   ```bash
   git commit -m "style: polish bot fix (refs #<issue-number>)"
   ```
   ```bash
   git push
   ```
6. Return to the original branch: `git checkout <original-branch>`
7. Re-run the inspector (Step 3) on the polished PR and re-prompt with the new verdict

**"Comment"** (FEEDBACK/REWORK/REJECT verdicts):
1. Post a concise comment to the PR (see format below)

**"Skip":** No action taken for this PR.

**Concise comment format** (not the full analysis):
```
<!-- line:inspect verdict -->
**Verdict: <VERDICT>**
<1-2 sentence rationale>
---
*Reviewed by `/inspect`.*
```

Post using:
```bash
gh pr comment <pr-number> --body "<comment>"
```

### Step 6: Output Summary

Display a summary report with all verdicts and actions taken:

```
╔══════════════════════════════════════════════════════════════╗
║  INSPECT: Bot PR Review Complete                             ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ PR #7   MERGE    Issue #6: <title>          → merged         │
│ PR #12  REJECT   Issue #11: <title>         → commented      │
│ PR #15  POLISH   Issue #14: <title>         → skipped        │
└─────────────────────────────────────────────────────────────┘

  MERGE:    1 — ready to merge
  REJECT:   1 — close issue and PR
  POLISH:   1 — polished and ready
```

Group the tally by verdict type. Only show lines for verdicts that have a count > 0. Annotate each PR line with the action taken (→ merged / → commented / → polished / → skipped).

## Error Handling

- **gh CLI not authenticated:** Report the error and stop.
- **Issue not found for a PR:** Skip that PR, note it in the summary as "SKIPPED — issue not found".
- **Inspector fails:** Skip that PR, note it in the summary as "SKIPPED — inspection failed".
- **Polisher fails on POLISH verdict:** Display the verdict anyway. Note in the summary that polish was attempted but failed.
- **Merge fails:** Note in the summary. The verdict was still computed.
