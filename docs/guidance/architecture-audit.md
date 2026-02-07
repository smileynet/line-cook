# Architecture Audit

> Systematic evaluation of codebase structure, quality, and maintainability.

Architecture audits identify structural issues, code smells, and refactoring opportunities before they compound into technical debt. Run audits before major refactoring, at project milestones, during onboarding, or quarterly for health checks.

## Quick Reference

```
Architecture Audit (/line:architecture-audit)   Plan Audit (/line:plan-audit)
├── Coupling analysis              ├── Bead hierarchy checks
├── Complexity metrics             ├── Content quality
├── Code smell detection           ├── Work hygiene
└── Refactoring candidates         └── Acceptance criteria
```

| Category | Focus | Detection Method |
|----------|-------|------------------|
| **Bloaters** | Overly large code units | LOC counts, complexity metrics |
| **Couplers** | Excessive interdependence | Import analysis, method calls |
| **Change Preventers** | Rigid structures | Git history, modification patterns |
| **Dispensables** | Dead or redundant code | Coverage, duplicate detection |
| **CLI-Specific** | Plugin architecture issues | Platform isolation checks |

## When to Audit

| Trigger | Scope | Focus |
|---------|-------|-------|
| Before refactoring | Target modules | Smells, complexity |
| At milestones | Full codebase | All categories |
| Onboarding | Full codebase | Structure, documentation |
| Quarterly | Full codebase | Trend analysis |
| After incident | Affected areas | Root cause patterns |

## Methodology

### Phase 1: Structural Analysis

Map the codebase organization:

```bash
# Directory structure
tree -d -L 3

# Module sizes (LOC per directory)
find . -name "*.py" -o -name "*.ts" | xargs wc -l | sort -n

# Dependency mapping (Python)
pipdeptree --local-only

# Import relationships
grep -r "^import\|^from" --include="*.py" | cut -d: -f2 | sort | uniq -c | sort -rn
```

**Check for:**
- Clear module boundaries (each directory has single responsibility)
- Layered architecture (no upward dependencies)
- Platform isolation (platform-specific code in separate directories)

### Phase 2: Quality Metrics

Collect quantitative measurements:

| Metric | Good | Moderate | Refactor | Warning | Critical |
|--------|------|----------|----------|---------|----------|
| **Cyclomatic Complexity** | 1-4 | 5-7 | 8-10 | 10-15 | >15 |
| **Lines per Method** | <20 | 20-30 | 30-50 | 50-100 | >100 |
| **Lines per Class/Module** | <200 | 200-400 | 400-500 | 500-1000 | >1000 |
| **Parameters per Method** | 1-3 | 4 | 5-6 | 7-8 | >8 |
| **CBO (Coupling)** | <3 | 3-5 | 5-7 | 7-10 | >10 |
| **WMC (Weighted Methods)** | <30 | 30-50 | 50-80 | 80-120 | >120 |
| **Test Coverage (Line)** | >80% | 60-80% | 40-60% | 20-40% | <20% |
| **Duplicate Code** | <1% | 1-3% | 3-5% | 5-10% | >10% |

**Tools:**
- Python: `radon cc`, `radon mi`, `flake8`, `pylint`
- TypeScript: `eslint --ext .ts`, complexity rules
- General: `cloc`, `tokei` for LOC; `jscpd` for duplicates

### Phase 3: Code Smell Detection

Systematically check for each smell category.

#### Bloaters

Large code units that have grown unmanageable:

| Smell | Detection | Threshold | Impact |
|-------|-----------|-----------|--------|
| **Long Method** | LOC, complexity | >20 LOC or CC >10 | Hard to understand/test |
| **Large Class** | LOC, WMC | >500 LOC or WMC >80 | Too many responsibilities |
| **Primitive Obsession** | Type analysis | Strings for structured data | Scattered validation |
| **Long Parameter List** | Parameter count | >4 parameters | Complex interfaces |
| **Data Clumps** | Pattern matching | Same params in 3+ methods | Missing abstraction |

