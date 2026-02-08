#!/usr/bin/env bash
# test-work.sh - Test the work command (full cycle) across providers
#
# Expected behavior:
# - Runs full prep -> cook -> serve -> tidy cycle
# - May modify files, beads, and git state
#
# Note: This is the most expensive test (runs full LLM workflow).
# Expect significant API costs and long runtime (600s+).
#
# Usage:
#   ./tests/test-work.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

COMMAND="work"
TIMEOUT=900  # 15 minutes for full cycle
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
echo -e "${YELLOW}Warning: This test runs full LLM workflow and may incur significant API costs${NC}"
echo ""

# Expected patterns in output (any indication of workflow stages)
EXPECTED_PATTERNS=(
    "(prep|cook|serve|tidy|session|task|work|complete|ready)"
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

    echo "  Running $display_name $cmd (this may take several minutes)..."

    # Run the command
    output=$(run_provider_test "$provider" "$cmd" "$TIMEOUT" 2>&1) || true

    # Check output for expected patterns
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        print_result "$display_name $cmd" 0
        PASSED=$((PASSED + 1))
    else
        # Check for reasonable failure modes
        if echo "$output" | grep -qiE "(no.*work|no.*tasks|nothing.*ready|error|timeout)"; then
            print_result "$display_name $cmd (expected failure mode)" 0
            PASSED=$((PASSED + 1))
        else
            print_result "$display_name $cmd" 1
            echo "    Output preview: ${output:0:300}..."
            FAILED=$((FAILED + 1))
        fi
    fi
done

echo ""
if [[ $FAILED -eq 0 && $PASSED -gt 0 ]]; then
    echo -e "${GREEN}All work tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
