#!/bin/bash
# Install/update line-cook plugin for Claude Code

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
MARKETPLACE_DIR="$HOME/.claude/plugins/marketplaces/line-cook-marketplace"

echo "Installing line-cook plugin for Claude Code..."

# Create marketplace structure if needed
mkdir -p "$MARKETPLACE_DIR/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/.claude-plugin"
mkdir -p "$MARKETPLACE_DIR/line/commands"

# Copy marketplace manifest
cat > "$MARKETPLACE_DIR/.claude-plugin/marketplace.json" << 'EOF'
{
  "name": "line-cook-marketplace",
  "owner": { "name": "smileynet" },
  "metadata": {
    "description": "Task-focused workflow orchestration for Claude Code sessions",
    "version": "0.2.0"
  },
  "plugins": [
    {
      "name": "line",
      "source": "./line",
      "description": "Task-focused workflow orchestration - prep, cook, serve, tidy, work",
      "version": "0.2.0"
    }
  ]
}
EOF

# Copy plugin manifest
cp "$REPO_DIR/.claude-plugin/plugin.json" "$MARKETPLACE_DIR/line/.claude-plugin/"

# Copy all commands
cp "$REPO_DIR/commands/"*.md "$MARKETPLACE_DIR/line/commands/"

# List installed commands
echo ""
echo "Installed commands:"
for f in "$MARKETPLACE_DIR/line/commands/"*.md; do
  name=$(basename "$f" .md)
  echo "  /line:$name"
done

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Run '/plugin update line' in Claude Code to refresh the cache"
echo "  2. Restart Claude Code to pick up changes"
