# Changelog Guide

> Track what's different between releases.

Guidelines for maintaining a clear, useful changelog. Based on [Keep a Changelog](https://keepachangelog.com) specification.

## The Kitchen Analogy

Think of a changelog like the menu board showing what's new:

| Change Type | Kitchen Equivalent |
|-------------|-------------------|
| Added | New dish on the menu |
| Changed | Recipe revision |
| Fixed | Fixed a broken recipe |
| Deprecated | Seasonal item being phased out |
| Removed | 86'd from the menu |
| Security | Kitchen safety update |

The changelog tells guests (users) what's different since their last visit.

## Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature descriptions

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

## [1.0.0] - 2026-01-21

### Added
- Initial release features

[Unreleased]: https://github.com/user/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

## Guiding Principles

**Changelogs are for humans, not machines.**

- Entry for every version
- Group same types of changes
- Versions and sections are linkable
- Latest version comes first
- Display release date
- Follow Semantic Versioning

## Types of Changes

Use these categories consistently:

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Now removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

## Best Practices

### Write for Humans

**Do:**
- Use plain language
- Explain what changed and why
- Highlight user benefits
- Include examples when helpful

**Don't:**
- Use technical jargon without explanation
- Dump git commit logs
- Assume technical knowledge

**Example:**
```markdown
### Added
- Workflow automation. Run the full prep → cook → serve → tidy
  cycle with a single command.
```

### Keep an Unreleased Section

Track upcoming changes at the top:

```markdown
## [Unreleased]

### Added
- Task auto-selection
- Code review integration

### Fixed
- Session cleanup on timeout
```

At release time, move Unreleased content to a new version section.

### Use ISO 8601 Dates

Format: `YYYY-MM-DD` (e.g., `2026-01-21`)

- Unambiguous across regions
- Sorts chronologically
- ISO standard

### Document All Notable Changes

**Include:**
- New features (Added)
- Breaking changes (Changed with note)
- Bug fixes (Fixed)
- Deprecations (Deprecated)
- Security fixes (Security)

**Exclude:**
- Whitespace changes
- Internal refactoring (unless user-visible)
- Documentation typos
- Development tooling updates

### Highlight Breaking Changes

Make breaking changes obvious:

```markdown
## [2.0.0] - 2026-02-01

### Changed
- **BREAKING**: Config format changed from YAML to JSON.
  See migration guide in docs/migration/v2.md
```

### Link Versions

Include comparison links at bottom:

```markdown
[Unreleased]: https://github.com/user/project/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/project/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/user/project/releases/tag/v0.9.0
```

## Anti-patterns

### Commit Log Dumps

**Bad:**
```markdown
### Changed
- fix typo
- update deps
- refactor session manager
- merge PR #42
```

**Good:**
```markdown
### Changed
- Improved session cleanup reliability
- Updated dependencies for security patches
```

### Overly Technical Language

**Bad:**
```markdown
### Changed
- Refactored the worktree manager singleton to use dependency injection
  with interface-based polymorphism
```

**Good:**
```markdown
### Changed
- Improved worktree manager testability and flexibility
```

### Ignoring Deprecations

**Bad:**
```markdown
## [2.0.0] - 2026-02-01

### Removed
- Old config format (no warning in v1.x)
```

**Good:**
```markdown
## [1.5.0] - 2026-01-15

### Deprecated
- YAML config format. Use JSON instead. YAML support will be
  removed in v2.0.0. See docs/migration.md

## [2.0.0] - 2026-02-01

### Removed
- YAML config format (deprecated in v1.5.0)
```

### Sporadic Updates

**Bad:**
- Last update 6 months ago
- Multiple versions released without changelog updates
- Users discover changes by accident

**Good:**
- Update changelog with every release
- Keep Unreleased section current
- Regular, predictable updates

### Lack of Visibility

**Bad:**
- Changelog buried in docs/internal/
- No link from README
- Hard to find

**Good:**
- CHANGELOG.md in project root
- Linked from README
- Mentioned in release notes

### Not Highlighting Value

**Bad:**
```markdown
### Changed
- Updated UI
```

**Good:**
```markdown
### Changed
- Redesigned task status UI for faster scanning. Status indicators
  now use color and icons, reducing time to identify blocked tasks.
```

### Inconsistent Formatting

**Bad:**
```markdown
### Added
New feature X

### Changed
- Improved Y
- Updated Z

### Fixed
Fixed bug in A. Also fixed B.
```

**Good:**
```markdown
### Added
- New feature X with detailed description

### Changed
- Improved Y for better performance
- Updated Z to support new use cases

### Fixed
- Bug in A causing crashes on timeout
- Bug in B preventing cleanup
```

## Line Cook-Specific Guidelines

### Feature Releases

When completing a feature (multiple tasks):

```markdown
## [0.2.0] - 2026-01-25

### Added
- Full workflow automation. Run the complete sync → execute → review → commit
  cycle with a single command.
  - Automatic task selection
  - TDD cycle integration
  - Code review before commit
  - Push verification
```

### Task Releases

For individual task completions:

```markdown
## [Unreleased]

### Added
- Git sync on session start (lc-abc.1)
- Task auto-selection (lc-abc.2)
```

### Breaking Changes

Always document with migration path:

```markdown
## [2.0.0] - 2026-03-01

### Changed
- **BREAKING**: Configuration format changed. The `workflow.style`
  field is now required. Update configs:
  ```yaml
  workflow:
    style: vertical  # Add this line
  ```
```

## Maintenance

### Regular Updates

- Update Unreleased section with each merged PR
- Create version section on release
- Update comparison links
- Review for clarity before release

### Version Numbering

Follow [Semantic Versioning](https://semver.org):

- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features (backward compatible)
- **PATCH** (1.0.0 → 1.0.1): Bug fixes (backward compatible)

### Yanked Releases

If a release must be pulled:

```markdown
## [1.0.5] - 2026-01-20 [YANKED]

### Fixed
- Critical issue in session management

**Note**: This version was yanked due to a critical bug. Use 1.0.6 instead.
```

## Quick Checklist

Before releasing:

- [ ] All notable changes documented
- [ ] Changes categorized correctly
- [ ] User-friendly language used
- [ ] Breaking changes highlighted
- [ ] Version number follows SemVer
- [ ] Release date in ISO 8601 format
- [ ] Comparison links updated
- [ ] Unreleased section cleared

## References

- [Keep a Changelog](https://keepachangelog.com) - Format specification
- [Semantic Versioning](https://semver.org) - Version numbering
- [Conventional Commits](https://conventionalcommits.org) - Commit format for automation

## Related

- [Workflow](./workflow.md) - Overall workflow structure
- [Priorities](./priorities.md) - How to prioritize changes
- [Scope Management](./scope-management.md) - Managing change scope
