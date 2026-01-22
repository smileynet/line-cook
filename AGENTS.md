# Line Cook

> See [README.md](README.md) for philosophy, influences, and user documentation.

Technical details for working on Line Cook itself.

## Overview

```
/plan → /prep → /cook → /serve → /tidy → /dessert
  ↓       ↓       ↓       ↓        ↓        ↓
 plan    sync   execute  review   commit  validate
```

Or use `/work` to run the full service cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/getting-started` | Quick workflow guide for beginners |
| `/plan` | Create task graph with tracer bullet methodology |
| `/prep` | Sync git, load kitchen manual, show available work |
| `/cook` | Execute task with TDD cycle and automatic quality gates |
| `/serve` | Review work via sous-chef (code reviewer) |
| `/tidy` | Commit with kitchen log, file findings, push |
| `/dessert` | Feature validation and documentation |
| `/work` | Full service orchestration (prep→cook→serve→tidy→dessert) |

## Platform Command Naming

Claude Code and OpenCode use different command naming conventions:

| Platform | Syntax | Example |
|----------|--------|---------|
| Claude Code | `namespace:command` | `/line:prep` |
| OpenCode | `namespace-command` | `/line-prep` |

This is a fundamental platform difference, not a design choice. Each platform discovers and registers commands differently:

- **Claude Code**: Uses `plugin.json` namespace + flat filename → `line:prep`
- **OpenCode**: Uses file path as command name → `line-prep`

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** or **OpenCode** - AI coding assistant

## Agent Definitions

Line Cook uses kitchen-themed agents for specialized roles in the workflow:

| Agent | Role | Purpose |
|-------|------|---------|
| **chef** | Task execution | Execute the task with TDD cycle and quality gates |
| **sous-chef** | Code review | Review changes for correctness, security, style, completeness |
| **quality-control** | Test quality review | Review tests for isolation, clarity, structure, anti-patterns |
| **sommelier** | Feature test quality | Review BDD tests for acceptance criteria coverage and quality |
| **kitchen-manager** | Full orchestration | Orchestrate complete service cycle with automatic error handling |

### chef

- **Purpose**: Execute tasks with TDD cycle (Red-Green-Refactor)
- **Responsibilities**:
  - Break task into implementation steps
  - Write failing tests (RED)
  - Implement minimal code (GREEN)
  - Refactor while tests pass
  - Verify tests pass and code builds
- **Output**: `KITCHEN_COMPLETE` signal when task is ready for review

### sous-chef

- **Purpose**: Review code changes before committing
- **Responsibilities**:
  - Check correctness (logic, edge cases, error handling)
  - Check security (input validation, secrets, injection risks)
  - Verify style (naming, consistency with codebase patterns)
  - Assess completeness (fully addresses the task?)
- **Critical issues**: Block tidy phase (require fixes)
- **Output**: `ready_for_tidy`, `needs_changes`, or `blocked` assessment

### quality-control

- **Purpose**: Review test quality before implementation
- **Responsibilities**:
  - Check tests are isolated, fast, repeatable
  - Verify clear test names and error messages
  - Ensure proper structure (Setup-Execute-Validate-Cleanup)
  - Identify anti-patterns
- **Trigger**: Automatically after RED phase (write failing test)
- **Output**: Test quality assessment with critical issue blocking if needed

### sommelier

- **Purpose**: Review feature (BDD) test quality before dessert service
- **Responsibilities**:
  - Verify all acceptance criteria have tests
  - Check Given-When-Then structure
  - Ensure tests map to acceptance criteria
  - Verify user perspective documented
  - Check error scenarios included
- **Trigger**: Automatically before dessert service (feature completion)
- **Output**: BDD quality assessment with critical issue blocking if needed

### kitchen-manager

- **Purpose**: Orchestrate complete service cycle
- **Responsibilities**:
  - Run prep checks and present kitchen roster
  - Delegate cooking to chef subagent
  - Coordinate serving with sous-chef review
  - Manage tidy phase (commit, push)
  - Trigger dessert service for feature completion
  - Handle failure conditions and coordinate recovery
- **Output**: Kitchen report after successful service

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Beads Quick Reference

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

## Session Completion (Landing the Plane)

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File issues for remaining work** - Create beads for anything needing follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** - All changes committed AND pushed

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- If push fails, resolve and retry until it succeeds

## Project Structure

```
line-cook/
├── commands/              # Claude Code command definitions
│   ├── getting-started.md # → /line:getting-started
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   ├── tidy.md            # → /line:tidy
│   └── work.md            # → /line:work
├── scripts/               # Installation scripts
│   └── install-claude-code.sh
├── line-cook-opencode/    # OpenCode plugin
│   ├── package.json       # Plugin manifest
│   ├── install.sh         # Installation script
│   ├── AGENTS.md          # Agent instructions (bundled)
│   └── commands/          # OpenCode command definitions
│       ├── line-prep.md   # → /line-prep
│       ├── line-cook.md   # → /line-cook
│       ├── line-serve.md  # → /line-serve
│       ├── line-tidy.md   # → /line-tidy
│       ├── line-work.md   # → /line-work
│       └── line-getting-started.md # → /line-getting-started
├── line-cook-kiro/        # Kiro agent
│   ├── agents/line-cook.json # Agent definition
│   ├── steering/          # Workflow steering docs
│   └── skills/            # Skill definitions
├── .claude-plugin/
│   └── plugin.json        # Claude Code plugin manifest
├── AGENTS.md              # Agent workflow instructions (this file)
└── README.md              # User documentation
```

## Command Synchronization

Line Cook maintains commands for both Claude Code (`commands/`) and OpenCode (`line-cook-opencode/commands/`). To ensure consistency across platforms:

**Template system:**
- Source templates live in `commands/templates/`
- Use `@NAMESPACE@` placeholder for command prefixes
- Run sync script to generate both versions:

```bash
./scripts/sync-commands.sh
```

**Platform differences handled automatically:**
- Claude Code: `/line:cook` (colon separator)
- OpenCode: `/line-cook` (hyphen separator)
- OpenCode includes additional "When run via /line-work" instruction

**When to sync:**
- After editing any command template
- Before committing command changes
- As part of release process

## Installation

### Claude Code

**Remote (from GitHub) - recommended for auto-updates:**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

Update: `/plugin update line`

**Local (from clone) - for development or offline use:**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook && ./scripts/install-claude-code.sh
```

