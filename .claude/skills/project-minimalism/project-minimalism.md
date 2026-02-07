---
name: project-minimalism
description: Code minimalism, modularity patterns, and context hygiene. Use when designing new features, refactoring, reviewing code for bloat, or optimizing CLAUDE.md.
---

# Project Minimalism & Modularity

Guidelines for keeping codebases lean, modular, and maintainable—including Claude Code context hygiene.

## When to Use

- Designing new features (to avoid over-engineering)
- Refactoring existing code for clarity
- Reviewing code for bloat or unnecessary complexity
- Optimizing CLAUDE.md and project documentation
- Evaluating whether to add dependencies or abstractions

## Quick Reference

### Decision Table

| Situation | Prefer | Avoid |
|-----------|--------|-------|
| Three similar code blocks | Keep them separate | Premature abstraction |
| "Might need later" feature | Don't implement | Speculative code |
| Complex interface for flexibility | Simple interface for current need | Kitchen Sink pattern |
| Error handling for impossible cases | Trust internal code | Defensive overkill |
| Feature flag for migration | Direct code change | Backwards-compatibility hacks |
| Large CLAUDE.md with embedded content | Skills + progressive disclosure | Monolithic instructions |

### Core Principles (One-liners)

| Principle | Meaning |
|-----------|---------|
| YAGNI | Don't implement until you need it |
| KISS | Fewer integrated components is better |
| SRP | One reason to change per module |
| Rule of Three | Don't abstract until third occurrence |

## Topics

### Core Principles

<details><summary>YAGNI: You Ain't Gonna Need It</summary>

Implement features only when required, not when foreseen.

**Signs of violation:**
- Code paths never executed in production
- Configuration options no one uses
- "Future-proof" interfaces with one implementation

**Application:**
- Implement the simplest solution that works now
- Add complexity only when a second use case arrives
- Delete unused code rather than commenting it out

</details>

<details><summary>KISS: Keep It Simple</summary>

Fewer components, fewer integrations, fewer moving parts.

**Signs of violation:**
- Multiple abstraction layers for simple operations
- Dependency injection for everything
- Configuration that could be code

**Application:**
- Inline simple operations rather than extracting
- Use standard library before adding dependencies
- Question every new abstraction

</details>

<details><summary>Single Responsibility Principle</summary>

Each module/class/function has one reason to change.

**Signs of violation:**
- Module name includes "And" or "Manager"
- Changes to unrelated features require touching the same file
- Functions that take boolean flags to switch behavior

**Application:**
- Split modules when they serve multiple concerns
- Group related functions by what changes together
- Extract when a function does "one thing, then another thing"

</details>

### Modularity Patterns

<details><summary>Coupling and Cohesion</summary>

**High Cohesion (good):** Related functionality grouped together
- Functions that use the same data structures
- Code that changes for the same reasons
- Operations that form a logical workflow

**Low Coupling (good):** Minimal inter-module dependencies
- Modules communicate through well-defined interfaces
- Internal implementation details hidden
- Changes to one module don't cascade

**MIT 2025 Concept Model:**
- "Concepts" = single-purpose pieces that do one thing
- "Synchronizations" = how concepts fit together
- Design concepts independently, document synchronizations explicitly

</details>

<details><summary>Dependency Direction</summary>

Depend on abstractions, not implementations.

**Good:**
```
core/ → interfaces ← adapters/
```
Core logic defines interfaces. Adapters implement them.

**Bad:**
```
core/ → external-service
```
Core directly depends on external implementation.

</details>

### Context Hygiene (Claude Code)

<details><summary>Progressive Disclosure</summary>

Don't front-load all information—reveal details as needed.

**Levels:**
1. **Quick reference** - Most users stop here (decision tables, one-liners)
2. **Expanded sections** - When quick answer isn't enough
3. **Details blocks** - Deep examples for specific situations
4. **External references** - Full documentation elsewhere

**CLAUDE.md Application:**
- Tell Claude WHERE to find information, not THE information
- Use skills for domain-specific knowledge (loaded on-demand)
- Keep CLAUDE.md under ~150-200 instruction lines

</details>

<details><summary>Skills vs CLAUDE.md</summary>

