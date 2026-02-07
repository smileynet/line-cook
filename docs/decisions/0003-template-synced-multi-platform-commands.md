---
status: accepted
date: 2026-01-22
tags: [architecture, commands]
relates-to: []
superseded-by: null
---

# 0003: Template-synced multi-platform commands

## Context

Line Cook supports three AI coding platforms: Claude Code, OpenCode, and Kiro CLI. Each platform has different command syntax (colon vs hyphen separators), different CLI tool names, and minor behavioral differences. Maintaining separate command files per platform leads to drift — a bug fix in one platform's command doesn't propagate to others.

Options considered:
- **Separate codebases** — each platform gets independently maintained commands; maximum flexibility but guaranteed drift
- **Single source with runtime detection** — one command file adapts at runtime; not possible since platforms read static markdown
- **Template system with sync script** — source templates use placeholders (`@NAMESPACE@`, conditional blocks); a sync script generates platform-specific versions

## Decision

We will use a template system with a sync script (`scripts/sync-commands.sh`) because it maintains a single source of truth while accommodating platform differences through placeholder substitution. Templates live in `commands/templates/`, and the sync script generates Claude Code, OpenCode, and Kiro versions. Platform-specific additions (like OpenCode's `/line-run` instruction) are handled as template conditionals. A pre-commit hook enforces that generated files stay in sync with templates.

## Consequences

- Positive: Single source of truth prevents drift across all three platforms
- Positive: Bug fixes and improvements propagate to all platforms automatically
- Positive: Platform differences are explicit and documented via placeholders
- Positive: Pre-commit sync guard catches out-of-sync generated files before they're committed
- Positive: Kiro support added as third sync target with minimal overhead — shares OpenCode content via `@IF_OPENCODE@` blocks, uses `@line-` namespace, strips YAML frontmatter
- Negative: Adding a new synced command requires updating the template system
