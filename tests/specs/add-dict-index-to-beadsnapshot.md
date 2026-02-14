# Test Specification: Add dict index to BeadSnapshot.get_by_id()

## Tracer
Foundation for all performance work — O(1) lookups enable efficient caching

## Context
- Add _index field (Optional[dict]) to BeadSnapshot dataclass
- Lazy build on first access via _build_index()
- Replace linear scan with dict lookup
- Deliverable: O(1) get_by_id() with lazy index, existing tests pass

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| get_by_id("lc-abc") on snapshot with "lc-abc" | Returns matching BeadInfo | Basic lookup |
| get_by_id("nonexistent") | Returns None | Missing ID |
| get_by_id() called twice | Same result, index built once | Lazy initialization |
| Snapshot with 0 beads, get_by_id("any") | Returns None | Empty snapshot |
| repr(snapshot) | Does not include _index | Excluded from repr |

## Edge Cases
- [ ] Index not included in equality comparisons
- [ ] Index rebuilt if beads list changes (or immutable assumption)
- [ ] Thread safety of lazy initialization (not needed for single-threaded loop)

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Modify existing TestBeadSnapshot class and add index-specific tests.
