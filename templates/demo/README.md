# Line Cook Demo Template

A pre-staged demo environment for testing Line Cook commands and onboarding new users.

## Quick Start

Set up a test environment with the demo beads:

```bash
# Create test directory and initialize git
mkdir /tmp/line-cook-demo && cd /tmp/line-cook-demo
git init && git commit --allow-empty -m "Initial commit"
git config user.email "demo@test.com" && git config user.name "Demo"

# Copy CLAUDE.md for project context
cp ~/code/line-cook/templates/demo/CLAUDE.md .

# Initialize beads with demo prefix
bd init --prefix=demo

# Import demo issues from JSONL
cat ~/code/line-cook/templates/demo/issues.jsonl | bd import

# Set up dependency (demo-004 depends on demo-003)
bd dep add demo-004 demo-003

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
| 1 | demo-003 | Creates todo.js, runs tests, closes task |
| 2 | demo-004 | Adds toggle complete (unblocked by 003), closes |
| 3 | - | No ready tasks (feature complete), triggers plate |
| - | demo-002 | Feature validated, closes |
| 4 | - | No work items ready, loop stops |

## What's Included

### Files

- `issues.jsonl` - Demo beads in JSONL format for `bd import`
- `CLAUDE.md` - Project context for the TodoWebApp demo
- `.beads/` - Pre-configured beads (alternative to import)

### Beads Hierarchy

```
demo-001  Epic: TodoWebApp MVP
└── demo-002  Feature: User can manage todos
    ├── demo-003  Task: Add todo item [READY]
    └── demo-004  Task: Mark todo complete [BLOCKED by 003]

demo-100  Epic: Parking Lot
└── demo-101  Task: Consider cloud sync [PARKED]
```

### Expected Command Outputs

| Command | Shows |
|---------|-------|
| `bd ready` | demo-003 only (the one ready task) |
| `bd blocked` | demo-004 (blocked by demo-003) |
| `bd list --status=open` | All 6 beads |
| `bd show demo-003` | Full task context with test specs |
| `bd show demo-004` | Shows dependency on demo-003 |

## Demonstrates

1. **Epic → Feature → Task hierarchy** - Three-tier structure
2. **Dependency blocking** - demo-004 is blocked until demo-003 closes
3. **Parking lot pattern** - demo-101 is filtered from ready work
4. **Rich descriptions** - Acceptance criteria, test specs, implementation notes
5. **Phase-based execution** - cook → serve → tidy → plate
6. **Feature completion triggers** - plate phase when all tasks done
7. **Epic closure** - Automatic when all features complete

## Workflow Demo

```bash
# See what's ready to work on
bd ready

# Get full context for the ready task
bd show demo-003

# Start working on it
bd update demo-003 --status=in_progress

# Or use Line Cook commands
/line:prep           # Shows demo-003 as recommended
/line:cook demo-003  # Execute with TDD workflow

# After completing demo-003
bd close demo-003
bd ready             # Now shows demo-004 (unblocked!)
```

## Customization

To adapt this template for your own demo:

1. Edit `issues.jsonl` with your own issues
2. Update `CLAUDE.md` with your project context
3. Run `bd import` to load your issues
4. Set up dependencies with `bd dep add`
