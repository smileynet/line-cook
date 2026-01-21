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
| `/getting-started` | Quick workflow guide for beginners |
| `/prep` | Sync git, load context, show available work |
| `/cook` | Select and execute a task with guardrails |
| `/serve` | Review completed work via headless Claude |
| `/tidy` | Commit and push changes |

### Advanced Commands

| Command | Purpose |
|---------|---------|
| `/work` | Orchestrate full prep→cook→serve→tidy cycle |
| `/season` | Apply research findings to beads |
| `/setup` | Configure hooks for your project |
| `/compact` | Compact context with workflow state preserved |

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

## Bead Hierarchy

Line-cook uses a **3-tier hierarchy** for organizing work:

1. **Epics** - High-level capability areas (3+ sessions of work)
2. **User-Observable Features** - Acceptance-testable outcomes (first-level children of epics)
3. **Implementation Tasks** - Single-session work items (children of features)

### Structure

```
Epic (capability area)
├── Feature 1 (user-verifiable outcome)
│   ├── Task 1a (implementation step)
│   └── Task 1b (implementation step)
├── Feature 2 (user-verifiable outcome)
│   └── Task 2a (implementation step)
└── Feature 3 (user-verifiable outcome)
    ├── Task 3a (implementation step)
    └── Task 3b (depends on Task 3a)
```

**Exception: Research & Parking Lot epics** - These have tasks as direct children (no feature layer) since research tasks don't have user-observable outcomes.

### What Makes a User-Observable Feature

**A feature is user-observable when a human can verify it works.**

| Criterion | Feature | Task |
|-----------|---------|------|
| **Value** | Delivers visible benefit to user | Supports features, no standalone value |
| **Testable** | User can verify "it works" | Only devs can verify |
| **Perspective** | Human user's viewpoint | System/developer viewpoint |
| **Scope** | End-to-end (vertical slice) | Single layer/component |

**The "Who" Test:** If the beneficiary is "the system" or "developers," it's a task, not a feature.

### Naming Conventions

| Tier | Style | Examples |
|------|-------|----------|
| **Epic** | Noun phrase (capability area) | "Hook System Hardening", "AI Discoverability" |
| **Feature** | User-verifiable outcome | "Hooks work in all git configurations", "Scripts work on Windows" |
| **Task** | Action-oriented implementation | "Harden worktree detection", "Add Python fallback" |

### When to Create Each Tier

| Tier | When to Create |
|------|----------------|
| **Epic** | Work spans 3+ sessions OR multiple user-observable features |
| **Feature** | User could test/demonstrate it working; has acceptance criteria |
| **Task** | Implementation step completable in one session |

### Creating Hierarchy

```bash
# Create the epic
bd create --title="Hook System Hardening" --type=epic --priority=2

# Create features under epic
bd create --title="Hooks work in all git configurations" --type=feature --parent=lc-abc --priority=3
bd create --title="Scripts work across all platforms" --type=feature --parent=lc-abc --priority=3

# Create tasks under features
bd create --title="Harden worktree detection in pre-push" --type=task --parent=lc-abc.1
bd create --title="Add fallback for bare repos" --type=task --parent=lc-abc.1

# Add dependencies between tasks for ordering
bd dep add lc-xyz lc-def   # Task xyz depends on task def
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
| `--parent` (epic) | Feature belongs to an epic |
| `--parent` (feature) | Task implements a feature |
| `bd dep add` | Task must complete before another (ordering) |
| Epic depends on epic | One capability requires another first |

### Anti-patterns

- **System-as-User** - "As a system, I want to upgrade the database" → This is a task, not a feature
- **Prescribing Solutions** - "Add dropdown with autocomplete" → Better: "Users can quickly find products"
- **Layer-by-Layer Splitting** - "Build UI" → "Build API" → "Build DB" → Better: vertical slice that delivers value
- **Technical Tasks as Features** - "Refactor hook detection" → Should be a task under a feature
- **Flat task lists** - Group related work into epics with features
- **Over-nesting** - Max 3 levels: epic → feature → task

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
│   ├── setup.md           # → /line:setup
│   ├── compact.md         # → /line:compact
│   └── season.md          # → /line:season
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
│       ├── line-setup.md  # → /line-setup
│       ├── line-compact.md # → /line-compact
│       └── line-season.md  # → /line-season
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

Commands: `/line:getting-started`, `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:work`, `/line:season`, `/line:setup`, `/line:compact`

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

Commands: `/line-getting-started`, `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-work`, `/line-season`, `/line-setup`, `/line-compact`

## Hooks

### Plugin Hooks (Automatic)

The plugin.json includes hooks that run automatically when the plugin is installed:

- **SessionStart**: Primes beads workflow context when a session starts
- **PreCompact**: Preserves workflow context before conversation compaction

These hooks are defined in `.claude-plugin/plugin.json` and require no configuration.

### Project Hooks (Optional)

Additional hooks can be configured per-project. Run `/line:setup` to configure interactively, or see [HOOKS.md](HOOKS.md) for manual setup.

Optional project hooks:
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

# 3. Commit and push (release is created automatically)
git add .claude-plugin/plugin.json line-cook-opencode/package.json
git commit -m "chore: bump version to X.Y.Z"
bd sync
git push
```

> **Note:** GitHub Actions automatically creates a release when `plugin.json` is updated on `main`. See `.github/workflows/release.yml`.

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

### Pre-commit Version Check

A git pre-commit hook enforces version bumps for core files. When you stage core files without version files, the commit is blocked with options to proceed:

```
WARNING: Core file(s) changed without version bump
  commands/prep.md

To proceed:
  1. Bump version in both files, re-stage, commit
  2. Skip (WIP): SKIP_VERSION_CHECK=1 git commit ...
  3. Skip all: git commit --no-verify
```

**Bypass options:**
- `SKIP_VERSION_CHECK=1 git commit -m "..."` - Skip version check only (beads flush still runs)
- `git commit --no-verify` - Skip all pre-commit hooks

**Hard block (no bypass):** If version files are staged but have mismatched versions, the commit is blocked until fixed.

### Post-Release: User Instructions

After pushing a version bump, create a GitHub release with these instructions for users:

**Installation (new users):**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

**Update (existing users):**
```bash
/plugin update line
```

See [.github/release.md](.github/release.md) for the release notes template.
