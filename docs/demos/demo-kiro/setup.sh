#!/usr/bin/env bash
# Setup script for Line Cook Kiro demo project.
#
# Usage:
#   bash ~/code/line-cook/docs/demos/demo-kiro/setup.sh [target-dir]
#
# Default target: /tmp/line-cook-demo-kiro

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINE_COOK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TARGET="${1:-/tmp/line-cook-demo-kiro}"

echo "=== Line Cook Kiro Demo Setup ==="
echo ""
echo "  Source:  $SCRIPT_DIR"
echo "  Target:  $TARGET"
echo "  Plugin:  $LINE_COOK_ROOT/plugins/kiro"
echo ""

# Preflight checks
for cmd in git python3 bd; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: $cmd not found. Please install it first."
    exit 1
  fi
done

# Clean previous demo if present
if [ -d "$TARGET" ]; then
  echo "Removing previous demo at $TARGET..."
  rm -rf "$TARGET"
fi

# Create and initialize project
echo "Creating project directory..."
mkdir -p "$TARGET"
cd "$TARGET"

echo "Initializing git repository..."
git init -q
git commit --allow-empty -q -m "Initial commit"

# Copy project README (Kiro reads README.md for project context)
echo "Copying project context..."
cp "$SCRIPT_DIR/project-readme.md" README.md

# Initialize beads
echo "Initializing beads..."
bd init --prefix=demo

# Import demo issues
echo "Importing demo issues..."
cat "$SCRIPT_DIR/issues.jsonl" | bd import

# Set up dependencies
echo "Setting up dependencies..."
bd dep add demo-001.1.2 demo-001.1.1

# Install Kiro plugin locally
echo "Installing Kiro plugin..."
python3 "$LINE_COOK_ROOT/plugins/kiro/install.py" --local

# Commit everything
echo "Committing initial state..."
git add .
git commit -q -m "Initial demo setup with Kiro plugin"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Project ready at: $TARGET"
echo ""

# Show state
echo "--- Beads State ---"
bd list --status=open
echo ""
echo "--- Ready Work ---"
bd ready
echo ""

echo "--- Next Steps ---"
echo ""
echo "  # Interactive testing:"
echo "  cd $TARGET"
echo "  kiro-cli chat --agent line-cook"
echo "  # Then type: @line-prep"
echo ""
echo "  # Autonomous loop:"
echo "  cd $TARGET"
echo "  python3 $LINE_COOK_ROOT/core/line-loop-cli.py \\"
echo "    --cli kiro --max-iterations 3 --skip-initial-sync -v"
echo ""