**Detection commands:**
```bash
# Long files (>500 LOC)
find . -name "*.py" -exec wc -l {} + | awk '$1 > 500' | sort -rn

# Long methods (Python)
radon cc -a -nc . | grep -E "^[A-Z]" | awk '$NF > 10'

# Parameter counts (grep for function definitions)
grep -rn "def.*(" --include="*.py" | grep -E ",.*,.*,.*,"
```

#### Couplers

Excessive dependencies between components:

| Smell | Detection | Indicator | Impact |
|-------|-----------|-----------|--------|
| **Feature Envy** | Method analysis | Method uses other class's data more than own | Misplaced responsibility |
| **Inappropriate Intimacy** | Access patterns | Classes accessing each other's internals | Fragile coupling |
| **Message Chains** | Call chains | `a.b().c().d()` patterns | Brittle dependencies |
| **Middle Man** | Delegation count | Class only delegates to another | Unnecessary indirection |

**Detection:**
```bash
# Import coupling (most imported modules)
grep -rh "^from\|^import" --include="*.py" | \
  sed 's/from \([^ ]*\).*/\1/; s/import \([^ ]*\).*/\1/' | \
  sort | uniq -c | sort -rn | head -20

# Message chains (long dot chains)
grep -rn "\.\w\+\.\w\+\.\w\+\.\w\+" --include="*.py"
```

#### Change Preventers

Structures that make changes difficult:

| Smell | Detection | Indicator | Impact |
|-------|-----------|-----------|--------|
| **Divergent Change** | Git history | One class changed for multiple reasons | Low cohesion |
| **Shotgun Surgery** | Git history | One change touches >3 files | High coupling |
| **Parallel Inheritance** | Class hierarchy | Matching subclass hierarchies | Redundant structure |

**Detection:**
```bash
# Files frequently modified together (shotgun surgery indicator)
git log --oneline --name-only | grep -v "^[a-f0-9]" | sort | uniq -c | sort -rn | head -20

# Files with high churn
git log --format='' --name-only | sort | uniq -c | sort -rn | head -20
```

#### Dispensables

Code that could be removed:

| Smell | Detection | Indicator | Impact |
|-------|-----------|-----------|--------|
| **Dead Code** | Coverage, usage | Unreachable or unused | Confusion, maintenance |
| **Duplicate Code** | Pattern matching | Similar blocks in 2+ places | Bug propagation |
| **Lazy Class** | Size analysis | Class does too little | Unnecessary complexity |
| **Speculative Generality** | Usage analysis | Unused abstractions | Over-engineering |

**Detection:**
```bash
# Dead imports
pylint --disable=all --enable=W0611 .

# Duplicate code (requires jscpd)
jscpd --reporters consoleFull --threshold 3 .

# Small files (potential lazy classes)
find . -name "*.py" -exec wc -l {} + | awk '$1 < 20 && $1 > 0' | sort -n
```

### Phase 4: CLI/Plugin-Specific Smells

Additional patterns for command-line tools and plugins:

| Smell | Detection | Threshold | Impact |
|-------|-----------|-----------|--------|
| **Command God Object** | Command file LOC | >300 LOC | Mixing parsing, logic, output |
| **Tight Platform Coupling** | Import analysis | Platform APIs in shared code | Portability issues |
| **Configuration Sprawl** | Config sources | Config in >3 locations | Inconsistent behavior |
| **Flag Proliferation** | Flag count | >10 flags per command | Complex interfaces |

**Detection:**
```bash
# Command file sizes
find commands/ -name "*.md" -exec wc -l {} + | sort -rn

# Platform coupling (check for platform-specific imports in shared code)
grep -rn "claude\|opencode\|kiro" --include="*.py" scripts/

# Flag proliferation (count flags in command definitions)
grep -c "\-\-" commands/*.md | awk -F: '$2 > 10'
```

### Phase 5: Refactoring Candidates

Prioritize findings by impact and effort:

