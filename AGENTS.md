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

Line Cook provides separate implementations for each:
  - `plugins/claude-code/` = Claude Code plugin
  - `plugins/opencode/` = OpenCode plugin
  - `plugins/kiro/` = Kiro CLI agents

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** or **OpenCode** - AI coding assistant

## Agent Definitions

Line Cook provides agents for each platform:

### Kiro CLI Agents (plugins/kiro/agents/)

| Agent | Role | Purpose |
|-------|------|---------|
| **line-cook** | Orchestrator | Route workflow commands to template-synced prompts, enforce guardrails |
| **taster** | Test quality | Review tests for isolation, clarity, structure, anti-patterns |
| **sous-chef** | Code review | Review changes for correctness, security, style, completeness |
| **polisher** | Code refinement | Simplify and polish code before review |
| **maitre** | BDD review | Review feature acceptance and BDD test quality |
| **critic** | E2E review | Review epic-level E2E and user journey coverage |

### Claude Code Commands (plugins/claude-code/commands/)

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
| **/line:architecture-audit** | Code quality | Analyze codebase structure and code smells |
| **/line:decision** | ADR management | Record, list, or supersede architecture decisions |
| **/line:help** | Reference | Contextual help for Line Cook commands |
| **/line:loop** | Automation | Autonomous loop management |

### Claude Code Subagents (plugins/claude-code/agents/)

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

> **Note:** The shipped `plugins/claude-code/agents/sous-chef.md` is used directly for this project (no local override).

### OpenCode Plugin (plugins/opencode/)

OpenCode plugin uses OpenCode's built-in agent system:

| Component | Type | Purpose |
|----------|------|---------|
| **Commands** | OpenCode plugin | `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-mise`, `/line-brainstorm`, `/line-scope`, `/line-finalize`, `/line-plate`, `/line-run`, `/line-getting-started`, `/line-architecture-audit`, `/line-decision`, `/line-help`, `/line-loop`, `/line-plan-audit` |
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

Three zones: **plugins/** (shipped), **core/** (shared source), **dev/** (tooling)

```
plugins/          Shipped per-platform artifacts
  claude-code/    commands/, agents/, scripts/
  opencode/       commands/, src/, dist/
  kiro/           agents/, prompts/, steering/

core/             Shared source material
  templates/      *.md.template → plugins/*/commands|agents|steering
  line_loop/      Python package → bundled into plugins/claude-code/scripts/
  line-loop-cli.py  CLI wrapper source for bundling
docs/dev/
  line-loop-internals.md  Module architecture, data flow, and developer debug

dev/              Development tooling
  release.py, sync-commands.sh, check-*, doctor-*, validate-*
