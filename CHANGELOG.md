# Changelog

All notable changes to Line Cook will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `/line:season` command to apply research findings to beads

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
