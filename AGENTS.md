# Line Cook

> See [README.md](README.md) for philosophy, influences, and user documentation.

Technical details for working on Line Cook itself.

## Kitchen Theme

**Goal**: Low cognitive load with light theming for disambiguation.

### Why Kitchen Terms?

Command names use creative kitchen terms to help users distinguish Line Cook commands from other plugins. `/line:mise` won't be confused with another tool's `/plan` command.

### When to Use Theme vs. Direct Terms

| Context | Use | Example |
|---------|-----|---------|
| **Command names** | Themed (disambiguation) | `/line:mise`, `/line:plate` |
| **Command descriptions** | Direct (clarity) | "Create work breakdown before starting" |
| **Tutorials & casual docs** | Light flavor text OK | "Check the ticket rail (ready tasks)" |
| **Technical docs** | Direct terms only | "ready tasks", not just "ticket rail" |

The theme is a **recognition aid**, not a **learning barrier**. Always include the actual meaning.

### Terminology Glossary

| Theme Term | Actual Meaning | Use in... |
|------------|----------------|-----------|
| Ticket Rail | Ready task list | Flavor text only |
| House Rules | Project config (CLAUDE.md) | Flavor text only |
| Plate Check | Quality verification | Flavor text only |
| Shift Notes | Commit message | Flavor text only |
| House Book | Git remote | Flavor text only |
| Tasting Dish | Minimal e2e proof | Flavor text only |
| ORDER_UP | Task ready for review | Internal signal |
| GOOD_TO_GO | Review passed | Internal signal |

## Overview

```
/mise → /prep → /cook → /serve → /tidy → /plate
   ↓       ↓       ↓       ↓        ↓        ↓
 plan    sync   execute  review   commit  validate
```

