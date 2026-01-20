# Feature Design Guide

How to structure work in beads using the 3-tier hierarchy: **Epic → Feature → Task**.

## The 3-Tier Hierarchy

| Tier | Purpose | Example |
|------|---------|---------|
| **Epic** | Capability area spanning 3+ sessions | "Hook System Hardening" |
| **Feature** | User-verifiable outcome | "Hooks work in all git configurations" |
| **Task** | Implementation step (1 session) | "Harden worktree detection in pre-push" |

```
Epic (capability area)
├── Feature 1 (user-verifiable outcome)
│   ├── Task 1a (implementation step)
│   └── Task 1b (implementation step)
└── Feature 2 (user-verifiable outcome)
    └── Task 2a (implementation step)
```

## What Makes a User-Observable Feature

**A feature is user-observable when a human can verify it works.**

The key question: *Can a non-developer confirm this is working?*

### The "Who" Test

Ask yourself: "Who benefits from this?"

| Beneficiary | Result |
|-------------|--------|
| End user | Feature |
| System/infrastructure | Task |
| Developer only | Task |

If the answer is "the system" or "developers," it's a task, not a feature.

### Feature vs Task Criteria

| Criterion | Feature | Task |
|-----------|---------|------|
| **Value** | Delivers visible benefit to user | Supports features, no standalone value |
| **Testable** | User can verify "it works" | Only devs can verify |
| **Perspective** | Human user's viewpoint | System/developer viewpoint |
| **Scope** | End-to-end (vertical slice) | Single layer/component |

### Good Feature Examples

| Feature | Why It's a Feature |
|---------|-------------------|
| "Hooks work in git worktrees" | User can verify: run hook in worktree, it works |
| "Scripts work on Windows" | User can verify: run on Windows, no errors |
| "SKILL.md loads in Claude Code" | User can verify: Claude discovers line-cook |
| "Users can filter search results" | User can verify: filter controls work |

### Good Task Examples

| Task | Why It's a Task |
|------|-----------------|
| "Harden worktree detection in pre-push" | Technical implementation detail |
| "Add Python fallback for shell scripts" | Technical decision/implementation |
| "Refactor hook detection logic" | Internal code quality |
| "Update database schema for new field" | Infrastructure change |

## Anti-Patterns

### 1. System-as-User

**Bad:** "As a system, I want to upgrade the database"

Systems don't perceive value. This is infrastructure work that supports features, not a feature itself.

**Better:** Task under a feature like "Users can access their historical data"

### 2. Prescribing Solutions

**Bad:** "Add dropdown with autocomplete and API-based search"

This specifies implementation, not outcome. It constrains solutions prematurely.

**Better:** "Users can quickly find products" (leave implementation to tasks)

### 3. Layer-by-Layer Splitting

**Bad:**
- "Build UI for product filter"
- "Build API for product filter"
- "Build database schema for filter"

This delivers no value until all layers are done. It's developer-centric, not user-centric.

**Better:** "Users can filter products by category" (vertical slice touching all layers)

### 4. Technical Tasks as Features

**Bad feature:** "Refactor authentication module"

Refactoring is invisible to users. It may improve code quality but delivers no new capability.

**Better:** Task under a feature, or standalone task if it's pure tech debt

### 5. Invisible Infrastructure

**Bad feature:** "Implement caching layer"

Users don't see caching. They see "page loads faster."

**Better:** Feature: "Search results load quickly" → Task: "Implement caching layer"

## Vertical Slicing

Features should be **vertical slices** that deliver end-to-end value, not horizontal layers.

### Horizontal (Bad)

```
Feature: "Build product UI"
Feature: "Build product API"
Feature: "Build product database"
```

Problems:
- No value until all are done
- Hard to test in isolation
- Risk of integration issues at the end

### Vertical (Good)

```
Feature: "Users can view product details"
  └── Tasks: UI component, API endpoint, database query

Feature: "Users can add products to cart"
  └── Tasks: Cart UI, cart API, cart storage
```

Benefits:
- Each feature delivers testable value
- Can ship incrementally
- Integration tested continuously

## Research Epics (Exception)

Research tasks don't have user-observable outcomes—they're investigations that inform future work. These go directly under a Research epic without a feature layer.

```
Research & Exploration [EPIC]
├── Research Gas Town context patterns [TASK]
├── Evaluate Python hook deprecation [TASK]
└── Investigate background execution [TASK]
```

Research produces knowledge, not features. The knowledge may later inform features in other epics.

## Acceptance Criteria

Every feature should have implicit or explicit acceptance criteria—how a user would verify it works.

| Feature | Acceptance Criteria |
|---------|-------------------|
| "Hooks work in git worktrees" | Run `git push` from worktree; hook executes without errors |
| "Scripts work on Windows" | Run setup script on Windows; completes successfully |
| "Search filters products" | Select category filter; only matching products shown |

If you can't write acceptance criteria a user could verify, it's probably a task.

## Naming Conventions

| Tier | Style | Pattern |
|------|-------|---------|
| **Epic** | Noun phrase | "[Capability Area]" |
| **Feature** | Outcome statement | "[Users/Things] can/work/have [outcome]" |
| **Task** | Action phrase | "[Verb] [specific thing]" |

### Examples

| Tier | Example |
|------|---------|
| Epic | "Hook System Hardening" |
| Feature | "Hooks work in all git configurations" |
| Task | "Harden worktree detection in pre-push hook" |

| Tier | Example |
|------|---------|
| Epic | "AI Discoverability" |
| Feature | "Claude Code discovers line-cook automatically" |
| Task | "Create SKILL.md following meta-agentic pattern" |

## When to Create Each Tier

| Situation | Create |
|-----------|--------|
| Work spans 3+ sessions | Epic |
| Multiple related features | Epic |
| User could test/demonstrate it | Feature |
| Has acceptance criteria | Feature |
| Single-session implementation | Task |
| Technical/infrastructure work | Task |
| Research/investigation | Task (under Research epic) |

## Quick Reference

**Is it a Feature?**
1. Can a user verify it works? → Yes = Feature
2. Does it deliver visible value? → Yes = Feature
3. Is the beneficiary "the system"? → No = Task
4. Is it a vertical slice? → Yes = Feature

**Creating the hierarchy:**
```bash
# Epic
bd create --title="Hook System Hardening" --type=epic --priority=2

# Feature under epic
bd create --title="Hooks work in all git configurations" --type=feature --parent=lc-xxx --priority=3

# Task under feature
bd create --title="Harden worktree detection" --type=task --parent=lc-xxx.1
```

## Sources

- [User Story Smells and Anti-patterns](https://www.kaizenko.com/9-user-story-smells-and-anti-patterns/)
- [Typical Antipatterns in User Stories](https://worldofagile.com/blog/typical-antipatterns-seen-in-a-user-story/)
- [Guide to Splitting User Stories](https://www.humanizingwork.com/the-humanizing-work-guide-to-splitting-user-stories/)
- [Acceptance Criteria Best Practices](https://www.atlassian.com/work-management/project-management/acceptance-criteria)
