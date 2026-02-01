# Line Cook Demo Template

A pre-staged demo environment for testing Line Cook commands and onboarding new users.

## Quick Start

Set up a test environment with the demo beads:

```bash
# Create test directory and initialize git
mkdir /tmp/line-cook-demo && cd /tmp/line-cook-demo
git init && git commit --allow-empty -m "Initial commit"

# Initialize beads with demo prefix
bd init --prefix=demo

# Copy demo issues (adjust path to your line-cook clone)
# Example: if cloned to ~/code/line-cook
cp -r ~/code/line-cook/templates/demo/.beads/issues/* .beads/issues/
cp ~/code/line-cook/templates/demo/.beads/config.yaml .beads/config.yaml

# Verify the demo beads
bd list --status=open
```

Or use the test setup script pattern from `tests/lib/setup-env.sh`.

## What's Included

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

1. Update `config.yaml` with your preferred prefix
2. Rename issue files to match new prefix
3. Update `id`, `parent`, and `depends_on` references
4. Modify descriptions for your domain
