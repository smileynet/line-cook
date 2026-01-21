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
├── hooks/            # Lifecycle event handlers
│   ├── session-start.sh
│   ├── pre-tool-use.sh
│   ├── post-tool-use.sh
│   ├── stop-check.sh
│   └── workflows/    # Manual-trigger workflow hooks
│       ├── prep.sh
│       ├── cook.sh
│       ├── serve.sh
│       └── tidy.sh
└── install.sh        # Installation script
```

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
