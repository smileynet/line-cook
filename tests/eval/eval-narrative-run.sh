#!/usr/bin/env bash
# eval-narrative-run.sh - Execute a multi-step narrative eval run
#
# Unlike eval-run.sh (single prompt), this runner executes multiple steps
# in sequence within the same test directory, calling eval_provider_run()
# once per step. Each step gets its own metrics.
#
# Narratives are defined as shell scripts in tests/eval/narratives/ that
# declare steps and validation functions.
#
# Usage:
#   ./tests/eval/eval-narrative-run.sh --provider claude --narrative onboard \
#       --test-dir /tmp/line-cook-eval.XXXX --run-id 1
#
# Output: JSON result file at tests/results/eval/<provider>-<narrative>-run<N>-<timestamp>.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$REPO_ROOT/tests/results/eval"

# Source libraries
source "$SCRIPT_DIR/lib/eval-provider.sh"
source "$SCRIPT_DIR/lib/narrative-utils.sh"
setup_colors

# Defaults
PROVIDER=""
NARRATIVE=""
TEST_DIR=""
RUN_ID="1"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider) PROVIDER="$2"; shift 2 ;;
        --narrative) NARRATIVE="$2"; shift 2 ;;
        --test-dir) TEST_DIR="$2"; shift 2 ;;
        --run-id) RUN_ID="$2"; shift 2 ;;
        --help|-h)
            echo "Usage: eval-narrative-run.sh --provider <claude|opencode|kiro> --narrative <name> --test-dir <path> [--run-id N]"
            echo ""
            echo "Narratives: onboard, single-task, task-chain, full-run, planning, recovery"
            exit 0
            ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate required args
if [[ -z "$PROVIDER" || -z "$NARRATIVE" || -z "$TEST_DIR" ]]; then
    log_error "Missing required arguments: --provider, --narrative, --test-dir"
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

