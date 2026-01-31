# Changelog

All notable changes to Line Cook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `/line:audit` command for bead hygiene checks
  - Validates bead structure, quality, and health
  - Scopes: `active` (default), `full`, or specific bead ID
  - Optional `--fix` flag for auto-fixable issues

### Changed
- Renamed `/line:plan` to `/line:scope` to avoid collision with Claude Code's native `/plan` command
  - Claude Code: `line:plan` → `line:scope`
  - OpenCode: `line-plan` → `line-scope`
  - Kiro: `@line-plan` → `@line-scope`
- `/line:audit` framed as optional hygiene tool, not mandatory workflow step
  - Removed from main workflow diagram sequence
  - Documented as "run periodically" rather than "after mise"

### Fixed
- `/line:cook` now always indicates `/line:serve` as next step (serve should never be skipped)
- Updated mermaid diagram to use `/scope` instead of `/plan`
- Fixed OpenCode tutorial `/mise` references
- Fixed workflow.md test output paths
- Updated mise.md to use 'Finalize' terminology consistently

### Documentation
- Added Part 10 to tutorial covering `/line:audit` usage
- Fixed tutorial accuracy issues and added plate phase documentation

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

[Unreleased]: https://github.com/smileynet/line-cook/compare/v0.8.3...HEAD
[0.8.3]: https://github.com/smileynet/line-cook/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/smileynet/line-cook/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/smileynet/line-cook/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/smileynet/line-cook/compare/v0.7.5...v0.8.0
[0.6.3]: https://github.com/smileynet/line-cook/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/smileynet/line-cook/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/smileynet/line-cook/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/smileynet/line-cook/releases/tag/v0.6.0
