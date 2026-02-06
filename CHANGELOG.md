# Changelog

All notable changes to Line Cook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.3] - 2026-02-06
### Fixed
- Fixed duplicate bundling bug in release.py that caused line-loop.py to be ~7000 lines instead of ~3600

## [0.9.2] - 2026-02-06
### Fixed
- `/line:loop` now works after marketplace installation
  - The `line_loop/` package was not being synced by Claude Code's plugin system
  - Added bundling step to `release.py` that creates a self-contained `line-loop.py`
- Changed `python` to `python3` in loop.md for Linux compatibility

## [0.9.1] - 2026-02-05
### Added
- `/line:architecture-audit` command for codebase structure and quality analysis
  - Validates project health via scripts, detects code smells, and generates optional reports
  - Scopes: `quick` (validation scripts only), `full` (includes metrics), or specific path
  - Complements `/line:plan-audit` (beads/plans) with codebase-level hygiene checks
- `critic` agent for epic-level end-to-end and smoke test review
  - Completes testing review hierarchy: `taster` (unit) → `maître` (acceptance) → `critic` (epic)
  - Validates test coverage across features and integration points
  - Architecture Decision Record 0010 documents epic-level testing guidance

### Changed
- Renamed `/line:audit` → `/line:plan-audit` to clarify scope (audits beads and plans, not code)
- README restructured following Diataxis framework for better navigation
  - Tutorials, how-to guides, reference, and explanation sections clearly separated
  - Condensed content with improved discoverability

## [0.9.0] - 2026-02-04
### Added
- `/line:decision` project command for managing architecture decision records (ADRs)
  - Create, list, view, and supersede decisions with markdown templates
  - Initial set of ADRs (0001-0009) documenting existing project conventions
- `demo-web` project template with 16 beads (9 tasks across 4 features) for building a Go + Templ + SQLite dashboard
  - Includes planning context artifacts (brainstorm, architecture, decisions log, menu plan)
- Interactive handoff prompts in planning commands (brainstorm → scope → finalize → prep)
  - Each phase prompts the user to continue, review, or stop instead of passive NEXT STEP text
  - Planning context persists across sessions in `docs/planning/context-<name>/` folders
- `/line:help` command for contextual command discovery
  - Detects workspace state (beads present, task counts, git status)
  - Suggests the most relevant next command based on context
- Language-agnostic `/line:plate` and testing documentation
  - Multi-language examples (Go, Python, JS/TS, Rust) with progressive disclosure
  - New `acceptance-testing` skill with cross-language BDD patterns
- Line-loop daemon enhancements:
  - Real-time progress tracking in status.json (current phase, action counts during long iterations)
  - Idle detection with `--idle-timeout` and `--idle-action` flags
  - `KITCHEN_IDLE` signal when no actionable work remains (clean exit)
  - Configurable per-phase timeouts (`--cook-timeout`, `--serve-timeout`, `--tidy-timeout`, `--plate-timeout`)
  - Skip list to prevent retry spirals on repeatedly failing tasks
  - Cook phase receives structured feedback from failed reviews for targeted rework
- Loop UX overhaul with improved terminal output:
  - Iteration headers with progress counters and ready-task counts
  - Phase dot indicators showing action density and duration
  - Bead delta tracking (newly closed/filed items after each iteration)
  - Task hierarchy display (parent feature/epic context)
  - Feature completion banners
- Enhanced `/line:loop` documentation with architecture diagrams, troubleshooting guides, and module reference

### Changed
- `/line:mise` now uses interactive handoff chain instead of running all phases sequentially
- Existing `demo` template renamed to `demo-simple`

### Fixed
- Serve phase now runs after cook timeout when the task was actually completed (code review was being incorrectly skipped)
- Corrected invalid status values in documentation (`--status=pending` → `--status=open`)

## [0.8.6] - 2026-02-01
### Changed
- `sous-chef` agent enhanced with detailed step-by-step review process and proactive invocation examples
- All review agents (`sous-chef`, `taster`, `maitre`) now use Opus model for higher quality reviews

