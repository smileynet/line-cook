#!/usr/bin/env bash
# eval.sh - Top-level orchestrator for cross-CLI evaluation
#
# Runs the full eval matrix: providers x scenarios x runs.
# Each combination gets an isolated environment, provider execution,
# validation, and teardown.
#
# Usage:
#   ./tests/eval/eval.sh                                    # Full matrix, 3 runs each
#   ./tests/eval/eval.sh --provider claude --scenario readonly --runs 1
#   ./tests/eval/eval.sh --skip-missing                     # Skip unavailable providers
#   ./tests/eval/eval.sh --dry-run                          # Show plan without running
#   ./tests/eval/eval.sh --provider claude --runs 3         # All scenarios, one provider
#
# Results: tests/results/eval/*.json
# Report:  tests/results/eval/report.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$REPO_ROOT/tests/results/eval"

source "$REPO_ROOT/tests/lib/test-utils.sh"
setup_colors

# ============================================================
# Configuration
# ============================================================

ALL_PROVIDERS=(claude opencode kiro)
ALL_SCENARIOS=(readonly analysis implement sequence)

# Defaults
PROVIDERS=()
SCENARIOS=()
RUNS=3
DRY_RUN=false
SKIP_MISSING=false
REPORT_ONLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDERS+=("$2")
            shift 2
            ;;
        --scenario)
            SCENARIOS+=("$2")
            shift 2
            ;;
        --runs)
            RUNS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-missing)
            SKIP_MISSING=true
            shift
            ;;
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Usage: eval.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --provider <name>   Provider to eval (claude|opencode|kiro). Repeatable."
            echo "  --scenario <name>   Scenario to run (readonly|analysis|implement|sequence). Repeatable."
            echo "  --runs N            Number of runs per combination (default: 3)"
            echo "  --dry-run           Show plan and cost estimate without running"
            echo "  --skip-missing      Skip providers that aren't installed"
            echo "  --report-only       Only generate report from existing results"
            echo "  --help              Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate --runs
if ! [[ "$RUNS" =~ ^[1-9][0-9]*$ ]]; then
    log_error "--runs must be a positive integer, got: $RUNS"
    exit 1
fi

