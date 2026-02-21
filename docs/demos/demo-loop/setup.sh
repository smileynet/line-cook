#!/usr/bin/env bash
# Setup script for Line Cook loop demo project.
#
# Usage:
#   bash ~/code/line-cook/docs/demos/demo-loop/setup.sh [--cli kiro|claude|opencode] [target-dir]
#
# Default target: /tmp/line-cook-demo-loop
# Default CLI: claude

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LINE_COOK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CLI="claude"
TARGET=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli)
      CLI="$2"
      shift 2
      ;;
    --cli=*)
      CLI="${1#--cli=}"
      shift
      ;;
    *)
      TARGET="$1"
      shift
      ;;
  esac
done

TARGET="${TARGET:-/tmp/line-cook-demo-loop}"

echo "=== Line Cook Loop Demo Setup ==="
echo ""
echo "  Source:  $SCRIPT_DIR"
echo "  Target:  $TARGET"
echo "  CLI:     $CLI"
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

# Copy project README
echo "Copying project context..."
cp "$SCRIPT_DIR/project-readme.md" README.md

# Initialize beads
echo "Initializing beads..."
bd init --prefix=demo

# Import demo issues
echo "Importing demo issues..."
bd import < "$SCRIPT_DIR/issues.jsonl"

# Set up dependencies (4 explicit)
echo "Setting up dependencies..."
bd dep add demo-001.1.2 demo-001.1.1
bd dep add demo-001.2.1 demo-001.1.1
bd dep add demo-002.1.1 demo-001.1.1
bd dep add demo-002.2.1 demo-002.1.1

# Install CLI plugin if needed
case "$CLI" in
  kiro)
    echo "Installing Kiro plugin..."
    python3 "$LINE_COOK_ROOT/plugins/kiro/install.py" --local
    ;;
  opencode)
    echo "Installing OpenCode plugin..."
    python3 "$LINE_COOK_ROOT/plugins/opencode/install.py" --local
    ;;
  claude)
    echo "Claude Code uses CLAUDE.md (no plugin install needed)."
    ;;
  *)
    echo "Warning: Unknown CLI '$CLI'. No plugin installed."
    ;;
esac

# Commit everything
echo "Committing initial state..."
git add .
git commit -q -m "Initial demo setup"

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
echo "--- Blocked Work ---"
bd blocked
echo ""

# CLI-specific next steps
echo "--- Next Steps ---"
echo ""
case "$CLI" in
  kiro)
    echo "  # Interactive testing:"
    echo "  cd $TARGET"
    echo "  kiro-cli chat --agent line-cook"
    echo "  # Then type: @line-prep"
    echo ""
    echo "  # Autonomous loop:"
    echo "  cd $TARGET"
    echo "  python3 $LINE_COOK_ROOT/core/line-loop-cli.py \\"
    echo "    --cli kiro --epic auto --max-iterations 10 --skip-initial-sync -v"
    ;;
  claude)
    echo "  # Interactive testing:"
    echo "  cd $TARGET"
    echo "  claude"
    echo "  # Then type: /line:prep"
    echo ""
    echo "  # Autonomous loop:"
    echo "  cd $TARGET"
    echo "  python3 $LINE_COOK_ROOT/core/line-loop-cli.py \\"
    echo "    --cli claude --epic auto --max-iterations 10 --skip-initial-sync -v"
    ;;
  opencode)
    echo "  # Interactive testing:"
    echo "  cd $TARGET"
    echo "  opencode"
    echo ""
    echo "  # Autonomous loop:"
    echo "  cd $TARGET"
    echo "  python3 $LINE_COOK_ROOT/core/line-loop-cli.py \\"
    echo "    --cli opencode --epic auto --max-iterations 10 --skip-initial-sync -v"
    ;;
esac
echo ""
