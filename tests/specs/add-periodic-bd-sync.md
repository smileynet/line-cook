# Test Specification: Add periodic bd sync every N iterations

## Tracer
Proves loop stays fresh during long runs — simplest resilience improvement

## Context
- Add PERIODIC_SYNC_INTERVAL = 5 to config.py
- Check iteration % interval == 0 in main loop
- Run bd sync with GIT_SYNC_TIMEOUT
- Deliverable: Periodic sync with configurable interval

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Iteration 5 | bd sync called | First sync point |
| Iteration 6 | bd sync NOT called | Not at interval |
| Iteration 10 | bd sync called | Second sync point |
| Iteration 0 | bd sync called (or skipped) | Edge: first iteration |
| PERIODIC_SYNC_INTERVAL = 1 | Sync every iteration | Min interval |

## Edge Cases
- [ ] Sync failure (should log and continue, not crash loop)
- [ ] Sync timeout (respects GIT_SYNC_TIMEOUT)
- [ ] PERIODIC_SYNC_INTERVAL = 0 (disable sync? or default to 5?)

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Tests will mock run_subprocess to verify sync calls at correct intervals.
