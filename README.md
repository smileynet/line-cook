# Line Cook

**Think big, execute small.**

Use the Mise Cycle to brainstorm freely — explore possibilities, ask hard questions, and plan ambitious work in a single creative session. Then hand off to the Run Cycle, where strong guardrails keep execution disciplined: small context windows prevent scope creep, and acceptance criteria at every level (task, feature, epic) ensure quality gates are met before work ships.

The result: you stay in deep work while AI handles structured execution with built-in checkpoints.

## The Two Cycles

```
  Mise Cycle                  Run Cycle
 ┌──────────────────┐       ┌──────────────────┐
 │                  │       │                  │
 │   /brainstorm    │       │   /prep ◄────┐   │
 │        ↓         │       │      ↓       │   │
 │     /scope       │       │   /cook      │   │
 │        ↓         │       │      ↓       │   │
 │   /finalize ─────┼─────► │   /serve     │   │
 │                  │       │      ↓       │   │
 └──────────────────┘       │   /tidy ─────┘   │
                            │    next task     │
                            └──────────────────┘
```

### Mise: Ideas → Tasks

Brainstorm → Scope → Finalize. Turn unstructured ideas into well-scoped, dependency-ordered tasks with test specs.

[Learn more →](docs/cycles/mise-cycle.md)

### Run: Tasks → Shipped Code

Prep → Cook → Serve → Tidy. Execute one task at a time with TDD, AI peer review, and automatic commit/push.

[Learn more →](docs/cycles/run-cycle.md)

### Loop: Autonomous Execution (Advanced)

Repeat Run Cycles hands-free until no ready tasks remain. Same quality gates, no supervision needed.

[Learn more →](docs/cycles/loop-cycle.md)

## Quick Start

```bash
bd init              # Initialize beads in your project
/line:mise           # Plan your work (brainstorm → scope → finalize)
# Clear context
/line:run            # Execute (prep → cook → serve → tidy)
```

> **New here?** See the [Getting Started](docs/getting-started.md) walkthrough.

## When to Use / Skip

**Use Line Cook when:**
- Work spans multiple sessions
- Tasks have dependencies
- You want automated code review
- You're building trust in AI workflows

**Skip it when:**
- Quick one-off fixes
- Exploratory coding or prototyping
- Active pair programming
- Setup takes longer than the work

## Installation

### 1. Install beads

[Beads](https://github.com/steveyegge/beads) provides git-native issue tracking with memory between sessions.

```bash
brew install steveyegge/beads/bd
```

> See [beads repo](https://github.com/steveyegge/beads) for npm/go options.

### 2. Install Line Cook

| Platform | Install | Details |
|----------|---------|---------|
| **Claude Code** | `/plugin marketplace add smileynet/line-cook` then `/plugin install line@line-cook` | [Full guide](docs/installation/claude-code.md) |
| **OpenCode** | `git clone ... && ./install.sh` | [Full guide](docs/installation/opencode.md) |
| **Kiro** | `git clone ... && python3 install.py` | [Full guide](docs/installation/kiro.md) |

## Learn More

- [Getting Started](docs/getting-started.md) — Walkthrough from install to first shipped task
- [FAQ](docs/faq.md) — Common questions and troubleshooting
- [Command Reference](docs/reference/commands.md) — All commands and options
- [AGENTS.md](AGENTS.md) — Technical reference for contributors

## Spice Rack

Domain-specific addons that enhance planning. Spices load automatically during `/mise` when relevant project context is detected.

| Spice | What it adds |
|-------|-------------|
| [game-spice](https://github.com/smileynet/game-spice) | MLP scoping, core loop design, game planning anti-patterns |

```bash
/plugin install game-spice@line-cook
```

## License

MIT

## Related

- [beads](https://github.com/steveyegge/beads) — Git-native issue tracking
- [Gas Town](https://github.com/steveyegge/gastown) — Autonomous agent framework
