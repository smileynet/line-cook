#!/usr/bin/env bash
# smoke-test-epic.sh - Epic branching blackbox tests for Line Cook workflows
#
# Modular smoke test for epic branch management with separate setup, validate,
# and teardown phases. Tests the automatic branch creation, switching, and
# merge behavior when working with epic hierarchies.
#
# Usage:
#   ./tests/smoke-test-epic.sh --setup              # Create env with epic hierarchy
#   ./tests/smoke-test-epic.sh --validate-s1 <dir>  # Validate S1: Branch creation
#   ./tests/smoke-test-epic.sh --validate-s2 <dir>  # Validate S2: Branch reuse
#   ./tests/smoke-test-epic.sh --validate-s3 <dir>  # Validate S3: WIP auto-commit
#   ./tests/smoke-test-epic.sh --validate-s4 <dir>  # Validate S4: Epic merge
#   ./tests/smoke-test-epic.sh --teardown <dir>     # Clean up test directory
#   ./tests/smoke-test-epic.sh --cleanup            # Remove stale test directories
#   ./tests/smoke-test-epic.sh --dry-run            # Check dependencies only
#
# Test Scenarios:
#   S1: Epic Branch Creation - First task creates epic branch
#   S2: Epic Branch Reuse - Subsequent tasks reuse existing branch
#   S3: WIP Auto-Commit - Uncommitted changes committed when switching epics
#   S4: Epic Merge on Completion - Epic branch merged to main with --no-ff
#
# Interactive workflow (Claude runs this):
#   1. TEST_DIR=$(./tests/smoke-test-epic.sh --setup)
#   2. cd $TEST_DIR && run /line:run --max-iterations=1
#   3. ./tests/smoke-test-epic.sh --validate-s1 $TEST_DIR
#   4. Continue work, validate other scenarios as appropriate
#   5. ./tests/smoke-test-epic.sh --teardown $TEST_DIR

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
RESULTS_DIR="$SCRIPT_DIR/results"

