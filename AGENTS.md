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
/mise ─────────────────────────────────→ /prep → /cook → /serve → /tidy → /plate
  │                                         ↓       ↓       ↓        ↓        ↓
  ├─ /brainstorm → brainstorm.md          sync   execute  review   commit  validate
  ├─ /scope → menu-plan.yaml
  └─ /finalize → beads + specs
```

Or use `/run` to run the full execution cycle, `/mise` to run the full planning cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/getting-started` | Quick workflow guide for beginners |
| `/mise` | Create work breakdown (orchestrates brainstorm→scope→finalize) |
| `/brainstorm` | Explore problem space (divergent thinking) |
| `/scope` | Create structured work breakdown (convergent thinking) |
| `/finalize` | Convert plan to beads and create test specs |
| `/plan-audit` | Audit bead structure, quality, and hygiene |
| `/prep` | Sync git, show ready tasks |
| `/cook` | Execute task with TDD cycle |
| `/serve` | Review code changes |
| `/tidy` | Commit and push changes |
| `/plate` | Validate completed feature |
| `/run` | Run full workflow cycle |

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
| **line-cook** | Main agent | Execute workflow commands (prep, cook, serve, tidy, run) |
| **kitchen-manager** | Orchestrator | Coordinate full service cycle with automatic error handling |
| **taster** | Test quality | Review tests for isolation, clarity, structure, anti-patterns |
| **sous-chef** | Code review | Review changes for correctness, security, style, completeness |

### Claude Code Commands (commands/)

Claude Code uses slash commands instead of agents:

| Command | Role | Purpose |
|---------|------|---------|
| **/line:getting-started** | Tutorial | Quick workflow guide for beginners |
| **/line:mise** | Planning orchestrator | Brainstorm→scope→finalize with pauses |
| **/line:brainstorm** | Brainstorm phase | Explore problem space (divergent thinking) |
| **/line:scope** | Scope phase | Create structured work breakdown |
| **/line:finalize** | Finalize phase | Convert plan to beads + test specs |
| **/line:plan-audit** | Hygiene check | Audit bead structure, quality, work verification |
| **/line:prep** | Prep phase | Sync git, show ready tasks |
| **/line:cook** | Cook phase | Execute task with TDD cycle |
| **/line:serve** | Serve phase | Review code changes |
| **/line:tidy** | Tidy phase | Commit and push changes |
| **/line:plate** | Plate phase | Validate completed feature |
| **/line:run** | Execution orchestrator | Prep→cook→serve→tidy orchestration |

### Claude Code Subagents (agents/)

Claude Code subagents are specialized agents invoked during workflow phases:

| Agent | Phase | Purpose |
|-------|-------|---------|
| **taster** | Cook (RED) | Reviews test quality |
| **polisher** | Serve | Refines code for clarity before review |
| **sous-chef** | Serve | Reviews code changes |
| **maître** | Plate (Feature) | Reviews feature acceptance |
| **critic** | Plate (Epic) | Reviews E2E and user journey coverage |

### Project-Specific Agents (.claude/agents/)

Agents for Line Cook development (not shipped with the plugin):

| Agent | Purpose |
|-------|---------|
| **release-editor** | Interactive release coordinator for preparing new versions |

> **Note:** The shipped `agents/sous-chef.md` is used directly for this project (no local override).

### OpenCode Plugin (line-cook-opencode/)

OpenCode plugin uses OpenCode's built-in agent system:

| Component | Type | Purpose |
|----------|------|---------|
| **Commands** | OpenCode plugin | `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-mise`, `/line-brainstorm`, `/line-scope`, `/line-finalize`, `/line-plate`, `/line-run` |
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

### polisher

- **Purpose**: Refine code for clarity before review
- **Responsibilities**:
  - Reduce unnecessary complexity and nesting
  - Improve naming clarity
  - Remove dead code and redundancy
  - Follow project conventions from CLAUDE.md
  - Avoid nested ternaries (prefer if/else or switch)
- **Scope**: Only touches files modified in current changes
- **Constraint**: Never changes functionality—only how code is written
- **Output**: Summary of refinements made (file:line - change)

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

### critic

- **Purpose**: Review epic-level E2E and smoke test coverage
- **Responsibilities**:
  - Validate critical user journeys are tested
  - Check cross-feature integration points
  - Verify smoke tests exist for critical paths
  - Ensure testing approach fits project type
  - Identify antipatterns (ice cream cone, flaky tests)
