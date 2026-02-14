# Test Specification: Fix circuit breaker window logic

## Tracer
Proves breaker correctly evaluates full window — foundation for all failure handling

## Context
- Change `self.window[-self.failure_threshold:]` to `self.window` in is_open()
- Bug: currently checks only last 5 items, not full 10-item window
- Deliverable: Fixed CircuitBreaker.is_open() with new test cases

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Window [F,F,F,F,F,S,F,F,F,F] (9/10 failures) | is_open() = True | Bug case: currently returns False |
| Window [F,F,F,F,F,S,S,S,S,S] (5/10 failures) | is_open() = True | Boundary: exactly at threshold |
| Window [F,F,F,F,S,S,S,S,S,S] (4/10 failures) | is_open() = False | Below threshold |
| Window [S,S,S,S,S,S,S,S,S,S] (0/10 failures) | is_open() = False | No failures |
| Window [F,F,F,F,F,F,F,F,F,F] (10/10 failures) | is_open() = True | All failures |

## Edge Cases
- [ ] Window not yet full (fewer than window_size entries)
- [ ] Window exactly at failure_threshold count
- [ ] Failures clustered at start vs end vs distributed

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Add new test cases to existing TestCircuitBreaker class.
