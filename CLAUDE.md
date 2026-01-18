# line-cook

Task-focused workflow orchestration for Claude Code sessions.

## Overview

line-cook provides a structured workflow for AI-assisted development:

```
/prep  →  /cook  →  /serve  →  /tidy
  ↓         ↓         ↓         ↓
 sync    execute    review    commit
```

Or use `/work` to run the full cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/prep` | Sync git, load context, show available work |
| `/cook` | Select and execute a task with guardrails |
| `/serve` | Review completed work via headless Claude |
| `/tidy` | Commit and push changes |
| `/work` | Orchestrate full prep→cook→serve→tidy cycle |

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** - AI coding assistant

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Project Structure

```
line-cook/
├── commands/           # Slash command definitions
│   ├── prep.md
│   ├── cook.md
│   ├── serve.md
│   ├── tidy.md
│   └── work.md
├── skills/
│   └── workflows/      # Supporting skills
├── scripts/            # Hook scripts
└── .claude-plugin/
    └── plugin.json     # Plugin manifest
```

## Installation

```bash
# Add to Claude Code plugins
claude plugins add /path/to/line-cook
```

## Related

- [beads](https://github.com/smileynet/beads) - Issue tracking
- [meta-claude](https://github.com/smileynet/meta-claude) - Claude Code documentation
