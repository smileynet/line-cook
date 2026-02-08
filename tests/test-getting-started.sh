#!/usr/bin/env bash
# test-getting-started.sh - Test the getting-started command across providers
#
# Expected behavior:
# - Read-only operation (no state changes)
# - Outputs workflow guide containing: prep, cook, serve, tidy, beads
#
# Usage:
#   ./tests/test-getting-started.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"

setup_colors

COMMAND="getting-started"
TIMEOUT=120
MAX_RETRIES=2  # LLM output is non-deterministic; retry on pattern match failure
PROVIDERS=("${1:-claude}" "${1:-opencode}" "${1:-kiro}")

# If specific provider requested, use only that
if [[ -n "${1:-}" ]]; then
    PROVIDERS=("$1")
fi

echo "=== Test: $COMMAND ==="

# Expected patterns in output
EXPECTED_PATTERNS=(
    "prep"
    "cook"
    "serve"
    "tidy"
    "(beads|bd)"
)

PASSED=0
FAILED=0

for provider in "${PROVIDERS[@]}"; do
    if ! check_provider_available "$provider"; then
        echo -e "  ${YELLOW}SKIP${NC} $(get_provider_display_name "$provider") - not installed"
        continue
    fi

    cmd=$(get_provider_command "$provider" "$COMMAND")
    display_name=$(get_provider_display_name "$provider")

    # Use longer timeout for slow providers
    provider_timeout=$TIMEOUT
    if [[ "$provider" == "opencode" ]]; then
        provider_timeout=300
    fi

    # Retry loop — LLM output is non-deterministic
    test_passed=false
    for attempt in $(seq 1 "$MAX_RETRIES"); do
        # Run the command (no setup needed - read-only)
        output=$(run_provider_test "$provider" "$cmd" "$provider_timeout" 2>&1) || true

        # Check for expected patterns
        if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}" 2>/dev/null; then
            test_passed=true
            break
        fi

        if [[ "$attempt" -lt "$MAX_RETRIES" ]]; then
            echo -e "  ${YELLOW}RETRY${NC} $display_name (attempt $attempt/$MAX_RETRIES)" >&2
        fi
    done

    if $test_passed; then
        print_result "$display_name $cmd" 0
        PASSED=$((PASSED + 1))
    else
        print_result "$display_name $cmd" 1
        echo "    Output preview: ${output:0:200}..."
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [[ $FAILED -eq 0 && $PASSED -gt 0 ]]; then
    echo -e "${GREEN}All getting-started tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
