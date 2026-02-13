# Line Cook for Kiro CLI

Kiro CLI adapter for the line-cook workflow orchestration system.

## Directory Structure

```
kiro/
├── agents/           # Custom agent configurations
│   ├── line-cook.json
│   ├── taster.json
│   ├── sous-chef.json
│   ├── maitre.json
│   ├── polisher.json
│   └── critic.json
├── steering/         # Steering files (always-loaded context)
│   ├── line-cook.md
│   ├── beads.md
│   ├── session.md
│   ├── taster.md
│   ├── sous-chef.md
│   ├── maitre.md
│   ├── polisher.md
│   └── critic.md
├── prompts/          # @prompt invocations (17 prompts)
│   ├── line-architecture-audit.md
│   ├── line-brainstorm.md
│   ├── line-close-service.md
│   ├── line-cook.md
│   ├── line-decision.md
│   ├── line-finalize.md
│   ├── line-getting-started.md
│   ├── line-help.md
│   ├── line-loop.md
│   ├── line-mise.md
│   ├── line-plan-audit.md
│   ├── line-plate.md
│   ├── line-prep.md
│   ├── line-run.md
│   ├── line-scope.md
│   ├── line-serve.md
│   └── line-tidy.md
├── skills/           # Lazy-loaded documentation
│   └── line-cook/
│       └── SKILL.md
└── install.py        # Installation script
```

## Workflow Commands

Line Cook supports two invocation methods:

### 1. @Prompt Invocation (Explicit)

Use `@line-<phase>` for explicit workflow control:

| Prompt | Purpose |
|--------|---------|
| `@line-brainstorm` | Explore problem space (divergent thinking) |
| `@line-scope` | Structure work breakdown (convergent thinking) |
| `@line-finalize` | Convert plan to beads and test specs |
| `@line-mise` | Full planning (brainstorm→scope→finalize) |
| `@line-prep` | Sync state, show ready tasks |
| `@line-cook` | Execute task with TDD cycle |
| `@line-serve` | Review changes |
| `@line-tidy` | Commit and push |
| `@line-plate` | Validate completed feature |
| `@line-run` | Full cycle (prep→cook→serve→tidy) |
| `@line-decision` | Manage architecture decisions |
| `@line-close-service` | Validate and close completed epic |
| `@line-architecture-audit` | Audit codebase architecture |
| `@line-plan-audit` | Audit planning quality |
| `@line-help` | Show available commands |
| `@line-loop` | Manage autonomous loop |
| `@line-getting-started` | Show workflow guide |

**Examples:**
```
@line-prep
@line-cook lc-042
@line-run
```

### 2. Natural Language (Flexible)

The steering file teaches the agent to recognize these phrases:

| User Input | Workflow |
|------------|----------|
| "brainstorm", "explore", "diverge" | Explore problem space |
| "scope", "decompose", "break down" | Structure work breakdown |
| "finalize", "create beads", "persist plan" | Convert plan to beads |
| "mise", "plan", "planning" | Full planning cycle |
| "prep", "sync state" | Run prep workflow |
| "cook", "start task" | Run cook workflow (TDD cycle) |
| "serve", "review" | Run serve workflow |
| "tidy", "commit" | Run tidy workflow |
| "plate", "validate feature" | Validate completed feature |
| "close-service", "close epic" | Validate and close completed epic |
| "run", "full run", "full cycle" | Full run cycle |
| "decision", "adr" | Manage architecture decisions |
| "architecture-audit", "audit code" | Audit codebase architecture |
| "plan-audit", "audit plan" | Audit planning quality |
| "help", "commands" | Show available commands |
| "loop", "autonomous" | Manage autonomous loop |
| "getting started", "guide" | Show workflow guide |

**Recommendation:** Use @prompts for predictable behavior; use natural language for conversational flow.

## Installation

```bash
python3 install.py
```

## Usage

```bash
kiro-cli chat -a -r --agent line-cook
```

Then use `@line-prep` to start or say "prep".

## Known Issues

- `$ARGUMENTS` with special characters may not be passed correctly to prompts ([#4141](https://github.com/kirodotdev/Kiro/issues/4141))

## See Also

- [Line Cook README](../../README.md)
- [AGENTS.md](../../AGENTS.md) - Technical documentation
