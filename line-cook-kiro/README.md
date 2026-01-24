# Line Cook for Kiro CLI

Kiro CLI adapter for the line-cook workflow orchestration system.

## Directory Structure

```
line-cook-kiro/
├── agents/           # Custom agent configurations
│   ├── line-cook.json
│   ├── taster.json
│   ├── sous-chef.json
│   └── maitre.json
├── steering/         # Steering files (always-loaded context)
│   ├── line-cook.md
│   ├── beads.md
│   ├── session.md
│   ├── getting-started.md
│   ├── taster.md
│   ├── sous-chef.md
│   └── maitre.md
├── skills/           # Lazy-loaded documentation
│   └── line-cook/
│       └── SKILL.md
└── install.py        # Installation script
```

## Workflow Commands

Kiro CLI does **not** support custom slash commands. Workflow invocation uses **natural language recognition** via the steering file:

| User Input | Workflow |
|------------|----------|
| "getting started", "help", "guide" | Show workflow guide |
| "mise", "/mise", "plan", "planning" | Plan work breakdown |
| "prep", "/prep", "sync state" | Run prep workflow |
| "cook", "/cook", "start task" | Run cook workflow |
| "serve", "/serve", "review" | Run serve workflow |
| "tidy", "/tidy", "commit" | Run tidy workflow |
| "plate", "/plate", "validate feature" | Validate completed feature |
| "service", "/service", "full service" | Full service (mise→prep→cook→serve→tidy→plate) |
| "work", "/work", "full cycle" | Quick cycle (prep→cook→serve→tidy) |

The steering file (`steering/line-cook.md`) teaches the agent to recognize these phrases and execute the corresponding workflow.

## Installation

```bash
./install.py
# or: python3 install.py
```

## Usage

Start Kiro CLI with the line-cook agent:

```bash
kiro-cli --agent line-cook
```

## See Also

- [Line Cook README](../README.md)
- [AGENTS.md](../AGENTS.md) - Technical documentation