Update: `cd ~/line-cook && git pull && ./scripts/install-claude-code.sh`

> **Note:** Local and remote installations are tracked separately.
> Local plugins show "To update, modify the source at: ./line" and cannot use `/plugin update`.
> To switch from local to remote, uninstall first: `/plugin uninstall line`

Commands: `/line:getting-started`, `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:work`

### OpenCode

**Online (from GitHub):**
```bash
opencode plugin install https://github.com/smileynet/line-cook
```

**Offline (local clone):**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook/line-cook-opencode && ./install.sh
```

Commands: `/line-getting-started`, `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-work`

### Kiro

Copy the `line-cook-kiro/` directory to your `.kiro/` folder:

```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cp -r ~/line-cook/line-cook-kiro/* ~/.kiro/
```

Commands: `prep`, `cook`, `serve`, `tidy`, `work`

## Release Process

**Releases are targeted events triggered by human decision, not automatic enforcement.** Track changes in CHANGELOG.md, then release when ready.

### Changelog-Based Workflow

```bash
# During development: Add entries to CHANGELOG.md [Unreleased] section
vim CHANGELOG.md  # Add your changes under [Unreleased]

# When ready to release:
# 1. Update CHANGELOG.md: Create new version section from [Unreleased]
# 2. Bump versions in plugin.json files (must be identical)
# 3. Commit, sync beads, push (release created automatically)
```

### Files Requiring Version Update

| File | Field(s) |
|------|----------|
| `.claude-plugin/plugin.json` | `version` |
| `line-cook-opencode/package.json` | `version` AND `opencode.version` |
| `CHANGELOG.md` | New version section from [Unreleased] |

### Release Procedure

```bash
# 1. Update CHANGELOG.md
#    - Create new section: ## [X.Y.Z] - YYYY-MM-DD
#    - Move entries from [Unreleased] to new section
#    - Update version comparison links at bottom

# 2. Determine version (semantic versioning)
#    Patch: bug fixes → 0.4.5 → 0.4.6
#    Minor: new features → 0.4.5 → 0.5.0
#    Major: breaking changes → 0.4.5 → 1.0.0

# 3. Update all version locations (must be identical)
#    - .claude-plugin/plugin.json: "version"
#    - line-cook-opencode/package.json: "version" AND "opencode.version"

# 4. Commit and push (release is created automatically)
git add CHANGELOG.md .claude-plugin/plugin.json line-cook-opencode/package.json
git commit -m "chore: release X.Y.Z"
bd sync
git push
```

> **Note:** GitHub Actions automatically creates a release when `plugin.json` is updated on `main`. See `.github/workflows/release.yml`.

### What to Track in CHANGELOG.md

**Track in [Unreleased]:**
- Command changes (commands/*.md)
- Hook changes (hooks/*.py, src/*.ts)
- Plugin manifest changes
- Core workflow logic
- Significant user-facing features or fixes

**Don't track:**
- Documentation-only (README, AGENTS.md, docs/)
- CI/CD configuration
- .beads/ changes
- Test files only

### When to Release

**Release when:**
- [Unreleased] section has substantial changes worth shipping
- You've completed a feature or fix users need
- Ready to deploy to production

**You can commit without releasing:**
- Iterative development (track in CHANGELOG [Unreleased])
- Work-in-progress commits (no version bump needed)
- Small refactorings that don't affect users

### Changelog Format

The changelog uses [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:

```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Behavior change description

### Fixed
- Bug fix description

## [0.6.3] - 2026-01-19

### Added
- Released feature
```

### Post-Release: User Instructions

After pushing a release, create a GitHub release with these instructions for users:

**Installation (new users):**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

**Update (existing users):**
```bash
/plugin update line
```

See [.github/release.md](.github/release.md) for the release notes template.

## Line Cook Workflow

> **Context Recovery**: Run `lc work` or individual commands after compaction

### Commands
| Command | Purpose |
|---------|---------|
| `/line:plan` | Create task graph with tracer bullet methodology |
| `/line:prep` | Sync git/beads, show ready tasks |
| `/line:cook` | Execute task with TDD cycle and automatic quality gates |
| `/line:serve` | Review via sous-chef subagent |
| `/line:tidy` | Commit, file findings, push |
| `/line:dessert` | Feature validation and BDD test review |
| `/line:work` | Full cycle orchestration |

### CLI
```bash
lc plan              # Create task graph
lc prep              # Sync and show ready tasks
lc cook [id]         # Claim task, output AI context
lc serve [id]        # Output diff and review context
lc tidy              # Commit and push
lc dessert [id]      # Feature validation
lc work              # Full service cycle
```

### Core Guardrails
1. **Sync before work** - Always start with current state
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles
4. **File, don't block** - Discoveries become beads
5. **Push before stop** - Work isn't done until pushed

### TDD Cycle with Quality Gates

Line Cook follows the Red-Green-Refactor cycle with automatic quality checks:

**RED**: Write failing test
- Write test for the feature you're implementing
- Verify the test fails
- Trigger quality-control agent for test quality review
- Address critical issues before proceeding

**GREEN**: Implement minimal code
- Write the simplest code to make the test pass
- Verify tests pass
- No refactoring yet

**REFACTOR**: Clean up code
- Improve code structure while tests pass
- Ensure tests still pass after refactoring
- Verify all tests pass and code builds

**QUALITY GATES**:
- Tests pass: `go test ./...` (or project-specific test command)
- Code builds: `go build ./...` (or project-specific build command)
- Test quality approved by quality-control agent
- Code quality approved by sous-chef agent (in serve phase)

## Kitchen Terminology

Line Cook uses restaurant/kitchen terminology throughout its workflow:

| Term | Meaning | Context |
|------|---------|---------|
| **Prep** | Sync git/beads, load kitchen manual, show ready orders | `/prep` phase |
| **Cook** | Execute task with TDD cycle and quality gates | `/cook` phase |
| **Serve** | Review work via sous-chef (code reviewer) | `/serve` phase |
| **Tidy** | Commit with kitchen log, file findings, push | `/tidy` phase |
| **Dessert** | Feature validation and BDD test review | `/dessert` phase |
| **Full Service** | Complete orchestration through all phases | `/work` phase |
| **Kitchen Manual** | AGENTS.md or .claude/CLAUDE.md - work structure documentation | Loaded during prep |
| **Kitchen Order System** | beads issue tracker - manages work orders | Synced during prep |
| **Kitchen Roster** | List of ready orders (tasks) | Displayed in prep |
| **Order** | Task or feature to execute | bead issue |
| **Recipe** | Task description and implementation plan | Task details |
| **Ingredients** | Required context files and documentation | Loaded before cooking |
| **Dish** | Completed work output | Results of cook phase |
| **Kitchen Equipment** | Build systems, test frameworks, linters | Verified before completion |
| **Quality Gates** | Automatic quality checks (test, code review, BDD) | Enforced in cook/serve/dessert |
| **Chef** | Subagent that executes tasks with TDD cycle | `/cook` phase |
| **Sous-Chef** | Subagent that reviews code changes | `/serve` phase |
| **Quality-Control** | Subagent that reviews test quality | After RED phase |
| **Sommelier** | Subagent that reviews BDD test quality | `/dessert` phase |
| **Kitchen-Manager** | Subagent that orchestrates full service | `/work` phase |
| **KITCHEN_COMPLETE** | Signal emitted when task is ready for review | End of cook phase |
| **READY_FOR_TIDY** | Assessment from sous-chef indicating code is ready to commit | After serve phase |
| **Kitchen Log** | Detailed commit message with implementation details | Commit format in tidy |
| **Kitchen Ledger** | Git remote repository - records all completed work | Push destination |
| **Service** | Complete workflow cycle (prep→cook→serve→tidy→dessert) | Full workflow |
| **Tracer** | Task that proves one aspect of a feature through all layers | Planning methodology |
| **Feature Complete** | All tasks for a feature closed, ready for dessert service | `/dessert` phase trigger |
| **Acceptance Report** | Document validating feature against acceptance criteria | Created in dessert |