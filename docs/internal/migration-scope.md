# Migration Scope: Python Hooks to Go CLI

**Issue**: lc-aal
**Date**: 2026-01-19
**Purpose**: Define the migration path from current Python hooks to Go CLI.

## Executive Summary

This document scopes the migration from the current Python-based hook system to a Go CLI (`lc`). The migration enables:
- Single binary distribution (no Python runtime required)
- Faster startup times
- Consistent cross-platform behavior
- Easier installation and updates

## Current State

### Python Hook Scripts

| Hook | File | Purpose | Trigger |
|------|------|---------|---------|
| SessionStart | `hooks/session_start.py` | Prime beads workflow context | Session start |
| PreToolUse | `hooks/pre_tool_use.py` | Block dangerous Bash commands | Before Bash |
| PostToolUse | `hooks/post_tool_use.py` | Auto-format edited files | After Edit/Write |
| Stop | `hooks/stop_check.py` | Warn about uncommitted work | Session stop |

### Hook Utilities

- `hooks/hook_utils.py` - Shared logging, JSON parsing, output utilities

### Settings Configuration

- `.claude/settings.json` - Hook configuration pointing to Python scripts

### Slash Commands (Markdown)

| Command | File | Purpose |
|---------|------|---------|
| `/line:prep` | `commands/prep.md` | Sync state, show ready tasks |
| `/line:cook` | `commands/cook.md` | Execute a task with guardrails |
| `/line:serve` | `commands/serve.md` | Review via headless Claude |
| `/line:tidy` | `commands/tidy.md` | Commit, sync, push |
| `/line:work` | `commands/work.md` | Full prep→cook→serve→tidy cycle |
| `/line:setup` | `commands/setup.md` | Configure hooks |
| `/line:getting-started` | `commands/getting-started.md` | Workflow guide |

## Target State

### Go CLI Binary (`lc`)

Single binary replacing all Python hooks:

```
lc
├── hook                    # Hook handlers (called by Claude Code)
│   ├── session-start       # Prime workflow context
│   ├── pre-tool <tool>     # Pre-tool validation
│   ├── post-tool <tool>    # Post-tool actions (formatting)
│   └── stop                # Session completion check
│
├── prep                    # Sync state, show ready work
├── cook [id]               # Execute a task with guardrails
├── serve                   # Review completed work
├── tidy                    # Commit, sync, push
├── work [id]               # Full cycle
│
├── init                    # Initialize line-cook in project
├── setup                   # Interactive hook configuration
├── config                  # Configuration management
└── version                 # Show version info
```

