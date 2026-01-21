#!/usr/bin/env bash
# test-serve.sh - Test the serve command across providers
#
# Expected behavior:
# - Reviews completed work via headless analysis
# - May identify issues and create beads
# - Does NOT commit or push
#
# Note: This test works best when there are changes to review.
# We create some staged changes for review.
#
# Usage:
#   ./tests/test-serve.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

COMMAND="serve"
TIMEOUT=300
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

# Create some changes to review
cd "$TEST_DIR"
cat >> src/validation.py << 'EOF'


def validate_username(username: str) -> bool:
    """Validate username format.

    Args:
        username: Username to validate

    Returns:
        True if valid username
    """
    return len(username) >= 3 and username.isalnum()
EOF
git add src/validation.py

# Expected patterns in output
EXPECTED_PATTERNS=(
    "(review|changes|validation|diff|verdict|analysis)"
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

    # Check git state (serve shouldn't commit)
    git_after=$(git rev-parse HEAD)

    # Verify output patterns
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        if [[ "$git_before" == "$git_after" ]]; then
            print_result "$display_name $cmd" 0
            ((PASSED++))
        else
            print_result "$display_name $cmd" 1
            echo "    Git state changed unexpectedly (serve shouldn't commit)"
            ((FAILED++))
        fi
    else
        # Check if it failed due to no changes (still valid)
        if echo "$output" | grep -qiE "(no.*changes|nothing.*review|clean)"; then
            print_result "$display_name $cmd (no changes)" 0
            ((PASSED++))
        else
            print_result "$display_name $cmd" 1
            echo "    Output preview: ${output:0:300}..."
            ((FAILED++))
        fi
    fi
done

echo ""
if [[ $FAILED -eq 0 && $PASSED -gt 0 ]]; then
    echo -e "${GREEN}All serve tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
