# Line Cook Demo Template (Kiro)

A pre-staged demo environment for testing Line Cook with **Kiro CLI**. Uses a Python todo CLI project — no build tools or frameworks required.

## Prerequisites

- Python 3.8+
- [beads](https://github.com/smileynet/beads) (`bd` CLI)
- [Kiro CLI](https://kiro.dev) (`kiro-cli`)

## Quick Start

### Automated Setup

```bash
# Run the setup script (creates project at /tmp/line-cook-demo-kiro)
bash ~/code/line-cook/docs/demos/demo-kiro/setup.sh
```

### Manual Setup

```bash
# Create test directory and initialize git
mkdir /tmp/line-cook-demo-kiro && cd /tmp/line-cook-demo-kiro
git init && git commit --allow-empty -m "Initial commit"

# Copy project README (Kiro reads README.md for project context)
cp ~/code/line-cook/docs/demos/demo-kiro/project-readme.md ./README.md

# Initialize beads with demo prefix
bd init --prefix=demo

# Import demo issues from JSONL
cat ~/code/line-cook/docs/demos/demo-kiro/issues.jsonl | bd import

# Set up dependency (demo-001.1.2 depends on demo-001.1.1)
bd dep add demo-001.1.2 demo-001.1.1

# Install Kiro plugin locally
python3 ~/code/line-cook/plugins/kiro/install.py --local

# Commit initial state
git add . && git commit -m "Initial demo setup with Kiro plugin"

# Verify
bd list --status=open
bd ready
```

## Test Individual Phases (Interactive)

Start Kiro with the line-cook agent:

```bash
cd /tmp/line-cook-demo-kiro
kiro-cli chat --agent line-cook
```

Then use `@line-*` prompts or natural language:

```
# Show ready work
@line-prep

# Execute the ready task with TDD
@line-cook

# Or use natural language (better for passing arguments)
cook demo-001.1.1

# Review changes
@line-serve

# Commit and push
@line-tidy

# Full cycle (prep + cook + serve + tidy)
@line-run
```

> **Note:** Kiro discards text after `@` commands ([kiro#4141](https://github.com/aws/kiro/issues/4141)).
> Use natural language for commands with arguments: say `cook demo-001.1.1` instead of `@line-cook demo-001.1.1`.

## Test Autonomous Loop

Run the loop with Kiro as the AI backend:

```bash
cd /tmp/line-cook-demo-kiro

# Run 3 iterations with verbose output
python3 ~/code/line-cook/core/line-loop-cli.py \
  --cli kiro \
  --max-iterations 3 \
  --skip-initial-sync \
  -v

# Or with shorter timeouts for quick testing
python3 ~/code/line-cook/core/line-loop-cli.py \
  --cli kiro \
  --max-iterations 5 \
  --cook-timeout 600 \
  --serve-timeout 300 \
  --skip-initial-sync \
  -v
```

### Expected Results

| Iteration | Task | Outcome |
|-----------|------|---------|
| 1 | demo-001.1.1 | Creates todo.py with add/list, runs tests, closes task |
| 2 | demo-001.1.2 | Adds complete command (unblocked by 001.1.1), closes |
| 3 | - | No ready tasks, triggers plate for feature |
| - | demo-001.1 | Feature validated, closes |
| 4 | - | No work items ready, loop stops |

## What's Included

### Files

- `issues.jsonl` - Demo beads in JSONL format for `bd import`
- `project-readme.md` - Project context (copied as `README.md` into demo)
- `setup.sh` - Automated setup script

### Beads Hierarchy

```
demo-001  Epic: Python Todo CLI
+-- demo-001.1  Feature: User can manage todos via CLI
    +-- demo-001.1.1  Task: Add todo command [READY]
    +-- demo-001.1.2  Task: Complete todo command [BLOCKED by 001.1.1]

demo-100  Epic: Retrospective & Parking Lot
+-- demo-100.1  Task: Consider SQLite storage [PARKED]
```

### Expected Command Outputs

| Command | Shows |
|---------|-------|
| `bd ready` | demo-001.1.1 only (the one ready task) |
| `bd blocked` | demo-001.1.2 (blocked by demo-001.1.1) |
| `bd list --status=open` | All 6 beads |
| `bd show demo-001.1.1` | Full task context with test specs |
| `bd show demo-001.1.2` | Shows dependency on demo-001.1.1 |

## Kiro vs Claude Code

| Aspect | Kiro | Claude Code |
|--------|------|-------------|
| Agent config | `.kiro/agents/*.json` | Built-in via CLAUDE.md |
| Context | `.kiro/steering/*.md` | CLAUDE.md + hooks |
| Phase commands | `@line-prep` or "prep" | `/line:prep` |
| Loop CLI flag | `--cli kiro` | `--cli claude` (default) |
| Output format | Plain text | Streaming JSON |
| Permission model | `--trust-all-tools` | `--dangerously-skip-permissions` |

## Troubleshooting

```bash
# Verify Kiro plugin is installed
ls .kiro/agents/   # Should list 6 JSON files
ls .kiro/prompts/  # Should list 21 MD files

# Check beads state
bd doctor
bd stats

# Verify Kiro can see the agent
kiro-cli agents list  # Should show line-cook

# Re-install plugin if needed
python3 ~/code/line-cook/plugins/kiro/install.py --local
```

## Cleanup

```bash
rm -rf /tmp/line-cook-demo-kiro
```
