# Architecture Audit Report: Line Cook

**Date:** 2026-02-05
**Auditor:** Claude (automated analysis)
**Scope:** Full codebase

## Executive Summary

| Category | Status | Critical | High | Medium | Low |
|----------|--------|----------|------|--------|-----|
| Structural | OK | 0 | 0 | 0 | 0 |
| Complexity | WARN | 0 | 2 | 1 | 0 |
| Code Smells | WARN | 0 | 1 | 3 | 2 |
| Documentation | WARN | 0 | 0 | 3 | 2 |
| Platform Parity | OK | 0 | 0 | 3 | 0 |

**Overall Assessment:** The codebase is well-organized with clear module boundaries and good separation of concerns. The main areas for improvement are:
1. Two large files in `scripts/line_loop/` that could benefit from further decomposition
2. One command file (`loop.md`) that has grown into a large specification
3. Minor documentation link issues

No critical or blocking issues found. The project follows its own conventions consistently.

---

## Structural Analysis

### Module Organization

```
line-cook/
├── agents/              # 4 agents (taster, sous-chef, maitre, critic)
├── commands/           # 15 commands (Claude Code plugin)
├── docs/               # Documentation (guidance, decisions, templates)
├── scripts/            # Utility scripts + line_loop package
│   └── line_loop/      # Modular autonomous loop implementation
├── line-cook-opencode/ # OpenCode plugin port (11 commands)
├── line-cook-kiro/     # Kiro plugin port (agents + steering)
└── tests/              # Test suite
```

**Findings:**
- Clear separation between Claude Code (root), OpenCode, and Kiro platforms
- `scripts/line_loop/` is well-decomposed into focused modules
- Documentation follows consistent structure (guidance/, decisions/, templates/)
- No circular dependencies detected

### Platform Isolation

| Platform | Commands | Agents | Notes |
|----------|----------|--------|-------|
| Claude Code | 15 | 4 | Primary implementation |
| OpenCode | 11 | 0 | Command parity achieved, agents pending |
| Kiro | 1 (steering) | 5 | Agent-based architecture (by design) |

**Missing Parity:**
- Claude Code missing `service` command (deprecated per ADR)
- OpenCode missing `work` command (OpenCode-specific, per ADR)
- OpenCode has no agents (known gap - SDK supports them)

### Dependency Analysis (line_loop)

Import graph shows proper layering:

```
config.py (constants, no deps)
    ↓
models.py (dataclasses, imports config)
    ↓
parsing.py (parsing functions, imports config/models)
    ↓
phase.py (phase execution, imports config/models/parsing)
    ↓
iteration.py (iteration logic, imports all above)
    ↓
loop.py (orchestration, imports all above)
    ↓
__init__.py (re-exports)
```

No circular dependencies. Clean layered architecture.

---

## Quality Metrics

### Lines of Code by Component

| Component | LOC | Assessment |
|-----------|-----|------------|
| Commands (total) | 5,826 | Within norms |
| `commands/loop.md` | 1,766 | **HIGH** - exceeds 300 LOC threshold |
| `scripts/line_loop/` (total) | 3,752 | Reasonable for complexity |
| `scripts/line_loop/iteration.py` | 1,308 | **HIGH** - exceeds 500 LOC |
| `scripts/line_loop/loop.py` | 947 | **MEDIUM** - near threshold |
| Utility scripts | 3,116 | Normal |
| Agents | 558 | Compact, focused |

### Function Counts

| File | Functions | Avg LOC/Function |
|------|-----------|------------------|
| `iteration.py` | 28 | ~47 |
| `loop.py` | 16 | ~59 |
| `parsing.py` | 8 | ~46 |
| `phase.py` | 5 | ~63 |
| `models.py` | 13 | ~45 |

**Analysis:**
- Functions are reasonably sized (most under 50 LOC)
- No single function appears to exceed 100 LOC
- Module boundaries are appropriate for function grouping

### Test Coverage

Test file exists: `tests/test_line_loop.py` (1,026 LOC)

Coverage not measured (no coverage tool available), but test structure indicates:
- Unit tests for parsing functions
- Integration tests for phase execution
- Snapshot testing available

---

## Code Smells Detected

### HIGH Priority

#### 1. Large File: `commands/loop.md` (1,766 LOC)

