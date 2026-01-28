#!/bin/bash
set -e

# Sync command templates to both Claude Code and OpenCode destinations
# Usage: ./sync-commands.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/commands/templates"
CLAUDE_DIR="$REPO_ROOT/commands"
OPENCODE_DIR="$REPO_ROOT/line-cook-opencode/commands"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Syncing command templates...${NC}"

# Sync cook command
echo "  cook.md"
sed 's/@NAMESPACE@/line:/g' "$TEMPLATES_DIR/cook.md.template" > "$CLAUDE_DIR/cook.md"
sed 's/@NAMESPACE@/line-/g' "$TEMPLATES_DIR/cook.md.template" > "$OPENCODE_DIR/line-cook.md"

# Add platform-specific STOP instruction for OpenCode
sed -i '/STOP after completing/c\**When run directly:** STOP after completing, show NEXT STEP, and wait for user.\
**When run via `\/line-run`:** Continue to the next step without stopping.' "$OPENCODE_DIR/line-cook.md"

# TODO: Add other commands (prep, serve, tidy, run) as needed

echo -e "${GREEN}✓ Commands synced${NC}"
