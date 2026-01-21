#!/usr/bin/env bash
# teardown-env.sh - Clean up test environment
#
# Removes:
# - TEST_DIR temp directory
# - REMOTE_DIR temp directory
#
# Usage:
#   source tests/lib/teardown-env.sh

set -euo pipefail

echo "Cleaning up test environment..."

if [[ -n "${TEST_DIR:-}" && -d "$TEST_DIR" ]]; then
    rm -rf "$TEST_DIR"
    echo "  Removed: $TEST_DIR"
fi

if [[ -n "${REMOTE_DIR:-}" && -d "$REMOTE_DIR" ]]; then
    rm -rf "$REMOTE_DIR"
    echo "  Removed: $REMOTE_DIR"
fi

unset TEST_DIR
unset REMOTE_DIR

echo "Cleanup complete."