| Use CLAUDE.md for | Use Skills for |
|-------------------|----------------|
| Always-needed context | Domain-specific knowledge |
| Project-wide conventions | Task-specific patterns |
| Critical safety rules | Reference documentation |
| Build/test commands | Detailed procedures |

**Key insight:** CLAUDE.md loads every session. Skills load on-demand.

</details>

<details><summary>Lazy Loading Pattern</summary>

Provide methodology for discovery rather than exhaustive lists.

**Instead of:** 50 anti-patterns enumerated in CLAUDE.md

**Provide:**
- Decision criteria for recognizing anti-patterns
- Template for documenting new ones as discovered
- Cross-reference to external sources

</details>

### Measuring Complexity

| Metric | What It Indicates | Target |
|--------|-------------------|--------|
| Lines per function | Function doing too much | <30 lines |
| Parameters per function | Poor abstraction | <5 parameters |
| Cyclomatic complexity | Too many branches | <10 per function |
| Import count per file | Coupling | <10 imports |
| Files changed per feature | Poor modularity | <5 files for small features |

## Anti-Patterns

### Organized by Symptom

| Symptom | Pattern Name | Fix |
|---------|--------------|-----|
| "This interface handles everything" | Kitchen Sink | Split into focused interfaces |
| Unused code everyone's afraid to delete | Boat Anchor | Delete it (git has history) |
| Undocumented code everyone builds around | Lava Flow | Document or refactor |
| Same code copy-pasted in 5 places | Copy-Paste | Extract only if >2 occurrences AND stable |
| "We might need this later" | Speculative Generality | Delete until needed |
| Empty catch blocks, ignored returns | Swallowed Errors | Handle or propagate |
| Boolean parameters switching behavior | Flag Arguments | Split into separate functions |

### Anti-Pattern Deep Dives

<details><summary>Kitchen Sink Interface</summary>

**Symptom:** Interface has 20+ methods "for all possible uses"

**Cause:** Trying to anticipate every use case upfront

**Fix:**
1. Identify actual current use cases
2. Extract minimal interface for each
3. Allow composition for complex cases

**Example:**
```
# BAD: One interface for everything
class DataProcessor:
    def read_csv(self): ...
    def read_json(self): ...
    def read_xml(self): ...
    def write_csv(self): ...
    def write_json(self): ...
    def transform(self): ...
    def validate(self): ...
    # ... 15 more methods

# GOOD: Focused interfaces
class CsvReader: ...
class JsonReader: ...
class DataTransformer: ...
```

</details>

<details><summary>Boat Anchor</summary>

**Symptom:** Code exists but is never called; developers are afraid to delete it

**Cause:** "Someone might need it" or "It used to be used"

**Fix:**
1. Search for usages (grep the codebase)
2. Check git history for when it was last called
3. Delete if unused for >6 months
4. Trust git to recover if needed

</details>

<details><summary>Lava Flow</summary>

**Symptom:** Mysterious code everyone works around but nobody understands

**Cause:** Original developer left; code was never documented

**Fix:**
1. Add tests that capture current behavior
2. Document what it does (even if not why)
3. Refactor incrementally once behavior is captured

</details>

## Checklists

### Before Commit

- [ ] No speculative code ("might need later")
- [ ] No unused imports, variables, or functions
- [ ] No commented-out code
- [ ] Each function does one thing
- [ ] No boolean flags switching behavior

### Code Review (Minimalism Focus)

- [ ] Could this be simpler?
- [ ] Is there dead code being added?
- [ ] Are new abstractions justified (rule of three)?
- [ ] Does the change scope match the request?
- [ ] Any "improvements" beyond what was asked?

### CLAUDE.md Health Check

- [ ] Under 200 instruction lines
- [ ] No embedded file contents (use file paths)
- [ ] Domain knowledge in skills, not CLAUDE.md
- [ ] Progressive disclosure: quick reference before details

## See Also

- [Troubleshooting Guide](./../troubleshooting-guide/troubleshooting-guide.md) - Progressive disclosure patterns
- [Stop Bloating Your CLAUDE.md](https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/) - Original research
- [MIT 2025: Legible Modular Software](https://news.mit.edu/2025/mit-researchers-propose-new-model-for-legible-modular-software-1106) - Concepts model
