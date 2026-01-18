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
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   └── tidy.md            # → /line:tidy
├── line-cook-opencode/    # OpenCode plugin
│   ├── package.json       # Plugin manifest
│   ├── install.sh         # Installation script
│   ├── AGENTS.md          # Agent instructions (bundled)
│   └── commands/          # OpenCode command definitions
│       ├── line-prep.md   # → /line-prep
│       ├── line-cook.md   # → /line-cook
│       ├── line-serve.md  # → /line-serve
│       └── line-tidy.md   # → /line-tidy
├── skills/
│   └── workflows/         # Supporting skills
├── scripts/               # Hook scripts
├── .claude-plugin/
│   └── plugin.json        # Claude Code plugin manifest
├── AGENTS.md              # Agent workflow instructions
└── TESTING.md             # Testing guide for both platforms
```

## Installation

### Claude Code

```bash
# Load plugin from local directory
claude --plugin-dir /path/to/line-cook

# Commands available as: /line:prep, /line:cook, /line:serve, /line:tidy
```

### OpenCode

```bash
# Run the install script
cd /path/to/line-cook/line-cook-opencode
./install.sh

# Commands available as: /line-prep, /line-cook, /line-serve, /line-tidy
```

## Testing

See [TESTING.md](TESTING.md) for validation and testing methods.

## Related

- [beads](https://github.com/smileynet/beads) - Issue tracking
- [meta-claude](https://github.com/smileynet/meta-claude) - Claude Code documentation
