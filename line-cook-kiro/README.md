# Line Cook for Kiro CLI

Kiro CLI adapter for the line-cook workflow orchestration system.

## Directory Structure

```
line-cook-kiro/
├── agents/           # Custom agent configurations
│   └── line-cook.json
├── steering/         # Steering files (always-loaded context)
│   ├── line-cook.md
│   ├── beads.md
│   └── session.md
├── skills/           # Lazy-loaded documentation
│   └── line-cook/
│       └── SKILL.md
├── scripts/          # Hook scripts (referenced from agent JSON)
│   ├── session-start.sh
│   ├── pre-tool-use.sh
│   ├── post-tool-use.sh
│   └── stop-check.sh
└── install.sh        # Installation script
```

## Hook Architecture

**Important**: Kiro CLI hooks are defined **inline in agent JSON**, not as separate configuration files. The `scripts/` directory contains shell scripts that are referenced by path from the agent configuration:

```json
{
  "name": "line-cook",
  "hooks": {
    "AgentSpawn": {
      "command": "bash ~/.kiro/scripts/session-start.sh",
      "timeout_ms": 30000
    },
    "Stop": {
      "command": "bash ~/.kiro/scripts/stop-check.sh",
      "timeout_ms": 30000
    }
  }
}
```

**Note**: Paths shown assume global installation to `~/.kiro/`. For project-local installation, use `.kiro/scripts/` relative paths.

Kiro CLI has 5 hook types: `AgentSpawn`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`.

## Workflow Commands

Kiro CLI does **not** support custom slash commands. Workflow invocation uses **natural language recognition** via the steering file:

| User Input | Workflow |
|------------|----------|
| "prep", "/prep", "sync state" | Run prep workflow |
| "cook", "/cook", "start task" | Run cook workflow |
| "serve", "/serve", "review" | Run serve workflow |
| "tidy", "/tidy", "commit" | Run tidy workflow |
| "work", "/work", "full cycle" | Run prep→cook→serve→tidy sequentially |

The steering file (`steering/line-cook.md`) teaches the agent to recognize these phrases and execute the corresponding workflow.

## Installation

```bash
./install.sh
```

## Usage

Start Kiro CLI with the line-cook agent:

```bash
kiro-cli --agent line-cook
```

## See Also

- [Research: Kiro Command System](../docs/internal/research/kiro-command-system.md)
- [Line Cook README](../README.md)
