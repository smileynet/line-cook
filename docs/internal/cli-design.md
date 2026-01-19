# Line Cook CLI Design

**Issue**: lc-4vk
**Date**: 2026-01-19
**Purpose**: Define command structure for the line-cook Go CLI tool.

## Executive Summary

The line-cook CLI (`lc`) orchestrates AI-assisted development workflows. It provides:
- Workflow commands mirroring current slash commands (prep, cook, serve, tidy, work)
- Hook handlers for Claude Code integration
- Configuration and setup utilities

**Command name**: `lc` (short, matches `bd` pattern, easy to type)

## Command Tree

```
lc
├── prep          # Sync state, show ready work
├── cook [id]     # Execute a task with guardrails
├── serve         # Review completed work
├── tidy          # Commit, sync, push
├── work [id]     # Full prep→cook→serve→tidy cycle
│
├── hook          # Hook handlers (called by Claude Code)
│   ├── session-start     # Prime workflow context
│   ├── pre-compact       # Save context before compaction
│   ├── pre-tool [tool]   # Pre-tool validation
│   ├── post-tool [tool]  # Post-tool actions
│   └── stop              # Session completion check
│
├── init          # Initialize line-cook in a project
├── setup         # Interactive hook configuration
├── config        # Configuration management
│   ├── show              # Display current config
│   ├── set <key> <val>   # Set a config value
│   └── edit              # Open config in editor
│
├── version       # Show version info
└── help [cmd]    # Help for commands
```

## Command Groups

Following the beads pattern, commands are organized into groups for help display:

```go
rootCmd.AddGroup(
    &cobra.Group{ID: "workflow", Title: "Workflow Commands:"},
    &cobra.Group{ID: "hooks", Title: "Hook Handlers:"},
    &cobra.Group{ID: "setup", Title: "Setup & Configuration:"},
)
```

## Workflow Commands

### `lc prep`

Sync state and identify ready tasks.

```bash
lc prep

# Output:
# SESSION: line-cook @ main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sync: ✓ up to date
# Ready: 3 tasks | In progress: 1 | Blocked: 2
#
# NEXT TASK:
#   lc-042 [P1] Implement auth flow
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--no-sync` | Skip git fetch/pull |
| `--json` | Output as JSON |

### `lc cook [id]`

Execute a task with guardrails.

```bash
lc cook             # Pick highest priority ready task
lc cook lc-042      # Execute specific task
```

**Behavior:**
1. Select task (from arg or `bd ready`)
2. Claim task (`bd update --status=in_progress`)
3. Display task details for AI execution
4. Track progress via stdout
5. Verify completion guardrails

**Flags:**
| Flag | Description |
|------|-------------|
| `--dry-run` | Show what would be done |
| `--json` | Output as JSON |

### `lc serve`

Review completed work via headless Claude.

```bash
lc serve

# Output:
# REVIEW: lc-042 - Implement auth flow
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Files: 3 changed
# Verdict: APPROVED | NEEDS_WORK | BLOCKED
# Findings: <issues for tidy to file>
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--json` | Output as JSON |

### `lc tidy`

Commit, sync beads, and push.

```bash
lc tidy

# Output:
# TIDY: Committing and pushing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [✓] Files staged
# [✓] Committed: abc1234
# [✓] Beads synced
# [✓] Pushed to origin
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--no-push` | Commit but don't push |
| `--message, -m` | Custom commit message |
| `--json` | Output as JSON |

### `lc work [id]`

Run full prep→cook→serve→tidy cycle.

```bash
lc work             # Full cycle with auto-selected task
lc work lc-042      # Full cycle with specific task
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--no-serve` | Skip review step |
| `--json` | Output as JSON |

## Hook Commands

Hook commands are called by Claude Code's hook system, not directly by users.

### `lc hook session-start`

Called on SessionStart event. Primes workflow context.

```bash
lc hook session-start

# Output: Workflow context for AI (markdown)
```

### `lc hook pre-compact`

Called before context compaction. Saves important state.

```bash
lc hook pre-compact
```

### `lc hook pre-tool <tool>`

Called before tool execution. Returns validation result.

**Input:** Receives JSON via stdin (Claude Code hook protocol):
```json
{"tool_input": {"command": "rm -rf /"}}
```

**Output:** JSON to stdout:
```json
{"decision": "block", "message": "Destructive command blocked"}
```

```bash
# From Claude Code (automatic)
echo '{"tool_input":{"command":"rm -rf /"}}' | lc hook pre-tool Bash

# For manual testing
lc hook pre-tool Bash --input='rm -rf /'
```

**Exit codes:**
- 0: Allow (or decision: "allow" in JSON output)
- 2: Block (with decision: "block" in JSON output)
- 1: Error

**Flags:**
| Flag | Description |
|------|-------------|
| `--input` | Tool input for manual testing (bypasses stdin) |
| `--json` | Force JSON output (default when stdin is piped) |

### `lc hook post-tool <tool>`

Called after tool execution. Performs cleanup/formatting.

**Input:** Receives JSON via stdin (Claude Code hook protocol):
```json
{"tool_input": {"file_path": "src/main.go", "content": "..."}}
```

```bash
# From Claude Code (automatic)
echo '{"tool_input":{"file_path":"src/main.go"}}' | lc hook post-tool Edit

# For manual testing
lc hook post-tool Edit --file=src/main.go
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--file` | File path for manual testing (bypasses stdin) |
| `--json` | Machine-readable output |

