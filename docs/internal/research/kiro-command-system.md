# Kiro CLI Command System Research

Research findings for Kiro CLI integration with line-cook workflow.

## Executive Summary

Kiro CLI provides a comprehensive agent customization system through:
- **Custom agents** (JSON configuration files)
- **Steering files** (markdown instructions)
- **Skills** (lazy-loaded documentation via `skill://` URIs)
- **Hooks** (lifecycle event handlers, defined inline in agent JSON)

The architecture closely mirrors Claude Code's plugin system, making adaptation straightforward. The recommended strategy is to create a `line-cook-kiro/` directory with custom agent configuration, steering files, and SKILL.md for discoverability.

## Kiro CLI Architecture Overview

### Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Custom Agents | `.kiro/agents/` (local) or `~/.kiro/agents/` (global) | Define agent behavior, tools, resources |
| Steering Files | `.kiro/steering/` (local) or `~/.kiro/steering/` (global) | Persistent project context |
| Skills | `.kiro/skills/**/SKILL.md` | Lazy-loaded documentation |
| Hook Scripts | `.kiro/scripts/` | Shell scripts referenced from agent JSON |
| AGENTS.md | Project root or `~/.kiro/steering/` | Always-loaded steering (standard format) |

### Agent Configuration Reference

Custom agents use JSON files with this structure:

```json
{
  "name": "line-cook",
  "description": "Task-focused workflow orchestration for AI-assisted development",
  "prompt": "file://.kiro/steering/line-cook.md",
  "tools": ["read", "write", "shell", "@builtin"],
  "allowedTools": ["read", "shell"],
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md",
    "skill://.kiro/skills/**/SKILL.md"
  ],
  "hooks": {
    "AgentSpawn": {
      "command": "bash .kiro/scripts/session-start.sh",
      "timeout_ms": 30000
    },
    "Stop": {
      "command": "bash .kiro/scripts/stop-check.sh",
      "timeout_ms": 30000
    }
  },
  "model": "claude-sonnet-4"
}
```

Key fields:
- **prompt**: System-level instructions (inline or `file://` URI)
- **tools**: Available tools (built-in or MCP)
- **allowedTools**: Pre-approved tools (no permission prompts)
- **resources**: Files and skills to load (`file://` or `skill://`)
- **hooks**: Lifecycle event handlers (defined inline, referencing scripts)

### Resource URI Schemes

| Scheme | Loading | Use Case |
|--------|---------|----------|
| `file://` | Immediate (at startup) | README, core docs, steering files |
| `skill://` | Lazy (on demand) | Reference docs, tutorials |

Skills require YAML frontmatter with `name` and `description` for indexing.

## Workflow Commands in Kiro CLI

Kiro CLI has built-in slash commands but **does not support custom slash commands** in the same way as Claude Code.

### How Workflow Commands Work

Kiro CLI only has 5 hook types: `AgentSpawn`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`.

**There is no "manual" hook type** for custom slash commands.

Workflow invocation relies on **agent steering + natural language recognition**:

```markdown
## Workflow Commands (in steering/line-cook.md)

When the user says any of these, execute the corresponding workflow:

| User Input | Execute |
|-----------|---------|
| "prep", "/prep", "sync state" | Run prep workflow |
| "cook", "/cook", "start task" | Run cook workflow |
| "serve", "/serve", "review" | Run serve workflow |
| "tidy", "/tidy", "commit" | Run tidy workflow |
| "work", "/work", "full cycle" | Run prep→cook→serve→tidy sequentially |
```

The steering file is the critical artifact—it trains the agent to recognize and execute workflow phases.

### Built-in Commands Relevant to Line Cook

| Command | Purpose |
|---------|---------|
| `/agent swap` | Switch between agents |
| `/agent generate` | Create new agent interactively |
| `/context` | Manage context files |
| `/compact` | Summarize conversation (context management) |
| `/tools` | View/control tool permissions |
| `/todos` | Manage to-do lists |

### Adapter Strategy for Commands

Since Kiro lacks custom slash commands, line-cook commands must be implemented as:

1. **Agent steering** - Steering file teaches agent to recognize workflow commands
2. **Natural language** - Users invoke via "run prep", "start cooking", etc.
3. **Slash-like syntax** - Steering recognizes "/prep", "/cook", etc. as commands

## Steering Files

### Standard Files Created Automatically

Kiro suggests these foundation files:
- `product.md` - Product purpose, target users, features
- `tech.md` - Frameworks, libraries, tools
- `structure.md` - File organization, naming conventions

### Line Cook Steering Strategy

Create steering files that mirror AGENTS.md structure:

```
.kiro/steering/
├── line-cook.md       # Core workflow instructions
├── beads.md           # Beads quick reference
└── session.md         # Session management protocol
```

These will be loaded via:
```json
"resources": ["file://.kiro/steering/**/*.md"]
```

**Important**: Steering files are NOT automatically included with custom agents. They must be explicitly added to the `resources` array.

## Skills (skill:// Resources)

### SKILL.md Format

```yaml
---
name: line-cook
description: AI-supervised development workflow. Use when running prep/cook/serve/tidy commands, managing beads issues, or following workflow cycle.
---

