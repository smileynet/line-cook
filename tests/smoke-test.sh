#!/usr/bin/env bash
# smoke-test.sh - Cross-platform smoke test for Line Cook workflows
#
# Modular smoke test with separate setup, validate, and teardown phases.
# Designed for interactive Claude sessions to execute the workflow directly,
# avoiding API conflicts from spawning headless subprocesses.
#
# Usage:
#   ./tests/smoke-test.sh --setup              # Create env, output TEST_DIR path
#   ./tests/smoke-test.sh --validate <dir>     # Validate artifacts in dir
#   ./tests/smoke-test.sh --teardown <dir>     # Clean up test directory
#   ./tests/smoke-test.sh --cleanup            # Remove stale test directories only
#   ./tests/smoke-test.sh --dry-run            # Check dependencies only
#
# Interactive workflow (Claude runs this):
#   1. TEST_DIR=$(./tests/smoke-test.sh --setup)
#   2. cd $TEST_DIR && run Line Cook commands
#   3. ./tests/smoke-test.sh --validate $TEST_DIR
#   4. ./tests/smoke-test.sh --teardown $TEST_DIR
#
# Cost estimate: ~$0.50-2.00 per run (primarily the cook phase)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
RESULTS_DIR="$SCRIPT_DIR/results"

# Colors (disabled in CI mode or when piping)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    BOLD=''
    NC=''
fi

# Defaults
MODE=""
TARGET_DIR=""
PLATFORM="claude"
DRY_RUN=false
VERBOSE=false
SKIP_COOK=false

# Logging functions (output to stderr so stdout is clean for --setup)
log() {
    echo -e "$@" >&2
}

log_phase() {
    log ""
    log "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "${BOLD}$1${NC}"
    log "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_step() {
    log "  ${BLUE}▶${NC} $1"
}

log_success() {
    log "  ${GREEN}✓${NC} $1"
}

log_error() {
    log "  ${RED}✗${NC} $1"
}

log_warning() {
    log "  ${YELLOW}!${NC} $1"
}

# Clean up stale test directories from previous runs
cleanup_stale_tests() {
    local found=0
    for dir in /tmp/line-cook-smoke* /tmp/line-cook-smoke-remote*; do
        if [[ -d "$dir" ]]; then
            log_warning "Removing stale test directory: $dir"
            rm -rf "$dir"
            found=$((found + 1))
        fi
    done
    if [[ $found -gt 0 ]]; then
        log_success "Cleaned up $found stale test director(ies)"
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            MODE="setup"
            shift
            ;;
        --validate)
            MODE="validate"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --validate requires a directory argument" >&2
                exit 1
            fi
            shift 2
            ;;
        --teardown)
            MODE="teardown"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --teardown requires a directory argument" >&2
                exit 1
            fi
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            MODE="dry-run"
            shift
            ;;
        --cleanup)
            MODE="cleanup"
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --skip-cook-check)
            SKIP_COOK=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            head -22 "$0" | tail -18
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Check dependencies
check_dependencies() {
    log_phase "Dependency Check"

    local missing=()

    for dep in git jq bd python3; do
        if command -v "$dep" >/dev/null 2>&1; then
            log_success "Found: $dep"
        else
            log_error "Missing: $dep"
            missing+=("$dep")
        fi
    done

    # Check for validation script
    if [[ -f "$REPO_ROOT/scripts/validate-smoke-test.py" ]]; then
        log_success "Found: validate-smoke-test.py"
    else
        log_error "Missing: scripts/validate-smoke-test.py"
        missing+=("validate-smoke-test.py")
    fi

    # Check for fixtures
    if [[ -d "$FIXTURES_DIR/smoke-beads" ]]; then
        log_success "Found: smoke-beads fixtures"
    else
        log_error "Missing: tests/fixtures/smoke-beads/"
        missing+=("smoke-beads fixtures")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log ""
        log_error "Missing dependencies: ${missing[*]}"
        return 1
    fi

    log ""
    log_success "All dependencies satisfied"
    return 0
}

