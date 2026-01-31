# Test Specification: Add --max-iterations safety limit

**Bead:** lc-cnl

## Tracer

Safety - proves iteration limits work

## Context

- Parse $ARGUMENTS for --max-iterations N or -n N
- Default to 25 if not specified
- Track iteration count
- Stop loop when limit reached
- Include limit status in final summary


**Deliverable:** --max-iterations flag with default of 25

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
