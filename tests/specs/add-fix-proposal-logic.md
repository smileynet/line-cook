# Test Specification: Add fix-proposal logic to analysis prompt

## Bead
lc-p62.1.2

## Tracer
Decision layer — proves Claude can distinguish fixable vs unclear issues and act accordingly

## Context
- Extend prompt with fix-or-ask decision logic
- Add structured comment template for proposals
- Deliverable: Prompt that proposes fixes when confident, asks questions when not

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Issue with clear typo in code | Fix branch created with correction | High confidence fix |
| Issue with broken import | Fix branch with corrected import | High confidence fix |
| Issue with vague "doesn't work" | Clarifying questions, no branch | Low confidence |
| Issue affecting >3 files | Questions instead of fix (scope guard) | Guardrail |
| Fix branch comment | Contains branch name, checkout cmd, test steps | Template |

## Validation Checklist
- [ ] Prompt includes confidence assessment logic
- [ ] Fix branch naming: `fix/issue-{number}`
- [ ] Commit message references issue number
- [ ] Comment template includes: what changed, branch name, checkout command, test steps, verification request
- [ ] 3-file modification guardrail is enforced
- [ ] Low-confidence issues get questions, not bad fixes
- [ ] Never auto-merge language in comments

## Implementation Notes
Quality depends on prompt engineering. Test with a variety of issue types to calibrate confidence threshold.
