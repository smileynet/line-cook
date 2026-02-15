# Command Reference

All Line Cook commands organized by lifecycle phase.

---

## Planning Commands

### /line:mise

Run the full planning cycle with pause points between phases.

```
/line:mise                   # Full cycle: brainstorm → scope → finalize
/line:mise skip-brainstorm   # Skip brainstorm, start at scope
```

Pauses after each phase for review. See [Mise Cycle](../cycles/mise-cycle.md).

### /line:brainstorm

Explore the problem space (divergent thinking).

- Asks clarifying questions
- Explores technical approaches
- Identifies risks and unknowns
- Output: `docs/planning/brainstorm-<name>.md`

### /line:scope

Create structured work breakdown (convergent thinking).

- Loads brainstorm document if available
- Creates YAML menu plan with hierarchy, dependencies, acceptance criteria
- Output: `docs/planning/menu-plan.yaml`

### /line:finalize

Convert menu plan to tracked work items.

- Creates beads (epic → feature → task) with dependencies
- Creates BDD test specs (`.feature` files)
- Creates TDD test specs (`.md` files)
- Output: `.beads/` + test specifications

---

## Execution Commands

### /line:run

Run the full execution cycle: prep → cook → serve → tidy.

```
/line:run
```

See [Run Cycle](../cycles/run-cycle.md).

### /line:prep

Sync state and identify ready tasks.

```
/line:prep
```

- Syncs git and beads with remote
- Shows ready, in-progress, and blocked task counts
- Recommends highest-priority unblocked task
- Read-only — safe to run anytime

### /line:cook

Execute a task with TDD cycle (Red-Green-Refactor).

```
/line:cook           # Auto-select highest-priority unblocked task
/line:cook <id>      # Work on a specific task
```

- Claims the task (status → in_progress)
- Follows TDD: write failing test → implement → refactor
- Captures discoveries for filing in Tidy
- Closes task when all checks pass

### /line:serve

AI peer review of code changes.

```
/line:serve
```

- Polisher agent refines code clarity
- Sous-chef agent reviews correctness, security, style, completeness
- Returns verdict: APPROVED, NEEDS_CHANGES, or BLOCKED
- NEEDS_CHANGES loops back to Cook

### /line:tidy

Commit changes, file discoveries, push to remote.

```
/line:tidy
```

- Files Cook/Serve discoveries as tracked issues
- Creates conventional commit
- Syncs beads
- Pushes to remote

### /line:plate

Validate completed feature against acceptance criteria.

```
/line:plate           # Auto-detect close-eligible features
/line:plate <id>      # Validate a specific feature
```

- Runs BDD acceptance tests
- Verifies all child tasks closed
- Creates acceptance documentation
- Closes feature (and parent epic if all features done)

### /line:close-service

Validate completed epic (all features plated).

```
/line:close-service            # Auto-detect close-eligible epics
/line:close-service <id>       # Validate a specific epic
```

- Verifies all child features are closed
- Critic agent reviews E2E and cross-feature integration coverage
- Creates epic acceptance documentation
- Closes the epic and merges epic branch to main

---

## Autonomous Execution

### /line:loop

Run multiple execution cycles autonomously.

```
/line:loop                     # Run until no ready tasks
/line:loop max-iterations=5    # Limit to 5 cycles
```

Repeats the Run Cycle until no ready tasks remain. Same quality gates as `/line:run`. See [Loop Cycle](../cycles/loop-cycle.md).

---

## Utility Commands

### /line:plan-audit

Validate bead structure and quality.

```
/line:plan-audit               # Check open items
/line:plan-audit full          # Comprehensive audit including closed items
/line:plan-audit <id>          # Check specific epic/feature and children
/line:plan-audit --fix         # Auto-fix safe issues
```

Checks: structural integrity, quality (acceptance criteria, priorities), health (stale items), and work verification.

### /line:architecture-audit

Analyze codebase structure, code smells, and quality metrics.

```
/line:architecture-audit
```

Checks: coupling, complexity, code smells (bloaters, couplers, change preventers, dispensables), documentation health.

### /line:decision

Record, list, or view architecture decision records (ADRs).

```
/line:decision                 # Record a new decision
/line:decision list            # List all decisions
/line:decision show NNN        # View a specific decision
```

### /line:help

Contextual help for Line Cook commands.

```
/line:help
/line:help <command>
```

### /line:getting-started

Interactive workflow guide with bead reference.

```
/line:getting-started
```

---

## Beads Commands (Quick Reference)

These are `bd` CLI commands, not Line Cook commands. See [Beads Reference](beads.md) for more detail.

| Command | Purpose |
|---------|---------|
| `bd init` | Initialize beads in project |
| `bd ready` | Show unblocked tasks |
| `bd show <id>` | View issue details |
| `bd update <id> --status=in_progress` | Claim work |
| `bd close <id>` | Complete work |
| `bd create --title="..." --type=task` | Create issue |
| `bd dep add <issue> <depends-on>` | Add dependency |
| `bd blocked` | Show blocked issues |
| `bd stats` | Project statistics |
| `bd sync` | Sync with git remote |
| `bd epic status` | Show epic progress |
