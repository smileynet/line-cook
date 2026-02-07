# Line Cook Demo Template (Web Dashboard)

A multi-feature demo environment for testing Line Cook's loop, plate, and epic completion across 9 tasks. Builds a Go + Templ + SQLite dashboard that monitors Line Cook operations.

## Prerequisites

- Go 1.25+
- templ CLI: `go install github.com/a-h/templ/cmd/templ@latest`

## Quick Start

Set up a test environment with the demo-web beads:

```bash
# Create test directory and initialize git
mkdir /tmp/line-cook-demo-web && cd /tmp/line-cook-demo-web
git init && git commit --allow-empty -m "Initial commit"

# Copy CLAUDE.md for project context
cp ~/code/line-cook/templates/demo-web/CLAUDE.md .

# Initialize beads with demo prefix
bd init --prefix=demo

# Import demo issues from JSONL
cat ~/code/line-cook/templates/demo-web/issues.jsonl | bd import

# Set up dependencies
bd dep add demo-001.1.2 demo-001.1.1
bd dep add demo-001.1.3 demo-001.1.2
bd dep add demo-001.2.1 demo-001.1.2
bd dep add demo-001.2.2 demo-001.2.1
bd dep add demo-001.3.1 demo-001.1.2
bd dep add demo-001.3.2 demo-001.3.1
bd dep add demo-001.4.1 demo-001.1.3
bd dep add demo-001.4.2 demo-001.4.1

# Commit initial state
git add . && git commit -m "Initial demo setup"

# Verify the demo beads
bd list --status=open
bd ready
```

## Run Loop

Run the autonomous loop:

```bash
# Run with verbose output
python ~/code/line-cook/plugins/claude-code/scripts/line-loop.py -n 10 -v --skip-initial-sync

# Or with default settings
python ~/code/line-cook/plugins/claude-code/scripts/line-loop.py -n 12
```

### Expected Results

| Iteration | Task | Outcome |
|-----------|------|---------|
| 1 | demo-001.1.1 | Creates Go HTTP server with health endpoint |
| 2 | demo-001.1.2 | Adds SQLite schema and event storage (unblocked) |
| 3 | demo-001.1.3 | Dashboard page showing loop status (unblocked) |
| 4 | demo-001.2.1 | Ingest history.jsonl into SQLite (unblocked) |
| 5 | demo-001.3.1 | POST /events endpoint for hook data (unblocked) |
| 6 | demo-001.2.2 | Timeline component with iteration cards (unblocked) |
| 7 | demo-001.3.2 | Event feed with type filtering (unblocked) |
| 8 | demo-001.4.1 | WebSocket hub and client management (unblocked) |
| 9 | demo-001.4.2 | HTMX streaming for real-time updates (unblocked) |
| 10 | - | No ready tasks, triggers plate for features |
| 11 | - | Epic completion, loop stops |

## What's Included

### Files

- `issues.jsonl` - Demo beads in JSONL format for `bd import`
- `CLAUDE.md` - Project context for the Line Cook Dashboard

### Beads Hierarchy

```
demo-001  Epic: Line Cook Dashboard MVP (P2)
├── demo-001.1  Feature: Real-time loop status display
│   ├── demo-001.1.1  Task: Go HTTP server with health endpoint [READY]
│   ├── demo-001.1.2  Task: SQLite schema and event storage [blocked by .1.1]
│   └── demo-001.1.3  Task: Dashboard page showing loop status [blocked by .1.2]
├── demo-001.2  Feature: Iteration history timeline
│   ├── demo-001.2.1  Task: Ingest history.jsonl into SQLite [blocked by .1.2]
│   └── demo-001.2.2  Task: Timeline component with iteration cards [blocked by .2.1]
├── demo-001.3  Feature: Hook event receiver
│   ├── demo-001.3.1  Task: POST /events endpoint for hook data [blocked by .1.2]
│   └── demo-001.3.2  Task: Event feed with type filtering [blocked by .3.1]
└── demo-001.4  Feature: Live updates via WebSocket
    ├── demo-001.4.1  Task: WebSocket hub and client management [blocked by .1.3]
    └── demo-001.4.2  Task: HTMX streaming for real-time updates [blocked by .4.1]

demo-100  Epic: Parking Lot (P4)
└── demo-100.1  Task: Add metrics charts and performance graphs [PARKED]
```

### Expected Command Outputs

| Command | Shows |
|---------|-------|
| `bd ready` | demo-001.1.1 only (the one ready task) |
| `bd blocked` | 8 blocked tasks with their blockers |
| `bd list --status=open` | All 16 beads |
| `bd show demo-001` | Epic with 4 feature children |
| `bd show demo-001.1.1` | Full task context with test specs |

## Demonstrates

1. **Epic → Feature → Task hierarchy** - Three-tier structure with 4 features
2. **Complex dependency graph** - 8 dependency edges across features
3. **Cross-feature dependencies** - Tasks in different features sharing common blockers
4. **Parking lot pattern** - demo-100.1 is filtered from ready work
5. **Rich descriptions** - Requirements, test specs, implementation notes, manual verification
6. **Phase-based execution** - cook → serve → tidy → plate
7. **Feature completion triggers** - plate phase when all tasks in a feature done
8. **Epic closure** - Automatic when all features complete
9. **Realistic project structure** - Go web application with standard layout

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