| Priority | Criteria | Action |
|----------|----------|--------|
| **P0 (Critical)** | Circular dependencies, security issues, complexity >15 | Fix immediately |
| **P1 (High)** | Large classes, shotgun surgery, complexity 10-15 | Fix this sprint |
| **P2 (Medium)** | Feature envy, message chains, complexity 8-10 | Fix when nearby |
| **P3 (Low)** | Minor duplication, lazy classes | Track, fix opportunistically |

### Phase 6: Documentation Verification

Check documentation health:

```bash
# Run existing tools
./dev/doctor-docs.py

# Check ADR currency
ls -la docs/decisions/*.md | wc -l

# Find ADRs mentioning deprecated patterns
grep -l "deprecated\|superseded" docs/decisions/*.md
```

## Code Smells Catalog

### Bloaters

**Long Method** (>20 LOC, complexity >10)
- Symptom: Method does too many things
- Refactoring: Extract Method, Decompose Conditional

**Large Class** (>500 LOC, WMC >80)
- Symptom: Class has too many responsibilities
- Refactoring: Extract Class, Extract Subclass

**Primitive Obsession**
- Symptom: Using primitives instead of small objects (phone numbers as strings)
- Refactoring: Replace Primitive with Object, Introduce Parameter Object

**Long Parameter List** (>4 parameters)
- Symptom: Method requires too much context
- Refactoring: Introduce Parameter Object, Preserve Whole Object

**Data Clumps**
- Symptom: Same parameters appear together in multiple methods
- Refactoring: Extract Class, Introduce Parameter Object

### Couplers

**Feature Envy**
- Symptom: Method uses another class's data more than its own
- Refactoring: Move Method, Extract Method + Move

**Inappropriate Intimacy**
- Symptom: Classes know too much about each other's internals
- Refactoring: Move Method, Extract Class, Hide Delegate

**Message Chains** (>2 levels)
- Symptom: Long chains of method calls (`a.b().c().d()`)
- Refactoring: Hide Delegate, Extract Method

**Middle Man**
- Symptom: Class mostly delegates to another class
- Refactoring: Remove Middle Man, Inline Method

### Change Preventers

**Divergent Change**
- Symptom: Class changed for multiple unrelated reasons
- Refactoring: Extract Class (one per change reason)

**Shotgun Surgery** (>3 files for one change)
- Symptom: One change requires modifying many classes
- Refactoring: Move Method, Move Field, Inline Class

**Parallel Inheritance**
- Symptom: Creating subclass in one hierarchy requires subclass in another
- Refactoring: Move Method, Move Field to eliminate one hierarchy

### Dispensables

**Dead Code**
- Symptom: Code that is never executed
- Refactoring: Delete it

**Duplicate Code** (>3% of codebase)
- Symptom: Identical or similar code in multiple places
- Refactoring: Extract Method, Pull Up Method, Form Template Method

**Lazy Class**
- Symptom: Class that doesn't do enough to justify existence
- Refactoring: Inline Class, Collapse Hierarchy

**Speculative Generality**
- Symptom: Abstractions created for "future needs" that never materialize
- Refactoring: Collapse Hierarchy, Inline Class, Remove Parameter

### CLI/Plugin-Specific

**Command God Object** (>300 LOC per command)
- Symptom: Command file handles parsing, validation, logic, and formatting
- Refactoring: Extract handler classes, separate concerns

**Tight Platform Coupling**
- Symptom: Platform-specific code (Claude/OpenCode/Kiro) in shared modules
- Refactoring: Extract platform adapters, use dependency injection

**Configuration Sprawl**
- Symptom: Configuration in files, flags, env vars, and hardcoded values
- Refactoring: Consolidate into single configuration system

**Flag Proliferation** (>10 flags)
- Symptom: Command has too many options
- Refactoring: Split into subcommands, use configuration file

## Refactoring Techniques Reference

