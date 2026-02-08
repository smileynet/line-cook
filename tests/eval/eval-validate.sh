#!/usr/bin/env bash
# eval-validate.sh - Validate artifacts after an eval run
#
# Performs scenario-specific validation checks on the test directory
# and outputs a JSON validation report.
#
# Usage:
#   ./tests/eval/eval-validate.sh --test-dir /tmp/line-cook-eval.XXXX \
#       --scenario implement --run-file /path/to/run-result.json
#
# Output: JSON validation file at tests/results/eval/<name>-validate.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$REPO_ROOT/tests/results/eval"

source "$REPO_ROOT/tests/lib/test-utils.sh"
setup_colors

# Defaults
TEST_DIR=""
SCENARIO=""
RUN_FILE=""
PROVIDER=""
RUN_ID=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test-dir) TEST_DIR="$2"; shift 2 ;;
        --scenario) SCENARIO="$2"; shift 2 ;;
        --run-file) RUN_FILE="$2"; shift 2 ;;
        --provider) PROVIDER="$2"; shift 2 ;;
        --run-id) RUN_ID="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: eval-validate.sh --test-dir <path> --scenario <name> [--run-file <path>] [--provider <name>] [--run-id N]"
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

if [[ -z "$TEST_DIR" || -z "$SCENARIO" ]]; then
    log_error "Missing required: --test-dir, --scenario"
    exit 1
fi

if [[ ! -d "$TEST_DIR" ]]; then
    log_error "Test directory does not exist: $TEST_DIR"
    exit 1
fi

# Extract metadata from run file if provided
if [[ -n "$RUN_FILE" && -f "$RUN_FILE" ]]; then
    PROVIDER="${PROVIDER:-$(jq -r '.provider // "unknown"' "$RUN_FILE")}"
    RUN_ID="${RUN_ID:-$(jq -r '.run_id // "0"' "$RUN_FILE")}"
fi
PROVIDER="${PROVIDER:-unknown}"
RUN_ID="${RUN_ID:-0}"

cd "$TEST_DIR"

log_phase "Eval Validate: $SCENARIO ($PROVIDER, run $RUN_ID)"

# ============================================================
# Validation Check Helpers
# ============================================================

# Accumulate checks as JSON array
CHECKS="[]"

# Get bead status with JSON parsing fallback
# Args: bead_id
get_bead_status() {
    local bead_id="$1"
    bd show "$bead_id" --json 2>/dev/null | jq -r '.[0].status // .status // "unknown"' 2>/dev/null || echo "unknown"
}

# Add a check result to CHECKS array and log it
# Args: name, passed (true/false), message, [details]
add_check() {
    local name="$1"
    local passed="$2"
    local message="$3"
    local details="${4:-}"

    CHECKS=$(echo "$CHECKS" | jq \
        --arg name "$name" \
        --argjson passed "$passed" \
        --arg message "$message" \
        --arg details "$details" \
        '. + [{ name: $name, passed: $passed, message: $message, details: $details }]')

    if [[ "$passed" == "true" ]]; then
        log_success "$name: $message"
    else
        log_error "$name: $message"
        if [[ -n "$details" ]]; then
            log "    $details"
        fi
    fi
}

# ============================================================
# Common Checks
# ============================================================

check_run_exit_code() {
    if [[ -z "$RUN_FILE" || ! -f "$RUN_FILE" ]]; then
        return 0
    fi

    local exit_code
    exit_code=$(jq -r '.exit_code' "$RUN_FILE")
    if [[ "$exit_code" -eq 0 ]]; then
        add_check "run_exit_code" true "Provider exited cleanly"
    else
        add_check "run_exit_code" false "Provider exited with code $exit_code"
    fi
}

# ============================================================
# Scenario-Specific Checks
# ============================================================

validate_readonly() {
    check_run_exit_code

    # Verify provider produced output
    if [[ -n "$RUN_FILE" && -f "$RUN_FILE" ]]; then
        local result_len
        result_len=$(jq -r '.result | length' "$RUN_FILE")
        if [[ "$result_len" -gt 10 ]]; then
            add_check "has_output" true "Provider produced output ($result_len chars)"
        else
            add_check "has_output" false "Provider produced little or no output"
        fi

        # Check output mentions demo-001.1.1
        if jq -r '.result' "$RUN_FILE" | grep -qi "demo-001.1.1"; then
            add_check "mentions_ready_task" true "Output mentions demo-001.1.1"
        else
            add_check "mentions_ready_task" false "Output does not mention demo-001.1.1"
        fi
    fi

    # Verify no source files were created (readonly shouldn't modify)
    if [[ ! -f "src/todo.js" && ! -f "src/todo.test.js" ]]; then
        add_check "no_modifications" true "No source files created (readonly)"
    else
        add_check "no_modifications" false "Source files were created during readonly scenario"
    fi
}

validate_analysis() {
    check_run_exit_code

    if [[ -n "$RUN_FILE" && -f "$RUN_FILE" ]]; then
        local provider_output
        provider_output=$(jq -r '.result' "$RUN_FILE")

        # Check that analysis mentions key files
        if echo "$provider_output" | grep -qi "todo.js"; then
            add_check "mentions_source_file" true "Analysis mentions todo.js"
        else
            add_check "mentions_source_file" false "Analysis does not mention todo.js"
        fi

        if echo "$provider_output" | grep -qi "test"; then
            add_check "mentions_tests" true "Analysis mentions tests"
        else
            add_check "mentions_tests" false "Analysis does not mention tests"
        fi
    fi

    # Verify no source files were created (analysis shouldn't modify)
    if [[ ! -f "src/todo.js" && ! -f "src/todo.test.js" ]]; then
        add_check "no_modifications" true "No source files created (analysis)"
    else
        add_check "no_modifications" false "Source files were created during analysis scenario"
    fi
}

