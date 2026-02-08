#!/usr/bin/env bash
# eval-teardown.sh - Clean up isolated eval environment
#
# Removes the test directory and its bare remote created by eval-setup.sh.
#
# Usage:
#   ./tests/eval/eval-teardown.sh /tmp/line-cook-eval.XXXXXX
#   ./tests/eval/eval-teardown.sh --cleanup   # Remove all stale eval dirs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

source "$REPO_ROOT/tests/lib/test-utils.sh"
setup_colors

if [[ $# -eq 0 ]]; then
    echo "Usage: eval-teardown.sh <test-dir> | --cleanup" >&2
    exit 1
fi

if [[ "$1" == "--cleanup" ]]; then
    log_phase "Eval Cleanup: Removing Stale Directories"
    cleanup_stale_tests "/tmp/line-cook-eval*" "/tmp/line-cook-eval-remote*"
    log ""
    log_success "Cleanup complete"
    exit 0
fi

TEST_DIR="$1"

log_phase "Eval Teardown"

if [[ ! -d "$TEST_DIR" ]]; then
    log_warning "Test directory does not exist: $TEST_DIR"
    exit 0
fi

# Remove remote dir if stored
if [[ -f "$TEST_DIR/.eval-remote-dir" ]]; then
    REMOTE_DIR=$(cat "$TEST_DIR/.eval-remote-dir")
    if [[ -d "$REMOTE_DIR" ]]; then
        rm -rf "$REMOTE_DIR"
        log_success "Removed remote: $REMOTE_DIR"
    fi
fi

# Remove test directory
rm -rf "$TEST_DIR"
log_success "Removed test dir: $TEST_DIR"

log ""
log_success "Teardown complete"