# Load narrative definition
NARRATIVE_FILE="$SCRIPT_DIR/narratives/${NARRATIVE}.sh"
if [[ ! -f "$NARRATIVE_FILE" ]]; then
    log_error "Narrative not found: $NARRATIVE_FILE"
    log "Available narratives:"
    for f in "$SCRIPT_DIR"/narratives/*.sh; do
        [[ -f "$f" ]] && log "  $(basename "$f" .sh)"
    done
    exit 1
fi

source "$NARRATIVE_FILE"

# ============================================================
# Narrative Interface
# ============================================================
# Each narrative must define:
#   NARRATIVE_STEPS     - Array of step names (e.g., "getting-started" "prep")
#   NARRATIVE_FIXTURE   - Fixture type (demo-simple or demo-planning)
#
# And these arrays indexed by step number (0-based):
#   STEP_COMMAND[N]     - Command name for the step
#   STEP_CONTEXT[N]     - Additional context/instructions
#   STEP_ARGUMENT[N]    - Optional command argument
#   STEP_TIMEOUT[N]     - Timeout in seconds
#   STEP_MAX_TURNS[N]   - Max turns for claude
#   STEP_TYPE[N]        - "readonly" or "mutating" (for tool permissions)
#   STEP_GOAL[N]        - Human-readable goal for agent validation (optional)
#
# Optional per-step validation:
#   narrative_validate_step_N()  - Called after step N with $STEP_RESULT_TEXT
#
# Required final validation:
#   narrative_validate_final()   - Called after all steps complete

# Verify narrative defines required interface
if [[ -z "${NARRATIVE_STEPS[*]:-}" ]]; then
    log_error "Narrative '$NARRATIVE' does not define NARRATIVE_STEPS"
    exit 1
fi

log_phase "Narrative Run: $PROVIDER / $NARRATIVE (run $RUN_ID)"
log_step "Provider: $(get_provider_display_name "$PROVIDER")"
log_step "Narrative: $NARRATIVE"
log_step "Steps: ${#NARRATIVE_STEPS[@]}"
log_step "Test dir: $TEST_DIR"

# ============================================================
# Step Execution Loop
# ============================================================

cd "$TEST_DIR"

# Accumulate step results as JSON array
STEP_RESULTS="[]"
ALL_STEPS_PASSED=true
total_wall_time_ms=0
total_input_tokens=0
total_output_tokens=0

# Temp directory for per-step capture files (cleaned up on exit)
STEP_TMPDIR=$(mktemp -d -t narrative-step.XXXXXX)
trap "rm -rf '$STEP_TMPDIR'" EXIT

# ============================================================
# Validation Helpers (inline — avoids sourcing eval-validate.sh)
# ============================================================

CHECKS="[]"

get_bead_status() {
    local bead_id="$1"
    bd show "$bead_id" --json 2>/dev/null | jq -r '.[0].status // .status // "unknown"' 2>/dev/null || echo "unknown"
}

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

for step_idx in "${!NARRATIVE_STEPS[@]}"; do
    step_name="${NARRATIVE_STEPS[$step_idx]}"
    command_name="${STEP_COMMAND[$step_idx]}"
    context="${STEP_CONTEXT[$step_idx]:-}"
    argument="${STEP_ARGUMENT[$step_idx]:-}"
    timeout="${STEP_TIMEOUT[$step_idx]:-120}"
    max_turns="${STEP_MAX_TURNS[$step_idx]:-10}"
    step_type="${STEP_TYPE[$step_idx]:-mutating}"

    step_num=$((step_idx + 1))
    log ""
    log_step "Step $step_num/${#NARRATIVE_STEPS[@]}: $step_name ($command_name)"

    # Build the prompt — narrative can override with narrative_build_prompt()
    if declare -f narrative_build_prompt >/dev/null 2>&1; then
        step_prompt=$(narrative_build_prompt "$PROVIDER" "$command_name" "$context" "$argument")
    else
        step_prompt=$(build_step_prompt "$PROVIDER" "$command_name" "$context" "$argument")
    fi

    # Determine tool permissions
    allowed_tools=$(get_step_tools "$step_type")

    # Run the provider with step-specific tool permissions
    step_exit=0
    if [[ "$PROVIDER" == "claude" ]]; then
        # Claude requires direct invocation to override allowedTools per step
        stdout_file="$STEP_TMPDIR/stdout-${step_idx}"
        stderr_file="$STEP_TMPDIR/stderr-${step_idx}"

        start_ns=$(get_timestamp_ns)

        timeout "$timeout" claude -p "$step_prompt" \
            --output-format json \
            --allowedTools "$allowed_tools" \
            --dangerously-skip-permissions \
            --model sonnet \
            --max-turns "$max_turns" \
            --max-budget-usd 5.00 \
            --no-session-persistence \
            >"$stdout_file" 2>"$stderr_file" || step_exit=$?

        end_ns=$(get_timestamp_ns)
        wall_time_ms=$(( (end_ns - start_ns) / 1000000 ))

        raw_output=$(cat "$stdout_file")
        stderr_output=$(cat "$stderr_file")

        tokens=$(parse_tokens "$PROVIDER" "$raw_output")
        result_text=$(parse_result "$PROVIDER" "$raw_output")
    else
        # For opencode/kiro, use eval_provider_run directly
        step_result=$(eval_provider_run "$PROVIDER" "$step_prompt" "$timeout" "$TEST_DIR" "$max_turns" "5.00") || step_exit=$?

        wall_time_ms=$(echo "$step_result" | jq -r '.wall_time_ms // 0')
        tokens=$(echo "$step_result" | jq -r '.tokens')
        result_text=$(echo "$step_result" | jq -r '.result // ""')
        raw_output=$(echo "$step_result" | jq -r '.raw_output // ""')
        stderr_output=$(echo "$step_result" | jq -r '.stderr // ""')
        step_exit=$(echo "$step_result" | jq -r '.exit_code // 0')
    fi

    # Truncate large fields
    result_text=$(truncate_string "${result_text:-}" 10000)
    stderr_output=$(truncate_string "${stderr_output:-}" 5000)
    raw_output=$(truncate_string "${raw_output:-}" 10000)

    total_wall_time_ms=$((total_wall_time_ms + wall_time_ms))
    input_tok=$(echo "$tokens" | jq -r '.input // 0')
    output_tok=$(echo "$tokens" | jq -r '.output // 0')
    total_input_tokens=$((total_input_tokens + input_tok))
    total_output_tokens=$((total_output_tokens + output_tok))

    wall_time_sec=$((wall_time_ms / 1000))

    # Agent-based step validation
    step_goal="${STEP_GOAL[$step_idx]:-}"
    agent_passed=true
    agent_reasoning=""
    if [[ -n "$step_goal" ]]; then
        log "  Validating step with agent..."
        agent_result=$(agent_validate_step "$step_goal" "$result_text" "$command_name")
        agent_passed=$(echo "$agent_result" | jq -r '.passed // false')
        agent_reasoning=$(echo "$agent_result" | jq -r '.reasoning // ""')

        if [[ "$agent_passed" == "true" ]]; then
            log_success "Agent: passed — $agent_reasoning (${wall_time_sec}s)"
        else
            log_warning "Agent: failed — $agent_reasoning (${wall_time_sec}s)"
        fi
    else
        log_warning "No STEP_GOAL defined for step $step_num — using exit code only"
        if [[ "$step_exit" -eq 0 ]]; then
            log_success "Completed (${wall_time_sec}s)"
        else
            log_error "Failed exit=$step_exit (${wall_time_sec}s)"
            agent_passed=false
            agent_reasoning="Non-zero exit code: $step_exit"
        fi
    fi

    # Run per-step validation if defined
    step_checks="[]"
    STEP_RESULT_TEXT="$result_text"
    export STEP_RESULT_TEXT

    validate_fn="narrative_validate_step_${step_num}"
    if declare -f "$validate_fn" >/dev/null 2>&1; then
        # Reset CHECKS for per-step validation
        CHECKS="[]"
        "$validate_fn"
        step_checks="$CHECKS"

        # Check if any step checks failed
        step_failed=$(echo "$step_checks" | jq '[.[] | select(.passed | not)] | length')
        if [[ "$step_failed" -gt 0 ]]; then
            ALL_STEPS_PASSED=false
        fi
    fi

    # Build step result JSON
    step_json=$(jq -n \
        --arg step_name "$step_name" \
        --arg command "$command_name" \
        --arg argument "${argument:-}" \
        --argjson step_num "$step_num" \
        --argjson wall_time_ms "$wall_time_ms" \
        --argjson exit_code "$step_exit" \
        --argjson tokens "$tokens" \
        --argjson agent_passed "$agent_passed" \
        --arg agent_reasoning "$agent_reasoning" \
        --arg step_goal "${step_goal:-}" \
        --arg result "$result_text" \
        --arg stderr "$stderr_output" \
        --argjson checks "$step_checks" \
        '{
            step: $step_num,
            name: $step_name,
            command: $command,
            argument: $argument,
            wall_time_ms: $wall_time_ms,
            exit_code: $exit_code,
            tokens: $tokens,
            agent_passed: $agent_passed,
            agent_reasoning: $agent_reasoning,
            step_goal: $step_goal,
            result: $result,
            stderr: $stderr,
            checks: $checks
        }')

    STEP_RESULTS=$(echo "$STEP_RESULTS" | jq --argjson step "$step_json" '. + [$step]')
done

# ============================================================
# Final Validation
# ============================================================

log ""
log_step "Final validation..."
CHECKS="[]"

if declare -f narrative_validate_final >/dev/null 2>&1; then
    narrative_validate_final
fi

final_checks="$CHECKS"
final_failed=$(echo "$final_checks" | jq '[.[] | select(.passed | not)] | length')
if [[ "$final_failed" -gt 0 ]]; then
    ALL_STEPS_PASSED=false
fi

# ============================================================
# Emit Combined Result
# ============================================================

mkdir -p "$RESULTS_DIR"
timestamp=$(date +%Y%m%d-%H%M%S)
result_file="$RESULTS_DIR/${PROVIDER}-${NARRATIVE}-run${RUN_ID}-${timestamp}.json"

# Compute total cost and cache tokens
total_cost_usd=$(echo "$STEP_RESULTS" | jq '[.[].tokens.cost_usd // 0] | add // 0')
total_cache_read=$(echo "$STEP_RESULTS" | jq '[.[].tokens.cache_read // 0] | add // 0')

jq -n \
    --arg provider "$PROVIDER" \
    --arg scenario "$NARRATIVE" \
    --arg narrative "$NARRATIVE" \
    --arg run_id "$RUN_ID" \
    --argjson wall_time_ms "$total_wall_time_ms" \
    --argjson exit_code "$(if $ALL_STEPS_PASSED; then echo 0; else echo 1; fi)" \
    --argjson tokens "$(jq -n \
        --argjson input "$total_input_tokens" \
        --argjson output "$total_output_tokens" \
        --argjson cache_read "$total_cache_read" \
        --argjson cost_usd "$total_cost_usd" \
        '{ input: $input, output: $output, cache_read: $cache_read, cache_creation: 0, cost_usd: $cost_usd }')" \
    --argjson steps "$STEP_RESULTS" \
    --argjson final_checks "$final_checks" \
    --arg result "narrative:$NARRATIVE" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg workdir "$TEST_DIR" \
    --argjson is_narrative true \
    '{
        provider: $provider,
        scenario: $scenario,
        narrative: $narrative,
        run_id: $run_id,
        is_narrative: $is_narrative,
        wall_time_ms: $wall_time_ms,
        exit_code: $exit_code,
        tokens: $tokens,
        steps: $steps,
        final_checks: $final_checks,
        result: $result,
        timestamp: $timestamp,
        workdir: $workdir
    }' > "$result_file"

# Also generate a matching validate file for the report pipeline
validate_file="$RESULTS_DIR/${PROVIDER}-${NARRATIVE}-run${RUN_ID}-${timestamp}-validate.json"

# Collect all checks from all steps + final
all_step_checks=$(echo "$STEP_RESULTS" | jq '[.[].checks[]]')
all_checks=$(jq -n --argjson steps "$all_step_checks" --argjson final "$final_checks" '$steps + $final')
total_checks=$(echo "$all_checks" | jq 'length')
passed_checks=$(echo "$all_checks" | jq '[.[] | select(.passed)] | length')
failed_checks=$(echo "$all_checks" | jq '[.[] | select(.passed | not)] | length')

jq -n \
    --arg provider "$PROVIDER" \
    --arg scenario "$NARRATIVE" \
    --arg run_id "$RUN_ID" \
    --arg test_dir "$TEST_DIR" \
    --argjson checks "$all_checks" \
    --argjson all_passed "$ALL_STEPS_PASSED" \
    --argjson total "$total_checks" \
    --argjson passed "$passed_checks" \
    --argjson failed "$failed_checks" \
    --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    --arg run_file "$result_file" \
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

# Summary
log ""
total_steps=${#NARRATIVE_STEPS[@]}
total_sec=$((total_wall_time_ms / 1000))

if $ALL_STEPS_PASSED; then
    log_success "Narrative '$NARRATIVE' completed: $total_steps steps in ${total_sec}s"
else
    log_error "Narrative '$NARRATIVE' had failures: $total_steps steps in ${total_sec}s"
fi
log_step "Tokens: ${total_input_tokens} in / ${total_output_tokens} out"
log_step "Result: $result_file"

# Output result file path to stdout
echo "$result_file"

# Exit with non-zero if any checks failed
$ALL_STEPS_PASSED || exit 1