| Technique | Use When | Steps |
|-----------|----------|-------|
| **Extract Method** | Long method, duplicate code | 1. Identify code block 2. Create method 3. Replace with call |
| **Extract Class** | Large class, data clumps | 1. Identify responsibility 2. Create class 3. Move methods/fields |
| **Move Method** | Feature envy | 1. Identify target class 2. Copy method 3. Adjust references |
| **Introduce Parameter Object** | Long parameter list, data clumps | 1. Create class for params 2. Add to signature 3. Move params to object |
| **Replace Conditional with Polymorphism** | Complex conditionals | 1. Create class hierarchy 2. Move condition to overrides |
| **Hide Delegate** | Message chains | 1. Create wrapper method 2. Clients call wrapper |
| **Inline Class** | Lazy class | 1. Move all features to another class 2. Delete empty class |

## Quality Checklist

### Structure
- [ ] Directory structure reflects architecture
- [ ] Clear module boundaries (single responsibility)
- [ ] No circular dependencies
- [ ] Platform-specific code isolated
- [ ] Layered dependencies (no upward refs)

### Smells
- [ ] No files >500 LOC
- [ ] No methods >50 LOC
- [ ] No functions with >6 parameters
- [ ] No complexity >10 without justification
- [ ] <3% duplicate code

### Testing
- [ ] >60% line coverage (>80% preferred)
- [ ] Tests exist for public interfaces
- [ ] No flaky tests in CI

### Documentation
- [ ] ADRs current (no superseded without replacement)
- [ ] README up to date
- [ ] Internal links valid
- [ ] API documentation exists

## Audit Types Comparison

| Aspect | Architecture Audit (/line:architecture-audit) | Plan Audit (/line:plan-audit) |
|--------|-------------------|--------------------------|
| **Focus** | Code structure, quality | Work item content |
| **Checks** | Coupling, complexity, smells | Hierarchy, criteria, hygiene |
| **Targets** | Source files, modules | Beads (epics, features, tasks) |
| **When** | Before refactoring, quarterly | Before work sessions |
| **Output** | Refactoring candidates | Issue list with fixes |
| **Tools** | Static analyzers, LOC counters | bd commands, audit command |

## Output Format

Architecture audit reports should include:

```markdown
# Architecture Audit Report: [Project]
Date: YYYY-MM-DD

## Executive Summary
| Category | Status | Issues |
|----------|--------|--------|
| Structural | [OK/WARN/FAIL] | count |
| Complexity | [OK/WARN/FAIL] | count |
| Code Smells | [OK/WARN/FAIL] | count |
| Documentation | [OK/WARN/FAIL] | count |

## Structural Analysis
[Findings about module organization, dependencies, platform isolation]

## Quality Metrics
[Complexity scores, coverage, duplicate percentages]

## Code Smells Detected
### Critical
[List with file locations and recommended fixes]

### High
[...]

## Refactoring Recommendations
| Issue | Smell | Technique | Priority | Effort |
|-------|-------|-----------|----------|--------|

## Action Items
1. [Prioritized list]
```

## Running an Audit

```bash
# 1. Run automated validation
./dev/check-plugin-health.py
./dev/check-platform-parity.py
./dev/doctor-docs.py

# 2. Collect metrics
cloc .                           # LOC by language
radon cc -a . 2>/dev/null        # Complexity (Python)

# 3. Check for smells
find . -name "*.py" -exec wc -l {} + | awk '$1 > 500'  # Large files
jscpd --threshold 3 .            # Duplicates

# 4. Review git history
git log --format='' --name-only | sort | uniq -c | sort -rn | head -10  # Churn

# 5. Document findings
# Write to docs/features/architecture-audit-YYYY-MM-DD.md
```

## Related

- [Workflow](./workflow.md) - How audits fit in the development cycle
- [Epic-Level Testing](./epic-testing.md) - Quality validation at epic completion
- [TDD/BDD Workflow](./tdd-bdd.md) - Test-driven quality practices
- [Plan Audit](../../plugins/claude-code/commands/plan-audit.md) - Bead content quality checks