- **Trigger**: Automatically during epic plate (when last feature completes)
- **Output**: E2E coverage assessment (PASS, NEEDS_WORK, or FAIL)
- **Documentation**: See [Epic-Level Testing](docs/guidance/epic-testing.md)

### kitchen-manager (expeditor)

- **Purpose**: Orchestrate complete service cycle (prep→cook→serve→tidy→plate)
- **Responsibilities**:
  - Run prep checks and auto-select next task
  - Execute cook phase directly (or delegate to chef)
  - Coordinate serving with sous-chef review
  - Manage tidy phase (commit, push)
  - Trigger plate phase for feature completion
  - Handle failure conditions and abort protocol
- **Failure Conditions** (stop execution):
  - Tests fail
  - Build fails
  - Reviewer blocks (BLOCKED verdict)
  - BDD quality blocks
  - Git operations fail
- **Output**: Service report after successful tidy
- **Implementation**: `line-cook-kiro/agents/kitchen-manager.json`

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Beads Reference

See [Beads Reference](docs/guidance/beads-reference.md) for hierarchy, CLI commands, and best practices.

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

See [Project Structure](docs/dev/project-structure.md) for full directory layout.

## Command Synchronization

Line Cook maintains commands for Claude Code (`commands/`), OpenCode (`line-cook-opencode/commands/`), and Kiro (`line-cook-kiro/prompts/`). All are generated from shared templates to prevent drift.

**Template system:**
- Source templates live in `commands/templates/` (11 templates)
- Use placeholders for platform-specific differences:
  - `@NAMESPACE@` - Command prefix (`line:` for Claude Code, `line-` for OpenCode/Kiro)
  - `@IF_CLAUDECODE@`...`@ENDIF_CLAUDECODE@` - Claude Code only content
  - `@IF_OPENCODE@`...`@ENDIF_OPENCODE@` - OpenCode and Kiro shared content
  - `@IF_KIRO@`...`@ENDIF_KIRO@` - Kiro only content

**Platform differences handled automatically:**
- Claude Code: `/line:cook` (colon separator), includes `Skill()` calls and subagent details
- OpenCode: `/line-cook` (hyphen separator), simplified step numbering
- Kiro: `@line-cook` (at-sign prefix), same content as OpenCode but no YAML frontmatter

**Synced commands:** All 11 — brainstorm, cook, finalize, getting-started, mise, plate, prep, run, scope, serve, tidy

**When to sync:**
- After editing any command template
- Before committing command changes (pre-commit hook enforces this)
- As part of release process

```bash
./scripts/sync-commands.sh
```

## Installation

See [README.md#installation](README.md#installation) for platform-specific installation instructions.

> **Important - Command Discovery:** Claude Code caches commands based on `plugin.json` version. After adding new commands, bump the version and run `/clear` in a new session.

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
- Script changes (scripts/*.py, scripts/*.sh)
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

### Version Bump Requirements

Claude Code caches the available commands list based on the plugin version. This affects when you need to bump versions:

**Must bump version:**
- Adding new commands (files in `commands/`)
- Adding new agents (files in `agents/`)
- Adding new scripts that skills depend on
- Any change you want users to see immediately

**Can skip version bump:**
- Editing existing command content (behavior changes work after install script re-run)
- Documentation changes
- Internal refactoring

**How caching works:**
1. When plugin is installed, Claude Code reads `plugin.json` version and scans directories
2. Command list is cached per version number
3. Re-running install script copies new files but doesn't trigger rescan
4. Bumping version forces Claude Code to rescan and discover new commands
5. Users must start new session (`/clear`) after plugin update

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

> **Note:** The `.github/workflows/release.yml` workflow automatically creates releases when `plugin.json` version changes on main.

## Line Cook Workflow

> **Context Recovery**: Run `/line:prep` after compaction

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
- Tests pass: `<test command>` (e.g., `go test ./...`, `pytest`, `npm test`, `cargo test`)
- Code builds: `<build command>` (e.g., `go build ./...`, `npm run build`, `cargo build`)
- Test quality approved by taster agent
- Code quality approved by sous-chef agent (in serve phase)

## Kitchen Terminology

See [Kitchen Glossary](docs/guidance/kitchen-glossary.md) for the full terminology reference.