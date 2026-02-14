# Test Specification: Add integration tests for resilience features

## Tracer
Proves resilience features work together correctly

## Context
- TestPeriodicSync: verify sync at correct intervals
- TestPerPhaseIdleTimeout: verify phase-specific idle timeout lookup
- TestIdleDetection: test check_idle() with various time deltas
- Update TestDefaultPhaseTimeouts for new values
- Deliverable: Integration test classes for resilience features

## Test Cases

| Test Class | Scenario | Expected |
|------------|----------|----------|
| TestPeriodicSync | Iteration 5 | Sync called |
| TestPeriodicSync | Iteration 3 | Sync not called |
| TestPeriodicSync | Sync fails | Logged, loop continues |
| TestPerPhaseIdleTimeout | Cook phase | 180s idle timeout |
| TestPerPhaseIdleTimeout | Serve phase | 300s idle timeout |
| TestPerPhaseIdleTimeout | Override with explicit | Uses explicit value |
| TestIdleDetection | No output for 200s (cook) | Idle detected |
| TestIdleDetection | No output for 100s (cook) | Not idle |
| TestDefaultPhaseTimeouts | serve | 450s (was 600s) |
| TestDefaultPhaseTimeouts | plate | 450s (was 600s) |
| TestDefaultPhaseTimeouts | close-service | 750s (was 900s) |

## Edge Cases
- [ ] Periodic sync + idle timeout interaction
- [ ] Phase timeout vs idle timeout (idle is subset of phase timeout)
- [ ] check_idle() at exact boundary

## Implementation Notes
These specs will be translated to unittest test classes in tests/test_line_loop.py during /cook.
