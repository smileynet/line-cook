#!/bin/bash
# Install line-cook commands for OpenCode
# Usage: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCODE_COMMANDS="${HOME}/.config/opencode/commands"

echo "Installing line-cook commands for OpenCode..."

# Create commands directory if it doesn't exist
mkdir -p "$OPENCODE_COMMANDS"

# Copy command files
cp "$SCRIPT_DIR/commands/"*.md "$OPENCODE_COMMANDS/"

# Copy AGENTS.md for reference
mkdir -p "${HOME}/.config/opencode"
cp "$SCRIPT_DIR/AGENTS.md" "${HOME}/.config/opencode/line-cook-AGENTS.md"

echo "Installed commands:"
ls -1 "$OPENCODE_COMMANDS/line-"*.md 2>/dev/null | xargs -I{} basename {} | sed 's/.md$//' | sed 's/^/  \//'

echo ""
echo "Installation complete!"
echo "Commands available: /line-prep, /line-cook, /line-serve, /line-tidy"
echo ""
echo "Note: AGENTS.md copied to ~/.config/opencode/line-cook-AGENTS.md"
