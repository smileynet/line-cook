# Research: Claude Code Plugin Architecture

**Issue**: lc-bkx
**Date**: 2026-01-19
**Purpose**: Study Claude Code plugin system and how CLI tools can integrate.

## Executive Summary

Claude Code plugins provide a structured way to extend Claude Code with:
- Custom slash commands (namespaced)
- Hook event handlers
- Agent definitions
- Skills with lazy-loaded documentation
- MCP servers for tool integration

Plugins are distributed via marketplaces (GitHub repos or local directories) and installed to a local cache. The `beads` plugin is the primary reference implementation.

## 1. Plugin Manifest Structure (plugin.json)

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique identifier (kebab-case). Becomes namespace for commands. |

### Recommended Fields

```json
{
  "name": "my-plugin",
  "description": "Brief plugin description",
  "version": "1.0.0",
  "author": {
    "name": "Author Name",
    "url": "https://github.com/author"
  },
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "homepage": "https://docs.example.com",
  "keywords": ["keyword1", "keyword2"]
}
```

### Component Path Fields

| Field | Type | Default |
|-------|------|---------|
| `commands` | string\|array | `./commands/` |
| `agents` | string\|array | `./agents/` |
| `skills` | string\|array | `./skills/` |
| `hooks` | string\|object | Inline or `./hooks/hooks.json` |
| `mcpServers` | string\|object | Inline or `./.mcp.json` |
| `lspServers` | string\|object | Inline or `./.lsp.json` |
| `outputStyles` | string\|array | Custom output style files |

Note: Default directories are loaded automatically in addition to custom paths.

### Environment Variables

| Variable | Expands To |
|----------|-----------|
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to plugin directory |

## 2. Directory Structure

### Standard Layout

```
my-plugin/
├── .claude-plugin/           # Metadata (required)
│   └── plugin.json           # Plugin manifest
├── commands/                 # Slash commands (default)
│   └── *.md
├── agents/                   # Subagents (default)
│   └── *.md
├── skills/                   # Skills (default)
│   └── my-skill/
│       ├── SKILL.md
│       └── resources/
├── hooks/                    # Hook configs
│   └── hooks.json
└── scripts/                  # Hook scripts
```

### Critical Rule

Only `plugin.json` goes in `.claude-plugin/`. All other directories (`commands/`, `agents/`, `skills/`) go at the plugin root.

## 3. Slash Commands

### Location and Namespace

- Files in `commands/` directory as Markdown
- Automatically namespaced: `hello.md` → `/plugin-name:hello`

### Command Format

```markdown
---
description: Brief description shown in /help
---

# Command Name

Instructions for Claude.

Use $ARGUMENTS for user input.
```

### Example: beads commands

The beads plugin has 30+ commands including:
- `/beads:create`, `/beads:update`, `/beads:close`
- `/beads:list`, `/beads:ready`, `/beads:blocked`
- `/beads:sync`, `/beads:prime`

## 4. Hooks

### Hook Configuration

Can be inline in `plugin.json` or in separate file:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bd prime"
      }]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "bd prime"
      }]
    }]
  }
}
```

### Available Hook Events

| Event | When | Use Case |
|-------|------|----------|
| `SessionStart` | Session begins | Load context |
| `SessionEnd` | Session ends | Cleanup, archiving |
| `PreToolUse` | Before tool executes | Validation, approval |
| `PostToolUse` | After tool succeeds | Formatting, logging |
| `PostToolUseFailure` | After tool fails | Error handling |
| `PreCompact` | Before compaction | Preserve context |
| `Stop` | Claude attempts stop | Completion guards |
| `SubagentStart` | Subagent starts | Agent setup |
| `SubagentStop` | Subagent terminates | Agent cleanup |
| `Notification` | Notification sent | Custom notifications |
| `UserPromptSubmit` | Prompt submitted | Enhancement |
| `PermissionRequest` | Permission dialog | Auto-approval logic |

### Hook Types

| Type | Usage |
|------|-------|
| `command` | Shell command or executable |
| `prompt` | LLM-evaluated prompt |
| `agent` | Agentic verification |

### Hook Matcher

- Empty string `""` or `"*"` matches all events
- Regex pattern to match specific tools: `"matcher": "Write|Edit"`
- SessionStart matchers: `startup`, `resume`, `clear`, `compact`
- PreCompact matchers: `manual`, `auto`
- Notification matchers: `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog`

## 5. Skills

### SKILL.md Format

```markdown
---
name: skill-name
description: >
  Multi-line description for AI discovery.
allowed-tools: "Read,Bash(bd:*)"
---

# Skill Name

Main content loaded when skill is invoked.

## Resources

