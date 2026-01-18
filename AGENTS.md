# Line Cook

> See [README.md](README.md) for philosophy, influences, and user documentation.

Technical details for working on Line Cook itself.

## Overview

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
| `/setup` | Configure hooks for your project (interactive) |

## Platform Command Naming

Claude Code and OpenCode use different command naming conventions:

| Platform | Syntax | Example |
|----------|--------|---------|
| Claude Code | `namespace:command` | `/line:prep` |
| OpenCode | `namespace-command` | `/line-prep` |

This is a fundamental platform difference, not a design choice. Each platform discovers and registers commands differently:

- **Claude Code**: Uses `plugin.json` namespace + flat filename → `line:prep`
- **OpenCode**: Uses file path as command name → `line-prep`

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work
- **Claude Code** or **OpenCode** - AI coding assistant

## Workflow Principles

1. **Sync before work** - Always start with current state
2. **Track with beads** - Strategic work lives in issue tracker
3. **Guardrails on completion** - Verify before marking done
4. **Push before stop** - Work isn't done until pushed
5. **File, don't block** - Discovered issues become beads, not interruptions

## Beads Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Session Completion (Landing the Plane)

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File issues for remaining work** - Create beads for anything needing follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** - All changes committed AND pushed

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- If push fails, resolve and retry until it succeeds

## Project Structure

```
line-cook/
├── commands/              # Claude Code command definitions
│   ├── getting-started.md # → /line:getting-started
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   ├── tidy.md            # → /line:tidy
│   ├── work.md            # → /line:work
│   └── setup.md           # → /line:setup
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
│       ├── line-work.md   # → /line-work
│       └── line-setup.md  # → /line-setup
├── hooks/                 # Claude Code hooks
│   ├── setup.sh           # Onboarding: detect project, generate hooks
│   ├── session-start.sh   # SessionStart: prime workflow context
│   ├── pre-tool-use-bash.sh # PreToolUse: block dangerous commands
│   ├── post-tool-use-edit.sh # PostToolUse: auto-format (template)
│   ├── stop-workflow-check.sh # Stop: verify work is saved
│   └── settings.json      # Hook configuration (template)
├── .claude-plugin/
│   ├── plugin.json        # Claude Code plugin manifest
│   └── marketplace.json   # Marketplace definition for GitHub install
├── AGENTS.md              # Agent workflow instructions (this file)
├── HOOKS.md               # Hooks documentation
└── TESTING.md             # Testing guide for both platforms
```

## Installation

### Claude Code

**Online (from GitHub):**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

**Offline (local clone):**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
/plugin marketplace add line-cook --source directory --path ~/line-cook
/plugin install line@line-cook
```

**Updating:**
```bash
/plugin update line
```

Commands: `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:work`, `/line:setup`

### OpenCode

**Online (from GitHub):**
```bash
opencode plugin install https://github.com/smileynet/line-cook
```

**Offline (local clone):**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook/line-cook-opencode && ./install.sh
```

Commands: `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-work`, `/line-setup`

## Hooks (Optional)

Claude Code hooks can automate workflow stages. Run `/line:setup` to configure interactively, or see [HOOKS.md](HOOKS.md) for manual setup.

Available hooks:
- SessionStart: Auto-prime beads workflow context
- PreToolUse: Block dangerous commands
- PostToolUse: Auto-format edited files
- Stop: Verify work is committed/pushed

## Testing

See [TESTING.md](TESTING.md) for validation and testing methods.
