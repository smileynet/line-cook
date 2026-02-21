# Line Cook Loop Demo

A comprehensive test environment for validating **all line loop features** in a single run. Uses a Python Bookmark CLI project with a rich bead hierarchy that exercises every loop code path.

## Prerequisites

- Python 3.8+
- [beads](https://github.com/smileynet/beads) (`bd` CLI)
- A supported AI CLI: Claude Code, Kiro, or OpenCode

## Quick Start

```bash
# Setup (default: Claude Code)
bash ~/code/line-cook/docs/demos/demo-loop/setup.sh

# Or with a specific CLI
bash ~/code/line-cook/docs/demos/demo-loop/setup.sh --cli kiro
bash ~/code/line-cook/docs/demos/demo-loop/setup.sh --cli opencode

# Run the loop
cd /tmp/line-cook-demo-loop
python3 ~/code/line-cook/core/line-loop-cli.py \
  --epic auto --max-iterations 10 --skip-initial-sync -v
```

## Beads Hierarchy

```
demo-001  Epic: Bookmark Manager Core (P2)
├── demo-001.1  Feature: Add and view bookmarks
│   ├── demo-001.1.1  Task: Implement data model and add command  [READY]
│   └── demo-001.1.2  Task: Implement list command formatting     [blocked by 001.1.1]
├── demo-001.2  Feature: Manage bookmarks
│   └── demo-001.2.1  Task: Implement delete command              [blocked by 001.1.1]

demo-002  Epic: Search & Export (P2)
├── demo-002.1  Feature: Search bookmarks
│   └── demo-002.1.1  Task: Search by keyword                     [blocked by 001.1.1]  ← cross-epic
├── demo-002.2  Feature: Export bookmarks
│   └── demo-002.2.1  Task: Export to JSON                        [blocked by 002.1.1]

demo-100  Epic: Retrospective & Parking Lot (P4)
└── demo-100.1  Task: Consider tag support                        [PARKED]
```

**Counts**: 3 epics, 4 features, 5 actionable tasks, 1 parked task = 13 beads

**Dependencies** (4 explicit):
- `demo-001.1.2` depends on `demo-001.1.1`
- `demo-001.2.1` depends on `demo-001.1.1`
- `demo-002.1.1` depends on `demo-001.1.1` (cross-epic)
- `demo-002.2.1` depends on `demo-002.1.1`

## Expected Flow (`--epic auto`)

| Iter | Task | Outcome | Features Exercised |
|------|------|---------|-------------------|
| 1 | demo-001.1.1 | Closes, unblocks 3 tasks | Basic completion, multi-unblock |
| 2 | demo-001.1.2 | Closes | Dependency unblock |
| — | demo-001.1 | Plates (2/2 tasks done) | Feature plate phase |
| 3 | demo-001.2.1 | Closes | Last task in feature |
| — | demo-001.2 | Plates (1/1 task done) | Feature plate phase |
| — | demo-001 | Close-service (all features done) | Epic completion, branch merge |
| 4 | demo-002.1.1 | Closes, unblocks 002.2.1 | Epic switching, cross-epic dep |
| — | demo-002.1 | Plates (1/1 task done) | Feature plate phase |
| 5 | demo-002.2.1 | Closes | Last task in epic |
| — | demo-002.2 | Plates (1/1 task done) | Feature plate phase |
| — | demo-002 | Close-service | Epic completion, branch merge |
| 6 | — | No actionable work (P4 only) | KITCHEN_IDLE / no_work termination |

## Loop Features Coverage

| Loop Feature | How Tested |
|-------------|------------|
| Basic task completion | Every iteration (5x) |
| Dependency unblocking | Iterations 2-5 |
| Multiple concurrent unblocks | After iteration 1 (3 tasks unblock) |
| Feature plate phase | 4 features plate |
| Epic close-service phase | 2 epics close-service |
| Epic branch management | epic/demo-001 and epic/demo-002 created + merged |
| Epic switching (`--epic auto`) | After demo-001 completes, switches to demo-002 |
| Cross-epic dependencies | demo-002.1.1 depends on demo-001.1.1 |
| Parking lot filtering | demo-100.1 (P4) never selected |
| KITCHEN_IDLE / no_work | Loop terminates after all real work done |
| Serve review | Every iteration |
| Retry on NEEDS_CHANGES | If serve rejects (opportunistic) |

## Verification Checklist (Post-Run)

After a successful run, verify:

```bash
cd /tmp/line-cook-demo-loop

# Closed items: 5 tasks + 4 features + 2 epics = 11 closed
bd list --status=closed

# Open items: only demo-100 epic + demo-100.1 task
bd list --status=open

# Git history shows commits from each iteration
git log --oneline

# No leftover epic branches (merged to main)
git branch

# Code exists and tests pass
python3 -m unittest test_bookmark -v

# Bookmark CLI works end-to-end
python3 bookmark.py add "https://example.com" --title "Example"
python3 bookmark.py list
python3 bookmark.py search "example"
python3 bookmark.py export
python3 bookmark.py delete "$(python3 bookmark.py list | head -1 | grep -o '\[.*\]' | tr -d '[]')"
```

## Expected Command Outputs (Pre-Run)

| Command | Shows |
|---------|-------|
| `bd ready` | demo-001.1.1 only (the one ready task) |
| `bd blocked` | demo-001.1.2, demo-001.2.1, demo-002.1.1, demo-002.2.1 |
| `bd list --status=open` | All 13 beads |
| `bd stats` | 13 open, 0 closed, 4 blocked |

## Troubleshooting

```bash
# Check beads state
bd doctor
bd stats

# Re-run setup from scratch
bash ~/code/line-cook/docs/demos/demo-loop/setup.sh --cli claude

# Run with shorter timeouts for quick testing
python3 ~/code/line-cook/core/line-loop-cli.py \
  --epic auto --max-iterations 10 \
  --cook-timeout 600 --serve-timeout 300 \
  --skip-initial-sync -v
```

## Cleanup

```bash
rm -rf /tmp/line-cook-demo-loop
```
