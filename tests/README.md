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

## Smoke Tests

The smoke test executes a real coding task through the full Line Cook workflow.

### Interactive Mode (Recommended)

Run the smoke test from within an interactive Claude session using the `/smoke-test` command:

```
/smoke-test
```

This avoids API conflicts that occur when spawning headless Claude subprocesses from an interactive session.

### Script Mode (Manual/CI)

For manual execution outside of Claude sessions, use the modular script:

```bash
# 1. Check dependencies
./tests/smoke-test.sh --dry-run

# 2. Setup creates an isolated test environment
TEST_DIR=$(./tests/smoke-test.sh --setup)

# 3. Run workflow manually in the test directory
cd $TEST_DIR
# ... run /line:prep, /line:cook smoke-001, /line:serve, /line:tidy ...

# 4. Validate artifacts
./tests/smoke-test.sh --validate $TEST_DIR

# 5. Cleanup
./tests/smoke-test.sh --teardown $TEST_DIR
```

### Script Options

```bash
./tests/smoke-test.sh --setup              # Create isolated env, output TEST_DIR
./tests/smoke-test.sh --validate <dir>     # Check proof-of-work artifacts
./tests/smoke-test.sh --teardown <dir>     # Clean up test directory
./tests/smoke-test.sh --dry-run            # Check dependencies only
./tests/smoke-test.sh --skip-cook-check    # Skip workflow validation (setup-only)
```

### What Smoke Tests Validate

| Artifact | Check |
|----------|-------|
| Code change | `validation.py` uses regex instead of placeholder |
| Tests exist | `test_validation.py` created |
| Tests pass | pytest exit code 0 |
| Bead closed | `smoke-001` has `status: closed` |
| Commit exists | Git log contains smoke-001 reference |
| Pushed | All commits pushed to remote |
| Clean tree | No uncommitted changes |

### Cost Estimate

~$0.50-2.00 per run (primarily the cook phase)

### Important Notes

- **Use `/smoke-test` command** for testing within interactive sessions
- Results are saved to `tests/results/smoke-*.json`
- Test environment includes a bare git remote for push validation

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
├── smoke-test.sh             # Cross-platform smoke test
├── lib/
│   ├── setup-env.sh          # Creates isolated git repo with beads
│   ├── teardown-env.sh       # Cleanup temp directories
│   └── test-utils.sh         # Common test utilities
├── fixtures/
│   ├── mock-beads/           # Test beads configuration
│   │   └── issues.jsonl      # 6 test issues (JSONL)
│   ├── smoke-beads/          # Smoke test bead (smoke-001)
│   │   └── issues.jsonl      # smoke-001 task (JSONL)
│   └── sample-project/       # Minimal project for testing
├── results/                  # Smoke test JSON output
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
