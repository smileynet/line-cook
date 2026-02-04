#!/usr/bin/env bash
# setup-env.sh - Create isolated test environment for Line Cook testing
#
# Creates:
# - Temp directory with git repo initialized
# - Mock beads configuration
# - Sample project files
# - Local bare remote for push testing
#
# Exports:
# - TEST_DIR - Path to temp test directory
# - REMOTE_DIR - Path to bare remote repo
#
# Usage:
#   source tests/lib/setup-env.sh
#   # ... run tests ...
#   source tests/lib/teardown-env.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIXTURES_DIR="$(cd "$SCRIPT_DIR/../fixtures" && pwd)"

# Clean up stale test directories from previous runs
cleanup_stale_tests() {
    local found=0
    for dir in /tmp/line-cook-test* /tmp/line-cook-remote*; do
        if [[ -d "$dir" ]]; then
            echo "  ! Removing stale test directory: $dir"
            rm -rf "$dir"
            found=$((found + 1))
        fi
    done
    if [[ $found -gt 0 ]]; then
        echo "  ✓ Cleaned up $found stale test director(ies)"
    fi
}

# Clean up before creating new directories
cleanup_stale_tests

# Create temp directories
export TEST_DIR="$(mktemp -d -t line-cook-test.XXXXXX)"
export REMOTE_DIR="$(mktemp -d -t line-cook-remote.XXXXXX)"

echo "Setting up test environment..."
echo "  TEST_DIR: $TEST_DIR"
echo "  REMOTE_DIR: $REMOTE_DIR"

# Initialize bare remote for push testing
git init --bare "$REMOTE_DIR" >/dev/null 2>&1

# Initialize test repo
cd "$TEST_DIR"
git init >/dev/null 2>&1
git config user.email "test@example.com"
git config user.name "Test User"
git remote add origin "$REMOTE_DIR"

# Copy sample project files
mkdir -p src
cp -r "$FIXTURES_DIR/sample-project/"* . 2>/dev/null || true

# Initial commit (required for beads to work)
git add -A
git commit -m "Initial commit" >/dev/null 2>&1
git push -u origin main >/dev/null 2>&1

# Initialize beads with test prefix
bd init --prefix=tc >/dev/null 2>&1

# Import mock beads issues from JSONL
bd import -i "$FIXTURES_DIR/mock-beads/issues.jsonl" >/dev/null 2>&1

# Add dependency (tc-003 depends on tc-001)
bd dep add tc-003 tc-001 >/dev/null 2>&1

# Commit beads setup
git add .beads/
git commit -m "Add beads configuration" >/dev/null 2>&1
git push >/dev/null 2>&1

echo "Test environment ready."
echo ""
