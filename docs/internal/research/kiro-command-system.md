# Kiro CLI Command System Research

Research findings for Kiro CLI integration with line-cook workflow.

## Executive Summary

Kiro CLI provides a comprehensive agent customization system through:
- **Custom agents** (JSON configuration files)
- **Steering files** (markdown instructions)
- **Skills** (lazy-loaded documentation via `skill://` URIs)
- **Hooks** (lifecycle event handlers)

The architecture closely mirrors Claude Code's plugin system, making adaptation straightforward. The recommended strategy is to create a `line-cook-kiro/` directory with custom agent configuration, steering files, and SKILL.md for discoverability.

## Kiro CLI Architecture Overview

### Core Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Custom Agents | `.kiro/agents/` (local) or `~/.kiro/agents/` (global) | Define agent behavior, tools, resources |
| Steering Files | `.kiro/steering/` (local) or `~/.kiro/steering/` (global) | Persistent project context |
| Skills | `.kiro/skills/**/SKILL.md` | Lazy-loaded documentation |
| Hooks | `.kiro/hooks/` | Lifecycle event automation |
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
    "stop": ".kiro/hooks/session-end.sh"
  },
  "model": "claude-sonnet-4"  // Note: Verify exact model ID format in Kiro docs
}
```

Key fields:
- **prompt**: System-level instructions (inline or `file://` URI)
- **tools**: Available tools (built-in or MCP)
- **allowedTools**: Pre-approved tools (no permission prompts)
- **resources**: Files and skills to load (`file://` or `skill://`)
- **hooks**: Lifecycle event handlers

### Resource URI Schemes

| Scheme | Loading | Use Case |
|--------|---------|----------|
| `file://` | Immediate (at startup) | README, core docs, steering files |
| `skill://` | Lazy (on demand) | Reference docs, tutorials |

Skills require YAML frontmatter with `name` and `description` for indexing.

## Slash Commands in Kiro CLI

Kiro CLI has built-in slash commands but **does not support custom slash commands** in the same way as Claude Code. Instead:

1. **Hooks with manual triggers** appear in the slash command menu
2. **Steering files configured with manual inclusion** appear in the menu
3. The `/agent generate` command creates new agent configurations

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

1. **Manual-trigger hooks** - Appear in `/` menu for quick access
2. **Agent prompts** - System prompt instructs agent to recognize workflow commands
3. **Natural language** - Users invoke via "run prep", "start cooking", etc.

**Recommended approach**: Create manual hooks for `/prep`, `/cook`, `/serve`, `/tidy`, `/work` that trigger agent prompts.

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

| Type | Trigger | Use Case |
|------|---------|----------|
| `agentSpawn` | Agent activates | Load initial context |
| `userPromptSubmit` | User sends message | Inject context, validate |
| `preToolUse` | Before tool runs | Block dangerous operations |
| `postToolUse` | After tool runs | Auto-format, validate |
| `stop` | Agent completes response | Run tests, commit checks |
| `manual` | User invokes from menu | On-demand operations |

### Hook Configuration

Hooks are JSON files in `.kiro/hooks/`:

```json
{
  "name": "session-end",
  "trigger": "stop",
  "command": "bash .kiro/hooks/session-end.sh",
  "timeout_ms": 30000
}
```

### Line Cook Hook Strategy

Port existing Python hooks to shell scripts:

| Current Hook | Kiro Equivalent |
|--------------|-----------------|
| `session_start.py` | `agentSpawn` hook |
| `pre_tool_use.py` | `preToolUse` hook |
| `post_tool_use.py` | `postToolUse` hook |
| `stop_check.py` | `stop` hook |

## Adapter Strategy: Final Recommendation

### Directory Structure

```
line-cook-kiro/
├── agents/
│   └── line-cook.json       # Main agent configuration
├── steering/
│   ├── line-cook.md         # Core workflow instructions (AGENTS.md content)
│   ├── beads.md             # Beads quick reference
│   └── session.md           # Session protocols
├── skills/
│   └── line-cook/
│       └── SKILL.md         # Lazy-loaded documentation
├── hooks/
│   ├── session-start.sh     # agentSpawn hook
│   ├── pre-tool-use.sh      # preToolUse hook
│   ├── post-tool-use.sh     # postToolUse hook
│   ├── stop-check.sh        # stop hook
│   └── workflows/
│       ├── prep.sh          # manual hook for /prep
│       ├── cook.sh          # manual hook for /cook
│       ├── serve.sh         # manual hook for /serve
│       └── tidy.sh          # manual hook for /tidy
└── install.sh               # Installation script
```

### Command Mapping

| Claude Code | OpenCode | Kiro |
|-------------|----------|------|
| `/line:prep` | `/line-prep` | Hook: "prep" (manual) OR agent recognizes "run prep" |
| `/line:cook` | `/line-cook` | Hook: "cook" (manual) OR agent recognizes "cook task" |
| `/line:serve` | `/line-serve` | Hook: "serve" (manual) OR agent recognizes "review changes" |
| `/line:tidy` | `/line-tidy` | Hook: "tidy" (manual) OR agent recognizes "commit and push" |
| `/line:work` | `/line-work` | Hook: "work" (manual) OR agent recognizes "start work cycle" |
| `/line:getting-started` | `/line-getting-started` | Steering file (manual include) for workflow guide |
| `/line:compact` | `/line-compact` | Hook: "compact" (manual) for context management |

### Agent Prompt Strategy

The agent prompt should include workflow command recognition:

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
mkdir -p "${KIRO_DIR}/hooks/workflows"

# Copy files
cp "${SCRIPT_DIR}/agents/line-cook.json" "${KIRO_DIR}/agents/"
cp "${SCRIPT_DIR}/steering/"*.md "${KIRO_DIR}/steering/"
cp "${SCRIPT_DIR}/skills/line-cook/SKILL.md" "${KIRO_DIR}/skills/line-cook/"
cp "${SCRIPT_DIR}/hooks/"*.sh "${KIRO_DIR}/hooks/"
cp "${SCRIPT_DIR}/hooks/workflows/"*.sh "${KIRO_DIR}/hooks/workflows/"

echo "Line Cook installed for Kiro CLI"
echo "Start a session with: kiro-cli --agent line-cook"
```

## Platform Comparison

| Feature | Claude Code | OpenCode | Kiro CLI |
|---------|-------------|----------|----------|
| Slash commands | Native (commands/) | Native (commands/) | Hooks with manual triggers |
| Skills | SKILL.md | SKILL.md | SKILL.md (same format) |
| Steering | CLAUDE.md, AGENTS.md | AGENTS.md | steering/*.md, AGENTS.md |
| Hooks | hooks/*.py | Plugin events | hooks/*.json + scripts |
| Agent config | settings.json | plugin.json | agents/*.json |
| Tool permissions | settings.json | plugin.json | agents/*.json (allowedTools) |

## Implementation Order

1. **Create directory structure** - Mirror OpenCode plugin layout
2. **Port AGENTS.md to steering** - Convert to Kiro steering format
3. **Create agent configuration** - Define tools, resources, permissions
4. **Create SKILL.md** - Ensure proper frontmatter for lazy loading
5. **Implement hooks** - Start with session-start and stop-check
6. **Create manual hooks** - For workflow commands
7. **Write installation script** - Single command setup
8. **Test workflow** - Verify prep→cook→serve→tidy cycle works

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
