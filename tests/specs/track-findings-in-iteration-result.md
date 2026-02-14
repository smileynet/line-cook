# Test Specification: Track findings in IterationResult

## Tracer
Proves finding metadata flows through the iteration pipeline

## Context
- Add findings_count: int = 0 to IterationResult
- Count delta.newly_filed items after tidy
- Show in human output, serialize in status/history
- Deliverable: Findings count in IterationResult, status output, and history

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| IterationResult(findings_count=3) | "Findings: 3 filed" in human output | Positive count shown |
| IterationResult(findings_count=0) | No findings line in human output | Zero suppressed |
| serialize_iteration_for_status() | {"findings_count": N} in JSON | Status includes count |
| serialize_full_iteration() | {"findings_count": N} in JSON | History includes count |
| Delta with 2 newly_filed items | findings_count=2 | Count derived from delta |

## Edge Cases
- [ ] Negative findings_count (should not happen, guard if needed)
- [ ] Very large findings_count (display formatting)
- [ ] findings_count in watch mode milestone display

## Implementation Notes
These specs will be translated to unittest test cases in tests/test_line_loop.py during /cook.
