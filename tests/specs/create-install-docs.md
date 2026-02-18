# Test Specification: Create installation workflow and documentation

## Bead
lc-769.2.2

## Tracer
Distribution layer — proves another repo can adopt the issue agent

## Context
- Create standalone workflow file for distribution
- Write setup instructions
- Deliverable: Installable workflow + documentation

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Fresh repo + copied workflow + secret | Agent responds to issues | End-to-end install |
| Setup instructions | Completeable in <5 minutes | Usability |
| Workflow without line-cook-specific refs | Works on any repo | Portability |
| Configuration docs | Cover --max-turns, --allowedTools, model | Customization |

## Validation Checklist
- [ ] Standalone workflow file created (no line-cook dependencies)
- [ ] Setup instructions: 1) copy workflow, 2) run claude setup-token, 3) add secret
- [ ] Tested on a fresh/test repository
- [ ] Configuration options documented
- [ ] Decision: spice vs workflow template documented

## Implementation Notes
Test on a real fresh repo to validate the install experience. Consider creating a minimal test repo for this purpose.