## [0.8.5] - 2026-02-01
### Added
- `/line:loop` command for managing autonomous loop execution from TUI
  - `start` - Launch line-loop.py in background with configurable iterations/timeout
  - `status` - Check current loop progress via live status JSON
  - `stop` - Graceful shutdown via SIGTERM
  - `tail` - View recent log output
  - Project-specific temp directories (`/tmp/line-loop-<project>/`) for isolation
- `line-loop.py` now supports `--pid-file` and `--status-file` for external process management
- `/line:plan-audit` command for bead hygiene checks (renamed from `/line:audit`)
  - Validates bead structure, quality, and health
  - Scopes: `active` (default), `full`, or specific bead ID
  - Optional `--fix` flag for auto-fixable issues
- `/line:architecture-audit` command for codebase quality analysis
  - Runs validation scripts and detects code smells
  - Scopes: `quick` (scripts only), `full` (metrics + smells), or specific path
  - Optional `--report` flag to generate dated report
- `watch` subcommand for live progress with milestones and context
- `history` subcommand for viewing iteration history with action details
- Smart default behavior (no args: watch if running, start if not)
- Action-level visibility tracking every tool call during iterations
- Progress reporting with before/after state snapshots
- Circuit breaker to prevent runaway failures (5 consecutive in 10-iteration window)
- Epic completion detection and celebration workflow
- `--history-file` option for JSONL action recording

### Changed
- Renamed `/line:plan` to `/line:scope` to avoid collision with Claude Code's native `/plan` command
  - Claude Code: `line:plan` → `line:scope`
  - OpenCode: `line-plan` → `line-scope`
  - Kiro: `@line-plan` → `@line-scope`
- `/line:loop` documentation completely revamped with Quick Start guide
- `/line:tidy` enhanced with improved bead creation patterns and kitchen report

### Fixed
- `/line:cook` now always indicates `/line:serve` as next step (serve should never be skipped)
- Circuit breaker now resets on successful iteration
- Serve verdict retry on parse failure (full cook→serve cycle retry)
- After-snapshot safety fallback when bead commands fail
- Action tracking uses ERROR: prefix for failed tool calls

## [0.8.3] - 2026-01-30
### Fixed
- OpenCode `/line-serve` now correctly loops back to `/line-cook` when verdict is `needs_changes`
  (ported fix from Claude Code to OpenCode platform)

## [0.8.2] - 2026-01-30
### Added
- `/line:brainstorm`, `/line:plan`, and `/line:finalize` commands for phased menu planning
  - Brainstorm: divergent exploration and research
  - Plan: convergent scoping and task decomposition
  - Finalize: create beads, write BDD/TDD specs
- Release automation with `scripts/release.py` and `release-editor` agent
  - Automates version sync across plugin files
  - Handles CHANGELOG transformation
  - Interactive changelog quality review

### Fixed
- `/line:serve` now correctly loops back to `/line:cook` when review verdict is `needs_changes`
  (previously continued toward tidy, losing the rework loop)

### Changed
- `/line:mise` now orchestrates brainstorm → plan → finalize with review pauses between phases

## [0.8.1] - 2026-01-28

### Added
- Kiro platform configuration with kitchen-manager orchestration prompts

### Changed
- Consolidated `/line:run` command (removed `/line:work` and `/line:service` aliases)
- Moved Quick Start section earlier in README for better discoverability

### Fixed
- NEEDS_CHANGES verdict now properly loops back to cook phase for rework
- Updated Kiro prompts to handle NEEDS_CHANGES rework loop correctly
- Fixed `/line:plan` references to use correct `/line:mise` command name

### Documentation
- Updated AGENTS.md to match actual repository structure
- Removed obsolete CAPSULE_MIGRATION_PLAN.md

### Internal
- Added stale test directory cleanup in smoke tests
- Rebuilt opencode plugin with latest changes

