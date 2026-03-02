---
description: Post a templated response to a GitHub issue as line-sous-chef[bot]
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

## Summary

**Post a standardized follow-up comment on a GitHub issue.** Renders a response template, shows a preview for approval, dispatches the GitHub Actions workflow to post as `line-sous-chef[bot]`, and records the response in feedback tracking.

**Usage:**
- `/respond 17 fix-shipped --version v0.20.0`
- `/respond 5 needs-info --questions "- What platform are you on?\n- What version of Claude Code?"`
- `/respond 9 duplicate --original-issue 3`
- `/respond 12 wont-fix --reason "This is working as designed — the timeout is configurable via --cook-timeout." --alternative "Try: /loop --cook-timeout 7200"`
- `/respond 8 workaround-available --workaround "Run /loop --cook-timeout 7200 to override the default." --fix-timeline "A proper default bump is planned for v0.21.0."`

---

## Process

### Step 1: Parse Arguments

Parse `$ARGUMENTS` in this format: `<issue_number> <template> [--key value ...]`

Extract:
- `issue_number` — the first positional argument (integer)
- `template` — the second positional argument (template name like `fix-shipped`)
- Key-value pairs — remaining `--key value` flags mapped to template variables

**Variable name mapping:** Convert CLI flags to template variable names:
- `--version` → `VERSION`
- `--workaround` → `WORKAROUND`
- `--fix-timeline` → `FIX_TIMELINE`
- `--questions` → `QUESTIONS`
- `--reason` → `REASON`
- `--alternative` → `ALTERNATIVE`
- `--original-issue` → `ORIGINAL_ISSUE`

General rule: strip `--`, replace `-` with `_`, uppercase.

**Auto-populated variables** (do not pass via CLI):
- `ISSUE_NUMBER` — extracted from the first positional argument
- `REPORTER` — fetched from the issue author's GitHub login

If `$ARGUMENTS` is empty or missing required positional args, show usage help and stop.

### Step 2: Read and Validate Template

Read the template file from `core/templates/responses/<template>.md`.

If the file doesn't exist, list available templates from `core/templates/responses/` (excluding `VOICE.md`) and stop.

Parse YAML frontmatter to extract:
- `name` — template identifier
- `close` — whether to close the issue after posting
- `close_reason` — reason for closing (if applicable)
- `variables` — map of variable names with `required` and `description` fields

**Validate required variables:** Check that all variables marked `required: true` in frontmatter have been provided via CLI flags. If any are missing, show which variables are needed with their descriptions and stop.

### Step 3: Fetch Issue Context

Fetch the target issue to confirm it exists and get context:

```bash
gh issue view <issue_number> --json number,title,state,author,labels
```

If the issue doesn't exist, report the error and stop.

If the issue is already closed, warn the user but allow proceeding (they may want to post a follow-up on a closed issue).

### Step 4: Check for Prior Responses

Read the feedback file if it exists:

```bash
cat .beads/inspect-feedback/issue-<issue_number>.json 2>/dev/null
```

If the file exists and has a `responses` array, check if the same template was already sent. If so, **warn the user**:

```
Warning: A "fix-shipped" response was already posted to issue #17 on 2026-03-02.
Posting again will create a duplicate comment.
```

Let them decide whether to proceed.

### Step 5: Render Preview

Substitute all variables into the template body (strip YAML frontmatter first):
- Replace `{{VAR}}` with the provided value for each variable
- Replace `{{ISSUE_NUMBER}}` with the issue number
- Replace `{{REPORTER}}` with the issue author's login

Display the rendered comment to the user with a clear preview header:

```
--- Preview: Response to Issue #17 ---

[rendered comment body]

--- End Preview ---

Template: fix-shipped
Close issue: no
```

### Step 6: Confirm with User

Use AskUserQuestion to confirm:

- **"Post"** — dispatch the workflow
- **"Edit"** — let the user modify variables and re-render
- **"Cancel"** — abort without posting

If they choose "Edit", ask which variable to change, update it, and return to Step 5.

### Step 7: Dispatch Workflow

Build the variables JSON from the collected key-value pairs and dispatch:

```bash
gh workflow run respond.yml \
  -f issue_number=<N> \
  -f template=<template_name> \
  -f variables='<json_string>' \
  -f close=<true|false> \
  -f close_reason=<reason>
```

The `close` and `close_reason` values come from the template frontmatter.

### Step 8: Poll for Completion

Wait briefly, then check the workflow run status:

```bash
gh run list --workflow=respond.yml --limit=1 --json status,conclusion,databaseId
```

If the run completes successfully, report success. If it fails, report the failure and suggest checking the Actions tab.

### Step 9: Write Feedback Record

Create or update the feedback file at `.beads/inspect-feedback/issue-<N>.json`.

```bash
mkdir -p .beads/inspect-feedback
```

**If the file already exists**, read it and append to the `responses` array:

```json
{
  "responses": [
    {
      "template": "fix-shipped",
      "posted_at": "2026-03-02T02:47:22Z",
      "variables": { "VERSION": "v0.20.0" }
    }
  ]
}
```

**If the file doesn't exist**, create a minimal one:

```json
{
  "type": "response_only",
  "issue_number": 17,
  "responses": [
    {
      "template": "fix-shipped",
      "posted_at": "2026-03-02T02:47:22Z",
      "variables": { "VERSION": "v0.20.0" }
    }
  ]
}
```

Use the current UTC timestamp for `posted_at`.

### Step 10: Report Result

Display a success summary:

```
Response posted to issue #17
  Template: fix-shipped
  Variables: VERSION=v0.20.0
  Close: no
  Feedback file: .beads/inspect-feedback/issue-17.json
  Actions run: https://github.com/smileynet/line-cook/actions/runs/<id>
```

## Error Handling

- **Template not found:** List available templates and stop.
- **Missing required variables:** Show which are needed with descriptions and stop.
- **Issue doesn't exist:** Report error and stop.
- **Workflow dispatch fails:** Report the gh CLI error. Suggest checking authentication.
- **Workflow run fails:** Report failure, link to Actions tab for logs.
- **Feedback file write fails:** Warn but don't fail — the comment was already posted.
- **Duplicate response warning:** Inform but let user decide.
