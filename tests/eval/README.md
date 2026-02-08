# Cross-CLI Evaluation Harness

Benchmarks AI coding CLI tools (Claude Code, OpenCode, Kiro) against identical tasks using `demo-simple` repo instances.

## Quick Start

```bash
# Single provider, single scenario, one run
./tests/eval/eval.sh --provider claude --scenario readonly --runs 1

# Full matrix with available providers
./tests/eval/eval.sh --skip-missing --runs 3

# Dry run to see plan and cost estimate
./tests/eval/eval.sh --dry-run
```

## Scripts

| Script | Purpose |
|--------|---------|
| `eval.sh` | Top-level orchestrator (runs full matrix) |
| `eval-setup.sh` | Create isolated demo-simple env per run |
| `eval-run.sh` | Execute single provider+scenario, capture metrics |
| `eval-validate.sh` | Validate artifacts post-run |
| `eval-teardown.sh` | Clean up env |
| `eval-report.py` | Aggregate results, compute stats, render report |
| `lib/eval-provider.sh` | Provider invocation with JSON/metrics capture |

## Scenarios

| Scenario | What it tests | Timeout | Approx. Cost |
|----------|--------------|---------|--------------|
| `readonly` | `bd ready`, `bd show`, `bd list` | 60s | $0.05 |
| `analysis` | Reasoning about task requirements | 120s | $0.10 |
| `implement` | Single task end-to-end (TDD, close, commit, push) | 600s | $1.00 |
| `sequence` | Both tasks in dependency order | 900s | $2.00 |

## Providers

| Provider | CLI | Install |
|----------|-----|---------|
| Claude Code | `claude` | `npm install -g @anthropic-ai/claude-code` |
| OpenCode | `opencode` | `curl -fsSL https://opencode.ai/install \| bash` |
| Kiro | `kiro-cli` | `curl -fsSL https://cli.kiro.dev/install \| bash` |

## Results

Results are saved to `tests/results/eval/` as JSON files:
- `<provider>-<scenario>-run<N>-<timestamp>.json` — Run metrics
- `<provider>-<scenario>-run<N>-<timestamp>-validate.json` — Validation checks
- `report.md` — Aggregated markdown report

## Manual Workflow

For debugging or step-by-step execution:

```bash
# 1. Setup
TEST_DIR=$(./tests/eval/eval-setup.sh)

# 2. Run
./tests/eval/eval-run.sh --provider claude --scenario readonly \
    --test-dir $TEST_DIR --run-id 1

# 3. Validate
./tests/eval/eval-validate.sh --test-dir $TEST_DIR --scenario readonly \
    --run-file tests/results/eval/<result-file>.json

# 4. Teardown
./tests/eval/eval-teardown.sh $TEST_DIR

# 5. Report (after multiple runs)
python3 tests/eval/eval-report.py --results-dir tests/results/eval/
```

## Design Principles

- **Isolation**: Fresh /tmp dir per run, no state bleed between runs
- **Statistical rigor**: Multiple runs per scenario, report mean + stddev
- **Provider neutrality**: Natural language prompts, no tool-specific syntax
- **Cost control**: `--dry-run` mode, cost estimates, `--max-budget-usd` for Claude
- **Reproducibility**: All raw output saved, exact prompts logged
- **Graceful degradation**: `--skip-missing` skips unavailable providers
