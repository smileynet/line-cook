# Brainstorm: Demo Template for Line Cook

> Exploration document from `/line:brainstorm` phase.

**Created:** 2026-02-01
**Status:** Ready for Planning

---

## Problem Statement

### What pain point are we solving?
New users and tool tests need a realistic pre-staged environment to explore Line Cook functionality without first creating their own work structure. Currently, users must either:
1. Create beads from scratch (high friction for learning)
2. Use minimal test fixtures that don't demonstrate the full workflow

### Who experiences this pain?
- **New users** learning Line Cook workflow
- **Tool tests** that need deterministic starting conditions
- **Demo/documentation authors** who want to show realistic examples

### What happens if we don't solve it?
- Higher onboarding friction for new users
- Tests may not cover realistic scenarios
- Documentation examples feel abstract rather than practical

---

## User Perspective

### Primary User
Developers learning Line Cook who want to immediately try commands like `/line:prep`, `/line:cook`, `bd ready`, etc.

### User Context
- Familiar with git and CLI tools
- May not understand beads hierarchy (epic → feature → task) yet
- Want to see how the system behaves before committing to using it

### Success Criteria (User's View)
- Run `/line:prep` and see meaningful ready tasks
- Run `bd show <id>` and see rich context with acceptance criteria
- Observe how dependencies block tasks
- Understand the parking lot pattern for deferred work
- Complete a task and see the workflow in action

---

## Technical Exploration

### Existing Patterns in Codebase

| Pattern | Location | Relevance |
|---------|----------|-----------|
| Test fixtures with status distribution | `tests/fixtures/mock-beads/issues.jsonl` | Shows JSONL format and field structure |
| Parking lot pattern | `tc-retro`, `tc-005` in `issues.jsonl` | Demonstrates epic filtering |
| Dependency blocking | `tc-003` in `issues.jsonl` | Shows `depends_on` field usage |
| Config structure | `bd init --prefix=demo` | Minimal required configuration |

### External Approaches Researched
N/A - This is an internal tooling concern, not a general software pattern.

### Constraints from Architecture
- Beads uses JSONL format in `.beads/issues.jsonl`
- Config requires `prefix` and `version` fields
- Parent-child relationships use `parent` field
- Dependencies use `depends_on` array
- Types: `epic`, `feature`, `task`, `bug`
- Statuses: `open`, `in_progress`, `closed`
- Priority: 0-4 (0=critical, 4=backlog)

---

## Technical Approaches Considered

### Option A: Minimal Demo (3 beads)
**Description:** One epic with 2-3 tasks, one blocked

**Pros:**
- Simple to understand
- Fewer files to maintain
- Quick to set up

**Cons:**
- Doesn't show feature hierarchy
- Limited dependency demonstration
- May feel too minimal

**Effort:** Low

### Option B: Full Hierarchy Demo (6-8 beads)
**Description:** Epic → Feature → Tasks structure with parking lot

**Pros:**
- Demonstrates complete workflow
- Shows hierarchy pattern
- Realistic representation

**Cons:**
- More complex
- More files to maintain
- May overwhelm new users

**Effort:** Medium

### Option C: TodoWebApp Theme (Recommended)
**Description:** 4-5 beads using familiar TodoWebApp domain with clear hierarchy

**Pros:**
- Familiar domain (CRUD operations)
- Demonstrates epic → feature → task pattern
- Shows dependency blocking naturally
- Includes parking lot pattern
- Balanced complexity

**Cons:**
- Slightly more than minimal

**Effort:** Low-Medium

---

## Risks and Unknowns

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JSONL format changes | Low | Medium | Use existing fixture format as reference |
| Prefix collision | Low | Low | Use unique prefix like `demo` |

### Dependency Risks
None - self-contained demo files

### Scope Risks
- Feature creep: Adding too many beads defeats the "simple demo" purpose
- Keeping it updated if beads format evolves

### Open Questions
All questions resolved:
- [x] Domain: TodoWebApp (user confirmed)
- [x] Include history: No, start fresh (user confirmed)
- [x] Location: `templates/demo/` (user confirmed)

---

## Recommended Direction

### Chosen Approach
**Option C: TodoWebApp themed demo** with 4-5 beads demonstrating:
1. Epic (TodoWebApp MVP)
2. Feature (User can manage todos)
3. Ready task (Add todo item functionality)
4. Blocked task (depends on #3)
5. Parking lot epic + deferred task

### Rationale
- TodoWebApp is universally familiar
- 4-5 beads is enough to show all patterns without overwhelming
- Natural fit for dependency demonstration (add before edit)
- Includes parking lot pattern for completeness

### Suggested Scope
| Scope | Recommendation |
|-------|----------------|
| MVP | 4 beads: 1 epic, 1 feature, 2 tasks (1 ready, 1 blocked) |
| Full Feature | 5 beads: Add parking lot epic with 1 deferred task |
| Epic | Not applicable - this is a simple template |

### Deferred Items
- Multiple features under epic (keep it simple)
- Bug examples (not needed for core workflow demo)
- Pre-existing comments/activity log (start fresh per user preference)

---

## Proposed Demo Structure

```
templates/demo/
├── issues.jsonl          # All demo beads (JSONL format, imported via bd import)
├── CLAUDE.md             # Project context
└── README.md             # Setup and usage instructions
```

### Ready Work Output
When user runs `bd ready`:
- `demo-001.1.1` - Add todo item functionality (only ready task)

When user runs `bd blocked`:
- `demo-001.1.2` - Mark todo complete (blocked by demo-001.1.1)

### Demonstrable Workflows
1. `bd ready` → shows demo-001.1.1
2. `bd show demo-001.1.1` → shows full context
3. `bd show demo-001.1.2` → shows blocked status
4. `/line:prep` → identifies demo-001.1.1 as next work
5. `/line:cook demo-001.1.1` → execute the task
6. After closing demo-001.1.1, demo-001.1.2 becomes ready

---

## Next Steps

- [x] Resolve open questions (all resolved)
- [ ] Proceed to `/line:scope` to create structured breakdown
- [ ] Create the demo template files

---
