# Beads Quick Reference

## Essential Commands

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Bead Hierarchy

Line-cook uses a **3-tier hierarchy** for organizing work:

1. **Epics** - High-level capability areas (3+ sessions of work)
2. **User-Observable Features** - Acceptance-testable outcomes (first-level children of epics)
3. **Implementation Tasks** - Single-session work items (children of features)

### Structure

```
Epic (capability area)
├── Feature 1 (user-verifiable outcome)
│   ├── Task 1a (implementation step)
│   └── Task 1b (implementation step)
├── Feature 2 (user-verifiable outcome)
│   └── Task 2a (implementation step)
└── Feature 3 (user-verifiable outcome)
    ├── Task 3a (implementation step)
    └── Task 3b (depends on Task 3a)
```

**Exception: Research & Parking Lot epics** - These have tasks as direct children (no feature layer) since research tasks don't have user-observable outcomes.

### What Makes a User-Observable Feature

**A feature is user-observable when a human can verify it works.**

| Criterion | Feature | Task |
|-----------|---------|------|
| **Value** | Delivers visible benefit to user | Supports features, no standalone value |
| **Testable** | User can verify "it works" | Only devs can verify |
| **Perspective** | Human user's viewpoint | System/developer viewpoint |
| **Scope** | End-to-end (vertical slice) | Single layer/component |

**The "Who" Test:** If the beneficiary is "the system" or "developers," it's a task, not a feature.

### Naming Conventions

| Tier | Style | Examples |
|------|-------|----------|
| **Epic** | Noun phrase (capability area) | "Hook System Hardening", "AI Discoverability" |
| **Feature** | User-verifiable outcome | "Hooks work in all git configurations", "Scripts work on Windows" |
| **Task** | Action-oriented implementation | "Harden worktree detection", "Add Python fallback" |

### When to Create Each Tier

| Tier | When to Create |
|------|----------------|
| **Epic** | Work spans 3+ sessions OR multiple user-observable features |
| **Feature** | User could test/demonstrate it working; has acceptance criteria |
| **Task** | Implementation step completable in one session |

### Creating Hierarchy

```bash
# Create the epic
bd create --title="Hook System Hardening" --type=epic --priority=2

# Create features under epic
bd create --title="Hooks work in all git configurations" --type=feature --parent=lc-abc --priority=3
bd create --title="Scripts work across all platforms" --type=feature --parent=lc-abc --priority=3

# Create tasks under features
bd create --title="Harden worktree detection in pre-push" --type=task --parent=lc-abc.1
bd create --title="Add fallback for bare repos" --type=task --parent=lc-abc.1

# Add dependencies between tasks for ordering
bd dep add lc-xyz lc-def   # Task xyz depends on task def
```

### Querying Epic Progress

```bash
bd epic status                    # Show all epics with child completion
bd epic status --eligible-only    # Show epics ready to close
bd list --parent=<epic-id>        # List children of an epic
bd list --parent=<epic-id> --all  # Include closed children
```

### When to Use Each Relationship

| Relationship | When to use |
|--------------|-------------|
| `--parent` (epic) | Feature belongs to an epic |
| `--parent` (feature) | Task implements a feature |
| `bd dep add` | Task must complete before another (ordering) |
| Epic depends on epic | One capability requires another first |

### Anti-patterns

- **System-as-User** - "As a system, I want to upgrade the database" → This is a task, not a feature
- **Prescribing Solutions** - "Add dropdown with autocomplete" → Better: "Users can quickly find products"
- **Layer-by-Layer Splitting** - "Build UI" → "Build API" → "Build DB" → Better: vertical slice that delivers value
- **Technical Tasks as Features** - "Refactor hook detection" → Should be a task under a feature
- **Flat task lists** - Group related work into epics with features
- **Over-nesting** - Max 3 levels: epic → feature → task
