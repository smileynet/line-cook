# Test Specification: Extract agent prompt to core/templates/

## Bead
lc-769.2.1

## Tracer
Template layer — proves prompt can be separated from workflow and synced

## Context
- Move prompt to core/templates/agents/issue-agent.md.template
- Integrate with existing sync infrastructure
- Deliverable: Agent prompt in template system

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Sync script execution | Template appears in all plugin dirs | Sync works |
| Template with @IF_CLAUDECODE@ | CC-specific output | Platform conditionals |
| Template without project-specific refs | Generic enough for any repo | Portability |
| Pre-commit hook | Detects out-of-sync templates | Drift prevention |

## Validation Checklist
- [ ] Template created at core/templates/agents/issue-agent.md.template
- [ ] Platform conditionals added where needed
- [ ] Sync script generates output in all 3 plugin dirs
- [ ] Pre-commit hook validates sync state
- [ ] Prompt is generic (no line-cook-specific references)
- [ ] Prompt relies on CLAUDE.md for project context

## Implementation Notes
Follow the pattern from core/templates/agents/sous-chef.md.template.