Or use `/service` to run the full workflow cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/getting-started` | Quick workflow guide for beginners |
| `/mise` | Create work breakdown before starting |
| `/prep` | Sync git, show ready tasks |
| `/cook` | Execute task with TDD cycle |
| `/serve` | Review code changes |
| `/tidy` | Commit and push changes |
| `/plate` | Validate completed feature |
| `/service` | Run full workflow cycle |

## Platform Command Naming

Claude Code and OpenCode use different command naming conventions:

| Platform | Syntax | Example |
|----------|--------|---------|
| Claude Code | `namespace:command` | `/line:prep` |
| OpenCode | `namespace-command` | `/line-prep` |

- **Claude Code**: Uses `plugin.json` namespace + flat filename → `line:prep`
- **OpenCode**: Uses file path as command name → `line-prep`

## Platform Architecture

**Line Cook supports THREE separate AI coding platforms:**

| Platform | Type | CLI Tool | Product |
|----------|------|----------|----------|
| Claude Code | Plugin system | claude CLI | Anthropic product |
| OpenCode | TUI application | opencode CLI | anomalyco/opencode |
| Kiro CLI | CLI application | kiro-cli | kiro.dev |

**Key Points:**
- **Claude Code**, **OpenCode**, and **Kiro CLI** are COMPLETELY UNRELATED PRODUCTS
- Each has its own CLI: `claude`, `opencode`, and `kiro` respectively
- Line Cook provides separate implementations for each:
  - `commands/` + `.claude-plugin/` = Claude Code plugin
  - `line-cook-opencode/` = OpenCode plugin  
  - `line-cook-kiro/` = Kiro CLI agents

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** or **OpenCode** - AI coding assistant

## Agent Definitions

Line Cook provides agents for each platform:

### Kiro CLI Agents (line-cook-kiro/agents/)

| Agent | Role | Purpose |
|-------|------|---------|
| **line-cook** | Main agent | Execute workflow commands (prep, cook, serve, tidy, service) |
| **taster** | Test quality | Review tests for isolation, clarity, structure, anti-patterns |
| **sous-chef** | Code review | Review changes for correctness, security, style, completeness |

### Claude Code Commands (commands/)

Claude Code uses slash commands instead of agents:

| Command | Role | Purpose |
|---------|------|---------|
| **/line:getting-started** | Tutorial | Quick workflow guide for beginners |
| **/line:mise** | Planning phase | Create work breakdown before starting |
| **/line:prep** | Prep phase | Sync git, show ready tasks |
| **/line:cook** | Cook phase | Execute task with TDD cycle |
| **/line:serve** | Serve phase | Review code changes |
| **/line:tidy** | Tidy phase | Commit and push changes |
| **/line:plate** | Plate phase | Validate completed feature |
| **/line:service** | Full cycle | Prep→cook→serve→tidy orchestration |

### Claude Code Subagents (agents/)

Claude Code subagents are specialized review agents invoked during workflow phases:

| Agent | Phase | Purpose |
|-------|-------|---------|
| **taster** | Cook (RED) | Reviews test quality |
| **sous-chef** | Serve | Reviews code changes |
| **maître** | Plate | Reviews feature acceptance |

### OpenCode Plugin (line-cook-opencode/)

OpenCode plugin uses OpenCode's built-in agent system:

| Component | Type | Purpose |
|----------|------|---------|
| **Commands** | OpenCode plugin | `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-mise`, `/line-plate`, `/line-service` |
| **Kiro Agents** | OpenCode agents | taster, sous-chef (via OpenCode's agent system) |

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

### taster

- **Purpose**: Review test quality before implementation
- **Responsibilities**:
  - Check tests are isolated, fast, repeatable
  - Verify clear test names and error messages
  - Ensure proper structure (Setup-Execute-Validate-Cleanup)
  - Identify anti-patterns
- **Trigger**: Automatically after RED phase (write failing test)
- **Output**: Test quality assessment with critical issue blocking if needed

### maître

- **Purpose**: Review feature (BDD) test quality before plate phase
- **Responsibilities**:
  - Verify all acceptance criteria have tests
  - Check Given-When-Then structure
  - Ensure tests map to acceptance criteria
  - Verify user perspective documented
  - Check error scenarios included
- **Trigger**: Automatically before plate phase (feature completion)
- **Output**: BDD quality assessment with critical issue blocking if needed

### expeditor

- **Purpose**: Orchestrate complete workflow cycle
- **Responsibilities**:
  - Run prep checks and present ready tasks
  - Delegate cooking to chef subagent
  - Coordinate serving with sous-chef review
  - Manage tidy phase (commit, push)
  - Trigger plate phase for feature completion
  - Handle failure conditions and coordinate recovery
- **Output**: Workflow report after successful service

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
├── agents/                # Claude Code subagent definitions
│   ├── taster.md          # Test quality review (cook RED phase)
│   ├── sous-chef.md       # Code review (serve phase)
│   └── maitre.md          # BDD test review (plate phase)
├── commands/              # Claude Code command definitions
│   ├── getting-started.md # → /line:getting-started
│   ├── mise.md            # → /line:mise (work breakdown)
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   ├── tidy.md            # → /line:tidy
│   ├── plate.md           # → /line:plate
│   └── service.md         # → /line:service
├── scripts/               # Installation and utility scripts
│   ├── install-claude-code.sh
│   └── sync-commands.sh   # Sync commands across platforms
├── line-cook-opencode/    # OpenCode plugin
│   ├── package.json       # Plugin manifest
│   ├── install.sh         # Installation script
│   ├── AGENTS.md          # Agent instructions (bundled)
│   └── commands/          # OpenCode command definitions
│       ├── line-prep.md   # → /line-prep
│       ├── line-cook.md   # → /line-cook
│       ├── line-serve.md  # → /line-serve
│       ├── line-tidy.md   # → /line-tidy
│       ├── line-mise.md   # → /line-mise
│       ├── line-plate.md  # → /line-plate
│       └── line-service.md # → /line-service
│   └── line-getting-started.md # → /line-getting-started
├── line-cook-kiro/        # Kiro agent
│   ├── agents/            # Agent definitions
│   │   ├── line-cook.json # Main agent
│   │   ├── taster.json    # Test quality review agent
│   │   ├── sous-chef.json # Code review agent
│   │   └── maitre.json    # BDD test quality agent
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
- Use placeholders for platform-specific differences:
  - `@NAMESPACE@` - Command prefix (`line:` for Claude, `line-` for OpenCode)
  - `@HEADLESSCLI@` - Headless CLI name (`claude` for Claude, `opencode` for OpenCode)
  - `@NAMESPACE@CLI` - CLI name reference in documentation
- Run sync script to generate both versions:

**Platform differences handled automatically:**
- Claude Code: `/line:cook` (colon separator), uses `claude` CLI
- OpenCode: `/line-cook` (hyphen separator), uses `opencode` CLI
- OpenCode includes additional "When run via /line-work" instruction

**Synced commands:**
- cook.md → uses `@NAMESPACE@`, `@HEADLESSCLI@`, `@NAMESPACE@CLI`
- serve.md → uses `@NAMESPACE@`, `@HEADLESSCLI@`, `@NAMESPACE@CLI`

**When to sync:**
- After editing any command template
- Before committing command changes
- As part of release process

```bash
./scripts/sync-commands.sh
```

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

Commands: `/line:getting-started`, `/line:mise`, `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:plate`, `/line:service`

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

> **Context Recovery**: Run `/line:prep` after compaction

### Commands
| Command | Purpose |
|---------|---------|
| `/line:mise` | Create work breakdown before starting |
| `/line:prep` | Sync git, show ready tasks |
| `/line:cook` | Execute task with TDD cycle |
| `/line:serve` | Review code changes |
| `/line:tidy` | Commit and push changes |
| `/line:plate` | Validate completed feature |
| `/line:service` | Run full workflow cycle |

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
- Trigger taster agent for test quality review
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
- Test quality approved by taster agent
- Code quality approved by sous-chef agent (in serve phase)

## Kitchen Terminology

Line Cook uses restaurant/kitchen terminology throughout its workflow:

| Term | Meaning | Context |
|------|---------|---------|
| **Mise** | Create work breakdown before starting | `/mise` phase |
| **Prep** | Sync git, show ready tasks | `/prep` phase |
| **Cook** | Execute task with TDD cycle | `/cook` phase |
| **Serve** | Review code changes | `/serve` phase |
| **Tidy** | Commit and push changes | `/tidy` phase |
| **Plate** | Validate completed feature | `/plate` phase |
| **Service** | Run full workflow cycle | `/service` phase |
| **Chef** | Subagent that executes tasks with TDD cycle | `/cook` phase |
| **Sous-Chef** | Subagent that reviews code changes | `/serve` phase |
| **Taster** | Subagent that reviews test quality | After RED phase |
| **Maître** | Subagent that reviews feature acceptance | `/plate` phase |
| **Expeditor** | Subagent that orchestrates full workflow | `/service` phase |
| **ORDER_UP** | Signal emitted when task is ready for review | End of cook phase |
| **GOOD_TO_GO** | Assessment from sous-chef indicating code is ready to commit | After serve phase |
| **Tracer** | Task that proves one aspect of a feature through all layers | Planning methodology |
| **Feature Complete** | All tasks for a feature closed, ready for plate phase | `/plate` phase trigger |
| **Acceptance Report** | Document validating feature against acceptance criteria | Created in plate |