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
VERSION=$(grep '"version"' "$REPO_DIR/.claude-plugin/plugin.json" | head -1 | sed 's/.*: *"\([^"]*\)".*/\1/')

echo "Installing line-cook plugin v$VERSION for Claude Code (local)..."

# Create marketplace structure if needed
mkdir -p "$MARKETPLACE_DIR/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/commands"

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
cp "$REPO_DIR/.claude-plugin/plugin.json" "$MARKETPLACE_DIR/line/.claude-plugin/"

# Clear old commands and copy fresh
rm -f "$MARKETPLACE_DIR/line/commands/"*.md
cp "$REPO_DIR/commands/"*.md "$MARKETPLACE_DIR/line/commands/"

# List installed commands
echo ""
echo "Installed commands:"
for f in "$MARKETPLACE_DIR/line/commands/"*.md; do
  name=$(basename "$f" .md)
  echo "  /line:$name"
done

echo ""
echo "Installation complete! (LOCAL)"
echo ""
echo "To update this local installation:"
echo "  cd $REPO_DIR && git pull && ./scripts/install-claude-code.sh"
echo ""
echo "For remote installation (auto-updates):"
echo "  /plugin uninstall line"
echo "  /plugin marketplace add smileynet/line-cook"
echo "  /plugin install line@line-cook"
