#!/usr/bin/env bash
# eval-run.sh - Execute a single provider+scenario eval run
#
# Runs one scenario against one provider in an isolated test directory,
# capturing metrics and raw output to JSON.
#
# Usage:
#   ./tests/eval/eval-run.sh --provider claude --scenario readonly \
#       --test-dir /tmp/line-cook-eval.XXXX --run-id 1
#
# Output: JSON result file at tests/results/eval/<provider>-<scenario>-<run_id>-<timestamp>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$REPO_ROOT/tests/results/eval"

# Source eval provider library
source "$SCRIPT_DIR/lib/eval-provider.sh"
setup_colors

# Defaults
PROVIDER=""
SCENARIO=""
TEST_DIR=""
RUN_ID="1"
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider) PROVIDER="$2"; shift 2 ;;
        --scenario) SCENARIO="$2"; shift 2 ;;
        --test-dir) TEST_DIR="$2"; shift 2 ;;
        --run-id) RUN_ID="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help|-h)
            echo "Usage: eval-run.sh --provider <claude|opencode|kiro> --scenario <name> --test-dir <path> [--run-id N]"
            echo ""
            echo "Scenarios: readonly, analysis, implement, sequence"
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate required args
if [[ -z "$PROVIDER" || -z "$SCENARIO" || -z "$TEST_DIR" ]]; then
    log_error "Missing required arguments: --provider, --scenario, --test-dir"
    exit 1
fi

if [[ ! -d "$TEST_DIR" ]]; then
    log_error "Test directory does not exist: $TEST_DIR"
    exit 1
fi

# Check provider availability
if ! check_provider_available "$PROVIDER"; then
    log_warning "Provider '$PROVIDER' not installed, skipping"
    exit 2  # Exit 2 = skipped
fi

# ============================================================
# Scenario Definitions
# ============================================================

# Each scenario function sets: PROMPT, TIMEOUT, MAX_TURNS, MAX_BUDGET

scenario_readonly() {
    PROMPT="Run 'bd ready' and list all ready task IDs. Then run 'bd list --status=open' and report how many open issues exist. Finally, run 'bd show demo-001.1.1' and summarize the task title and requirements."
    TIMEOUT=60
    MAX_TURNS=5
    MAX_BUDGET="1.00"
}

scenario_analysis() {
    PROMPT="Analyze task demo-001.1.1 by running 'bd show demo-001.1.1'. Based on the task description, list: (1) what source files need to be created, (2) what test files need to be created, (3) what the key acceptance criteria are. Do not modify any files."
    TIMEOUT=120
    MAX_TURNS=5
    MAX_BUDGET="1.00"
}

scenario_implement() {
    PROMPT="Implement task demo-001.1.1 for the TodoWebApp. Read the task details with 'bd show demo-001.1.1'. Write tests first in src/todo.test.js, then implement src/todo.js to make the tests pass. Verify tests pass with 'node src/todo.test.js'. After tests pass, close the bead with 'bd close demo-001.1.1', commit all changes with a message referencing demo-001.1.1, and push to origin."
    TIMEOUT=600
    MAX_TURNS=25
    MAX_BUDGET="5.00"
}

scenario_sequence() {
    PROMPT="Complete all ready tasks for the TodoWebApp project. Start by running 'bd ready' to find available work. For each ready task: read its details with 'bd show', write tests first, implement the feature, verify tests pass with 'node src/todo.test.js', close the bead with 'bd close', commit, and push. After completing a task, run 'bd ready' again to check if new tasks are unblocked. Continue until no more tasks are ready."
    TIMEOUT=900
    MAX_TURNS=50
    MAX_BUDGET="10.00"
}

# ============================================================
# Main Execution
# ============================================================

# Load scenario
case "$SCENARIO" in
    readonly)  scenario_readonly ;;
    analysis)  scenario_analysis ;;
    implement) scenario_implement ;;
    sequence)  scenario_sequence ;;
    *)
        log_error "Unknown scenario: $SCENARIO"
        log "Available: readonly, analysis, implement, sequence"
        exit 1
        ;;
esac

log_phase "Eval Run: $PROVIDER / $SCENARIO (run $RUN_ID)"
log_step "Provider: $(get_provider_display_name "$PROVIDER")"
log_step "Scenario: $SCENARIO"
log_step "Test dir: $TEST_DIR"
log_step "Timeout: ${TIMEOUT}s"
log_step "Max turns: $MAX_TURNS"
log_step "Max budget: \$$MAX_BUDGET"

if $DRY_RUN; then
    log ""
    log_success "Dry run — would execute with prompt:"
    log "  $PROMPT"
    exit 0
fi

# Ensure results directory exists
mkdir -p "$RESULTS_DIR"

# Run the provider
log_step "Running $PROVIDER..."

cd "$TEST_DIR"
run_result=$(eval_provider_run "$PROVIDER" "$PROMPT" "$TIMEOUT" "$TEST_DIR" "$MAX_TURNS" "$MAX_BUDGET")

# Add scenario metadata to result
timestamp=$(date +%Y%m%d-%H%M%S)
result_file="$RESULTS_DIR/${PROVIDER}-${SCENARIO}-run${RUN_ID}-${timestamp}.json"

echo "$run_result" | jq \
    --arg scenario "$SCENARIO" \
    --arg run_id "$RUN_ID" \
    '. + { scenario: $scenario, run_id: $run_id }' \
    > "$result_file"

# Log summary
exit_code=$(echo "$run_result" | jq -r '.exit_code // 0')
wall_time_ms=$(echo "$run_result" | jq -r '.wall_time_ms // 0')
input_tokens=$(echo "$run_result" | jq -r '.tokens.input // 0')
output_tokens=$(echo "$run_result" | jq -r '.tokens.output // 0')
cache_read=$(echo "$run_result" | jq -r '.tokens.cache_read // 0')
cost_usd=$(echo "$run_result" | jq -r '.tokens.cost_usd // 0')

wall_time_sec=$(( wall_time_ms / 1000 ))  # Convert milliseconds to seconds

log ""
if [[ "$exit_code" -eq 0 ]]; then
    log_success "Completed in ${wall_time_sec}s"
else
    log_error "Failed (exit code $exit_code) in ${wall_time_sec}s"
fi
log_step "Tokens: ${input_tokens} in / ${output_tokens} out (cache: ${cache_read} read)"
if [[ "$cost_usd" != "0" ]]; then
    log_step "Cost: \$${cost_usd}"
fi
log_step "Result: $result_file"

# Output result file path to stdout
echo "$result_file"
