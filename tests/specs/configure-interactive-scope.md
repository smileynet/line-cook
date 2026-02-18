# Test Specification: Configure interactive mode tool scope

## Bead
lc-p62.2.2

## Tracer
Scope layer — proves interactive responses are safe and useful

## Context
- Set appropriate --allowedTools for interactive mode
- May differ from automation mode scope
- Deliverable: Interactive mode with appropriate tool scoping

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| @claude "what does this function do?" | Read-only analysis response | Safe scope |
| @claude "can you fix this?" | May create branch if tools allow | Optional git access |
| Interactive session | Completes within --max-turns 8 | Usage cap |
| Follow-up after initial analysis | Response references prior context | Thread awareness |
| Multiple @claude in same thread | Each gets independent response | No state leakage |

## Validation Checklist
- [ ] --allowedTools set for interactive mode
- [ ] --max-turns 8 (shorter than auto-triage)
- [ ] Read-only access at minimum (Read, Grep, Glob)
- [ ] gh issue comment access for responding
- [ ] Git operations optional (consider per-request)
- [ ] Conversation flow tested: question → response → follow-up

## Implementation Notes
Consider whether interactive mode should share the same --allowedTools as automation mode or have a separate, more restrictive set.
