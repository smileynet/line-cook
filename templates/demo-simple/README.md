# Line Cook Demo Template (Simple)

A pre-staged demo environment for testing Line Cook commands and onboarding new users.

## Quick Start

Set up a test environment with the demo beads:

```bash
# Create test directory and initialize git
mkdir /tmp/line-cook-demo && cd /tmp/line-cook-demo
git init && git commit --allow-empty -m "Initial commit"

# Copy CLAUDE.md for project context
cp ~/code/line-cook/templates/demo-simple/CLAUDE.md .

# Initialize beads with demo prefix
bd init --prefix=demo

# Import demo issues from JSONL
cat ~/code/line-cook/templates/demo-simple/issues.jsonl | bd import

# Set up dependency (demo-001.1.2 depends on demo-001.1.1)
bd dep add demo-001.1.2 demo-001.1.1

# Commit initial state
git add . && git commit -m "Initial demo setup"

# Verify the demo beads
bd list --status=open
bd ready
```

Or use the test setup script pattern from `tests/lib/setup-env.sh`.

## Run Loop

Run the autonomous loop:

```bash
# Run with verbose output
python ~/code/line-cook/scripts/line-loop.py -n 3 -v --skip-initial-sync

# Or with default settings
python ~/code/line-cook/scripts/line-loop.py -n 5
```

### Expected Results

| Iteration | Task | Outcome |
|-----------|------|---------|
| 1 | demo-001.1.1 | Creates todo.js, runs tests, closes task |
| 2 | demo-001.1.2 | Adds toggle complete (unblocked by 001.1.1), closes |
| 3 | - | No ready tasks (feature complete), triggers plate |
| - | demo-001.1 | Feature validated, closes |
| 4 | - | No work items ready, loop stops |

## What's Included

### Files

- `issues.jsonl` - Demo beads in JSONL format for `bd import`
- `CLAUDE.md` - Project context for the TodoWebApp demo

### Beads Hierarchy

```
demo-001  Epic: TodoWebApp MVP
└── demo-001.1  Feature: User can manage todos
    ├── demo-001.1.1  Task: Add todo item [READY]
    └── demo-001.1.2  Task: Mark todo complete [BLOCKED by 001.1.1]

demo-100  Epic: Parking Lot
└── demo-100.1  Task: Consider cloud sync [PARKED]
```

### Expected Command Outputs

| Command | Shows |
|---------|-------|
| `bd ready` | demo-001.1.1 only (the one ready task) |
| `bd blocked` | demo-001.1.2 (blocked by demo-001.1.1) |
| `bd list --status=open` | All 6 beads |
| `bd show demo-001.1.1` | Full task context with test specs |
| `bd show demo-001.1.2` | Shows dependency on demo-001.1.1 |

## Demonstrates

1. **Epic → Feature → Task hierarchy** - Three-tier structure
2. **Dependency blocking** - demo-001.1.2 is blocked until demo-001.1.1 closes
3. **Parking lot pattern** - demo-100.1 is filtered from ready work
4. **Rich descriptions** - Acceptance criteria, test specs, implementation notes
5. **Phase-based execution** - cook → serve → tidy → plate
6. **Feature completion triggers** - plate phase when all tasks done
7. **Epic closure** - Automatic when all features complete

## Workflow Demo

```bash
# See what's ready to work on
bd ready

# Get full context for the ready task
bd show demo-001.1.1

# Start working on it
bd update demo-001.1.1 --status=in_progress

# Or use Line Cook commands
/line:prep              # Shows demo-001.1.1 as recommended
/line:cook demo-001.1.1 # Execute with TDD workflow

# After completing demo-001.1.1
bd close demo-001.1.1
bd ready             # Now shows demo-001.1.2 (unblocked!)
```

## Customization

To adapt this template for your own demo:

1. Edit `issues.jsonl` with your own issues
2. Update `CLAUDE.md` with your project context
3. Run `bd import` to load your issues
4. Set up dependencies with `bd dep add`
