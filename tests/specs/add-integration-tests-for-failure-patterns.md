# Test Specification: Add integration tests for failure patterns

## Tracer
Proves correctness across combined failure scenarios

## Context
- TestCircuitBreakerPatterns: intermittent, burst, recovery
- TestDetectWorkedTaskWithTarget: multi-task change, target absent/present
- Verify circuit breaker + skip list interaction
- Deliverable: New test classes covering failure edge cases

## Test Cases

| Test Class | Scenario | Expected |
|------------|----------|----------|
| TestCircuitBreakerPatterns | Intermittent [S,F,S,F,...] | Trips at threshold |
| TestCircuitBreakerPatterns | Burst [F,F,F,F,F,S,S,S,S,S] | Trips (5 failures) |
| TestCircuitBreakerPatterns | Recovery after trip | Resets on success |
| TestDetectWorkedTaskWithTarget | Multi-task change, target present | Returns target |
| TestDetectWorkedTaskWithTarget | Multi-task change, target absent | Returns heuristic |
| TestDetectWorkedTaskWithTarget | Single task, matches target | Returns target |
| Combined | Breaker + skip list | Skip list entries not re-attempted |

## Edge Cases
- [ ] Circuit breaker recovery: add success after trip, verify reset
- [ ] Skip list with target_task_id: target in skip list
- [ ] Empty changed set with target_task_id set

## Implementation Notes
These specs will be translated to new unittest test classes in tests/test_line_loop.py during /cook.
