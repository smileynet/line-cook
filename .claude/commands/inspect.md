---
description: Review bot-created issue/PR pairs before merging
allowed-tools: Bash, Read, Write, Glob, Grep, Task
---

## Summary

**Review all open bot-created PRs and produce a verdict for each.** Discovers PRs from `fix/issue-*` branches, delegates each to the inspector agent, acts on verdicts, and posts structured comments.

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

### Step 4: Act on Verdicts

For each verdict:

- **MERGE** — No action needed. The maintainer will merge manually.
- **POLISH** — Run the polisher agent on the PR's changed files:
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
- **FEEDBACK** — No code changes. Verdict comment only.
- **REWORK** — No code changes. Verdict comment only.
- **REJECT** — No code changes. Verdict comment only. Do NOT auto-close — the maintainer decides.

### Step 5: Post Verdict to PR

For each PR, write the inspector's full analysis to a temp file and post it as a PR comment.

Write the comment file:
```
Write /tmp/inspect-verdict-<pr-number>.md with contents:

<!-- line:inspect verdict -->
## Inspection Report

<inspector's full output (all 5 dimensions + verdict)>

---
*Automated review by `/inspect`. Verdicts are advisory — maintainer decides.*
```

Post it:
```bash
gh pr comment <pr-number> --body-file /tmp/inspect-verdict-<pr-number>.md
```

### Step 6: Output Summary

Display a summary report with all verdicts:

```
╔══════════════════════════════════════════════════════════════╗
║  INSPECT: Bot PR Review Complete                             ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ PR #7   MERGE    Issue #6: <title truncated to fit>         │
│ PR #12  REJECT   Issue #11: <title truncated to fit>        │
└─────────────────────────────────────────────────────────────┘

  MERGE:    1 — ready to merge
  POLISH:   0 — polished and ready
  FEEDBACK: 0 — needs maintainer judgment
  REWORK:   0 — fix needs rework
  REJECT:   1 — close issue and PR

Verdict comments posted to each PR.
```

Group the tally by verdict type. Only show lines for verdicts that have a count > 0.

## Error Handling

- **gh CLI not authenticated:** Report the error and stop.
- **Issue not found for a PR:** Skip that PR, note it in the summary as "SKIPPED — issue not found".
- **Inspector fails:** Skip that PR, note it in the summary as "SKIPPED — inspection failed".
- **Polisher fails on POLISH verdict:** Post the verdict comment anyway. Note in the summary that polish was attempted but failed.
- **Comment posting fails:** Note in the summary. The verdict was still computed.
