# Line Cook

Task-focused workflow orchestration for AI-assisted development.

## Overview

```
/prep  →  /cook  →  /serve  →  /tidy
  ↓         ↓         ↓         ↓
 sync    execute    review    commit
```

Or use `/line-work` to run the full cycle.

## Commands

| Command | Purpose |
|---------|---------|
| `/line-prep` | Sync git, load context, show available work |
| `/line-cook` | Select and execute a task with guardrails |
| `/line-serve` | Review completed work via headless Claude |
| `/line-tidy` | Commit and push changes |
| `/line-work` | Orchestrate full prep→cook→serve→tidy cycle |
| `/line-setup` | Configure hooks for your project (interactive) |
| `/line-season` | Apply research findings to beads - add context, create work |

## Dependencies

- **beads** (`bd`) - Git-native issue tracking for multi-session work

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

Epics organize related work into coherent groups using a **child-based** model:

1. **Epics contain children** - Use `--parent=<epic-id>` when creating tasks
2. **Dependencies order children** - Use `bd dep add` to establish order within an epic
3. **Dependencies order epics** - Epics can depend on other epics for sequencing
4. **Cross-epic dependencies (rare)** - A child of one epic may block another epic

```bash
# Create epic structure
bd create --title="Feature X" --type=epic --priority=1
bd create --title="Design X" --type=task --parent=lc-abc
bd create --title="Implement X" --type=task --parent=lc-abc
bd dep add lc-def lc-ghi  # Implement depends on Design

# Query progress
bd epic status                    # Show all epics with child completion
bd list --parent=<epic-id> --all  # List children of an epic
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

## Plugin Events

The line-cook OpenCode plugin hooks into these events:

| Event | Purpose |
|-------|---------|
| `session.created` | Detect beads-enabled projects, suggest workflow |
| `session.idle` | Remind about `/line-tidy` for uncommitted work |
| `command.executed` | Track line-cook command usage |
| `file.edited` | Track edits to workflow files (.beads/, AGENTS.md) |

### Tool Execution Hooks

These hooks provide safety guardrails and automation:

| Hook | Purpose |
|------|---------|
| `tool.execute.before` | Block dangerous bash commands (git push --force, rm -rf /, etc.) |
| `tool.execute.after` | Auto-format edited files based on extension (prettier, ruff, gofmt, etc.) |

### Permission Hooks

| Hook | Purpose |
|------|---------|
| `permission.ask` | Auto-approve read-only operations and beads commands, deny dangerous operations |

### Experimental Hooks

These hooks use OpenCode's experimental plugin API:

| Hook | Purpose |
|------|---------|
| `experimental.session.compacting` | Inject beads context before session summarization to preserve workflow state |

### Error Handling

| Event | Purpose |
|-------|---------|
| `session.error` | Detect common error patterns (auth, rate limit, context length) and suggest recovery steps |

### Event Reference

OpenCode provides events across these categories:

- **Session**: `session.created`, `session.idle`, `session.compacted`, `session.error`
- **Tool**: `tool.execute.before`, `tool.execute.after`
- **File**: `file.edited`, `file.watcher.updated`
- **Command**: `command.executed`
- **Permission**: `permission.ask`
- **Experimental**: `experimental.session.compacting`

See [OpenCode Plugin Docs](https://opencode.ai/docs/plugins/) for the complete event reference.

## Release Process

**When making changes to core functionality** (commands, hooks, plugin logic), bump the version in:

| File | Field(s) |
|------|----------|
| `.claude-plugin/plugin.json` | `version` |
| `line-cook-opencode/package.json` | `version` AND `opencode.version` |

All three version values MUST be identical. See the main [AGENTS.md](../AGENTS.md) for full release checklist.
