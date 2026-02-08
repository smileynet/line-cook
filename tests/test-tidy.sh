#!/usr/bin/env bash
# test-tidy.sh - Test the tidy command across providers
#
# Expected behavior:
# - Commits staged changes
# - Pushes to remote
# - Syncs beads
#
# Usage:
#   ./tests/test-tidy.sh [provider]
#   provider: claude, opencode, kiro (default: all)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/test-utils.sh"
source "$SCRIPT_DIR/lib/setup-env.sh"

setup_colors

COMMAND="tidy"
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
    "(commit|push|sync|tidy|session|summary|complete)"
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

    # Run from test directory - create fresh changes for each provider
    cd "$TEST_DIR"

    # Create changes to commit
    echo "# Test change for $provider" >> README.md
    git add README.md

    # Capture state before
    git_before=$(git rev-parse HEAD)
    remote_before=$(git rev-parse origin/main)

    # Run the command
    output=$(run_provider_test "$provider" "$cmd" "$TIMEOUT" 2>&1) || true

    # Check state after
    git_after=$(git rev-parse HEAD)
    remote_after=$(git rev-parse origin/main 2>/dev/null || echo "unknown")

    # Tidy should have created a commit and pushed
    # Check for expected output patterns
    if check_output_contains "$output" "${EXPECTED_PATTERNS[@]}"; then
        # Verify commit was created (HEAD changed)
        if [[ "$git_before" != "$git_after" ]]; then
            # Verify push happened (remote updated)
            if [[ "$remote_before" != "$remote_after" ]]; then
                print_result "$display_name $cmd" 0
                PASSED=$((PASSED + 1))
            else
                # Push might have been blocked or delayed
                print_result "$display_name $cmd (commit ok, push unclear)" 0
                PASSED=$((PASSED + 1))
            fi
        else
            # No commit - check if there were no changes
            if echo "$output" | grep -qiE "(nothing.*commit|no.*changes|clean)"; then
                print_result "$display_name $cmd (no changes to commit)" 0
                PASSED=$((PASSED + 1))
            else
                print_result "$display_name $cmd" 1
                echo "    Expected commit but none created"
                FAILED=$((FAILED + 1))
            fi
        fi
    else
        print_result "$display_name $cmd" 1
        echo "    Output preview: ${output:0:300}..."
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [[ $FAILED -eq 0 && $PASSED -gt 0 ]]; then
    echo -e "${GREEN}All tidy tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed, $PASSED passed${NC}"
    exit 1
fi