| Resource | Content |
|----------|---------|
| [REFERENCE.md](resources/REFERENCE.md) | Detailed docs |
```

### SKILL.md Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Lowercase, hyphens, max 64 chars |
| `description` | Yes | What it does and when to use it (max 1024 chars) |
| `allowed-tools` | No | Tools Claude can use without asking permission |
| `model` | No | Specific model to use when skill is active |
| `context` | No | Set to `fork` for isolated sub-agent context |
| `agent` | No | Agent type when `context: fork` (e.g., `Explore`, `Plan`) |
| `hooks` | No | Lifecycle hooks (`PreToolUse`, `PostToolUse`, `Stop`) |
| `user-invocable` | No | Controls slash command visibility (default: true) |

### Progressive Disclosure

Skills use lazy-loading:
1. SKILL.md frontmatter for discovery
2. Main content when invoked
3. Resources on-demand via links

## 6. Reference: beads Plugin Structure

```
beads/
├── .claude-plugin/
│   └── plugin.json        # Manifest with hooks
├── agents/
│   └── task-agent.md      # Specialized agent
├── commands/              # 30+ slash commands
│   ├── create.md
│   ├── update.md
│   ├── list.md
│   ├── ready.md
│   ├── sync.md
│   └── ...
└── skills/
    └── beads/
        ├── SKILL.md       # Main skill definition
        ├── CLAUDE.md      # AI instructions
        └── resources/     # 15+ reference docs
```

### beads plugin.json (v0.47.2 snapshot)

```json
{
  "name": "beads",
  "description": "AI-supervised issue tracker for coding workflows",
  "version": "0.47.2",  // Note: version at time of research
  "author": {
    "name": "Steve Yegge",
    "url": "https://github.com/steveyegge"
  },
  "repository": "https://github.com/steveyegge/beads",
  "license": "MIT",
  "hooks": {
    "SessionStart": [{
      "hooks": [{"type": "command", "command": "bd prime"}]
    }],
    "PreCompact": [{
      "hooks": [{"type": "command", "command": "bd prime"}]
    }]
  }
}
```

## 7. Reference: Current line-cook Plugin

```
line/
├── .claude-plugin/
│   └── plugin.json        # Minimal manifest
└── commands/
    ├── cook.md
    ├── getting-started.md
    ├── prep.md
    ├── serve.md
    ├── setup.md
    ├── tidy.md
    └── work.md
```

### Current line-cook plugin.json (v0.4.5)

```json
{
  "name": "line",
  "description": "Task-focused workflow orchestration for Claude Code sessions - prep, cook, serve, tidy",
  "version": "0.4.5",
  "author": {
    "name": "smileynet",
    "url": "https://github.com/smileynet"
  },
  "repository": "https://github.com/smileynet/line-cook",
  "license": "MIT",
  "homepage": "https://github.com/smileynet/line-cook",
  "keywords": ["claude-code", "workflow", "task-management", "beads", "productivity"]
}
```

### Missing from line-cook (opportunities)

1. **Hooks** - No SessionStart/PreCompact hooks
2. **Skills** - No SKILL.md for AI discovery
3. **Agents** - No specialized agents

## 8. Distribution and Installation

### Marketplaces

Plugins distributed via marketplace repos:
- GitHub: `"source": {"source": "github", "repo": "owner/repo"}`
- Directory: `"source": {"source": "directory", "path": "/local/path"}`

### Installation Scopes

| Scope | Location | Shared |
|-------|----------|--------|
| `user` | `~/.claude/settings.json` | All projects |
| `project` | `.claude/settings.json` | Via git |
| `local` | `.claude/settings.local.json` | None |

### Commands

```bash
/plugin marketplace add owner/repo
/plugin install plugin-name@marketplace
/plugin update plugin-name@marketplace
/plugin disable plugin-name@marketplace
```

### Plugin Cache

Installed plugins copied to cache:
```
~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
```

## 9. CLI Tool Integration Patterns

### Pattern 1: Commands invoke CLI

Slash commands call external CLI:
```markdown
# /beads:create

Run `bd create` with the following arguments...
```

### Pattern 2: Hooks call CLI

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "lc prime"
      }]
    }]
  }
}
```

### Pattern 3: MCP Server

Bundle MCP server in plugin:
```json
{
  "mcpServers": {
    "my-server": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

## 10. Line-cook Integration Plan

### Phase 1: Enhance Current Plugin

1. Add hooks to plugin.json:
```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{"type": "command", "command": "lc prime"}]
    }],
    "PreCompact": [{
      "hooks": [{"type": "command", "command": "lc preserve"}]
    }]
  }
}
```

2. Add SKILL.md for discoverability

### Phase 2: Go CLI Development

1. Create `lc` binary with subcommands:
   - `lc prime` - Load workflow context
   - `lc preserve` - Save state before compaction
   - `lc hook <event>` - Handle hook events

2. Update hooks to call `lc` instead of Python

### Phase 3: Advanced Integration

1. Git hooks via `lc hook pre-push`
2. Session completion enforcement
3. Optional MCP server for rich tool integration

## Key Takeaways

1. **Plugin namespace** - `line` namespace gives `/line:cook`, `/line:prep`, etc.
2. **Hooks are simple** - Just shell commands, no complex setup
3. **Skills enhance discovery** - AI can find and invoke automatically
4. **CLI is the foundation** - Hooks and commands delegate to CLI
5. **beads is the model** - Follow its patterns for consistency

## References

- Current line-cook plugin: `~/.claude/plugins/cache/line-cook-marketplace/line/`
- beads plugin reference: `~/.claude/plugins/cache/beads-marketplace/beads/`
- Claude Code docs: https://code.claude.com/docs/
