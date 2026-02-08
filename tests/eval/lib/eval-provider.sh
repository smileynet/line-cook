#!/usr/bin/env bash
# eval-provider.sh - Enhanced provider invocation with JSON/metrics capture
#
# Sources tests/lib/test-utils.sh for base provider abstractions.
# Adds eval_provider_run() that captures wall time, tokens, and structured output.
#
# Usage:
#   source tests/eval/lib/eval-provider.sh
#   eval_provider_run "claude" "Run bd ready" 60 /path/to/workdir

set -euo pipefail

EVAL_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EVAL_DIR="$(cd "$EVAL_LIB_DIR/.." && pwd)"
REPO_ROOT="$(cd "$EVAL_DIR/../.." && pwd)"

# Source base test utilities
source "$REPO_ROOT/tests/lib/test-utils.sh"

# Get nanosecond timestamp (fallback for macOS where %N not supported)
get_timestamp_ns() {
    local ts
    ts=$(date +%s%N 2>/dev/null)
    # On macOS, %N is literal "N" — detect and fall back
    if [[ "$ts" == *N ]]; then
        # Fallback: seconds * 1_000_000_000
        echo "$(( $(date +%s) * 1000000000 ))"
    else
        echo "$ts"
    fi
}

# Parse token usage from provider JSON output
# Args: provider, raw_output
# Outputs: JSON object { input: N, output: N }
parse_tokens() {
    local provider="$1"
    local raw_output="$2"
    local input_tokens=0
    local output_tokens=0

    case "$provider" in
        claude)
            # Claude --output-format json: { result, session_id, usage: { input_tokens, output_tokens } }
            input_tokens=$(echo "$raw_output" | jq -r '.usage.input_tokens // 0' 2>/dev/null || echo 0)
            output_tokens=$(echo "$raw_output" | jq -r '.usage.output_tokens // 0' 2>/dev/null || echo 0)
            ;;
        opencode)
            # OpenCode -f json: parse if available
            input_tokens=$(echo "$raw_output" | jq -r '.usage.input_tokens // .input_tokens // 0' 2>/dev/null || echo 0)
            output_tokens=$(echo "$raw_output" | jq -r '.usage.output_tokens // .output_tokens // 0' 2>/dev/null || echo 0)
            ;;
        kiro)
            # Kiro --format json: parse if available
            input_tokens=$(echo "$raw_output" | jq -r '.usage.input_tokens // .tokens.input // 0' 2>/dev/null || echo 0)
            output_tokens=$(echo "$raw_output" | jq -r '.usage.output_tokens // .tokens.output // 0' 2>/dev/null || echo 0)
            ;;
    esac

    echo "{\"input\": $input_tokens, \"output\": $output_tokens}"
}

# Extract result text from provider JSON output
parse_result() {
    local provider="$1"
    local raw_output="$2"

    case "$provider" in
        claude)
            echo "$raw_output" | jq -r '.result // empty' 2>/dev/null || echo "$raw_output"
            ;;
        opencode)
            echo "$raw_output" | jq -r '.result // .output // empty' 2>/dev/null || echo "$raw_output"
            ;;
        kiro)
            echo "$raw_output" | jq -r '.result // .response // empty' 2>/dev/null || echo "$raw_output"
            ;;
    esac
}

# Run a provider headlessly with metrics capture
#
# Args:
#   provider    - claude|opencode|kiro
#   prompt      - The prompt to send
#   timeout_sec - Timeout in seconds
#   workdir     - Working directory (metadata only; caller must cd first)
#   max_turns   - Max turns (claude only, default 10)
#   max_budget  - Max budget USD (claude only, default 5.00)
#
# Output: JSON to stdout with structure:
#   { provider, prompt, wall_time_ms, exit_code, tokens: {input, output},
#     result, stderr, raw_output, timestamp }
eval_provider_run() {
    local provider="$1"
    local prompt="$2"
    local timeout_sec="${3:-120}"
    local workdir="${4:-.}"
    local max_turns="${5:-10}"
    local max_budget="${6:-5.00}"

    local start_ns end_ns wall_time_ms
    local raw_output="" stderr_output="" exit_code=0

    # Temp files for capturing output
    local stdout_file stderr_file
    stdout_file=$(mktemp)
    stderr_file=$(mktemp)
    trap "rm -f '$stdout_file' '$stderr_file'" RETURN

    start_ns=$(get_timestamp_ns)

    case "$provider" in
        claude)
            timeout "$timeout_sec" claude -p "$prompt" \
                --output-format json \
                --allowedTools "Bash,Read,Edit,Glob,Grep,Write" \
                --dangerously-skip-permissions \
                --model sonnet \
                --max-turns "$max_turns" \
                --max-budget-usd "$max_budget" \
                --no-session-persistence \
                >"$stdout_file" 2>"$stderr_file" || exit_code=$?
            ;;
        opencode)
            timeout "$timeout_sec" opencode -p "$prompt" \
                -f json \
                -q \
                >"$stdout_file" 2>"$stderr_file" || exit_code=$?
            ;;
        kiro)
            timeout "$timeout_sec" kiro-cli chat \
                --no-interactive \
                --trust-all-tools \
                --format json \
                "$prompt" \
                >"$stdout_file" 2>"$stderr_file" || exit_code=$?
            ;;
        *)
            echo "{\"error\": \"Unknown provider: $provider\"}" >&2
            rm -f "$stdout_file" "$stderr_file"
            return 1
            ;;
    esac

    end_ns=$(get_timestamp_ns)
    wall_time_ms=$(( (end_ns - start_ns) / 1000000 ))

    raw_output=$(cat "$stdout_file")
    stderr_output=$(cat "$stderr_file")

    # Parse tokens and result
    local tokens result_text
    tokens=$(parse_tokens "$provider" "$raw_output")
    result_text=$(parse_result "$provider" "$raw_output")

    # Truncate large fields for JSON safety
    local max_field_len=10000
    if [[ ${#result_text} -gt $max_field_len ]]; then
        result_text="${result_text:0:$max_field_len}...[truncated]"
    fi
    if [[ ${#stderr_output} -gt $max_field_len ]]; then
        stderr_output="${stderr_output:0:$max_field_len}...[truncated]"
    fi
    if [[ ${#raw_output} -gt $max_field_len ]]; then
        raw_output="${raw_output:0:$max_field_len}...[truncated]"
    fi

    # Emit structured JSON
    jq -n \
        --arg provider "$provider" \
        --arg prompt "$prompt" \
        --argjson wall_time_ms "$wall_time_ms" \
        --argjson exit_code "$exit_code" \
        --argjson tokens "$tokens" \
        --arg result "$result_text" \
        --arg stderr "$stderr_output" \
        --arg raw_output "$raw_output" \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --arg workdir "$workdir" \
        '{
            provider: $provider,
            prompt: $prompt,
            wall_time_ms: $wall_time_ms,
            exit_code: $exit_code,
            tokens: $tokens,
            result: $result,
            stderr: $stderr,
            raw_output: $raw_output,
            timestamp: $timestamp,
            workdir: $workdir
        }'
}
