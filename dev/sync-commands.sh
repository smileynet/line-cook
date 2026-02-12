#!/bin/bash
set -e

# Sync command templates to Claude Code, OpenCode, and Kiro destinations
# Usage: ./dev/sync-commands.sh

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/core/templates/commands"
CLAUDE_DIR="$REPO_ROOT/plugins/claude-code/commands"
OPENCODE_DIR="$REPO_ROOT/plugins/opencode/commands"
KIRO_DIR="$REPO_ROOT/plugins/kiro/prompts"

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

# === Agent template sync ===

AGENT_TEMPLATES_DIR="$REPO_ROOT/core/templates/agents"
AGENT_CC_DIR="$REPO_ROOT/plugins/claude-code/agents"
AGENT_OC_DIR="$REPO_ROOT/plugins/opencode/agents"
AGENT_KIRO_DIR="$REPO_ROOT/plugins/kiro/steering"

mkdir -p "$AGENT_OC_DIR"

echo -e "${BLUE}Syncing agent templates...${NC}"

for template in "$AGENT_TEMPLATES_DIR"/*.md.template; do
    [ -f "$template" ] || continue
    name=$(basename "$template" .md.template)

    echo "  $name.md"

    # Claude Code version: keep CC blocks, strip OpenCode/Kiro blocks, squeeze blank lines
    sed '/@IF_OPENCODE@/,/@ENDIF_OPENCODE@/d' "$template" \
      | sed '/@IF_KIRO@/,/@ENDIF_KIRO@/d' \
      | sed '/@IF_CLAUDECODE@/d; /@ENDIF_CLAUDECODE@/d' \
      | cat -s \
      > "$AGENT_CC_DIR/${name}.md"

    # OpenCode version: keep OpenCode blocks, strip CC/Kiro blocks, squeeze blank lines
    sed '/@IF_CLAUDECODE@/,/@ENDIF_CLAUDECODE@/d' "$template" \
      | sed '/@IF_KIRO@/,/@ENDIF_KIRO@/d' \
      | sed '/@IF_OPENCODE@/d; /@ENDIF_OPENCODE@/d' \
      | cat -s \
      > "$AGENT_OC_DIR/${name}.md"

    # Kiro version: keep Kiro blocks, strip CC/OpenCode blocks, strip frontmatter, squeeze blank lines
    sed '/@IF_CLAUDECODE@/,/@ENDIF_CLAUDECODE@/d' "$template" \
      | sed '/@IF_OPENCODE@/,/@ENDIF_OPENCODE@/d' \
      | sed '/@IF_KIRO@/d; /@ENDIF_KIRO@/d' \
      | awk 'BEGIN{c=0;p=0} NR==1 && !/^---$/ {p=1} /^---$/ && !p {c++; if(c==2) p=1; next} p{print}' \
      | sed '/./,$!d' \
      | cat -s \
      > "$AGENT_KIRO_DIR/${name}.md"
done

echo -e "${GREEN}✓ Agents synced${NC}"

# === Local dev: copy OpenCode agents to .opencode/agents/ ===

LOCAL_OC_AGENTS="$REPO_ROOT/.opencode/agents"
if [ -d "$LOCAL_OC_AGENTS" ]; then
    cp "$AGENT_OC_DIR/"*.md "$LOCAL_OC_AGENTS/" 2>/dev/null && \
        echo -e "${GREEN}✓ Local .opencode/agents/ updated${NC}"
fi
