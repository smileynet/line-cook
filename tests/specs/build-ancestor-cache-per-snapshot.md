# Test Specification: Build ancestor cache per snapshot

## Tracer
Proves hierarchy walks can be done once per snapshot — eliminates repeated parent lookups

## Context
- Add build_epic_ancestor_map(snapshot, cwd) -> dict[str, Optional[str]]
- Walk every ready_work item's parent chain once
- Deliverable: Ancestor cache function, integrated into loop.py

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Task under feature under epic | {task_id: epic_id} | Full hierarchy |
| Task under feature (no epic) | {task_id: None} | No epic ancestor |
| Task directly under epic | {task_id: epic_id} | Skip feature level |
| Multiple tasks under same epic | All map to same epic_id | Shared ancestor |
| Standalone task (no parent) | {task_id: None} | Orphan task |

## Edge Cases
- [ ] Circular parent references (should not happen, but guard)
- [ ] Bead in snapshot but parent not in snapshot (needs subprocess fallback)
- [ ] Empty ready_work list
- [ ] All beads are epics (nothing to map)

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
Create new TestBuildEpicAncestorMap test class.