# Setup isolated test environment
# Outputs: TEST_DIR path to stdout (other output to stderr)
do_setup() {
    log_phase "Setup: Creating Isolated Test Environment"

    # Clean up stale directories from previous runs
    cleanup_stale_tests

    # Create temp directories
    local TEST_DIR
    TEST_DIR="$(mktemp -d -t line-cook-smoke.XXXXXX)"
    local REMOTE_DIR
    REMOTE_DIR="$(mktemp -d -t line-cook-smoke-remote.XXXXXX)"

    # Store remote dir path for teardown
    echo "$REMOTE_DIR" > "$TEST_DIR/.smoke-remote-dir"

    log_step "Created TEST_DIR: $TEST_DIR"
    log_step "Created REMOTE_DIR: $REMOTE_DIR"

    # Initialize bare remote
    git init --bare "$REMOTE_DIR" >/dev/null 2>&1
    log_success "Initialized bare remote"

    # Initialize test repo
    cd "$TEST_DIR"
    git init >/dev/null 2>&1
    git config user.email "smoke-test@line-cook.dev"
    git config user.name "Smoke Test"
    git remote add origin "$REMOTE_DIR"
    log_success "Initialized test repository"

    # Copy sample project
    mkdir -p src tests
    if [[ -d "$FIXTURES_DIR/sample-project" ]]; then
        cp -r "$FIXTURES_DIR/sample-project/"* . 2>/dev/null || true
        log_success "Copied sample project files"
    fi

    # Ensure validation.py has placeholder (reset to fixture state)
    cat > src/validation.py << 'EOF'
#!/usr/bin/env python3
"""Input validation utilities."""

import re


def validate_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    # TODO: Replace with proper regex validation (smoke-001)
    return "@" in email


def validate_password(password: str) -> bool:
    """Validate password strength.

    Args:
        password: Password to validate

    Returns:
        True if password meets requirements
    """
    return len(password) >= 8
EOF
    log_success "Set validation.py to placeholder state"

    # Create .gitignore for clean working tree (T3)
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Smoke test workflow markers (ephemeral, not committed)
.smoke-markers/
EOF
    log_success "Created .gitignore"

    # Create minimal AGENTS.md (T4)
    cat > AGENTS.md << 'EOF'
# Agents

Minimal agents file for smoke test project.

## Overview

This project uses beads for task tracking.

## Commands

- `bd list` - List issues
- `bd ready` - Show ready tasks
- `bd show <id>` - Show issue details
EOF
    log_success "Created AGENTS.md"

    # Create .gitattributes for consistent line endings (T4)
    cat > .gitattributes << 'EOF'
* text=auto
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
EOF
    log_success "Created .gitattributes"

    # Create pyproject.toml for proper imports (T6)
    cat > pyproject.toml << 'EOF'
[project]
name = "smoke-test-project"
version = "0.1.0"
description = "Smoke test project for Line Cook"
requires-python = ">=3.8"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
EOF
    log_success "Created pyproject.toml"

    # Create venv with pytest (T5)
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv >/dev/null 2>&1
        .venv/bin/pip install --quiet pytest >/dev/null 2>&1
        log_success "Created .venv with pytest"
    else
        log_warning "python3 not found, skipping venv creation"
    fi

    # Initial commit (includes .gitignore, AGENTS.md, .gitattributes, pyproject.toml)
    git add -A
    git commit -m "Initial commit" >/dev/null 2>&1
    git push -u origin main >/dev/null 2>&1
    log_success "Created initial commit"

    # Initialize beads with smoke prefix
    bd init --prefix=smoke >/dev/null 2>&1
    log_success "Initialized beads (prefix: smoke)"

    # Create smoke test bead via bd create (not YAML copy - beads uses JSONL database)
    bd create --id=smoke-001 \
        --title="Replace placeholder email validation with regex" \
        --type=task \
        --priority=1 \
        --label=smoke-test \
        --label=validation \
        --description="The validate_email() function in src/validation.py currently uses a placeholder implementation that only checks for @ in the email. Replace with proper regex validation: Use a standard email regex pattern, handle edge cases (empty string, None), and add corresponding tests in tests/test_validation.py. This is a smoke test task for validating the Line Cook workflow." \
        >/dev/null 2>&1
    log_success "Created smoke-001 bead via bd create"

    # Create a simple CLAUDE.md for the test project
    cat > CLAUDE.md << 'EOF'
# Smoke Test Project

A minimal Python project for testing Line Cook workflows.

## Structure
- src/validation.py - Input validation utilities
- tests/ - Test files

## Task
Task smoke-001 requires replacing the placeholder email validation with proper regex.
EOF
    log_success "Created CLAUDE.md"

    # Commit beads setup (bd init modifies .gitattributes and AGENTS.md)
    git add .beads/ CLAUDE.md .gitattributes AGENTS.md
    git commit -m "Add beads configuration with smoke-001" >/dev/null 2>&1
    git push >/dev/null 2>&1
    log_success "Committed beads setup"

    log ""
    log_success "Environment ready!"
    log ""
    log "Next steps for interactive workflow:"
    log "  1. cd $TEST_DIR"
    log "  2. Run /line:prep"
    log "  3. Run /line:cook smoke-001"
    log "  4. Run /line:serve"
    log "  5. Run /line:tidy"
    log "  6. ./tests/smoke-test.sh --validate $TEST_DIR"
    log "  7. ./tests/smoke-test.sh --teardown $TEST_DIR"

    # Output TEST_DIR to stdout (this is the return value)
    echo "$TEST_DIR"
}

