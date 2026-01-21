#!/bin/bash
# Install line-cook for Kiro CLI
# Usage: ./install.sh [--global | --local]
#
# --global: Install to ~/.kiro/ (default)
# --local:  Install to .kiro/ in current directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
INSTALL_MODE="global"
for arg in "$@"; do
    case $arg in
        --global)
            INSTALL_MODE="global"
            ;;
        --local)
            INSTALL_MODE="local"
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--global | --local]"
            echo ""
            echo "  --global  Install to ~/.kiro/ (default)"
            echo "  --local   Install to .kiro/ in current directory"
            exit 0
            ;;
    esac
done

if [ "$INSTALL_MODE" = "global" ]; then
    KIRO_DIR="${HOME}/.kiro"
    echo "Installing line-cook for Kiro CLI (global)..."
else
    KIRO_DIR=".kiro"
    echo "Installing line-cook for Kiro CLI (local)..."
fi

# Create directories
mkdir -p "$KIRO_DIR/agents"
mkdir -p "$KIRO_DIR/steering"
mkdir -p "$KIRO_DIR/skills/line-cook"
mkdir -p "$KIRO_DIR/scripts"

# Copy agent configuration
echo "Installing agent configuration..."
cp "$SCRIPT_DIR/agents/line-cook.json" "$KIRO_DIR/agents/"

# Copy steering files
echo "Installing steering files..."
cp "$SCRIPT_DIR/steering/"*.md "$KIRO_DIR/steering/"

# Copy skills
echo "Installing skills..."
cp "$SCRIPT_DIR/skills/line-cook/SKILL.md" "$KIRO_DIR/skills/line-cook/"

# Copy placeholder script files if they exist
if [ -d "$SCRIPT_DIR/scripts" ] && [ "$(ls -A "$SCRIPT_DIR/scripts" 2>/dev/null)" ]; then
    echo "Installing hook scripts..."
    for f in "$SCRIPT_DIR/scripts/"*.sh; do
        [ -f "$f" ] && cp "$f" "$KIRO_DIR/scripts/" && chmod +x "$KIRO_DIR/scripts/$(basename "$f")"
    done
fi

# Update agent JSON to use correct paths
if [ "$INSTALL_MODE" = "local" ]; then
    # For local install, paths are already relative (.kiro/)
    :
else
    # For global install, update paths to use ~/.kiro/
    sed -i 's|\.kiro/|~/.kiro/|g' "$KIRO_DIR/agents/line-cook.json" 2>/dev/null || \
    sed -i '' 's|\.kiro/|~/.kiro/|g' "$KIRO_DIR/agents/line-cook.json"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Installed to: $KIRO_DIR"
echo ""
echo "Files installed:"
echo "  agents/line-cook.json      - Agent configuration"
echo "  steering/line-cook.md      - Workflow instructions"
echo "  steering/beads.md          - Beads quick reference"
echo "  steering/session.md        - Session protocols"
echo "  skills/line-cook/SKILL.md  - Lazy-loaded documentation"
echo ""
echo "Next steps:"
echo "  1. Start Kiro CLI with: kiro-cli --agent line-cook"
echo "  2. Say 'prep' or 'work' to start the workflow"
echo ""
echo "Note: Hooks are configured but hook scripts are not yet implemented."
echo "The workflow commands work without hooks."