# Source shared test utilities (includes git assertion helpers)
source "$SCRIPT_DIR/lib/test-utils.sh"

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
VERBOSE=false

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

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            MODE="setup"
            shift
            ;;
        --validate-s1)
            MODE="validate-s1"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --validate-s1 requires a directory argument" >&2
                exit 1
            fi
            shift 2
            ;;
        --validate-s2)
            MODE="validate-s2"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --validate-s2 requires a directory argument" >&2
                exit 1
            fi
            shift 2
            ;;
        --validate-s3)
            MODE="validate-s3"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --validate-s3 requires a directory argument" >&2
                exit 1
            fi
            shift 2
            ;;
        --validate-s4)
            MODE="validate-s4"
            TARGET_DIR="${2:-}"
            if [[ -z "$TARGET_DIR" ]]; then
                echo "Error: --validate-s4 requires a directory argument" >&2
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
            MODE="dry-run"
            shift
            ;;
        --cleanup)
            MODE="cleanup"
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            head -26 "$0" | tail -22
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# ============================================================
# Clean up stale test directories from previous runs
# ============================================================
cleanup_stale_tests() {
    local found=0
    for dir in /tmp/line-cook-epic-smoke* /tmp/line-cook-epic-remote*; do
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

# ============================================================
# Check dependencies
# ============================================================
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

    # Check for epic hierarchy fixtures
    if [[ -f "$FIXTURES_DIR/epic-hierarchy/issues.jsonl" ]]; then
        log_success "Found: epic-hierarchy fixtures"
    else
        log_error "Missing: tests/fixtures/epic-hierarchy/issues.jsonl"
        missing+=("epic-hierarchy fixtures")
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

# ============================================================
# Setup isolated test environment with epic hierarchy
# ============================================================
do_setup() {
    log_phase "Setup: Creating Isolated Test Environment with Epic Hierarchy"

    # Clean up stale directories from previous runs
    cleanup_stale_tests

    # Create temp directories
    local TEST_DIR
    TEST_DIR="$(mktemp -d -t line-cook-epic-smoke.XXXXXX)"
    local REMOTE_DIR
    REMOTE_DIR="$(mktemp -d -t line-cook-epic-remote.XXXXXX)"

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
    # TODO: Replace with proper regex validation (smoke-task-001)
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

    # Create .gitignore
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
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Smoke test workflow markers
.smoke-markers/

# Line Cook
.line-cook/
EOF
    log_success "Created .gitignore"

    # Create minimal AGENTS.md
    cat > AGENTS.md << 'EOF'
# Agents

Minimal agents file for epic smoke test project.

## Overview

This project uses beads for task tracking with epic hierarchy.

## Commands

- `bd list` - List issues
- `bd ready` - Show ready tasks
- `bd show <id>` - Show issue details
EOF
    log_success "Created AGENTS.md"

    # Create .gitattributes
    cat > .gitattributes << 'EOF'
* text=auto
*.py text eol=lf
*.sh text eol=lf
*.md text eol=lf
EOF
    log_success "Created .gitattributes"

    # Create pyproject.toml
    cat > pyproject.toml << 'EOF'
[project]
name = "smoke-test-epic-project"
version = "0.1.0"
description = "Epic smoke test project for Line Cook"
requires-python = ">=3.8"

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
EOF
    log_success "Created pyproject.toml"

    # Create venv with pytest
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv >/dev/null 2>&1
        .venv/bin/pip install --quiet pytest >/dev/null 2>&1
        log_success "Created .venv with pytest"
    else
        log_warning "python3 not found, skipping venv creation"
    fi

    # Initial commit
    git add -A
    git commit -m "Initial commit" >/dev/null 2>&1
    git push -u origin main >/dev/null 2>&1
    log_success "Created initial commit"

    # Initialize beads with smoke prefix
    bd init --prefix=smoke >/dev/null 2>&1
    log_success "Initialized beads (prefix: smoke)"

    # Import epic hierarchy from fixture
    bd import -i "$FIXTURES_DIR/epic-hierarchy/issues.jsonl" >/dev/null 2>&1
    log_success "Imported epic hierarchy (epic→feature→tasks)"

    # Create a simple CLAUDE.md for the test project
    cat > CLAUDE.md << 'EOF'
# Epic Smoke Test Project

A minimal Python project for testing Line Cook epic branching workflows.

## Structure
- src/validation.py - Input validation utilities
- tests/ - Test files

## Epic Hierarchy
- smoke-epic-001: Email Validation Epic
  - smoke-feat-001: Add Regex Validation
    - smoke-task-001: Implement email regex
    - smoke-task-002: Add edge case tests

## Task
Tasks under this epic should be worked on the epic/smoke-epic-001 branch.
EOF
    log_success "Created CLAUDE.md"

    # Commit beads setup
    git add .beads/ CLAUDE.md .gitattributes AGENTS.md
    git commit -m "Add beads configuration with epic hierarchy" >/dev/null 2>&1
    git push >/dev/null 2>&1
    log_success "Committed beads setup"

    log ""
    log_success "Environment ready!"
    log ""
    log "Epic hierarchy:"
    log "  smoke-epic-001: Email Validation Epic"
    log "    └─ smoke-feat-001: Add Regex Validation"
    log "        ├─ smoke-task-001: Implement email regex"
    log "        └─ smoke-task-002: Add edge case tests"
    log ""
    log "Next steps for S1 (Branch Creation):"
    log "  1. cd $TEST_DIR"
    log "  2. Run: /line:run --max-iterations=1"
    log "  3. Verify: ./tests/smoke-test-epic.sh --validate-s1 $TEST_DIR"
    log ""
    log "Other scenarios:"
    log "  S2 (Branch Reuse):    Work another task, verify still on epic/smoke-epic-001"
    log "  S3 (WIP Auto-Commit): Create uncommitted changes, switch epics"
    log "  S4 (Epic Merge):      Complete all tasks, verify merge to main"

    # Output TEST_DIR to stdout (this is the return value)
    echo "$TEST_DIR"
}

# ============================================================
# Scenario Validators
# ============================================================

# S1: Epic Branch Creation
# After first task in epic, verify epic branch was created
do_validate_s1() {
    local test_dir="$1"
    local errors=0

    log_phase "Validate S1: Epic Branch Creation"

    if [[ ! -d "$test_dir" ]]; then
        log_error "Test directory does not exist: $test_dir"
        return 1
    fi

    cd "$test_dir"

    # Verbose: show git state
    if $VERBOSE; then
        log "  [verbose] Git branches:"
        git branch -a 2>/dev/null | while read -r line; do log "    $line"; done
        log "  [verbose] Recent commits:"
        git log --oneline -5 2>/dev/null | while read -r line; do log "    $line"; done
    fi

    # Check 1: Epic branch exists
    log_step "Checking epic branch exists..."
    if verify_branch_exists "epic/smoke-epic-001"; then
        log_success "Branch epic/smoke-epic-001 exists"
    else
        log_error "Branch epic/smoke-epic-001 does not exist"
        errors=$((errors + 1))
    fi

    # Check 2: Currently on epic branch
    log_step "Checking current branch..."
    local current_branch
    current_branch=$(get_current_branch)
    if [[ "$current_branch" == "epic/smoke-epic-001" ]]; then
        log_success "Currently on branch: $current_branch"
    else
        log_error "Expected to be on epic/smoke-epic-001, but on: $current_branch"
        errors=$((errors + 1))
    fi

    # Check 3: Task status changed (in_progress or closed)
    log_step "Checking task status..."
    local task_status
    task_status=$(get_bead_status "smoke-task-001")
    if [[ "$task_status" == "in_progress" || "$task_status" == "closed" ]]; then
        log_success "Task smoke-task-001 status: $task_status"
    else
        log_error "Task smoke-task-001 expected in_progress or closed, got: $task_status"
        errors=$((errors + 1))
    fi

    # Summary
    log ""
    if [[ $errors -eq 0 ]]; then
        log_success "S1: All validations passed"
        return 0
    else
        log_error "S1: $errors validation(s) failed"
        return 1
    fi
}

# S2: Epic Branch Reuse
# After subsequent task in same epic, verify still on same branch (not recreated)
do_validate_s2() {
    local test_dir="$1"
    local errors=0

    log_phase "Validate S2: Epic Branch Reuse"

    if [[ ! -d "$test_dir" ]]; then
        log_error "Test directory does not exist: $test_dir"
        return 1
    fi

    cd "$test_dir"

    # Verbose: show git state
    if $VERBOSE; then
        log "  [verbose] Git branches:"
        git branch -a 2>/dev/null | while read -r line; do log "    $line"; done
        log "  [verbose] Recent commits on epic branch:"
        git log "epic/smoke-epic-001" --oneline -5 2>/dev/null | while read -r line; do log "    $line"; done
    fi

    # Check 1: Still on epic branch
    log_step "Checking current branch..."
    local current_branch
    current_branch=$(get_current_branch)
    if [[ "$current_branch" == "epic/smoke-epic-001" ]]; then
        log_success "Still on branch: $current_branch"
    else
        log_error "Expected to be on epic/smoke-epic-001, but on: $current_branch"
        errors=$((errors + 1))
    fi

    # Check 2: Multiple commits on epic branch (work was added)
    log_step "Checking for work on epic branch..."
    local commit_count
    commit_count=$(git log "epic/smoke-epic-001" --oneline | wc -l)
    if [[ $commit_count -gt 2 ]]; then
        log_success "Epic branch has $commit_count commits (work added)"
    else
        log_warning "Epic branch has only $commit_count commits (expected more work)"
    fi

    # Check 3: At least one task is in_progress or closed
    log_step "Checking task progress..."
    local task1_status
    local task2_status
    task1_status=$(get_bead_status "smoke-task-001")
    task2_status=$(get_bead_status "smoke-task-002")
    if [[ "$task1_status" == "closed" || "$task2_status" == "in_progress" || "$task2_status" == "closed" ]]; then
        log_success "Tasks progressing: task-001=$task1_status, task-002=$task2_status"
    else
        log_warning "Expected more task progress: task-001=$task1_status, task-002=$task2_status"
    fi

    # Summary
    log ""
    if [[ $errors -eq 0 ]]; then
        log_success "S2: All validations passed"
        return 0
    else
        log_error "S2: $errors validation(s) failed"
        return 1
    fi
}

# S3: WIP Auto-Commit on Epic Switch
# When switching between epics, uncommitted work should be auto-committed
do_validate_s3() {
    local test_dir="$1"
    local errors=0

    log_phase "Validate S3: WIP Auto-Commit on Epic Switch"

    if [[ ! -d "$test_dir" ]]; then
        log_error "Test directory does not exist: $test_dir"
        return 1
    fi

    cd "$test_dir"

    # Check 1: WIP commit exists on original epic branch
    log_step "Checking for WIP commit..."
    if verify_wip_commit_exists "epic/smoke-epic-001"; then
        log_success "WIP commit found on epic/smoke-epic-001"
    else
        log_error "No WIP commit found on epic/smoke-epic-001"
        errors=$((errors + 1))
    fi

    # Check 2: Working tree is clean (no uncommitted changes lost)
    log_step "Checking working tree..."
    local status
    status=$(git status --porcelain)
    if [[ -z "$status" ]]; then
        log_success "Working tree is clean"
    else
        log_warning "Working tree has uncommitted changes"
        if $VERBOSE; then
            log "  Status: $status"
        fi
    fi

    # Summary
    log ""
    if [[ $errors -eq 0 ]]; then
        log_success "S3: All validations passed"
        return 0
    else
        log_error "S3: $errors validation(s) failed"
        return 1
    fi
}

# S4: Epic Merge on Completion
# When epic completes, branch should be merged to main with --no-ff
do_validate_s4() {
    local test_dir="$1"
    local errors=0

    log_phase "Validate S4: Epic Merge on Completion"

    if [[ ! -d "$test_dir" ]]; then
        log_error "Test directory does not exist: $test_dir"
        return 1
    fi

    cd "$test_dir"

    # Verbose: show git state
    if $VERBOSE; then
        log "  [verbose] Git branches:"
        git branch -a 2>/dev/null | while read -r line; do log "    $line"; done
        log "  [verbose] Recent commits (showing merges):"
        git log --oneline --graph -10 2>/dev/null | while read -r line; do log "    $line"; done
    fi

    # Check 1: Currently on main branch
    log_step "Checking current branch..."
    local current_branch
    current_branch=$(get_current_branch)
    if [[ "$current_branch" == "main" ]]; then
        log_success "Currently on main branch"
    else
        log_error "Expected to be on main, but on: $current_branch"
        errors=$((errors + 1))
    fi

    # Check 2: Merge commit exists
    log_step "Checking for merge commit..."
    if verify_merge_commit_exists "Merge epic smoke-epic-001"; then
        log_success "Merge commit found for epic smoke-epic-001"
    else
        log_error "No merge commit found for epic smoke-epic-001"
        errors=$((errors + 1))
    fi

    # Check 3: Merge was --no-ff (visible in graph)
    log_step "Checking --no-ff merge..."
    if verify_no_ff_merge "Merge epic smoke-epic-001"; then
        log_success "Merge was --no-ff (has two parents)"
    else
        log_warning "Could not verify --no-ff merge"
    fi

    # Check 4: Epic branch deleted
    log_step "Checking epic branch cleanup..."
    if verify_branch_deleted "epic/smoke-epic-001"; then
        log_success "Epic branch deleted locally"
    else
        log_error "Epic branch still exists locally"
        errors=$((errors + 1))
    fi

    # Check 5: Epic status is closed
    log_step "Checking epic status..."
    local epic_status
    epic_status=$(get_bead_status "smoke-epic-001")
    if [[ "$epic_status" == "closed" ]]; then
        log_success "Epic smoke-epic-001 is closed"
    else
        log_error "Epic smoke-epic-001 expected closed, got: $epic_status"
        errors=$((errors + 1))
    fi

    # Check 6: All child tasks are closed
    log_step "Checking all tasks closed..."
    local task1_status
    local task2_status
    task1_status=$(get_bead_status "smoke-task-001")
    task2_status=$(get_bead_status "smoke-task-002")
    if [[ "$task1_status" == "closed" && "$task2_status" == "closed" ]]; then
        log_success "All tasks closed: task-001=$task1_status, task-002=$task2_status"
    else
        log_error "Not all tasks closed: task-001=$task1_status, task-002=$task2_status"
        errors=$((errors + 1))
    fi

    # Summary
    log ""
    if [[ $errors -eq 0 ]]; then
        log_success "S4: All validations passed"
        return 0
    else
        log_error "S4: $errors validation(s) failed"
        return 1
    fi
}

# ============================================================
# Teardown test environment
# ============================================================
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

# ============================================================
# Main execution
# ============================================================
main() {
    case "$MODE" in
        setup)
            if ! check_dependencies; then
                exit 1
            fi
            do_setup
            ;;
        validate-s1)
            do_validate_s1 "$TARGET_DIR"
            ;;
        validate-s2)
            do_validate_s2 "$TARGET_DIR"
            ;;
        validate-s3)
            do_validate_s3 "$TARGET_DIR"
            ;;
        validate-s4)
            do_validate_s4 "$TARGET_DIR"
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
            echo "Use --setup, --validate-s1 <dir>, --teardown <dir>, --cleanup, or --dry-run" >&2
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
