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

- Include an entry for every version
- Group same types of changes
- Make versions and sections linkable
- List latest version first
- Include release date
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

### Focus on User Value

Every changelog entry should answer one of two questions: **"What can users now do?"** or **"What problem does this solve?"** Lead with the value, not the implementation.

**Do:**
- Start with what changed for the user
- Explain _why_ this matters
- Use active language ("you can now...", "no longer crashes when...")

**Don't:**
- Lead with internal mechanism names
- List implementation details without explaining user impact
- Use jargon the user would need to read source code to understand

**Before (too technical):**
```markdown
### Added
- Line Loop Process Optimization (lc-egd)
  - Correct loop failure handling: circuit breaker, skip list, and escalation
    for repeated task failures (lc-egd.1)
  - Reduced iteration overhead: cached hierarchy maps and snapshot-first
    task selection (lc-egd.2)
```

**After (user-value-focused):**
```markdown
### Added
- `/loop` now automatically skips tasks that repeatedly fail instead of
  retrying them indefinitely, and escalates when too many failures pile up
- `/loop` iterations start faster — task selection uses cached snapshots
  instead of querying the tracker on every cycle
```

**Litmus test:** Would a plugin user notice this change while using Line Cook in their project? If the answer is "only if they read the source code" or "only if they contribute to Line Cook," exclude it.

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

### Audience: Plugin Users

The changelog is for **plugin users** — people who install Line Cook into their editor and use its commands/agents in their own projects. Filter every entry through this lens.

**Include** (user-facing plugin functionality):
- New user-invocable commands (slash commands)
- Changes to command/agent behavior that users interact with directly
- New workflow capabilities users can invoke
- Breaking changes to existing user-facing features
- Bug fixes users would encounter in their workflows

**Exclude** (internal/dev tooling):
- Evaluation/benchmarking tooling (`eval/`, harnesses, test infrastructure)
- Developer-facing skills or documentation (guidance docs, contributor patterns)
- Template syncing or build infrastructure (sync scripts, bundling changes)
- Agent review rule changes (what agents check for internally)
- New dev scripts or tooling (`dev/`, `scripts/`)
- CI/workflow changes
- Documentation updates (unless user-facing command docs)
- .beads/ changes (sync commits, metadata updates)
- Test-only changes (new/modified tests with no user-facing code change)
- Internal refactoring with no user impact

**Examples:**

Good (user value clear):
- `/prep` shows "READY TO CLOSE" section when completed features are waiting
- Running `/loop` with no arguments automatically shows status if already running, or starts a new loop if not

Bad (too technical / internal):
- "Action-level visibility tracking every tool call during iterations"
- "README restructured following Diataxis framework"
- "Local development install instructions in AGENTS.md for all three platforms"

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
- Changelog last updated 6 months ago
- Multiple versions released without changelog entries
- Users discover changes by accident

**Good:**
- Changelog updated with every release
- Unreleased section kept current
- Updates are regular and predictable

### Lack of Visibility

**Bad:**
- Changelog buried in `docs/internal/`
- Not linked from README
- Hard to find

**Good:**
- Changelog lives in project root as `CHANGELOG.md`
- Linked from README
- Referenced in release notes

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

- Update the Unreleased section with each merged PR
- Create a version section on release
- Update comparison links at the bottom of the file
- Review entries for clarity before release

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
- [ ] Version number set per SemVer
- [ ] Release date formatted as ISO 8601
- [ ] Comparison links updated
- [ ] Unreleased section cleared

## References

- [Keep a Changelog](https://keepachangelog.com) - Format specification
- [Semantic Versioning](https://semver.org) - Version numbering
- [Conventional Commits](https://conventionalcommits.org) - Commit format for automation

## Related

- [Run Cycle](../cycles/run-cycle.md) - Overall workflow structure
- [FAQ — Work Organization](../faq.md#work-organization) - Priorities and scope management
- [Release Editor Agent](../../.claude/agents/release-editor.md) - Interactive release coordinator that drafts and reviews changelogs