### `lc hook stop`

Called when session ends. Verifies work is saved.

```bash
lc hook stop

# Exit 1 with warning if uncommitted changes
# Exit 0 if clean
```

## Setup Commands

### `lc init`

Initialize line-cook in a project.

```bash
lc init

# Creates:
# - .line-cook/config.yaml (project config)
# - Installs git hooks if requested
# - Configures Claude Code plugin hooks
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--with-hooks` | Also install git hooks |
| `--force` | Overwrite existing config |

### `lc setup`

Interactive configuration wizard for hooks and project setup.

```bash
lc setup

# Interactive prompts:
# - Which hooks do you want to enable?
# - Configure blocked commands?
# - Set up formatters?
# - Install git hooks?
```

**Flags:**
| Flag | Description |
|------|-------------|
| `--non-interactive` | Use defaults, no prompts |

### `lc config`

Manage configuration.

```bash
lc config show              # Display all config
lc config set workflow.auto_push true
lc config edit              # Open in $EDITOR
```

## Global Flags

Available on all commands via rootCmd.PersistentFlags():

| Flag | Short | Description |
|------|-------|-------------|
| `--verbose` | `-v` | Debug output |
| `--quiet` | `-q` | Minimal output |
| `--json` | | JSON output (machine-readable) |
| `--no-color` | | Disable colored output |
| `--config` | `-c` | Config file path |

## Configuration

### File Locations (search order)

1. `--config` flag value
2. `.line-cook/config.yaml` (project, walks up)
3. `~/.config/lc/config.yaml` (user)
4. `~/.line-cook/config.yaml` (home)

### Environment Variables

Prefix: `LC_` with underscore replacement.

```bash
LC_VERBOSE=1 lc prep      # Same as --verbose
LC_NO_COLOR=1 lc work     # Same as --no-color
LC_CONFIG=/path/to/config # Same as --config
```

### Example Config

```yaml
# .line-cook/config.yaml

# Workflow settings
workflow:
  auto_sync: true           # Sync git in prep
  auto_push: true           # Push in tidy
  require_review: false     # Skip serve by default

# Hook settings
hooks:
  session_start: true
  pre_tool:
    enabled: true
    blocked_commands:
      - "rm -rf"
      - "git push --force"
  post_tool:
    format_on_save: true
    formatters:
      go: "gofmt -w"
      ts: "prettier --write"
      py: "black"
  stop:
    warn_uncommitted: true

# Output settings
output:
  color: true
  verbose: false
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success / Hook allows action |
| 1 | General error |
| 2 | Hook blocked action (with JSON decision output) |
| 3 | Invalid arguments |
| 4 | Verification failed (guardrails) |

## Plugin Integration

### plugin.json

```json
{
  "name": "line-cook",
  "version": "1.0.0",
  "description": "Structured AI workflow execution",
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "lc hook session-start"}]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "lc hook pre-compact"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "lc hook pre-tool Bash"}]
    }],
    "PostToolUse": [{
      "matcher": "Edit",
      "hooks": [{"type": "command", "command": "lc hook post-tool Edit"}]
    }],
    "Stop": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "lc hook stop"}]
    }]
  }
}
```

### SKILL.md

```markdown
---
name: line-cook
description: Structured AI workflow execution with guardrails
allowed-tools: "Read,Bash(lc:*),Bash(bd:*)"
version: "1.0.0"
---

Line Cook orchestrates prep→cook→serve→tidy workflow...
```

## Usage Examples

### Basic Workflow

```bash
# Start work session
lc prep

# Execute a task
lc cook lc-042

# Review (optional)
lc serve

# Commit and push
lc tidy
```

### Full Cycle

```bash
# One command does it all
lc work

# With specific task
lc work lc-042
```

### Debugging

```bash
# Verbose output
lc -v prep

# JSON for scripting
lc prep --json | jq '.next_task.id'

# Check config
lc config show
```

### Hook Testing

```bash
# Test pre-tool validation
lc hook pre-tool Bash --input='rm -rf /'
# Should exit 1

# Test session start
lc hook session-start
# Should output workflow context
```

## Migration from Python Hooks

| Current (Python) | New (Go CLI) |
|------------------|--------------|
| `hooks/session-start.sh` | `lc hook session-start` |
| `hooks/pre-tool-use-bash.sh` | `lc hook pre-tool Bash` |
| `hooks/post-tool-use-edit.sh` | `lc hook post-tool Edit` |
| `hooks/stop-workflow-check.sh` | `lc hook stop` |

Benefits:
- Single binary, no Python runtime required
- Consistent cross-platform behavior
- Faster startup (no interpreter)
- Easier distribution via GoReleaser

## Future Considerations

### Phase 2 Commands (not in initial release)

```
lc fresh          # Clear context and restart
lc compact        # Manual context compaction
lc status         # Quick workflow status
```

### Integration Points

- **beads**: `lc` calls `bd` for issue tracking
- **Claude Code**: Via plugin.json hooks
- **OpenCode**: Via plugin system (different mechanism)
- **Git**: Direct git commands for sync/push

## References

- Research: [docs/research-beads-go-cli.md](research-beads-go-cli.md)
- Beads source: Reference for cobra patterns
- Cobra docs: https://cobra.dev/
- Viper docs: https://github.com/spf13/viper
