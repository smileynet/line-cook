# Test Specification: Write analysis prompt with classification and labeling

## Bead
lc-wbo.1.2

## Tracer
Intelligence layer — proves Claude can analyze issues, search codebase, and produce structured responses

## Context
- Write automation prompt for claude-code-action
- Scope --allowedTools for safe read-only + labeling access
- Deliverable: Complete prompt with classification, labeling, and structured response

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Issue describing a bug | Label: "bug", analysis of relevant code | Classification accuracy |
| Issue describing a feature request | Label: "enhancement", acknowledgement | Classification accuracy |
| Issue asking a question | Label: "question", helpful response | Classification accuracy |
| Issue with specific file reference | Analysis includes that file's content | Codebase search |
| Vague issue with no clear problem | Clarifying questions, no diagnosis | Uncertainty handling |
| Issue referencing error message | Grep for error message in codebase | Search capability |

## Validation Checklist
- [ ] Prompt interpolates issue title, body, and number
- [ ] --allowedTools includes: Read, Grep, Glob, Bash(gh issue:*), Bash(gh label:*)
- [ ] --allowedTools does NOT include: Edit, Write, Bash(git:*)
- [ ] Response format is structured markdown (not free-form)
- [ ] Classification covers: bug, enhancement, question
- [ ] Labels are applied via `gh issue edit --add-label`
- [ ] Clarifying questions are specific, not generic

## Implementation Notes
Test by creating real issues with known answers and verifying the response quality.
