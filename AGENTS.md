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

## Epic Philosophy

Epics organize related work into coherent groups. Line-cook uses a **child-based** model:

### Structure

```
Epic (parent)
├── Child task 1
├── Child task 2 (depends on Child 1)
├── Child task 3 (depends on Child 1)
└── Child task 4 (depends on Child 2, 3)
```

### Rules

1. **Epics contain children** - Use `--parent=<epic-id>` when creating tasks that belong to an epic
2. **Dependencies order children** - Use `bd dep add` to establish order within an epic
3. **Dependencies order epics** - Epics can depend on other epics for sequencing
4. **Cross-epic dependencies (rare)** - A child of one epic may block another epic when there's a genuine prerequisite

### Creating Epic Structure

```bash
# Create the epic
bd create --title="Implement auth system" --type=epic --priority=1

# Create children with --parent
bd create --title="Design auth flow" --type=task --parent=lc-abc
bd create --title="Implement login" --type=task --parent=lc-abc
bd create --title="Implement logout" --type=task --parent=lc-abc
bd create --title="Add session management" --type=task --parent=lc-abc

# Add dependencies between children for ordering
bd dep add lc-def lc-ghi   # "Implement login" depends on "Design auth flow"
bd dep add lc-jkl lc-ghi   # "Implement logout" depends on "Design auth flow"
bd dep add lc-mno lc-def   # "Session mgmt" depends on "Implement login"
bd dep add lc-mno lc-jkl   # "Session mgmt" depends on "Implement logout"
```

### Querying Epic Progress

```bash
bd epic status                    # Show all epics with child completion
bd epic status --eligible-only    # Show epics ready to close
bd list --parent=<epic-id>        # List children of an epic
bd list --parent=<epic-id> --all  # Include closed children
```

### When to Use Each Relationship

| Relationship | When to use |
|--------------|-------------|
| `--parent` | Task belongs to an epic (grouping) |
| `bd dep add` | Task must complete before another (ordering) |
| Epic depends on epic | One feature requires another feature first |
| Child blocks epic (rare) | Specific prerequisite from another group |

### Anti-patterns

- **Don't use dependencies instead of children** - If tasks belong together, use `--parent`
- **Don't create flat task lists** - Group related work into epics
- **Don't over-nest** - Epics should be shallow (1 level of children)

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

**Remote (from GitHub) - recommended for auto-updates:**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

Update: `/plugin update line`

**Local (from clone) - for development or offline use:**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook && ./scripts/install-claude-code.sh
```

Update: `cd ~/line-cook && git pull && ./scripts/install-claude-code.sh`

> **Note:** Local and remote installations are tracked separately.
> Local plugins show "To update, modify the source at: ./line" and cannot use `/plugin update`.
> To switch from local to remote, uninstall first: `/plugin uninstall line`

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

## Release Process

**When making changes to core functionality** (commands, hooks, plugin manifests, workflow logic), you MUST bump the version and push updates.

### Files Requiring Version Update

| File | Field(s) |
|------|----------|
| `.claude-plugin/plugin.json` | `version` |
| `line-cook-opencode/package.json` | `version` AND `opencode.version` |

### Version Bump Procedure

```bash
# 1. Determine version (semantic versioning)
#    Patch: bug fixes → 0.4.5 → 0.4.6
#    Minor: new features → 0.4.5 → 0.5.0
#    Major: breaking changes → 0.4.5 → 1.0.0

# 2. Update all version locations (must be identical)
#    - .claude-plugin/plugin.json: "version"
#    - line-cook-opencode/package.json: "version" AND "opencode.version"

# 3. Commit and push
git add .claude-plugin/plugin.json line-cook-opencode/package.json
git commit -m "chore: bump version to X.Y.Z"
bd sync
git push
```

### When to Bump Version

**DO bump for:**
- Command changes (commands/*.md)
- Hook changes (hooks/*.py, src/*.ts)
- Plugin manifest changes
- Core workflow logic

**DON'T bump for:**
- Documentation-only (README, AGENTS.md, docs/)
- CI/CD configuration
- .beads/ changes
- Test files only
