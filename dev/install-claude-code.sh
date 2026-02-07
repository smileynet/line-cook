#!/bin/bash
# Install/update line-cook plugin for Claude Code
#
# This creates a LOCAL installation. To update, re-run this script.
# For remote installation (auto-updates via GitHub), use:
#   /plugin marketplace add smileynet/line-cook
#   /plugin install line@line-cook

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/line-cook-marketplace"

# Get version from plugin.json
VERSION=$(grep '"version"' "$REPO_DIR/plugins/claude-code/.claude-plugin/plugin.json" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/')

echo "Installing line-cook plugin v$VERSION for Claude Code (local)..."

# Create marketplace structure if needed
mkdir -p "$MARKETPLACE_DIR/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/commands"
mkdir -p "$MARKETPLACE_DIR/line/agents"
mkdir -p "$MARKETPLACE_DIR/line/scripts"

# Copy marketplace manifest with dynamic version
cat > "$MARKETPLACE_DIR/.claude-plugin/marketplace.json" << EOF
{
  "name": "line-cook-marketplace",
  "owner": { "name": "smileynet" },
  "metadata": {
    "description": "Task-focused workflow orchestration for Claude Code sessions",
    "version": "$VERSION",
    "install_type": "local",
    "source_path": "$REPO_DIR"
  },
  "plugins": [
    {
      "name": "line",
      "source": "./line",
      "description": "Task-focused workflow orchestration - prep, cook, serve, tidy, work",
      "version": "$VERSION"
    }
  ]
}
EOF

# Copy plugin manifest
cp "$REPO_DIR/plugins/claude-code/.claude-plugin/plugin.json" "$MARKETPLACE_DIR/line/.claude-plugin/"

# Clear old commands and copy fresh
rm -f "$MARKETPLACE_DIR/line/commands/"*.md
cp "$REPO_DIR/plugins/claude-code/commands/"*.md "$MARKETPLACE_DIR/line/commands/"

# Clear old agents and copy fresh
rm -f "$MARKETPLACE_DIR/line/agents/"*.md
cp "$REPO_DIR/plugins/claude-code/agents/"*.md "$MARKETPLACE_DIR/line/agents/"

# Clear old scripts and copy fresh
rm -f "$MARKETPLACE_DIR/line/scripts/"*.py
cp "$REPO_DIR/plugins/claude-code/scripts/"*.py "$MARKETPLACE_DIR/line/scripts/" 2>/dev/null || true

# List installed commands
echo ""
echo "Installed commands:"
for f in "$MARKETPLACE_DIR/line/commands/"*.md; do
  name=$(basename "$f" .md)
  echo "  /line:$name"
done

# List installed agents
echo ""
echo "Installed agents:"
for f in "$MARKETPLACE_DIR/line/agents/"*.md; do
  name=$(basename "$f" .md)
  echo "  line:$name"
done

# List installed scripts
if ls "$MARKETPLACE_DIR/line/scripts/"*.py 1>/dev/null 2>&1; then
  echo ""
  echo "Installed scripts:"
  for f in "$MARKETPLACE_DIR/line/scripts/"*.py; do
    name=$(basename "$f")
    echo "  $name"
  done
fi

echo ""
echo "Installation complete! (LOCAL) - v$VERSION"
echo ""
echo "IMPORTANT: Start a new Claude Code session (/clear) for changes to take effect."
echo "           Claude Code caches commands per version - new commands require version bump."
echo ""
echo "To update this local installation:"
echo "  cd $REPO_DIR && git pull && ./dev/install-claude-code.sh"
echo ""
echo "For remote installation (auto-updates):"
echo "  /plugin uninstall line"
echo "  /plugin marketplace add smileynet/line-cook"
echo "  /plugin install line@line-cook"
