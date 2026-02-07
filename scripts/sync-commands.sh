#!/bin/bash
set -e

# Sync command templates to both Claude Code and OpenCode destinations
# Usage: ./scripts/sync-commands.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/commands/templates"
CLAUDE_DIR="$REPO_ROOT/commands"
OPENCODE_DIR="$REPO_ROOT/line-cook-opencode/commands"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Syncing command templates...${NC}"

for template in "$TEMPLATES_DIR"/*.md.template; do
    [ -f "$template" ] || continue
    name=$(basename "$template" .md.template)

    echo "  $name.md"

    # Claude Code version: line: namespace, keep CC blocks, strip OC blocks
    sed 's/@NAMESPACE@/line:/g' "$template" \
      | sed '/@IF_OPENCODE@/,/@ENDIF_OPENCODE@/d' \
      | sed '/@IF_CLAUDECODE@/d; /@ENDIF_CLAUDECODE@/d' \
      > "$CLAUDE_DIR/${name}.md"

    # OpenCode version: line- namespace, keep OC blocks, strip CC blocks
    sed 's/@NAMESPACE@/line-/g' "$template" \
      | sed '/@IF_CLAUDECODE@/,/@ENDIF_CLAUDECODE@/d' \
      | sed '/@IF_OPENCODE@/d; /@ENDIF_OPENCODE@/d' \
      > "$OPENCODE_DIR/line-${name}.md"
done

echo -e "${GREEN}✓ Commands synced${NC}"
