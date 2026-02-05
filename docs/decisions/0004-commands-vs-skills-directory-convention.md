---
status: accepted
date: 2026-02-04
tags: [commands, architecture]
relates-to: []
superseded-by: null
---

# 0004: Commands vs skills directory convention

## Context

Claude Code has evolved its terminology — `.claude/commands/` is now considered legacy, with `.claude/skills/` as the recommended format. The question arose whether `/decision` (and other project-local commands) should migrate from `.claude/commands/` to `.claude/skills/`.

Line Cook already uses both directories with a clear semantic split:

- `.claude/skills/` contains **passive knowledge bases** (acceptance-testing patterns, Python scripting guides, troubleshooting references) that inform agent behavior without being invoked directly.
- `.claude/commands/` contains **active workflow commands** (`smoke-test.md`, `decision.md`) with explicit step-by-step instructions invoked as `/slash-commands`.
- `commands/` contains **shipped plugin commands** (`prep.md`, `cook.md`, etc.).

Both formats produce identical slash-command behavior — Claude Code merges them internally. The advanced skill features (supporting files, `disable-model-invocation`, `context: fork`, `argument-hint`) are not needed by the current project-local commands.

## Decision

Keep project-local executable commands in `.claude/commands/` and passive knowledge in `.claude/skills/`. Do not migrate to the "everything is a skill" pattern that Claude Code recommends.

The project's convention maps to a real semantic difference (knowledge vs action) that is more useful than collapsing everything into one directory. Consistency between `smoke-test.md` and `decision.md` matters more than following upstream naming trends with no functional benefit.

## Consequences

- Positive: Clean separation between reference material and executable workflows; consistent with existing README documentation and project vocabulary
- Positive: No unnecessary churn — both formats work identically
- Negative: Diverges from Claude Code's official recommendation; new contributors familiar with the docs may expect `.claude/skills/` for everything
- Neutral: If advanced skill features are needed later, migration is straightforward (move file, adjust frontmatter)
