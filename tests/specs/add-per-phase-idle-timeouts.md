# Test Specification: Add per-phase idle timeouts and tune phase timeouts

## Tracer
Proves phases are monitored with appropriate sensitivity

## Context
- Add DEFAULT_PHASE_IDLE_TIMEOUTS dict to config.py
- Look up phase-specific idle timeout in run_phase()
- Reduce serve/plate/close-service timeouts
- Deliverable: Per-phase idle timeouts, tuned phase timeouts

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| run_phase("cook") no explicit idle | idle_timeout=180 | Cook default |
| run_phase("serve") no explicit idle | idle_timeout=300 | Serve default |
| run_phase("tidy") no explicit idle | idle_timeout=90 | Tidy default |
| run_phase("cook", idle_timeout=60) | idle_timeout=60 | Explicit override |
| DEFAULT_PHASE_TIMEOUTS["serve"] | 450 | Reduced from 600 |
| DEFAULT_PHASE_TIMEOUTS["plate"] | 450 | Reduced from 600 |
| DEFAULT_PHASE_TIMEOUTS["close-service"] | 750 | Reduced from 900 |

## Edge Cases
- [ ] Unknown phase name (fallback to default idle timeout)
- [ ] idle_timeout=0 (should it disable idle detection?)
- [ ] Phase not in DEFAULT_PHASE_IDLE_TIMEOUTS dict

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Update existing TestDefaultPhaseTimeouts assertions for new values.