validate_implement() {
    check_run_exit_code

    # Source files exist
    if [[ -f "src/todo.js" ]]; then
        add_check "source_file_exists" true "src/todo.js exists"
    else
        add_check "source_file_exists" false "src/todo.js not found"
    fi

    # Test files exist
    if [[ -f "src/todo.test.js" ]]; then
        add_check "test_file_exists" true "src/todo.test.js exists"
    else
        add_check "test_file_exists" false "src/todo.test.js not found"
    fi

    # Tests pass
    if [[ -f "src/todo.test.js" ]]; then
        if node src/todo.test.js >/dev/null 2>&1; then
            add_check "tests_pass" true "Tests pass (node src/todo.test.js)"
        else
            add_check "tests_pass" false "Tests fail"
        fi
    else
        add_check "tests_pass" false "No test file to run"
    fi

    # Bead closed
    local bead_status
    bead_status=$(get_bead_status demo-001.1.1)
    if [[ "$bead_status" == "closed" ]]; then
        add_check "bead_closed" true "demo-001.1.1 is closed"
    else
        add_check "bead_closed" false "demo-001.1.1 status: $bead_status (expected: closed)"
    fi

    # Commit with task ID
    if git log --oneline -20 | grep -qi "demo-001.1.1"; then
        add_check "commit_references_task" true "Commit references demo-001.1.1"
    else
        add_check "commit_references_task" false "No commit references demo-001.1.1"
    fi

    # Pushed to remote
    git fetch origin >/dev/null 2>&1 || true
    local unpushed
    unpushed=$(git log origin/main..HEAD --oneline 2>/dev/null || echo "error")
    if [[ -z "$unpushed" ]]; then
        add_check "pushed_to_remote" true "All commits pushed"
    else
        add_check "pushed_to_remote" false "Unpushed commits exist" "$unpushed"
    fi

    # Clean working tree (ignore beads lock files, they're ephemeral)
    local uncommitted_changes
    uncommitted_changes=$(git status --porcelain 2>/dev/null | grep -v '\.beads/\.jsonl\.lock' || true)
    if [[ -z "$uncommitted_changes" ]]; then
        add_check "clean_working_tree" true "Working tree is clean"
    else
        add_check "clean_working_tree" false "Uncommitted changes" "$uncommitted_changes"
    fi
}

validate_sequence() {
    # All checks from implement (includes check_run_exit_code)
    validate_implement

    # Additionally check demo-001.1.2 (the dependent task)
    local bead_status_2
    bead_status_2=$(get_bead_status demo-001.1.2)
    if [[ "$bead_status_2" == "closed" ]]; then
        add_check "sequence_bead_2_closed" true "demo-001.1.2 is closed"
    else
        add_check "sequence_bead_2_closed" false "demo-001.1.2 status: $bead_status_2 (expected: closed)"
    fi

    # Check demo-001.1.2 commit
    if git log --oneline -20 | grep -qi "demo-001.1.2"; then
        add_check "sequence_commit_2" true "Commit references demo-001.1.2"
    else
        add_check "sequence_commit_2" false "No commit references demo-001.1.2"
    fi

    # Verify toggle-complete functionality was actually implemented
    if [[ -f "src/todo.js" ]]; then
        if grep -qiE '(complete|toggle|done)' src/todo.js; then
            add_check "sequence_toggle_implemented" true "src/todo.js contains complete/toggle logic"
        else
            add_check "sequence_toggle_implemented" false "src/todo.js missing complete/toggle logic" \
                "demo-001.1.2 requires toggle-complete functionality"
        fi
    else
        add_check "sequence_toggle_implemented" false "src/todo.js not found"
    fi
}

# ============================================================
# Run Validation
# ============================================================

case "$SCENARIO" in
    readonly)  validate_readonly ;;
    analysis)  validate_analysis ;;
    implement) validate_implement ;;
    sequence)  validate_sequence ;;
    *)
        log_error "Unknown scenario: $SCENARIO"
        exit 1
        ;;
esac

# Compute summary
total_checks=$(echo "$CHECKS" | jq 'length')
passed_checks=$(echo "$CHECKS" | jq '[.[] | select(.passed)] | length')
failed_checks=$(echo "$CHECKS" | jq '[.[] | select(.passed | not)] | length')
all_passed=$(echo "$CHECKS" | jq 'all(.passed)')

# Build validation report
mkdir -p "$RESULTS_DIR"
timestamp=$(date +%Y%m%d-%H%M%S)
validate_file="$RESULTS_DIR/${PROVIDER}-${SCENARIO}-run${RUN_ID}-${timestamp}-validate.json"

jq -n \
    --arg provider "$PROVIDER" \
    --arg scenario "$SCENARIO" \
    --arg run_id "$RUN_ID" \
    --arg test_dir "$TEST_DIR" \
    --argjson checks "$CHECKS" \
    --argjson all_passed "$all_passed" \
    --argjson total "$total_checks" \
    --argjson passed "$passed_checks" \
    --argjson failed "$failed_checks" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg run_file "${RUN_FILE:-}" \
    '{
        provider: $provider,
        scenario: $scenario,
        run_id: $run_id,
        test_dir: $test_dir,
        timestamp: $timestamp,
        run_file: $run_file,
        passed: $all_passed,
        summary: { total: $total, passed: $passed, failed: $failed },
        checks: $checks
    }' > "$validate_file"

log ""
if [[ "$all_passed" == "true" ]]; then
    log_success "All $total_checks checks passed"
else
    log_error "$failed_checks/$total_checks checks failed"
fi
log_step "Report: $validate_file"

# Output validation file path
echo "$validate_file"

# Exit with failure if any checks failed
[[ "$all_passed" == "true" ]]
