#!/bin/bash
# Install line-cook plugin for OpenCode
# Usage: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_PLUGINS="${HOME}/.config/opencode/plugins"
OPENCODE_COMMANDS="${HOME}/.config/opencode/commands"
OPENCODE_AGENTS="${HOME}/.config/opencode/agents"

echo "Installing line-cook plugin for OpenCode..."

# Build the plugin first
echo "Building plugin..."
cd "$SCRIPT_DIR"
if command -v bun &> /dev/null; then
    bun install --silent
    bun run build
else
    echo "Error: bun is required to build the plugin"
    echo "Install bun: https://bun.sh"
    exit 1
fi

# Create directories if they don't exist
mkdir -p "$OPENCODE_PLUGINS" "$OPENCODE_COMMANDS" "$OPENCODE_AGENTS"

# Copy plugin files
echo "Installing plugin..."
cp "$SCRIPT_DIR/dist/line-cook-plugin.js" "$OPENCODE_PLUGINS/"
cp "$SCRIPT_DIR/package.json" "$OPENCODE_PLUGINS/line-cook-package.json"

# Copy command files
echo "Installing commands..."
cp "$SCRIPT_DIR/commands/"*.md "$OPENCODE_COMMANDS/"

# Copy agent files
echo "Installing agents..."
if ls "$SCRIPT_DIR/agents/"*.md 1> /dev/null 2>&1; then
    cp "$SCRIPT_DIR/agents/"*.md "$OPENCODE_AGENTS/"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Plugin installed to: $OPENCODE_PLUGINS/line-cook-plugin.js"
echo ""
echo "Commands installed:"
ls -1 "$OPENCODE_COMMANDS/line-"*.md 2>/dev/null | xargs -I{} basename {} | sed 's/.md$//; s/^/  \//'
echo ""
echo "Agents installed:"
ls -1 "$OPENCODE_AGENTS/"*.md 2>/dev/null | xargs -I{} basename {} | sed 's/.md$//; s/^/  /'
echo ""
echo "Next steps:"
echo "  1. Restart OpenCode"
echo "  2. Run /line-getting-started for workflow guide"