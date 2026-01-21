# Line Cook Cross-Provider Test Suite

Integration tests for Line Cook commands across Claude Code, OpenCode, and Kiro.

## Quick Start

```bash
# Run dependency check (no API calls)
./tests/run-tests.sh --dry-run

# Run fast unit tests only
./tests/run-tests.sh --tier unit

# Run all tests (will prompt about API costs)
./tests/run-tests.sh
```

## Test Tiers

| Tier | Tests | API Cost | Time |
|------|-------|----------|------|
| `unit` | getting-started | ~$0.01 | ~1min |
| `integration` | getting-started, prep, serve, tidy | ~$0.10 | ~5min |
| `full` | All tests including cook, work | ~$0.50-2.00 | ~30min |

## Options

```bash
./tests/run-tests.sh [options]

Options:
  --provider <name>   Test specific provider: claude, opencode, kiro
  --test <name>       Run specific test: getting-started, prep, cook, serve, tidy, work
  --tier <level>      Run by tier: unit, integration, full (default: full)
  --dry-run           Check dependencies only
  --help              Show help
```

## Directory Structure

```
tests/
├── run-tests.sh              # Main test runner
├── lib/
│   ├── setup-env.sh          # Creates isolated git repo with beads
│   ├── teardown-env.sh       # Cleanup temp directories
│   └── test-utils.sh         # Common test utilities
├── fixtures/
│   ├── mock-beads/           # Test beads configuration
│   │   ├── config.yaml
│   │   └── issues/           # 6 test issues
│   └── sample-project/       # Minimal project for testing
├── test-getting-started.sh   # Tests /line:getting-started
├── test-prep.sh              # Tests /line:prep
├── test-cook.sh              # Tests /line:cook (LLM-heavy)
├── test-serve.sh             # Tests /line:serve
├── test-tidy.sh              # Tests /line:tidy
└── test-work.sh              # Tests /line:work (LLM-heavy)
```

## Test Fixtures

### Mock Beads Issues

| Issue | Type | Status | Purpose |
|-------|------|--------|---------|
| tc-001 | task | open | Ready task (P1, no deps) - auto-selection |
| tc-002 | task | open | Ready task (P2) - explicit selection |
| tc-003 | task | open | Blocked (depends on tc-001) |
| tc-004 | task | in_progress | Active work |
| tc-retro | epic | open | Parking lot epic |
| tc-005 | task | open | Under retro (should filter) |

### Sample Project

Minimal Python project with validation utilities:
- `CLAUDE.md` - Agent instructions
- `README.md` - Documentation
- `src/main.py` - Entry point
- `src/validation.py` - Validation utilities (has TODOs for tc-001)

## Provider Commands

| Provider | Command Syntax | Example |
|----------|---------------|---------|
| Claude Code | `/line:command` | `/line:prep` |
| OpenCode | `/line-command` | `/line-prep` |
| Kiro | `command` | `prep` |

## Writing New Tests

1. Create `tests/test-<name>.sh`
2. Source `lib/test-utils.sh` for utilities
3. Source `lib/setup-env.sh` for isolated environment
4. Use `run_provider_test` to invoke commands
5. Use `check_output_contains` to validate output
6. Trap `lib/teardown-env.sh` for cleanup

Example template:

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

cleanup() { source "$SCRIPT_DIR/lib/teardown-env.sh"; }
trap cleanup EXIT

# Test logic here...
```

## CI Integration

For GitHub Actions, set `ANTHROPIC_API_KEY` secret:

```yaml
- name: Run Line Cook tests
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    ./tests/run-tests.sh --tier unit --provider claude
```