### Plugin Integration

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{"type": "command", "command": "lc hook session-start"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "lc hook pre-tool Bash"}]
    }],
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{"type": "command", "command": "lc hook post-tool Edit"}]
    }],
    "Stop": [{
      "hooks": [{"type": "command", "command": "lc hook stop"}]
    }]
  }
}
```

### Slash Commands

Commands remain as Markdown files but invoke CLI where beneficial:
- Some commands stay pure markdown (workflow orchestration)
- Others may invoke `lc` for complex operations

## Functionality to Port

### 1. Session Start Hook

**Current Python behavior:**
- Check for `.beads/` directory
- Output workflow context (markdown) to stdout
- Log execution to `.claude/hooks.log`

**Go CLI equivalent:**
- `lc hook session-start`
- Same behavior, embedded context string
- Structured logging via slog

**Complexity:** Low

### 2. Pre-Tool Use Hook (Bash validation)

**Current Python behavior:**
- Parse JSON input from stdin
- Check command against dangerous patterns:
  - `git push --force`
  - `git reset --hard`
  - `rm -rf /`, `rm -rf ~`, `rm -rf $HOME`
  - Windows: `rmdir /s /q C:\`, `del /f /s /q C:\`, `format [A-Z]:`
  - Fork bomb, disk writes
- Return JSON with permission decision
- Exit code: 0 (allow), 2 (block)

**Go CLI equivalent:**
- `lc hook pre-tool Bash`
- Read JSON from stdin, parse command
- Configurable blocked patterns (via config file)
- Structured JSON output

**Complexity:** Medium (regex compilation, config system)

### 3. Post-Tool Use Hook (Auto-formatting)

**Current Python behavior:**
- Parse JSON input for file path
- Check file extension against formatter map
- Attempt formatters in order until one succeeds:
  - Python: ruff, black
  - JS/TS: prettier, biome
  - Go: goimports, gofmt
  - Rust: rustfmt
  - Shell: shfmt + shellcheck
  - Ruby: rubocop
  - GDScript: gdformat
- Output JSON with formatter used
- Skip sensitive paths (`.env`, `.git/`, `.ssh/`, etc.)

**Go CLI equivalent:**
- `lc hook post-tool Edit`
- Configurable formatter map
- `exec.Command` to run formatters
- Same extension/formatter mapping

**Complexity:** Medium (external process execution, config)

### 4. Stop Hook

**Current Python behavior:**
- Count uncommitted changes via `git status --porcelain`
- Count unpushed commits via `git log @{upstream}..HEAD`
- Log warnings (don't output to user)
- Always allow stop (exit 0)

**Go CLI equivalent:**
- `lc hook stop`
- Same git commands via `os/exec`
- Optional: configurable behavior (warn vs block)

**Complexity:** Low

### 5. Hook Utilities

**Current Python utilities:**
- `setup_logging()` - File-based logging
- `log_hook_start/end()` - Structured log messages
- `read_hook_input()` - JSON stdin parsing
- `output_json()` - JSON stdout

**Go equivalents:**
- `internal/logging` - slog-based file logging
- `internal/hooks` - Shared hook utilities
- Standard `encoding/json` for I/O

**Complexity:** Low

## New Capabilities Enabled by CLI

### 1. Git Hooks Integration

**Not possible with Python hooks:**
- Pre-push session completion enforcement
- Post-checkout context recovery
- Pre-commit validation

**With Go CLI:**
- `lc hooks install` - Install thin shim git hooks
- Shims call `lc hook <event>` (follows beads pattern)
- Version tracking for hook upgrades

### 2. Unified Configuration

**Current:** Scattered across Python files

**With CLI:**
```yaml
# .line-cook/config.yaml
workflow:
  auto_sync: true
  auto_push: true
hooks:
  pre_tool:
    blocked_commands: [...]
  post_tool:
    formatters:
      go: "goimports -w"
      py: "ruff format"
