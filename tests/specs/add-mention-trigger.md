# Test Specification: Add issue_comment trigger with @mention guard

## Bead
lc-p62.2.1

## Tracer
Trigger layer — proves interactive mode activates only on @claude mentions

## Context
- Add issue_comment trigger to existing workflow
- Guard with @claude contains check
- Deliverable: Workflow responds to @claude mentions

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Comment containing "@claude help" | Workflow triggers | Mention detection |
| Comment containing "thanks @claude" | Workflow triggers | Mention anywhere in text |
| Comment without @claude | Workflow does not trigger | Guard works |
| Bot comment with @claude | Workflow skips | Bot loop prevention |
| @claude in issue body (not comment) | Handled by issues trigger, not comment | Trigger separation |

## Validation Checklist
- [ ] `issue_comment: [created]` added to triggers
- [ ] `if:` contains `contains(github.event.comment.body, '@claude')`
- [ ] Bot comments excluded
- [ ] Interactive mode auto-detected by claude-code-action (no explicit prompt)
- [ ] Full issue thread context passed to Claude

## Implementation Notes
claude-code-action automatically enters interactive mode for comment-triggered events.
