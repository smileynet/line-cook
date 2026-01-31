# Test Specification: Add task-by-task progress output

**Bead:** lc-cnl

## Tracer

UX - proves progress tracking works

## Context

- Track iteration count
- After each /line:run, output progress block:
  - Task N: <id> - <title>
  - Status: completed/failed
  - Time: (optional, if available)
- Running totals: completed X, remaining Y


**Deliverable:** Progress output after each task completion

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| TODO | TODO | Define based on tracer strategy |

## Edge Cases

- [ ] Define edge cases based on implementation
- [ ] Consider error conditions
- [ ] Consider boundary values

## Implementation Notes

These specs will be translated to language-specific tests during /cook RED phase.

Reference the tracer strategy to determine:
1. What minimal test proves the layer works?
2. What would be the simplest way to verify success?
3. What's the first thing that could go wrong?