# Default to all if none specified
if [[ ${#PROVIDERS[@]} -eq 0 ]]; then
    PROVIDERS=("${ALL_PROVIDERS[@]}")
fi
if [[ ${#SCENARIOS[@]} -eq 0 ]]; then
    SCENARIOS=("${ALL_SCENARIOS[@]}")
fi

# ============================================================
# Report-only mode
# ============================================================

if $REPORT_ONLY; then
    log_phase "Generating Report"
    python3 "$SCRIPT_DIR/eval-report.py" --results-dir "$RESULTS_DIR"
    python3 "$SCRIPT_DIR/eval-report.py" --results-dir "$RESULTS_DIR" --output "$RESULTS_DIR/report.md"
    exit 0
fi

# ============================================================
# Cost Estimation
# ============================================================

# Per-scenario approximate cost (based on typical Sonnet usage).
# Keep in sync with README.md scenario table.
declare -A SCENARIO_COST
SCENARIO_COST[readonly]=0.05
SCENARIO_COST[analysis]=0.10
SCENARIO_COST[implement]=1.00
SCENARIO_COST[sequence]=2.00

estimate_cost() {
    local total_cost=0
    local run_count=0
    for provider in "${PROVIDERS[@]}"; do
        for scenario in "${SCENARIOS[@]}"; do
            local scenario_cost=${SCENARIO_COST[$scenario]:-0.50}
            total_cost=$(awk "BEGIN { printf \"%.2f\", $total_cost + $scenario_cost * $RUNS }")
            run_count=$((run_count + RUNS))
        done
    done
    printf '%d runs, estimated cost: $%s\n' "$run_count" "$total_cost"
}

# ============================================================
# Provider Availability Check
# ============================================================

check_providers() {
    local available=()
    local missing=()

    for provider in "${PROVIDERS[@]}"; do
        if check_provider_available "$provider"; then
            available+=("$provider")
            log_success "$(get_provider_display_name "$provider") available"
        else
            missing+=("$provider")
            if $SKIP_MISSING; then
                log_warning "$(get_provider_display_name "$provider") not installed (skipping)"
            else
                log_error "$(get_provider_display_name "$provider") not installed"
            fi
        fi
    done

    if [[ ${#available[@]} -eq 0 ]]; then
        log_error "No providers available"
        exit 1
    fi

    if [[ ${#missing[@]} -gt 0 ]] && ! $SKIP_MISSING; then
        log_error "Missing providers: ${missing[*]}"
        log "Use --skip-missing to skip unavailable providers"
        exit 1
    fi

    PROVIDERS=("${available[@]}")
}

# ============================================================
# Main Execution
# ============================================================

log_phase "Cross-CLI Evaluation Harness"
log_step "Providers: ${PROVIDERS[*]}"
log_step "Scenarios: ${SCENARIOS[*]}"
log_step "Runs per combination: $RUNS"

# Check dependencies
check_dependencies git jq bd || exit 1
log_success "Core dependencies satisfied"

# Check providers
check_providers

# Cost estimate
log ""
log_step "$(estimate_cost)"

if $DRY_RUN; then
    log ""
    log_phase "Dry Run Plan"
    for provider in "${PROVIDERS[@]}"; do
        for scenario in "${SCENARIOS[@]}"; do
            for run in $(seq 1 "$RUNS"); do
                log "  $(get_provider_display_name "$provider") / $scenario / run $run"
            done
        done
    done
    log ""
    log_success "Dry run complete. Use without --dry-run to execute."
    exit 0
fi

log ""

# Ensure results directory
mkdir -p "$RESULTS_DIR"

# Track overall results
total_runs=0
passed_runs=0
failed_runs=0
skipped_runs=0

# Run the matrix
for provider in "${PROVIDERS[@]}"; do
    for scenario in "${SCENARIOS[@]}"; do
        for run in $(seq 1 "$RUNS"); do
            total_runs=$((total_runs + 1))

            log_phase "[$total_runs] $provider / $scenario / run $run"

            # Per-run log file for debugging
            timestamp=$(date +%Y%m%d-%H%M%S)
            run_log="$RESULTS_DIR/${provider}-${scenario}-run${run}-${timestamp}.log"

            # Setup
            log_step "Setting up environment..."
            TEST_DIR=$("$SCRIPT_DIR/eval-setup.sh" 2>"$run_log") || {
                log_error "Setup failed (see $run_log)"
                failed_runs=$((failed_runs + 1))
                continue
            }
            log_success "Environment: $TEST_DIR"

            # Run
            log_step "Running $provider..."
            RUN_FILE=""
            run_exit=0
            RUN_FILE=$("$SCRIPT_DIR/eval-run.sh" \
                --provider "$provider" \
                --scenario "$scenario" \
                --test-dir "$TEST_DIR" \
                --run-id "$run" 2>>"$run_log") || run_exit=$?

            if [[ $run_exit -eq 2 ]]; then
                log_warning "Provider skipped"
                skipped_runs=$((skipped_runs + 1))
                "$SCRIPT_DIR/eval-teardown.sh" "$TEST_DIR" >>"$run_log" 2>&1
                continue
            elif [[ $run_exit -ne 0 ]]; then
                log_error "Run failed (exit $run_exit, see $run_log)"
            fi

            # Validate
            log_step "Validating..."
            VALIDATE_FILE=""
            VALIDATE_FILE=$("$SCRIPT_DIR/eval-validate.sh" \
                --test-dir "$TEST_DIR" \
                --scenario "$scenario" \
                --run-file "${RUN_FILE:-}" \
                --provider "$provider" \
                --run-id "$run" 2>>"$run_log") && {
                passed_runs=$((passed_runs + 1))
                log_success "Validation passed"
            } || {
                failed_runs=$((failed_runs + 1))
                log_error "Validation failed (see $run_log)"
            }

            # Teardown
            "$SCRIPT_DIR/eval-teardown.sh" "$TEST_DIR" >>"$run_log" 2>&1
            log_success "Environment cleaned up"
        done
    done
done

# ============================================================
# Summary and Report
# ============================================================

log_phase "Eval Summary"
log_step "Total: $total_runs"
log_success "Passed: $passed_runs"
if [[ $failed_runs -gt 0 ]]; then
    log_error "Failed: $failed_runs"
fi
if [[ $skipped_runs -gt 0 ]]; then
    log_warning "Skipped: $skipped_runs"
fi

# Generate report
log ""
log_step "Generating report..."
python3 "$SCRIPT_DIR/eval-report.py" --results-dir "$RESULTS_DIR" --output "$RESULTS_DIR/report.md" 2>/dev/null && {
    log_success "Report: $RESULTS_DIR/report.md"
} || {
    log_warning "Report generation failed (may need more results)"
}

# Also output to terminal
python3 "$SCRIPT_DIR/eval-report.py" --results-dir "$RESULTS_DIR" 2>/dev/null || true

log ""
if [[ $failed_runs -eq 0 ]]; then
    log_success "All runs passed!"
else
    log_error "$failed_runs/$total_runs runs failed"
    exit 1
fi
