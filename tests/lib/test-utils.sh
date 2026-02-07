#!/usr/bin/env bash
# test-utils.sh - Common utilities for Line Cook tests
#
# Functions:
# - check_output_contains - Verify output contains expected patterns
# - run_provider_test - Run a command for a specific provider
# - print_result - Print pass/fail result
# - setup_colors - Initialize color codes
#
# Git State Assertion Helpers:
# - verify_branch_exists - Check if a git branch exists locally
# - get_current_branch - Get current git branch name
# - verify_current_branch - Check if we're on a specific branch
# - verify_merge_commit_exists - Check if a merge commit exists in recent history
# - verify_no_ff_merge - Check if a --no-ff merge was used
# - verify_branch_deleted - Check if a branch was deleted
# - verify_wip_commit_exists - Check if there's a WIP commit on a branch
# - get_bead_status - Check bead status via bd show

set -euo pipefail

# Initialize colors (call at start of test)
setup_colors() {
    if [[ -t 1 ]]; then
        RED='\033[0;31m'
        GREEN='\033[0;32m'
        YELLOW='\033[1;33m'
        BLUE='\033[0;34m'
        NC='\033[0m' # No Color
    else
        RED=''
        GREEN=''
        YELLOW=''
        BLUE=''
        NC=''
    fi
    export RED GREEN YELLOW BLUE NC
}

# Print pass/fail result
# Usage: print_result "Test name" 0|1
print_result() {
    local name="$1"
    local status="$2"

    if [[ "$status" -eq 0 ]]; then
        echo -e "  ${GREEN}PASS${NC} $name"
        return 0
    else
        echo -e "  ${RED}FAIL${NC} $name"
        return 1
    fi
}

# Check if output contains expected patterns
# Usage: check_output_contains "$output" "pattern1" "pattern2" ...
# Returns 0 if ALL patterns found, 1 otherwise
check_output_contains() {
    local output="$1"
    shift
    local patterns=("$@")

    for pattern in "${patterns[@]}"; do
        if ! echo "$output" | grep -qiE "$pattern"; then
            echo "  Missing pattern: $pattern" >&2
            return 1
        fi
    done
    return 0
}

# Run command for specific provider
# Usage: run_provider_test "provider" "command" [timeout]
# Returns: output in stdout, exit code
run_provider_test() {
    local provider="$1"
    local command="$2"
    local timeout="${3:-120}"

    local output=""
    local exit_code=0

    case "$provider" in
        claude)
            # Claude Code headless mode
            output=$(timeout "$timeout" claude -p "$command" \
                --allowedTools "Bash(read-only:*),Read,Glob,Grep,TodoWrite" \
                --output-format text 2>&1) || exit_code=$?
            ;;
        opencode)
            # OpenCode headless mode
            output=$(timeout "$timeout" opencode run --command "$command" 2>&1) || exit_code=$?
            ;;
        kiro)
            # Kiro CLI (natural language)
            output=$(timeout "$timeout" kiro-cli chat --agent line-cook \
                --no-interactive "$command" 2>&1) || exit_code=$?
            ;;
        *)
            echo "Unknown provider: $provider" >&2
            return 1
            ;;
    esac

    echo "$output"
    return $exit_code
}

# Get provider display name
get_provider_display_name() {
    local provider="$1"
    case "$provider" in
        claude) echo "Claude Code" ;;
        opencode) echo "OpenCode" ;;
        kiro) echo "Kiro" ;;
        *) echo "$provider" ;;
    esac
}

# Get command syntax for provider
get_provider_command() {
    local provider="$1"
    local command="$2"

    case "$provider" in
        claude) echo "/line:$command" ;;
        opencode) echo "/line-$command" ;;
        kiro) echo "$command" ;;
        *) echo "$command" ;;
    esac
}

# Check if provider CLI is available
check_provider_available() {
    local provider="$1"
    case "$provider" in
        claude) command -v claude >/dev/null 2>&1 ;;
        opencode) command -v opencode >/dev/null 2>&1 ;;
        kiro) command -v kiro-cli >/dev/null 2>&1 ;;
        *) return 1 ;;
    esac
}

# ============================================================
# Git State Assertion Helpers
# ============================================================

# Check if a git branch exists locally
# Usage: verify_branch_exists <branch_name>
verify_branch_exists() {
    local branch="$1"
    git show-ref --verify "refs/heads/$branch" >/dev/null 2>&1
}

# Get current git branch name
# Usage: get_current_branch
get_current_branch() {
    git branch --show-current
}

# Check if we're on a specific branch
# Usage: verify_current_branch <branch_name>
verify_current_branch() {
    local expected="$1"
    local current
    current=$(get_current_branch)
    [[ "$current" == "$expected" ]]
}

# Check if a merge commit exists in recent history
# Usage: verify_merge_commit_exists <pattern>
verify_merge_commit_exists() {
    local pattern="$1"
    git log --oneline --merges -10 | grep -q "$pattern"
}

# Check if a --no-ff merge was used (commit has 2 parents)
# Usage: verify_no_ff_merge <commit_pattern>
verify_no_ff_merge() {
    local pattern="$1"
    local merge_commit
    merge_commit=$(git log --oneline --merges -10 | grep "$pattern" | head -1 | cut -d' ' -f1)
    if [[ -z "$merge_commit" ]]; then
        return 1
    fi
    # Check if commit has a second parent (indicates --no-ff merge)
    git rev-parse --verify "${merge_commit}^2" >/dev/null 2>&1
}

# Check if a branch was deleted (no longer exists)
# Usage: verify_branch_deleted <branch_name>
verify_branch_deleted() {
    local branch="$1"
    ! git show-ref --verify "refs/heads/$branch" >/dev/null 2>&1
}

# Check if there's a WIP commit on a branch
# Usage: verify_wip_commit_exists <branch_name>
verify_wip_commit_exists() {
    local branch="$1"
    git log "$branch" --oneline -10 | grep -q "WIP:"
}

# Check bead status via bd show
# Usage: get_bead_status <bead_id>
get_bead_status() {
    local bead_id="$1"
    bd show "$bead_id" --json 2>/dev/null | jq -r '.status // empty'
}