```

### 3. Better Cross-Platform Support

**Current:** Relies on Python being installed, path issues

**With CLI:**
- Single static binary per platform
- No runtime dependencies
- Build tags for platform-specific code

### 4. Performance

**Current:** ~100-200ms Python startup per hook

**With CLI:**
- ~10-20ms Go binary startup
- Important for `pre-tool` hooks (runs frequently)

### 5. Distribution

**Current:** Python scripts must be copied with plugin

**With CLI:**
- GoReleaser for cross-platform builds
- Homebrew, npm, curl installer options
- Plugin hooks point to `lc` binary

## MVP vs Full Feature Set

### MVP (Phase 1)

**Core hook commands:**
- [ ] `lc hook session-start`
- [ ] `lc hook pre-tool Bash`
- [ ] `lc hook post-tool Edit`
- [ ] `lc hook stop`

**Supporting infrastructure:**
- [ ] Root command with version
- [ ] Basic config loading
- [ ] JSON input/output handling
- [ ] Logging

**Distribution:**
- [ ] `go install` compatible
- [ ] GitHub releases

### Full Feature Set (Phases 2-3)

**Workflow commands:**
- [ ] `lc prep`
- [ ] `lc cook`
- [ ] `lc serve`
- [ ] `lc tidy`
- [ ] `lc work`

**Setup commands:**
- [ ] `lc init`
- [ ] `lc setup`
- [ ] `lc config show/set/edit`

**Git hooks:**
- [ ] `lc hooks install/uninstall/list`
- [ ] Pre-push session completion
- [ ] Post-checkout context recovery

**Advanced:**
- [ ] `lc hook pre-compact`
- [ ] MCP server integration (optional)
- [ ] Daemon mode (optional, if needed)

## Phased Migration Approach

### Phase 1: Core Hook Commands (Foundation)

**Goal:** Replace Python hooks with Go CLI

**Tasks:**
1. Set up Go module with cobra CLI structure
2. Implement `lc hook session-start`
3. Implement `lc hook pre-tool`
4. Implement `lc hook post-tool`
5. Implement `lc hook stop`
6. Create plugin.json with hooks pointing to `lc`
7. Test cross-platform builds

**Milestone:** Hooks work via `lc` instead of Python

### Phase 2: Configuration and Setup

**Goal:** Configurable hooks and easy setup

**Tasks:**
1. Implement viper configuration system
2. Add `lc config` subcommands
3. Add `lc init` command
4. Add `lc setup` command (interactive)
5. Support project/user config hierarchy

**Milestone:** Users can configure line-cook without editing files

### Phase 3: Workflow Commands

**Goal:** CLI alternatives to slash commands

**Tasks:**
1. Implement `lc prep`
2. Implement `lc cook`
3. Implement `lc serve`
4. Implement `lc tidy`
5. Implement `lc work`
6. JSON output mode for scripting

**Milestone:** Full workflow available via CLI

### Phase 4: Git Hooks and Distribution

**Goal:** Production-ready distribution

**Tasks:**
1. Implement `lc hooks install/uninstall/list`
2. Pre-push session completion enforcement
3. GoReleaser configuration
4. Homebrew tap
5. npm package
6. curl/PowerShell installers

**Milestone:** Easy installation across platforms

### Phase 5: Deprecate Python Hooks

**Goal:** Clean up legacy code

**Tasks:**
1. Update documentation
2. Remove Python hook files
3. Update plugin to remove Python references
4. Migration guide for existing users

**Milestone:** Python-free line-cook

## Effort Estimates

| Phase | Components | Relative Effort |
|-------|------------|-----------------|
| Phase 1 | Core hooks | Medium |
| Phase 2 | Configuration | Medium |
| Phase 3 | Workflow commands | Large (if ported, Medium if kept as markdown) |
| Phase 4 | Git hooks + distribution | Medium |
| Phase 5 | Deprecation | Small |

**Note:** Phase 3 workflow commands may remain as markdown slash commands. The CLI versions would be optional convenience features for non-Claude Code usage.

## Dependencies

### Blocking This Work

- [x] lc-cvo: Research beads Go CLI architecture
- [x] lc-bkx: Research Claude Code plugin architecture
- [x] lc-ayt: Research git hooks integration patterns

### Blocked By This Work

- lc-45k: Reimagine line-cook as Go CLI tool (epic)
- lc-b1n: Set up Go module with cobra CLI structure
- lc-48r: Create Claude Code plugin.json manifest

## Risk Assessment

### Low Risk

- Hook functionality is well-understood
- Beads provides proven patterns
- Go tooling is mature

### Medium Risk

- Cross-platform formatter detection
- Windows path handling edge cases
- Config file migration for existing users

### Mitigation

- Extensive testing on all platforms
- Graceful fallback when formatters not found
- Migration command to convert existing configs

## Success Criteria

1. All Python hook functionality replicated in Go
2. No Python runtime required
3. Cross-platform binaries available
4. Hooks execute in <50ms (vs ~150ms for Python)
5. Existing users can migrate without losing configuration

## References

- [CLI Design](cli-design.md) - Command structure and interface
- [Research: Beads Go CLI](research-beads-go-cli.md) - Architecture patterns
- [Research: Git Hooks](research/git-hooks-integration.md) - Git integration
- [Research: Plugin Architecture](research/claude-code-plugin-architecture.md) - Plugin integration
