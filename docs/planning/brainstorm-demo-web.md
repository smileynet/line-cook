# Brainstorm: Demo Web Template for Line Cook

> Exploration document from `/line:brainstorm` phase.

**Created:** 2026-02-04
**Status:** Ready for Planning

---

## Problem Statement

### What pain point are we solving?
The existing demo template (demo-simple) is a minimal TodoWebApp with only 2 tasks. It exercises basic bead operations but doesn't test Line Cook's full capabilities: complex dependency graphs, cross-feature dependencies, multi-iteration loops, feature plate validation, or epic completion across multiple features.

### Who experiences this pain?
- **Line Cook users** testing the loop workflow with realistic multi-feature projects
- **Line Cook developers** validating that loop, plate, and epic completion work across complex dependency graphs
- **New users** who want to see a non-trivial project built incrementally via Line Cook

### What happens if we don't solve it?
- Users only test with trivial 2-task demos that don't exercise real-world complexity
- Loop/plate/epic completion bugs may go undetected in simple scenarios
- No demonstration of cross-feature dependency resolution

---

## User Perspective

### Primary User
Line Cook users and developers testing the full workflow with a realistic project.

### User Context
- Familiar with Line Cook basics (have used demo-simple)
- Want to validate the full loop cycle with 8+ tasks
- Need a project domain that produces visible, testable output at each iteration

### Success Criteria (User's View)
- Run loop and see 9 tasks complete in dependency order
- Each iteration produces a working increment (compilable, testable Go code)
- Features complete and trigger plate validation
- Epic closes when all features are done
- Dashboard is a real, functional web application at the end

---

## Technical Exploration

### Existing Patterns in Codebase

| Pattern | Location | Relevance |
|---------|----------|-----------|
| Go + Templ + SQLite architecture | ~/code/observability | Reference app with same stack |
| WebSocket broadcast hub | ~/code/observability/internal/ws/ | Pattern for live updates |
| Templ HTML templating | ~/code/observability/internal/web/templates/ | Component patterns |
| HTMX interactivity | ~/code/observability | CDN-based, no build step |
| Demo template structure | templates/demo-simple/ | JSONL + CLAUDE.md + README format |

### External Approaches Researched
N/A - Using established patterns from the observability reference app.

### Constraints from Architecture
- Beads JSONL format with parent/depends_on fields
- Demo prefix convention (demo-NNN)
- Template must be self-contained (CLAUDE.md + issues.jsonl + README.md)
- Dependencies added via `bd dep add` after import

---

## Technical Approaches Considered

### Option A: Node.js Dashboard
**Description:** Express + React dashboard for monitoring

**Pros:**
- Familiar to many developers
- Large ecosystem

**Cons:**
- Build step required (React)
- Heavier dependency footprint
- No reference app to model from

**Effort:** Medium

### Option B: Go + Templ + SQLite Dashboard (Recommended)
**Description:** Go web dashboard matching ~/code/observability architecture

**Pros:**
- Reference implementation exists (~/code/observability)
- No build step (Templ compiles to Go, Tailwind/HTMX via CDN)
- SQLite for zero-config persistence
- Standard library HTTP (no framework dependencies)
- Each task produces testable Go code

**Cons:**
- Requires Go 1.25+ and templ CLI
- Smaller ecosystem than Node.js

**Effort:** Medium

### Option C: Static HTML Dashboard
**Description:** Pure HTML/CSS/JS dashboard with fetch API

**Pros:**
- No backend needed
- Zero dependencies

**Cons:**
- No persistence layer to demonstrate database patterns
- Limited architectural depth (few layers to slice through)
- Doesn't exercise Go testing patterns

**Effort:** Low

---

## Risks and Unknowns

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tasks too large for single cook cycle | Medium | Medium | Keep task scope narrow, reference specific files |
| Templ CLI not installed | Low | Low | Document in prerequisites |
| SQLite CGO dependency issues | Low | Medium | Use modernc.org/sqlite (pure Go) |

### Dependency Risks
- Requires Go 1.25+ and templ CLI installed
- Reference app (~/code/observability) should be available for Claude to reference

### Scope Risks
- 9 tasks is the sweet spot: enough to test complex dependencies without being overwhelming
- Each task must be completable in a single cook cycle

### Open Questions
All questions resolved:
- [x] Stack: Go + Templ + SQLite (user confirmed)
- [x] Data sources: Both loop files and hook events (user confirmed)
- [x] Approach: Build from scratch via beads (user confirmed)

---

## Recommended Direction

### Chosen Approach
**Option B: Go + Templ + SQLite Dashboard** modeled on ~/code/observability, with 9 tasks across 4 features, plus a parking lot item.

### Rationale
- Matches existing reference app architecture for reliable Claude Code execution
- Each task produces a testable vertical slice through the application
- Dependencies enforce a natural build order (server → database → pages → API → realtime)
- 9 tasks exercise complex dependency resolution including cross-feature blocking

### Suggested Scope
| Scope | Recommendation |
|-------|----------------|
| MVP | 9 tasks across 4 features under 1 epic |
| Full Feature | Add parking lot with metrics charts task |
| Epic | Not applicable - this is a demo template |

### Deferred Items
- Metrics charts and performance graphs (parking lot)
- Authentication
- Multi-project support
- Deployment configuration

---

## Next Steps

- [x] Resolve open questions (all resolved)
- [x] Proceed to `/line:scope` to create structured breakdown
- [x] Create the demo template files
