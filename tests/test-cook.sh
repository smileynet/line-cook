#!/usr/bin/env bash
# test-cook.sh - Test the cook command across providers
#
# Expected behavior:
# - Selects or prompts for task
# - Executes task with guardrails
# - May modify files and beads state
#
# Note: This is an LLM-heavy test that actually executes work.
# Expect API costs and longer runtimes (300-600s).
#
# Usage:
#   ./tests/test-cook.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

COMMAND="cook"
TIMEOUT=600  # Longer timeout for actual work
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
echo -e "${YELLOW}Warning: This test executes LLM work and may incur API costs${NC}"
echo ""

# Expected patterns in output (flexible - cook can do many things)
EXPECTED_PATTERNS=(
    "(cooking|task|work|executing|progress|tc-)"
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

    # Run the command
    output=$(run_provider_test "$provider" "$cmd" "$TIMEOUT" 2>&1) || true

    # Check output for expected patterns
    # Cook is successful if it shows any indication of working on a task
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        print_result "$display_name $cmd" 0
        PASSED=$((PASSED + 1))
    else
        # Check if it failed due to no work available (still valid)
        if echo "$output" | grep -qiE "(no.*ready|no.*tasks|nothing.*work)"; then
            print_result "$display_name $cmd (no work available)" 0
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
    echo -e "${GREEN}All cook tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