# Line Cook

[Content loaded on demand when agent determines it's needed]
```

### Key Requirements

1. **Frontmatter is critical** - `name` and `description` trigger skill loading
2. **Description triggers loading** - Include "when to use" context in description
3. **Body loads late** - Don't put "when to use" in body; agent won't see it until after triggering

### Line Cook Skill Strategy

Create `SKILL.md` following OpenCode pattern:

```
.kiro/skills/
└── line-cook/
    └── SKILL.md
```

## Hooks

### Hook Types

Kiro CLI supports exactly 5 hook types:

| Type | Trigger | Use Case |
|------|---------|----------|
| `AgentSpawn` | Agent activates | Load initial context |
| `UserPromptSubmit` | User sends message | Inject context, validate |
| `PreToolUse` | Before tool runs | Block dangerous operations |
| `PostToolUse` | After tool runs | Auto-format, validate |
| `Stop` | Agent completes response | Run tests, commit checks |

**Note**: There is no "manual" hook type for custom commands.

### Hook Configuration

Hooks are defined **inline in the agent JSON configuration**, not as separate files:

```json
{
  "name": "line-cook",
  "hooks": {
    "AgentSpawn": {
      "command": "bash .kiro/scripts/session-start.sh",
      "timeout_ms": 30000
    },
    "PreToolUse": {
      "command": "bash .kiro/scripts/pre-tool-use.sh",
      "timeout_ms": 10000
    },
    "PostToolUse": {
      "command": "bash .kiro/scripts/post-tool-use.sh",
      "timeout_ms": 10000
    },
    "Stop": {
      "command": "bash .kiro/scripts/stop-check.sh",
      "timeout_ms": 30000
    }
  }
}
```

Hook scripts can live anywhere—they're referenced by path from the agent JSON. The `scripts/` directory is the recommended location.

### Python Hook Support

**Research Conclusion (2026-01-20):**

The `command` field is shell-executed, meaning any language supported by the shell can be used. Python scripts CAN be used via explicit invocation:

```json
{
  "hooks": {
    "AgentSpawn": {
      "command": "python3 .kiro/scripts/session-start.py",
      "timeout_ms": 30000
    }
  }
}
```

**Key findings:**

1. **Shell Execution**: The command field runs through the shell, not direct execution
2. **Python Works**: `python3 script.py` or `python script.py` will execute Python scripts
3. **Shebang Not Required**: Since we invoke Python explicitly, shebang is optional (but still recommended for direct script execution)
4. **Environment Inherited**: Hooks inherit the shell's PATH and environment, so Python must be on PATH
5. **JSON I/O Compatible**: Python's json module handles stdin/stdout like shell scripts do

**Recommendation**: Use Python for complex hooks (session-start, stop-check) and shell for simple ones (pre/post-tool-use). This avoids porting complex logic unnecessarily.

Example Python hook invocations:

```json
{
  "hooks": {
    "AgentSpawn": {
      "command": "python3 .kiro/scripts/session-start.py",
      "timeout_ms": 30000
    },
    "PreToolUse": {
      "command": "bash .kiro/scripts/pre-tool-use.sh",
      "timeout_ms": 10000
    },
    "PostToolUse": {
      "command": "bash .kiro/scripts/post-tool-use.sh",
      "timeout_ms": 10000
    },
    "Stop": {
      "command": "python3 .kiro/scripts/stop-check.py",
      "timeout_ms": 30000
    }
  }
}
```

### Line Cook Hook Strategy

Retain Python for complex hooks, use shell for simple ones:

| Current Hook | Kiro Equivalent | Language |
|--------------|-----------------|----------|
| `session_start.py` | `AgentSpawn` hook | Python (complex logic) |
| `pre_tool_use.py` | `PreToolUse` hook | Shell (simple blocking) |
| `post_tool_use.py` | `PostToolUse` hook | Shell (simple formatting) |
| `stop_check.py` | `Stop` hook | Python (complex validation) |

## Adapter Strategy: Final Recommendation

### Directory Structure

```
line-cook-kiro/
├── agents/
│   └── line-cook.json       # Main agent configuration (hooks defined inline)
├── steering/
│   ├── line-cook.md         # Core workflow instructions (AGENTS.md content)
│   ├── beads.md             # Beads quick reference
│   └── session.md           # Session protocols
├── skills/
│   └── line-cook/
│       └── SKILL.md         # Lazy-loaded documentation
├── scripts/                  # Hook scripts (referenced from agent JSON)
│   ├── session-start.py     # AgentSpawn hook (Python - complex logic)
│   ├── pre-tool-use.sh      # PreToolUse hook (Shell - simple blocking)
│   ├── post-tool-use.sh     # PostToolUse hook (Shell - simple formatting)
│   └── stop-check.py        # Stop hook (Python - complex validation)
└── install.sh               # Installation script
```

### Command Mapping

| Claude Code | OpenCode | Kiro |
|-------------|----------|------|
| `/line:prep` | `/line-prep` | Agent recognizes "prep", "/prep", "run prep" |
| `/line:cook` | `/line-cook` | Agent recognizes "cook", "/cook", "start cooking" |
| `/line:serve` | `/line-serve` | Agent recognizes "serve", "/serve", "review changes" |
| `/line:tidy` | `/line-tidy` | Agent recognizes "tidy", "/tidy", "commit and push" |
| `/line:work` | `/line-work` | Agent recognizes "work", "/work", "start work cycle" |
| `/line:getting-started` | `/line-getting-started` | Steering file for workflow guide |
| `/line:compact` | `/line-compact` | Agent recognizes "compact", "/compact" |

### Agent Prompt Strategy

The steering file should include workflow command recognition:

```markdown
## Workflow Commands

When the user says any of these, execute the corresponding workflow:

| User says | Execute |
|-----------|---------|
| "prep", "/prep", "sync state" | Run prep workflow |
| "cook", "/cook", "start task" | Run cook workflow |
| "serve", "/serve", "review" | Run serve workflow |
| "tidy", "/tidy", "commit" | Run tidy workflow |
| "work", "/work", "start cycle" | Run full workflow |
```

### Installation Script

```bash
#!/bin/bash
# install.sh - Install line-cook for Kiro CLI

KIRO_DIR="${HOME}/.kiro"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create directories
mkdir -p "${KIRO_DIR}/agents"
mkdir -p "${KIRO_DIR}/steering"
mkdir -p "${KIRO_DIR}/skills/line-cook"
mkdir -p "${KIRO_DIR}/scripts"

# Copy files
cp "${SCRIPT_DIR}/agents/line-cook.json" "${KIRO_DIR}/agents/"
cp "${SCRIPT_DIR}/steering/"*.md "${KIRO_DIR}/steering/"
cp "${SCRIPT_DIR}/skills/line-cook/SKILL.md" "${KIRO_DIR}/skills/line-cook/"
cp "${SCRIPT_DIR}/scripts/"*.sh "${KIRO_DIR}/scripts/"

echo "Line Cook installed for Kiro CLI"
echo "Start a session with: kiro-cli --agent line-cook"
```

## Platform Comparison

| Feature | Claude Code | OpenCode | Kiro CLI |
|---------|-------------|----------|----------|
| Slash commands | Native (commands/) | Native (commands/) | Natural language via steering |
| Skills | SKILL.md | SKILL.md | SKILL.md (same format) |
| Steering | CLAUDE.md, AGENTS.md | AGENTS.md | steering/*.md, AGENTS.md |
| Hooks | hooks/*.py | Plugin events | Inline in agent JSON + scripts/ |
| Agent config | settings.json | plugin.json | agents/*.json |
| Tool permissions | settings.json | plugin.json | agents/*.json (allowedTools) |

## Implementation Order

1. **Create directory structure** - Mirror OpenCode plugin layout
2. **Port AGENTS.md to steering** - Convert to Kiro steering format
3. **Create agent configuration** - Define tools, resources, permissions, hooks
4. **Create SKILL.md** - Ensure proper frontmatter for lazy loading
5. **Implement hook scripts** - Start with session-start and stop-check
6. **Write installation script** - Single command setup
7. **Test workflow** - Verify prep→cook→serve→tidy cycle works

## Open Questions

1. **Headless mode for /serve**: Does Kiro CLI support spawning headless sessions for peer review?
2. **Context preservation**: Does Kiro have equivalent to `session.compacting` event?
3. **Beads integration**: Does Kiro work with git hooks for automatic bd sync?

## References

Sources consulted during research (verified via web search and fetch):

- [Kiro CLI Documentation](https://kiro.dev/docs/cli/)
- [Agent Configuration Reference](https://kiro.dev/docs/cli/custom-agents/configuration-reference/)
- [Steering Files](https://kiro.dev/docs/cli/steering/)
- [Hooks](https://kiro.dev/docs/cli/hooks/)
- [Slash Commands](https://kiro.dev/docs/cli/reference/slash-commands/)

**Note:** Some configuration examples are composites based on documented patterns. Verify specific syntax against current Kiro documentation before implementation.
