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
├── prompts/          # @prompt invocations
│   ├── line-prep.md
│   ├── line-cook.md
│   ├── line-serve.md
│   ├── line-tidy.md
│   ├── line-mise.md
│   ├── line-plate.md
│   ├── line-run.md
│   └── line-getting-started.md
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
| `@line-prep` | Sync state, show ready tasks |
| `@line-cook` | Execute task with TDD cycle |
| `@line-serve` | Review changes |
| `@line-tidy` | Commit and push |
| `@line-mise` | Create work breakdown |
| `@line-plate` | Validate completed feature |
| `@line-run` | Full cycle (prep→cook→serve→tidy) |
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
| "getting started", "help", "guide" | Show workflow guide |
| "mise", "plan", "planning" | Plan work breakdown |
| "prep", "sync state" | Run prep workflow |
| "cook", "start task" | Run cook workflow (TDD cycle) |
| "serve", "review" | Run serve workflow |
| "tidy", "commit" | Run tidy workflow |
| "plate", "validate feature" | Validate completed feature |
| "run", "full run", "full cycle" | Full run cycle |

**Recommendation:** Use @prompts for predictable behavior, natural language for conversational flow.

## Installation

```bash
python3 install.py
```

## Usage

```bash
kiro-cli chat -a -r --agent line-cook
```

Then use `@line-prep` to start or say "prep".

## See Also

- [Line Cook README](../README.md)
- [AGENTS.md](../AGENTS.md) - Technical documentation