# Validate test results
do_validate() {
    local test_dir="$1"
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)

    log_phase "Validate: Checking Artifacts"

    if [[ ! -d "$test_dir" ]]; then
        log_error "Test directory does not exist: $test_dir"
        return 1
    fi

    cd "$test_dir"

    # Ensure results directory exists
    mkdir -p "$RESULTS_DIR"

    local result_file="$RESULTS_DIR/smoke-${PLATFORM}-${timestamp}.json"
    local skip_cook_arg="false"
    if $SKIP_COOK; then
        skip_cook_arg="true"
    fi

    # Run validation script
    if python3 "$REPO_ROOT/scripts/validate-smoke-test.py" \
        --test-dir "$test_dir" \
        --platform "$PLATFORM" \
        --output "$result_file" \
        --skip-cook-check="$skip_cook_arg"; then
        log ""
        log_success "All validations passed"
        log "Results saved to: $result_file"
        return 0
    else
        log ""
        log_error "Some validations failed"
        log "Results saved to: $result_file"
        return 1
    fi
}

# Teardown test environment
do_teardown() {
    local test_dir="$1"

    log_phase "Teardown: Cleaning Up"

    if [[ ! -d "$test_dir" ]]; then
        log_warning "Test directory does not exist: $test_dir"
        return 0
    fi

    # Find and remove remote dir if stored
    if [[ -f "$test_dir/.smoke-remote-dir" ]]; then
        local remote_dir
        remote_dir=$(cat "$test_dir/.smoke-remote-dir")
        if [[ -d "$remote_dir" ]]; then
            rm -rf "$remote_dir"
            log_success "Removed remote directory: $remote_dir"
        fi
    fi

    # Remove test directory
    rm -rf "$test_dir"
    log_success "Removed test directory: $test_dir"

    log ""
    log_success "Cleanup complete"
}

# Main execution
main() {
    case "$MODE" in
        setup)
            if ! check_dependencies; then
                exit 1
            fi
            do_setup
            ;;
        validate)
            do_validate "$TARGET_DIR"
            ;;
        teardown)
            do_teardown "$TARGET_DIR"
            ;;
        dry-run)
            if check_dependencies; then
                log ""
                log_success "Dry run complete. Dependencies satisfied."
                exit 0
            else
                exit 1
            fi
            ;;
        cleanup)
            log_phase "Cleanup: Removing Stale Test Directories"
            cleanup_stale_tests
            log ""
            log_success "Cleanup complete"
            ;;
        "")
            echo "Error: No mode specified" >&2
            echo "Use --setup, --validate <dir>, --teardown <dir>, --cleanup, or --dry-run" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
        *)
            echo "Error: Unknown mode: $MODE" >&2
            exit 1
            ;;
    esac
}

main
