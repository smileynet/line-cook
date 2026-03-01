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
 │     /sample      │       │   /cook      │   │
 │        ↓         │       │      ↓       │   │
 │     /scope       │       │   /serve     │   │
 │        ↓         │       │      ↓       │   │
 │   /finalize ─────┼─────► │   /tidy ─────┘   │
 │                  │       │    next task     │
 └──────────────────┘       └──────────────────┘
```

### Mise: Ideas → Tasks

Brainstorm → Sample → Scope → Finalize. Turn unstructured ideas into well-scoped, dependency-ordered tasks with test specs.

[Learn more →](docs/cycles/mise-cycle.md)

### Run: Tasks → Shipped Code

Prep → Cook → Serve → Tidy. Execute one task at a time with TDD, AI peer review, and automatic commit/push.

[Learn more →](docs/cycles/run-cycle.md)

### Loop: Autonomous Execution (Advanced)

Repeat Run Cycles hands-free until no ready tasks remain. Same quality gates, no supervision needed. Supports Claude Code and Kiro via `--cli kiro`.

[Learn more →](docs/cycles/loop-cycle.md)

## Quick Start

```bash
/line:init           # Verify your setup
bd init              # Initialize beads in your project
/line:mise           # Plan your work (brainstorm → sample → scope → finalize)
# Clear context
/line:run            # Execute (prep → cook → serve → tidy)
```

> **New here?** Run `/line:init` to verify your setup, then see the [Getting Started](docs/getting-started.md) walkthrough.

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
brew install beads
```

> See [beads repo](https://github.com/steveyegge/beads) for npm/go options.

### 2. Install Line Cook

**Claude Code:**
```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```
> [Full guide](docs/installation/claude-code.md)

**OpenCode:**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
cd ~/line-cook/plugins/opencode && ./install.sh
```
> [Full guide](docs/installation/opencode.md)

**Kiro:**
```bash
git clone https://github.com/smileynet/line-cook.git ~/line-cook
python3 ~/line-cook/plugins/kiro/install.py
```
> [Full guide](docs/installation/kiro.md)

## Learn More

- [Getting Started](docs/getting-started.md) — Walkthrough from install to first shipped task
- [Command Reference](docs/reference/commands.md) — All commands and options
- [AGENTS.md](AGENTS.md) — Technical reference for contributors

## FAQ

**What if all my tasks are blocked?**
Run `/line:plan-audit` to check your dependency graph. Common causes: circular dependencies, a blocker that was never created, or a task that's done but wasn't closed (`bd close <id>`).

> More questions answered in the [full FAQ](docs/faq.md).

## Spice Rack

Domain-specific addons that enhance planning. Spices load automatically during `/mise` when relevant project context is detected.

| Spice | What it adds |
|-------|-------------|
| [game-spice](https://github.com/smileynet/game-spice) | Interactive game design workflow — brainstorm, simulate, and build-plan commands plus 14 knowledge skills covering MLP scoping, core loops, economy design, mechanics palette, playtesting, and architecture review |
| [code-spice](https://github.com/smileynet/code-spice) | Code quality foundations — readability, naming, refactoring, error handling, antipatterns, tradeoff analysis, testing guidance, and an automated code-quality critic for `/line:serve` |

**game-spice** is for game projects (design sessions, balance checks, walkthroughs). **code-spice** is for any software project (code quality, review prep, smell detection). Both can be installed together.

```bash
/plugin install game@line-cook   # game design workflow
/plugin install code@line-cook   # code quality toolkit
```

## License

MIT

## Related

- [beads](https://github.com/steveyegge/beads) — Git-native issue tracking
- [Gas Town](https://github.com/steveyegge/gastown) — Autonomous agent framework
