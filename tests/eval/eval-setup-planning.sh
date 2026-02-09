#!/usr/bin/env bash
# eval-setup-planning.sh - Create isolated environment for planning narratives
#
# Unlike eval-setup.sh (demo-simple), this creates an empty project with
# pre-seeded brainstorm.md and menu-plan.yaml but NO beads.
# The planning commands (brainstorm, scope, finalize) will create beads.
#
# Usage:
#   TEST_DIR=$(./tests/eval/eval-setup-planning.sh)
#   cd $TEST_DIR && <run eval>
#
# Output: TEST_DIR path to stdout (all other output to stderr)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEMO_DIR="$REPO_ROOT/docs/demos/demo-planning"

# Source shared test utilities
source "$REPO_ROOT/tests/lib/test-utils.sh"
setup_colors

# Verify fixtures exist
if [[ ! -f "$DEMO_DIR/CLAUDE.md" ]]; then
    log_error "Missing fixture: $DEMO_DIR/CLAUDE.md"
    exit 1
fi

log_phase "Eval Setup: Creating Planning Environment"

# Create temp directories
TEST_DIR="$(mktemp -d -t line-cook-eval.XXXXXX)"
REMOTE_DIR="$(mktemp -d -t line-cook-eval-remote.XXXXXX)"

# Store remote dir path for teardown
echo "$REMOTE_DIR" > "$TEST_DIR/.eval-remote-dir"

log_step "Created TEST_DIR: $TEST_DIR"
log_step "Created REMOTE_DIR: $REMOTE_DIR"

# Initialize bare remote
git init --bare "$REMOTE_DIR" >/dev/null 2>&1
log_success "Initialized bare remote"

# Initialize test repo
cd "$TEST_DIR"
git init >/dev/null 2>&1
git config user.email "eval@line-cook.dev"
git config user.name "Eval Harness"
git remote add origin "$REMOTE_DIR"
log_success "Initialized test repository"

# Copy project context
cp "$DEMO_DIR/CLAUDE.md" .
log_success "Copied CLAUDE.md"

# Copy pre-seeded planning artifacts
cp "$DEMO_DIR/brainstorm.md" .
log_success "Copied brainstorm.md"
cp "$DEMO_DIR/menu-plan.yaml" .
log_success "Copied menu-plan.yaml"

# Create minimal scaffold
mkdir -p src

cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TodoWebApp</title>
</head>
<body>
    <h1>Todo App</h1>
    <form id="todo-form">
        <input type="text" id="todo-input" placeholder="Add a todo...">
        <button type="submit">Add</button>
    </form>
    <ul id="todo-list"></ul>
    <script src="src/todo.js"></script>
</body>
</html>
EOF
log_success "Created index.html"

cat > package.json << 'EOF'
{
  "name": "todo-web-app",
  "version": "1.0.0",
  "description": "Vanilla JS todo app for Line Cook demo",
  "scripts": {
    "test": "node src/todo.test.js"
  }
}
EOF
log_success "Created package.json"

cat > .gitignore << 'EOF'
node_modules/
.DS_Store
EOF
log_success "Created .gitignore"

# Initial commit
git add -A
git commit -m "Initial commit: TodoWebApp scaffold with planning artifacts" >/dev/null 2>&1
git push -u origin main >/dev/null 2>&1
log_success "Created initial commit and pushed"

# Initialize beads (empty — planning commands will populate)
bd init --prefix=demo >/dev/null 2>&1
log_success "Initialized beads (prefix: demo, empty)"

# Commit beads setup
git add .beads/ .gitattributes AGENTS.md 2>/dev/null || git add .beads/
git commit -m "Add empty beads configuration" >/dev/null 2>&1
git push >/dev/null 2>&1
log_success "Committed and pushed beads setup"

log ""
log_success "Planning environment ready!"
log "  brainstorm.md — pre-seeded brainstorm output"
log "  menu-plan.yaml — pre-seeded scope output"
log "  bd list → (empty, no issues yet)"

# Output TEST_DIR to stdout
echo "$TEST_DIR"