## [0.8.0] - 2026-01-26

### Added
- `/line:mise` command for menu planning with tracer dish methodology
- `/line:plate` command for BDD feature validation (acceptance criteria testing)
- `/line:run` command for full-service workflow orchestration
- Claude Code subagent system with specialized review agents:
  - `taster` agent for test quality review during TDD RED phase
  - `sous-chef` agent for code review during serve phase
  - `maître` agent for BDD test quality review during plate phase
- Hierarchical context display in prep phase (shows epic/feature/task relationships)
- OpenCode integration with synchronized commands
- Kiro integration with kitchen-manager orchestration agent
- Comprehensive guidance documentation:
  - TDD/BDD workflow integration
  - Menu changes and recipe planning
  - Core workflow structure
- Project health maintenance scripts:
  - `check-platform-parity.py` - Validate command/agent consistency across platforms
  - `check-plugin-health.py` - Version sync and plugin currency validation
  - `doctor-docs.py` - Documentation validation and link checking
- `/smoke-test` command for end-to-end Line Cook workflow validation
  - Isolated test environment with ephemeral git repos
  - 10 proof-of-work validation checks
  - Workflow integrity validation (TDD cycle, code review, commit format)

### Changed
- Smoke test now validates workflow integrity, not just code artifacts
- Renamed `dessert` phase to `plate` throughout documentation and commands
- Updated documentation with consistent kitchen theming throughout
- Enhanced workflow descriptions to use kitchen metaphor (orders, recipes, dishes)
- TDD cycle integrated into cook workflow with RED-GREEN-REFACTOR phases
- Headless reviews now use verdict-based blocking (approved/needs_changes/blocked)

### Fixed
- Removed deprecated `lc` CLI references from documentation and plugin description
- Agent frontmatter now includes required fields for Claude Code compliance
- Fixed broken internal documentation links in OpenCode plugin

### Deprecated
- `lc` CLI binary - use `/line:*` slash commands instead

## [0.6.3] - 2026-01-19

### Added
- `/line:doctor` command to validate hook configurations and detect orphaned configs
- `hooks/line_doctor.py` validation script with cross-platform support

## [0.6.2] - 2026-01-19

### Added
- CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format

### Changed
- Release notes now extract human-written entries from CHANGELOG.md
- Simplified release notes with links to documentation instead of duplicated command list

## [0.6.1] - 2026-01-19

### Added
- Dynamic release changelog generation from git commits
- SessionStart and PreCompact hooks for automatic context loading
- `/line:compact` command for workflow-aware context compaction

### Fixed
- Release workflow now has correct permissions for creating releases

## [0.6.0] - 2026-01-19

### Added
- `/line:setup` command for interactive hook configuration
- `/line:getting-started` beginner tutorial
- Pre-push git hook for session completion enforcement
- GitHub Actions workflow for automated releases

### Changed
- Expanded tutorial with propose-review-approve pattern
- Improved brainstorming section documentation

[Unreleased]: https://github.com/smileynet/line-cook/compare/v0.9.3...HEAD
[0.9.3]: https://github.com/smileynet/line-cook/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/smileynet/line-cook/compare/v0.9.1...v0.9.2
[0.9.1]: https://github.com/smileynet/line-cook/compare/v0.9.0...v0.9.1
[0.9.0]: https://github.com/smileynet/line-cook/compare/v0.8.6...v0.9.0
[0.8.6]: https://github.com/smileynet/line-cook/compare/v0.8.5...v0.8.6
[0.8.5]: https://github.com/smileynet/line-cook/compare/v0.8.4...v0.8.5
[0.8.3]: https://github.com/smileynet/line-cook/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/smileynet/line-cook/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/smileynet/line-cook/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/smileynet/line-cook/compare/v0.7.5...v0.8.0
[0.6.3]: https://github.com/smileynet/line-cook/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/smileynet/line-cook/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/smileynet/line-cook/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/smileynet/line-cook/releases/tag/v0.6.0
