# Test Specification: Create issue-agent workflow with ADR-0013 hardening

## Bead
lc-wbo.1.1

## Tracer
Foundation — proves GitHub Actions triggers on issue events and runs claude-code-action

## Context
- Create .github/workflows/issue-agent.yml
- Follow ADR-0013 hardening patterns from existing workflows
- Deliverable: Working workflow with trigger and basic response

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| New issue opened by human | Workflow triggers and runs | Basic trigger test |
| New issue opened by bot | Workflow skips (`if:` guard) | Bot loop prevention |
| Workflow YAML | Has `permissions:` block | ADR-0013 compliance |
| Workflow YAML | Has `timeout-minutes:` | ADR-0013 compliance |
| Workflow YAML | Has `concurrency:` group | ADR-0013 compliance |
| claude-code-action step | Uses `claude_code_oauth_token` | Auth via Max subscription |
| claude-code-action step | Has `--max-turns 10` | Cost/usage cap |

## Validation Checklist
- [ ] Workflow triggers on `issues: [opened]`
- [ ] Permissions are explicit and minimal (`contents: read`, `issues: write`)
- [ ] Timeout is set (suggest 15 minutes for Claude analysis)
- [ ] Concurrency group prevents duplicate runs
- [ ] Bot-created issues are filtered out
- [ ] OAuth token is referenced from secrets
- [ ] Basic prompt produces a comment on a test issue

## Implementation Notes
These specs will be validated by YAML linting and manual trigger testing.
Reference: `.github/workflows/validate.yml` for hardening patterns.
