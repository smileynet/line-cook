# Test Specification: Fix detect_worked_task tiebreaker

## Tracer
Proves task attribution works when multiple tasks change — critical for retry logic

## Context
- Add optional target_task_id parameter to detect_worked_task()
- If target is in the changed set, prefer it over dot-count heuristic
- Deliverable: detect_worked_task with target preference, updated call sites, new tests

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Two tasks changed, target_task_id matches one | Returns target_task_id | Target preference over heuristic |
| Two tasks changed, target_task_id not in changed set | Returns heuristic winner | Falls back to dot-count |
| Two tasks changed, no target_task_id provided | Returns heuristic winner | Backward compatible |
| One task changed, target_task_id matches it | Returns target_task_id | Simple case |
| One task changed, target_task_id different | Returns the changed task | Only one candidate |

## Edge Cases
- [ ] target_task_id is None (backward compatibility)
- [ ] target_task_id is empty string
- [ ] Multiple tasks changed, target_task_id in set but has fewer dots
- [ ] No tasks changed at all (empty changed set)

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Add new test cases to TestDetectWorkedTask class and verify call sites in run_iteration().
