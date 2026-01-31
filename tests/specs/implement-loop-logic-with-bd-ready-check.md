# Test Specification: Implement loop logic with bd ready check

**Bead:** lc-cnl

## Tracer

Core loop - proves iteration and termination work

## Context

- Step 1: Check bd ready for available tasks
- Step 2: If empty, output final summary and exit
- Step 3: Call Skill("line:run")
- Step 4: Parse result status (success/failure)
- Step 5: If failure, stop with error summary
- Step 6: Output task progress, goto Step 1


**Deliverable:** Working loop that executes until done or failure

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
