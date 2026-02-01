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
| `$ARGUMENTS=""` | `max_iterations=25` | Default limit applied |
| `$ARGUMENTS="--max-iterations 10"` | `max_iterations=10` | Long form parsed |
| `$ARGUMENTS="-n 5"` | `max_iterations=5` | Short form parsed |
| `$ARGUMENTS="--max-iterations 0"` | Stops after ready check, 0 tasks executed | Edge: zero iterations (ready check still runs) |
| Loop runs 25+ times | Stops at iteration 25 | Default limit enforced |
| Limit reached | Output includes "Iteration Limit Reached" | Status in final summary |

## Edge Cases

- [x] Zero iterations (`-n 0`) - Ready check runs, then loop stops before executing any tasks
- [x] Invalid input (non-numeric) - AI parsing falls back to default of 25 (no explicit validation)
- [x] Very large limit - No artificial cap, uses user-specified value

## Implementation Notes

These specs will be translated to language-specific tests during /cook RED phase.

Reference the tracer strategy to determine:
1. What minimal test proves the layer works?
2. What would be the simplest way to verify success?
3. What's the first thing that could go wrong?
