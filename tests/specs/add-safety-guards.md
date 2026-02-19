# Test Specification: Add safety guards and loop prevention

## Bead
lc-wbo.1.3

## Tracer
Safety layer — proves the agent doesn't run on its own comments or spam issues

## Context
- Harden the workflow against edge cases and self-triggering
- Deliverable: Hardened workflow that handles edge cases gracefully

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Issue created by github-actions[bot] | Workflow skips | Bot filter |
| Issue created by the GitHub App (future) | Workflow skips | Self-loop prevention |
| Two issues created simultaneously | Only one workflow runs per issue | Concurrency group |
| Issue with empty body | Graceful handling, asks for details | Edge case |
| Issue with very long body (>10k chars) | Truncated or handled within --max-turns | Edge case |
| Issue with markdown tables/code blocks | Parsed correctly in prompt | Edge case |
| Rapid re-trigger on same issue | Previous run cancelled | Concurrency |

## Validation Checklist
- [ ] `if:` guard checks `github.event.issue.user.type != 'Bot'`
- [ ] Concurrency group uses issue number: `issue-agent-${{ github.event.issue.number }}`
- [ ] --max-turns is set and effective
- [ ] Empty body doesn't cause workflow failure
- [ ] Agent doesn't respond to its own comments (if re-triggered)

## Implementation Notes
Test edge cases manually by creating issues with various body formats.
