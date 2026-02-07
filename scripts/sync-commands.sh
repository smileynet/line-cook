#!/bin/bash
set -e

# Sync command templates to Claude Code, OpenCode, and Kiro destinations
# Usage: ./scripts/sync-commands.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/commands/templates"
CLAUDE_DIR="$REPO_ROOT/commands"
OPENCODE_DIR="$REPO_ROOT/line-cook-opencode/commands"
KIRO_DIR="$REPO_ROOT/line-cook-kiro/prompts"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Syncing command templates...${NC}"

for template in "$TEMPLATES_DIR"/*.md.template; do
    [ -f "$template" ] || continue
    name=$(basename "$template" .md.template)

    echo "  $name.md"

    # Claude Code version: `line:` namespace, keep CC blocks, strip OpenCode/Kiro blocks
    sed 's/@NAMESPACE@/line:/g' "$template" \
      | sed '/@IF_OPENCODE@/,/@ENDIF_OPENCODE@/d' \
      | sed '/@IF_KIRO@/,/@ENDIF_KIRO@/d' \
      | sed '/@IF_CLAUDECODE@/d; /@ENDIF_CLAUDECODE@/d' \
      > "$CLAUDE_DIR/${name}.md"

    # OpenCode version: `line-` namespace, keep OpenCode blocks, strip Claude Code/Kiro blocks
    sed 's/@NAMESPACE@/line-/g' "$template" \
      | sed '/@IF_CLAUDECODE@/,/@ENDIF_CLAUDECODE@/d' \
      | sed '/@IF_KIRO@/,/@ENDIF_KIRO@/d' \
      | sed '/@IF_OPENCODE@/d; /@ENDIF_OPENCODE@/d' \
      > "$OPENCODE_DIR/line-${name}.md"

    # Kiro version: `@line-` namespace, keep OpenCode+Kiro blocks, strip Claude Code blocks
    # Also strips YAML frontmatter (awk removes everything up to second --- delimiter)
    sed 's|/@NAMESPACE@|@line-|g' "$template" \
      | sed 's/@NAMESPACE@/line-/g' \
      | sed '/@IF_CLAUDECODE@/,/@ENDIF_CLAUDECODE@/d' \
      | sed '/@IF_OPENCODE@/d; /@ENDIF_OPENCODE@/d' \
      | sed '/@IF_KIRO@/d; /@ENDIF_KIRO@/d' \
      | awk 'BEGIN{c=0;p=0} /^---$/ && !p {c++; if(c==2) p=1; next} p{print}' \
      | sed '/./,$!d' \
      > "$KIRO_DIR/line-${name}.md"
done

echo -e "${GREEN}✓ Commands synced${NC}"