**Smell:** Command God Object
**Location:** `commands/loop.md`
**Issue:** This command file has grown into a comprehensive specification document combining:
- User-facing documentation
- Technical implementation details
- Signal definitions
- State machine descriptions

**Recommendation:** Consider splitting into:
- `commands/loop.md` - User-facing command documentation (~300 LOC)
- `docs/guidance/loop-implementation.md` - Technical specification
- Or accept as intentional comprehensive spec (document decision)

**Effort:** Medium (refactoring, link updates)

#### 2. Large Module: `scripts/line_loop/iteration.py` (1,308 LOC)

**Smell:** Large Class/Module
**Location:** `scripts/line_loop/iteration.py`
**Issue:** This module contains 28 functions covering multiple concerns:
- Iteration execution (`run_iteration`)
- Bead state queries (`get_bead_snapshot`, `get_task_info`, `get_children`)
- Completion checking (`check_task_completed`, `check_feature_completion`, `check_epic_completion`)
- Display formatting (`print_phase_progress`, `print_human_iteration`)
- Epic reporting (`generate_epic_closure_report`, `print_epic_completion`)

**Recommendation:** Consider extracting into sub-modules:
- `iteration/core.py` - Main `run_iteration` logic
- `iteration/bead_queries.py` - Bead state functions
- `iteration/completion.py` - Completion check functions
- `iteration/display.py` - Human-readable output formatting

**Effort:** Medium-High (careful refactoring needed)

### MEDIUM Priority

#### 3. Near-Threshold Module: `scripts/line_loop/loop.py` (947 LOC)

**Smell:** Approaching Large Module
**Location:** `scripts/line_loop/loop.py`
**Issue:** At 947 LOC, this module is approaching the 1000 LOC warning threshold.

**Recommendation:** Monitor for growth. If expanding, consider extracting:
- Status file writing functions
- Escalation report generation
- History management

**Effort:** Low (proactive monitoring)

#### 4. Similar Patterns in Platform Ports

**Smell:** Potential Duplicate Code
**Location:** `commands/*.md` vs `line-cook-opencode/commands/*.md`
**Issue:** Commands are copied between platforms with minor adaptations.

**Current Mitigation:** ADR 0003 documents template-syncing approach.
**Recommendation:** This is acknowledged technical debt per ADR 0003. Consider automated sync tooling if drift becomes problematic.

**Effort:** Low (tracking only)

#### 5. Template Placeholders in Epic Template

**Smell:** Incomplete Abstraction
**Location:** `docs/templates/epic-acceptance.md`
**Issue:** Contains placeholder links (`xxx.1-acceptance.md`, `xxx.2-acceptance.md`) that trigger broken link warnings.

**Recommendation:** Either:
- Mark as template comments (not links)
- Use a different placeholder syntax that doesn't parse as links

**Effort:** Low (template update)

### LOW Priority

#### 6. Long Parameter Lists

**Smell:** Long Parameter List
**Location:** `scripts/line_loop/iteration.py:run_iteration()`, `scripts/line_loop/loop.py:run_loop()`
**Issue:** These orchestration functions accept many parameters for configurability.

**Current State:** Parameters are documented and have sensible defaults.
**Recommendation:** Consider Parameter Object pattern if parameters grow further.

**Effort:** Low (future consideration)

#### 7. ADR Date Format Missing

**Smell:** Inconsistent Documentation
**Location:** `docs/decisions/0*.md`
**Issue:** ADRs don't include date headers in a parseable format.

**Recommendation:** Add `Date:` line to ADR template for traceability.

**Effort:** Low (template update)

---

## Documentation Analysis

### Automated Check Results

From `doctor-docs.py`:

| Check | Status | Issues |
|-------|--------|--------|
| Internal Links | WARN | 3 broken links |
| Command Frontmatter | OK | All 15 commands valid |
| Agent Frontmatter | OK | All 4 agents valid |
| Changelog Format | OK | Keep a Changelog compliant |
| Required Sections | WARN | README missing some expected sections |
| Entity Existence | OK | All referenced entities exist |

### Broken Links

1. `docs/templates/epic-acceptance.md` → `../features/xxx.1-acceptance.md` (placeholder)
2. `docs/templates/epic-acceptance.md` → `../features/xxx.2-acceptance.md` (placeholder)
3. `docs/guidance/architecture-audit.md` → `../commands/audit.md` (fixed during audit)

