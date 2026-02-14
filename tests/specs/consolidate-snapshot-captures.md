# Test Specification: Consolidate snapshot captures

## Tracer
Proves iteration works with minimal snapshots — largest subprocess reduction

## Context
- Remove redundant intermediate snapshots in run_iteration()
- Take before snapshot once, after once post-tidy
- Reuse after snapshot for completion cascade
- Deliverable: ~15 subprocess calls per iteration (down from ~30)

## Test Cases

| Scenario | Expected | Notes |
|----------|----------|-------|
| Normal iteration | 2 snapshot captures total | Before cook + after tidy |
| Iteration with timeout | Snapshot count unchanged | Timeout doesn't add extra |
| Completion cascade | Uses post-tidy snapshot | No additional bd show calls |
| get_task_info() during cascade | Cached result reused | Dict cache hit |
| Status/summary in loop.py | Uses iteration counts | No separate snapshot |

## Edge Cases
- [ ] Cook timeout path still works correctly
- [ ] Cascade with multiple completions
- [ ] get_task_info cache miss (new task during cascade)
- [ ] Snapshot reuse across iteration boundary (should NOT reuse)

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Tests will need mocked subprocess calls to count invocations.
