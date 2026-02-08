#!/usr/bin/env bash
# test-prep.sh - Test the prep command across providers
#
# Expected behavior:
# - Syncs git state
# - Shows ready tasks
# - Identifies next task recommendation
# - Does NOT modify beads state
#
# Usage:
#   ./tests/test-prep.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

COMMAND="prep"
TIMEOUT=180
PROVIDERS=("${1:-claude}" "${1:-opencode}" "${1:-kiro}")

# If specific provider requested, use only that
if [[ -n "${1:-}" ]]; then
    PROVIDERS=("$1")
fi

# Cleanup on exit
cleanup() {
    source "$SCRIPT_DIR/lib/teardown-env.sh"
}
trap cleanup EXIT

echo "=== Test: $COMMAND ==="

# Expected patterns in output
EXPECTED_PATTERNS=(
    "(session|ready|available|work|task)"
    "(tc-001|tc-002|validation|README)"
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

    # Run from test directory
    cd "$TEST_DIR"

    # Capture git state before
    git_before=$(git rev-parse HEAD)

    # Run the command
    output=$(run_provider_test "$provider" "$cmd" "$TIMEOUT" 2>&1) || true

    # Check git state unchanged (prep shouldn't commit)
    git_after=$(git rev-parse HEAD)

    # Verify output patterns
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        # Verify git state unchanged
        if [[ "$git_before" == "$git_after" ]]; then
            print_result "$display_name $cmd" 0
            PASSED=$((PASSED + 1))
        else
            print_result "$display_name $cmd" 1
            echo "    Git state changed unexpectedly"
            FAILED=$((FAILED + 1))
        fi
    else
        print_result "$display_name $cmd" 1
        echo "    Output preview: ${output:0:300}..."
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [[ $FAILED -eq 0 && $PASSED -gt 0 ]]; then
    echo -e "${GREEN}All prep tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