### ADR Currency

| ADR | Topic | Status |
|-----|-------|--------|
| 0001 | Beads for issue tracking | Active |
| 0002 | Kitchen metaphor | Active |
| 0003 | Template-synced multi-platform | Active |
| 0004 | Commands vs skills convention | Active |
| 0005 | Three-tier hierarchy | Active |
| 0006 | Phase-specialized agents | Active |
| 0007 | Fresh-context review | Active |
| 0008 | Three-phase mise | Active |
| 0009 | Autonomous loop external | Active |
| 0010 | Epic-level testing | Active |

**Finding:** All 10 ADRs appear current. None marked superseded.

---

## Platform Parity Report

From `check-platform-parity.py`:

### Warnings (Non-blocking)

1. **Claude Code missing `service` command** - Intentional (deprecated in favor of `/line:run`)
2. **OpenCode missing `work` command** - OpenCode-specific orchestration
3. **OpenCode has no agents** - Known gap; SDK supports agents but not yet implemented

### Command Coverage

| Command | Claude Code | OpenCode | Kiro |
|---------|-------------|----------|------|
| getting-started | ✓ | ✓ | ✓ (steering) |
| mise | ✓ | ✓ | - |
| brainstorm | ✓ | ✓ | - |
| scope | ✓ | ✓ | - |
| finalize | ✓ | ✓ | - |
| prep | ✓ | ✓ | - |
| cook | ✓ | ✓ | - |
| serve | ✓ | ✓ | - |
| tidy | ✓ | ✓ | - |
| plate | ✓ | ✓ | - |
| run | ✓ | ✓ | - |
| audit | ✓ | - | - |
| decision | ✓ | - | - |
| loop | ✓ | - | - |
| help | ✓ | - | - |

**Note:** Kiro uses agent-based architecture (line-cook + kitchen-manager agents) rather than individual commands.

---

## Refactoring Recommendations

| # | Issue | Smell | Technique | Priority | Effort |
|---|-------|-------|-----------|----------|--------|
| 1 | `commands/loop.md` 1,766 LOC | Command God Object | Extract Specification | P2 | Medium |
| 2 | `iteration.py` 1,308 LOC | Large Module | Extract Sub-modules | P2 | Medium-High |
| 3 | Template placeholder links | Incomplete Abstraction | Update Template | P3 | Low |
| 4 | ADR missing dates | Inconsistent Docs | Update Template | P4 | Low |
| 5 | OpenCode agent gap | Missing Feature | Implement Agents | P3 | High |

---

## Action Items

### Immediate (P2)

1. **Consider decomposing `loop.md`**
   - Evaluate whether specification should live in guidance/ vs commands/
   - If keeping as-is, document rationale in ADR

2. **Track `iteration.py` complexity**
   - Mark for refactoring if adding significant new functionality
   - Consider extracting display/reporting functions first (lowest risk)

### Short-term (P3)

3. **Fix template placeholder links**
   - Update `docs/templates/epic-acceptance.md` to use comments instead of placeholder links

4. **Evaluate OpenCode agent implementation**
   - Determine if agents are needed for OpenCode parity
   - File as feature request if desired

### Tracking (P4)

5. **Add dates to ADR template**
   - Update `docs/decisions/README.md` with date field recommendation

6. **Monitor `loop.py` growth**
   - Flag for attention if exceeds 1,000 LOC

---

## Appendix: Raw Metrics

### File Size Distribution

```
>1000 LOC:
  commands/loop.md        1,766
  iteration.py            1,308
  test_line_loop.py       1,026

500-1000 LOC:
  loop.py                   947
  validate-smoke-test.py    738
  release.py                660
  models.py                 587
  audit.md                  577

300-500 LOC:
  doctor-docs.py            534
  check-plugin-health.py    472
  taster.md (kiro)          437
  check-platform-parity.py  408
  plate.md                  396
  cook.md                   376
  tidy.md                   374
  parsing.py                365
```

### Validation Script Results

**check-plugin-health.py:** PASS (0 errors, 0 warnings)
**check-platform-parity.py:** PASS (0 errors, 3 warnings)
**doctor-docs.py:** WARN (3 errors - broken links, 2 warnings)
