# line-cook

Task-focused workflow orchestration for Claude Code and OpenCode sessions.

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

## Platform Command Naming

Claude Code and OpenCode use different command naming conventions:

| Platform | Syntax | Example |
|----------|--------|---------|
| Claude Code | `namespace:command` | `/line:prep` |
| OpenCode | `namespace-command` | `/line-prep` |

This is a fundamental platform difference, not a design choice. Each platform discovers and registers commands differently:

- **Claude Code**: Uses `plugin.json` namespace + flat filename → `line:prep`
- **OpenCode**: Uses file path as command name → `line-prep`

Folder structures cannot unify this (Claude Code doesn't traverse subfolders; OpenCode creates `/folder/command` slash syntax).

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** or **OpenCode** - AI coding assistant

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Project Structure

```
line-cook/
├── commands/              # Claude Code command definitions
│   ├── getting-started.md # → /line:getting-started
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   ├── tidy.md            # → /line:tidy
│   └── work.md            # → /line:work
├── scripts/               # Installation scripts
│   └── install-claude-code.sh
├── line-cook-opencode/    # OpenCode plugin
│   ├── package.json       # Plugin manifest
│   ├── install.sh         # Installation script
│   ├── AGENTS.md          # Agent instructions (bundled)
│   └── commands/          # OpenCode command definitions
│       ├── line-prep.md   # → /line-prep
│       ├── line-cook.md   # → /line-cook
│       ├── line-serve.md  # → /line-serve
│       ├── line-tidy.md   # → /line-tidy
│       └── line-work.md   # → /line-work
├── skills/
│   └── workflows/         # Supporting skills
├── .claude-plugin/
│   └── plugin.json        # Claude Code plugin manifest
├── AGENTS.md              # Agent workflow instructions
└── TESTING.md             # Testing guide for both platforms
```

## Installation

### Claude Code

**First-time setup:**
```bash
# Add marketplace (one-time)
/plugin marketplace add line-cook-marketplace --source directory --path /path/to/line-cook

# Install plugin
/plugin install line@line-cook-marketplace
```

**Updating after source changes:**
```bash
# Sync source to marketplace
./scripts/install-claude-code.sh

# Update plugin cache
/plugin update line
```

Commands available as: `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:work`

### OpenCode

```bash
# Run the install script
cd /path/to/line-cook/line-cook-opencode
./install.sh

# Commands available as: /line-prep, /line-cook, /line-serve, /line-tidy, /line-work
```

## Testing

See [TESTING.md](TESTING.md) for validation and testing methods.

## Related

- [beads](https://github.com/smileynet/beads) - Issue tracking
- [meta-claude](https://github.com/smileynet/meta-claude) - Claude Code documentation
