# Changelog

All notable changes to Line Cook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `/line:plan` command for menu planning with tracer dish methodology
- `/line:plate` command for BDD feature validation (acceptance criteria testing)
- `/line:season` command to apply research findings to beads
- `/line:service` command for full-service workflow orchestration
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

### Changed
- Renamed `dessert` phase to `plate` throughout documentation and commands
- Updated documentation with consistent kitchen theming throughout
- Enhanced workflow descriptions to use kitchen metaphor (orders, recipes, dishes)
- TDD cycle integrated into cook workflow with RED-GREEN-REFACTOR phases
- Headless reviews now use verdict-based blocking (approved/needs_changes/blocked)

### Fixed
- Removed deprecated `lc` CLI references from documentation and plugin description
- Agent frontmatter now includes required fields for Claude Code compliance

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

[Unreleased]: https://github.com/smileynet/line-cook/compare/v0.6.3...HEAD
[0.6.3]: https://github.com/smileynet/line-cook/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/smileynet/line-cook/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/smileynet/line-cook/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/smileynet/line-cook/releases/tag/v0.6.0
