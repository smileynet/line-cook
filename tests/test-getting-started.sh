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

    # Run the command (no setup needed - read-only)
    output=$(run_provider_test "$provider" "$cmd" "$TIMEOUT" 2>&1) || true

    # Check for expected patterns
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        print_result "$display_name $cmd" 0
        ((PASSED++))
    else
        print_result "$display_name $cmd" 1
        echo "    Output preview: ${output:0:200}..."
        ((FAILED++))
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