```

Data flow:

```
core/templates/commands/  ──sync──>  plugins/{claude-code,opencode,kiro}
core/templates/agents/    ──sync──>  plugins/{claude-code,kiro}
core/line_loop/           ──bundle──> plugins/claude-code/scripts/line-loop.py
```

See [Project Structure](docs/dev/project-structure.md) for full directory layout.

## Command Synchronization

Line Cook maintains commands for Claude Code (`plugins/claude-code/commands/`), OpenCode (`plugins/opencode/commands/`), and Kiro (`plugins/kiro/prompts/`). All are generated from shared templates to prevent drift.

**Template system:**
- Source templates live in `core/templates/commands/` (16 templates)
- Use placeholders for platform-specific differences:
  - `@NAMESPACE@` - Command prefix (`line:` for Claude Code, `line-` for OpenCode/Kiro)
  - `@IF_CLAUDECODE@`...`@ENDIF_CLAUDECODE@` - Claude Code only content
  - `@IF_OPENCODE@`...`@ENDIF_OPENCODE@` - OpenCode and Kiro shared content
  - `@IF_KIRO@`...`@ENDIF_KIRO@` - Kiro only content

**Platform differences handled automatically:**
- Claude Code: `/line:cook` (colon separator), includes `Skill()` calls and subagent details
- OpenCode: `/line-cook` (hyphen separator), simplified step numbering
- Kiro: `@line-cook` (at-sign prefix), same content as OpenCode but no YAML frontmatter

**Synced commands:** All 16 — architecture-audit, brainstorm, cook, decision, finalize, getting-started, help, loop, mise, plan-audit, plate, prep, run, scope, serve, tidy

### Agent Template Synchronization

Review agents are also generated from shared templates to prevent drift between Claude Code and Kiro.

**Agent template system:**
- Source templates live in `core/templates/agents/` (5 templates)
- Same conditional block syntax as commands: `@IF_CLAUDECODE@`, `@IF_KIRO@`
- No `@NAMESPACE@` substitution needed (agents don't reference command namespaces)
- No OpenCode output — OpenCode uses Claude Code's `plugins/claude-code/agents/` directory directly

**Platform differences handled automatically:**
- Claude Code: YAML frontmatter with `name`, `description`, `tools`, plus concise review format
- Kiro: No frontmatter (steering files only), includes context-loading instructions (`bd show`, `git diff`), detailed checklists, red flags, code examples, and anti-pattern sections

**Synced agents:** All 5 review agents — sous-chef, taster, maitre, polisher, critic

**NOT templatized:**
- Kiro JSON agent configs (`plugins/kiro/agents/*.json`) — platform-specific metadata
- Kiro orchestrator steering (line-cook.md) — routing table only, delegates to template-synced prompts
- Non-agent steering files (beads.md, session.md) — Kiro-only reference docs (CC equivalents in docs/guidance/ and AGENTS.md)

**When to sync:**
- After editing any command template
- Before committing command changes (pre-commit hook enforces this)
- As part of release process

```bash
./dev/sync-commands.sh
```

## Installation

See [README.md#installation](README.md#installation) for platform-specific installation instructions.

> **Important - Command Discovery:** Claude Code caches commands based on `plugin.json` version. After adding new commands, bump the version and run `/clear` in a new session.

## Testing

### Test Suite Overview

```
tests/
├── run-tests.sh              # Main orchestrator (--provider, --tier, --test)
├── test-getting-started.sh    # Unit: read-only guide output check
├── test-prep.sh               # Integration: sync + ready tasks
├── test-serve.sh              # Integration: headless review
├── test-tidy.sh               # Integration: commit + push
├── test-cook.sh               # Full: LLM task execution
├── test-work.sh               # Full: complete workflow cycle
├── lib/
│   ├── test-utils.sh          # Provider abstraction, logging, helpers
│   ├── setup-env.sh           # Isolated git+beads test environment
│   └── teardown-env.sh        # Cleanup
├── eval/
│   ├── eval.sh                # Eval orchestrator (matrix runner)
│   ├── eval-run.sh            # Single provider+scenario execution
│   ├── eval-narrative-run.sh  # Multi-step narrative runner
│   ├── eval-validate.sh       # Artifact validation checks
│   ├── eval-setup.sh          # Eval environment creation (demo-simple)
│   ├── eval-setup-planning.sh # Eval environment creation (demo-planning)
│   ├── eval-teardown.sh       # Eval environment cleanup
│   ├── eval-report.py         # Report generation (summary + per-step + compliance)
│   ├── lib/
│   │   ├── eval-provider.sh   # Enhanced provider invocation with metrics
│   │   └── narrative-utils.sh # Command loading, prompt building, agent validation
│   └── narratives/            # Narrative definitions
│       ├── onboard.sh         # getting-started + prep (read-only)
│       ├── single-task.sh     # prep → cook → serve → tidy
│       ├── task-chain.sh      # Two cycles + plate
│       ├── full-run.sh        # /run orchestrator
│       ├── planning.sh        # brainstorm → scope → finalize
│       └── recovery.sh        # Serve rejection + retry
└── results/eval/              # JSON results + report.md
```

### Running Tests

```bash
# Unit tests only (fast, read-only)
./tests/run-tests.sh --provider opencode --tier unit
./tests/run-tests.sh --provider kiro --tier unit

# Prompt eval scenarios (isolated environments, artifact validation)
./tests/eval/eval.sh --provider claude --scenario readonly --runs 1
./tests/eval/eval.sh --provider kiro --scenario analysis --runs 1

# Narrative eval scenarios (multi-step command workflows)
./tests/eval/eval.sh --scenario onboard --runs 1 --skip-missing
./tests/eval/eval.sh --scenario single-task --provider claude --runs 1
./tests/eval/eval.sh --scenario task-chain --provider claude --runs 1
./tests/eval/eval.sh --scenario planning --provider claude --runs 1

# Full report from existing results
./tests/eval/eval.sh --report-only
```

### Narrative Eval

Narrative scenarios test Line Cook's slash commands in realistic user journeys. Each narrative runs multiple steps (commands) in sequence against an isolated test environment.

**How it works:** Headless mode lacks native slash commands. Each step injects the command's markdown directly into the prompt so the LLM follows the command's instructions.

| # | Narrative | Commands Tested | Fixture |
|---|-----------|----------------|---------|
| 1 | `onboard` | getting-started, prep | demo-simple |
| 2 | `single-task` | prep, cook, serve, tidy | demo-simple |
| 3 | `task-chain` | prep, cook, serve, tidy (x2), plate | demo-simple |
| 4 | `full-run` | run | demo-simple |
| 5 | `planning` | brainstorm, scope, finalize | demo-planning |
| 6 | `recovery` | prep, cook, serve (reject), cook (retry) | demo-simple |

**Command coverage:**

| Command | Narratives |
|---------|-----------|
| getting-started | onboard |
| prep | onboard, single-task, task-chain, recovery |
| cook | single-task, task-chain, recovery |
| serve | single-task, task-chain, recovery |
| tidy | single-task, task-chain |
| plate | task-chain |
| run | full-run |
| brainstorm | planning |
| scope | planning |
| finalize | planning |

All providers are subscription-based; cost estimates in the report are informational only.

### Provider-Specific Testing Notes

**OpenCode** requires a pseudo-TTY to flush stdout during tool-call responses. All OpenCode invocations in the test harness use `script -q -c` as a wrapper. Without this, OpenCode buffers indefinitely when not attached to a terminal.

Override the default model with `OPENCODE_MODEL`:
```bash
OPENCODE_MODEL=deepseek/deepseek-chat ./tests/run-tests.sh --provider opencode --tier unit
```

**Kiro CLI** uses `@line-<command>` prompt syntax (not slash commands). The `get_provider_command` function in `test-utils.sh` maps command names to the correct provider-specific syntax:

| Provider | `--provider` flag | Command format | Example |
|----------|------------------|---------------|---------|
| Claude Code | `claude` | `/line:<command>` | `/line:getting-started` |
| OpenCode | `opencode` | `/line-<command>` | `/line-getting-started` |
| Kiro CLI | `kiro` | `@line-<command>` | `@line-getting-started` |

### Known Patterns

- **Bash arithmetic under `set -e`**: Use `VAR=$((VAR + 1))` instead of `((VAR++))`. When `VAR=0`, `((0++))` evaluates to 0 which is falsy, causing `set -e` to exit the script.
- **LLM non-determinism**: Unit tests use `MAX_RETRIES=2` to handle flaky LLM responses. If output doesn't match expected patterns on first try, the test retries.
- **Eval vs. unit tests**: Eval scenarios (readonly, analysis, implement, sequence) use isolated git repos and validate artifacts. Narrative eval scenarios test multi-step command workflows. Unit tests check command output patterns. Prefer eval for CI; unit tests are for quick smoke checks.

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
| `plugins/claude-code/.claude-plugin/plugin.json` | `version` |
| `plugins/opencode/package.json` | `version` AND `opencode.version` |
| `CHANGELOG.md` | New version section from [Unreleased] |

### Release Procedure

**Primary (release.py):**

```bash
./dev/release.py <version>            # Prepare release (interactive)
./dev/release.py <version> --push     # Prepare + push (triggers GH release)
./dev/release.py <version> --dry-run  # Preview what would change
./dev/release.py --check              # Validate current state only
./dev/release.py --bundle             # Bundle line_loop only (for dev testing)
```

The script handles: version sync across all manifests → CHANGELOG transformation → line_loop bundling → validation scripts → commit creation.

> **Note:** GitHub Actions automatically creates a release when `plugins/claude-code/.claude-plugin/plugin.json` is updated on `main`. See `.github/workflows/release.yml`.

**Manual (Fallback):**

Use only if release.py is broken or needs to be bypassed.

```bash
# 1. Determine version (semantic versioning)
#    Patch: bug fixes → 0.4.5 → 0.4.6
#    Minor: new features → 0.4.5 → 0.5.0
#    Major: breaking changes → 0.4.5 → 1.0.0

# 2. Update all version locations (must be identical)
#    - plugins/claude-code/.claude-plugin/plugin.json: "version"
#    - plugins/opencode/package.json: "version" AND "opencode.version"

# 3. Update CHANGELOG.md
#    - Create new section: ## [X.Y.Z] - YYYY-MM-DD
#    - Move entries from [Unreleased] to new section
#    - Update version comparison links at bottom

# 4. Bundle line_loop (easy to forget!)
python3 -c "from pathlib import Path; import sys; sys.path.insert(0, 'dev'); from release import bundle_line_loop; bundle_line_loop(Path('.'))"

# 5. Run validation
./dev/check-plugin-health.py --skip-changelog
./dev/check-platform-parity.py
./dev/doctor-docs.py

# 6. Commit and push
git add CHANGELOG.md plugins/claude-code/.claude-plugin/plugin.json plugins/opencode/package.json plugins/claude-code/scripts/line-loop.py
git commit -m "chore(release): vX.Y.Z"
bd sync
git push
```

### What to Track in CHANGELOG.md

The changelog is for **plugin users** — people who install Line Cook and use its commands/agents in their own projects.

**Track in [Unreleased]:**
- New or changed user-invocable commands (slash commands)
- Behavior changes users interact with directly
- New workflow capabilities users can invoke
- Breaking changes to existing user-facing features
- Bug fixes users would encounter in their workflows

**Don't track:**
- Documentation-only (README, AGENTS.md, docs/)
- CI/CD configuration and GitHub workflows
- .beads/ changes
- Test files only
- Evaluation/benchmarking tooling (eval/, harnesses)
- Developer-facing skills or contributor docs
- Template syncing or build infrastructure (sync scripts, bundling)
- Agent review rule changes (internal reviewer behavior)
- Dev scripts or tooling (dev/, scripts/)
- Internal refactoring with no user impact

**Litmus test:** Would a plugin user notice this change while using Line Cook in their project? If the answer is "only if they read the source code" or "only if they contribute to Line Cook," exclude it.

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
- Adding new commands (files in `plugins/claude-code/commands/`)
- Adding new agents (files in `plugins/claude-code/agents/`)
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