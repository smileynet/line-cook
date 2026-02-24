# Handoff: Validate Issue-Agent Auth & Permissions

**Commit:** 6001a86 (`fix: wire App token and fix allowedTools patterns in issue-agent`)
**Date:** 2026-02-22
**Branch:** main

## What Changed

Two bugs fixed in `.github/workflows/issue-agent.yml`:

1. **allowedTools patterns were exact matches** — `Bash(gh issue edit)` blocked `gh issue edit 1 --add-label "bug"`. Fixed by adding wildcard suffix (` *`).
2. **GitHub App token never wired in** — Added `actions/create-github-app-token@v2` to both jobs, passed via `github_token` input.

New file: `.github/workflows/check-oauth-token.yml` (monthly token expiry check).

## Prerequisites (Manual — Must Be Done by Human)

These cannot be automated. Verify before testing:

- [ ] `LINE_COOK_APP_ID` secret exists: `gh secret list | grep LINE_COOK_APP_ID`
- [ ] `LINE_COOK_APP_PRIVATE_KEY` secret exists: `gh secret list | grep LINE_COOK_APP_PRIVATE_KEY`
- [ ] `CLAUDE_CODE_OAUTH_TOKEN` is a long-lived token from `claude setup-token` (not extracted from `~/.claude/.credentials.json`)
- [ ] GitHub App is installed on the `smileynet/line-cook` repository

If any are missing, stop — the workflow will fail at the "Generate app token" step.

## Test Plan

### Test 1: Trigger Analyze Job (Label + Analysis)

```bash
# Close and reopen issue #1 to trigger the workflow
gh issue close 1 --comment "Closing to re-test issue agent"
sleep 2
gh issue reopen 1
```

**Watch the workflow:**
```bash
# Wait for run to appear (may take 10-30s)
sleep 30
gh run list --workflow=issue-agent.yml --limit=3
```

**Get the run ID and check logs:**
```bash
RUN_ID=$(gh run list --workflow=issue-agent.yml --limit=1 --json databaseId --jq '.[0].databaseId')
gh run watch $RUN_ID
```

**Expected outcomes:**
- [ ] Workflow triggers on `issues.reopened` event
- [ ] "Generate app token" step succeeds (no secret errors)
- [ ] "Analyze issue" step runs without `allowedTools` blocking errors
- [ ] A label is applied to the issue (bug, enhancement, or question)
- [ ] An analysis comment is posted on the issue

**Failure modes to check in logs:**
- `Error: Input required and not supplied: app-id` → `LINE_COOK_APP_ID` secret missing
- `Error: Could not create token` → App not installed or private key wrong
- Empty error after "Bash" tool call → `allowedTools` still blocking (grep logs for "not allowed")

### Test 2: Trigger Respond Job (@claude Mention)

```bash
gh issue comment 1 --body "@claude What files are related to the issue agent workflow?"
```

**Expected outcomes:**
- [ ] Respond job triggers (check Actions tab)
- [ ] Claude posts a reply referencing codebase files
- [ ] Comment is posted under the App bot identity (not `github-actions[bot]`)

### Test 3: Verify Bot Identity

After Tests 1-2 complete:

```bash
# Check who posted the analysis comment
gh issue view 1 --json comments --jq '.comments[-1].author.login'
```

**Expected:** The App bot username (e.g., `line-cook-app[bot]` or whatever the App slug resolves to), NOT `github-actions[bot]`.

### Test 4: Verify Token Check Workflow

```bash
gh workflow run check-oauth-token.yml
sleep 30
RUN_ID=$(gh run list --workflow=check-oauth-token.yml --limit=1 --json databaseId --jq '.[0].databaseId')
gh run watch $RUN_ID
```

**Expected outcomes:**
- [ ] "Test Claude Code auth" step succeeds (token is valid)
- [ ] "Alert on failure" step is skipped (since token works)
- [ ] No issue created

### Test 5: Verify Fix Branch CI Triggering (Optional)

This only applies if the agent creates a fix branch (confidence-dependent). If it does:

```bash
# Check if a fix branch was created
git fetch origin
git branch -r | grep fix/issue-
```

If a branch exists:
- [ ] Check the Validate workflow triggered on that branch
- [ ] Commit author shows App bot identity: `git log origin/fix/issue-1-* --format='%an <%ae>' -1`

## Validation Checklist (Summary)

| Check | Command | Expected |
|-------|---------|----------|
| App token generates | Workflow logs → "Generate app token" | Success |
| Labels applied | `gh issue view 1 --json labels` | Has classification label |
| Analysis posted | `gh issue view 1 --json comments` | Structured analysis comment |
| Bot identity | Comment author login | App bot, not github-actions |
| @claude responds | Post @claude comment, check reply | Reply posted |
| Token check works | `gh workflow run check-oauth-token.yml` | Success, no issue created |
| No blocked tools | Workflow logs → "Analyze issue" | No empty errors after Bash calls |

## Rollback

If the workflow is broken worse than before:

```bash
git revert 6001a86
git push
```

This restores the previous (non-functional but non-breaking) state.

## Files Modified

| File | What Changed |
|------|-------------|
| `.github/workflows/issue-agent.yml` | Wildcard `allowedTools`, App token steps, `github_token` input, bot identity |
| `.github/workflows/check-oauth-token.yml` | New — monthly token expiry check |
| `docs/installation/issue-agent.md` | Prerequisites, App setup steps, tool pattern docs, troubleshooting |
| `tests/specs/integrate-app-token.md` | Updated validation checklist |
| `docs/features/lc-769-acceptance.md` | Removed "not yet integrated" caveat |
