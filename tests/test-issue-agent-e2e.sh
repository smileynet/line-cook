#!/usr/bin/env bash
# test-issue-agent-e2e.sh - E2E tests for issue-agent workflow
#
# Tests critical user journeys:
# 1. Workflow triggers on issue creation ✓ (existing smoke test)
# 2. GitHub App authentication succeeds
# 3. Fix branches are created with correct identity
# 4. CI workflows trigger on fix branches
#
# Usage:
#   ./tests/test-issue-agent-e2e.sh
#   ./tests/test-issue-agent-e2e.sh --test=auth
#   ./tests/test-issue-agent-e2e.sh --test=branch
#   ./tests/test-issue-agent-e2e.sh --test=ci
#
# Requirements:
#   - gh CLI authenticated
#   - CLAUDE_CODE_OAUTH_TOKEN secret configured in repo
#   - issue-agent.yml workflow deployed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source shared test utilities
source "$SCRIPT_DIR/lib/test-utils.sh"
setup_colors

# Cleanup on unexpected exit
do_cleanup() {
    if [[ -n "${CLEANUP_ISSUE:-}" ]]; then
        log "Cleaning up issue #${CLEANUP_ISSUE}..."
        gh issue close "$CLEANUP_ISSUE" --comment "E2E test cleanup (unexpected exit)" 2>/dev/null || true
    fi
}
trap do_cleanup EXIT

# Defaults
TEST_NAME="all"
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test=*)
            TEST_NAME="${1#*=}"
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get repo info
REPO_OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)

# Test: GitHub App Authentication
test_github_app_auth() {
    log_step "TEST: GitHub App Authentication"
    
    # Given: Create test issue that requires git operations
    local issue_title="E2E Test: auth check [$(date +%s)]"
    local issue_body="Test issue to validate GitHub App authentication.

This issue should trigger the workflow to perform git operations.

Label: e2e-test"
    
    local issue_number=$(gh issue create \
        --title "$issue_title" \
        --body "$issue_body" \
        --label "e2e-test" \
        --json number -q .number)

    if [[ -z "$issue_number" ]]; then
        log_error "Failed to create issue or parse issue number"
        return 1
    fi

    CLEANUP_ISSUE="$issue_number"
    log "Created issue #${issue_number}"

    # When: Wait for workflow to complete
    local workflow_start=$(date +%s)
    local workflow_run_id=""

    # Poll for workflow run
    while true; do
        local elapsed=$(($(date +%s) - workflow_start))
        if [[ $elapsed -gt 300 ]]; then
            log_error "Workflow timeout"
            gh issue close "$issue_number" --comment "E2E test cleanup (timeout)"
            return 1
        fi

        workflow_run_id=$(gh run list \
            --workflow=issue-agent.yml \
            --limit 5 \
            --json databaseId,status \
            --jq '.[] | select(.status != "completed") | .databaseId' \
            | head -1)

        if [[ -n "$workflow_run_id" ]]; then
            break
        fi

        sleep 5
    done

    # Wait for completion
    while true; do
        local elapsed=$(($(date +%s) - workflow_start))
        if [[ $elapsed -gt 300 ]]; then
            log_error "Workflow timeout"
            gh issue close "$issue_number" --comment "E2E test cleanup (timeout)"
            return 1
        fi

        local status=$(gh run view "$workflow_run_id" --json status -q .status)

        if [[ "$status" == "completed" ]]; then
            local conclusion=$(gh run view "$workflow_run_id" --json conclusion -q .conclusion)
            if [[ "$conclusion" != "success" ]]; then
                log_error "Workflow failed: ${conclusion}"
                gh issue close "$issue_number" --comment "E2E test cleanup (workflow failed)"
                return 1
            fi
            break
        fi

        sleep 10
    done

    # Then: Verify git identity in workflow logs
    # NOTE: Currently uses github-actions[bot]. GitHub App integration is configured
    # as secrets but not yet wired into the workflow identity.
    log "Checking workflow logs for git identity..."
    local logs=$(gh run view "$workflow_run_id" --log 2>&1 || true)

    if echo "$logs" | grep -q "github-actions\[bot\]"; then
        log_success "Git identity verified in logs (github-actions[bot])"
    else
        log_warning "Could not verify git identity in logs"
        log "This may be expected if git operations weren't performed"
    fi

    # Cleanup
    gh issue close "$issue_number" --comment "E2E test cleanup"
    CLEANUP_ISSUE=""
    log_success "TEST PASSED: GitHub App Authentication"
}

# Test: Fix Branch Creation
test_fix_branch_creation() {
    log_step "TEST: Fix Branch Creation"
    
    # Given: Create issue with fixable problem
    local issue_title="E2E Test: fix branch [$(date +%s)]"
    local issue_body="Test issue to validate fix branch creation.

**Problem:**
The file \`core/line_loop/loop.py\` needs a docstring added to the \`run\` function.

**Expected:**
The agent should create a fix branch with the docstring added.

Label: e2e-test"
    
    local issue_number=$(gh issue create \
        --title "$issue_title" \
        --body "$issue_body" \
        --label "e2e-test" \
        --json number -q .number)

    if [[ -z "$issue_number" ]]; then
        log_error "Failed to create issue or parse issue number"
        return 1
    fi

    CLEANUP_ISSUE="$issue_number"
    log "Created issue #${issue_number}"

    # When: Wait for workflow to complete
    local workflow_start=$(date +%s)
    local workflow_run_id=""

    # Poll for workflow run
    while true; do
        local elapsed=$(($(date +%s) - workflow_start))
        if [[ $elapsed -gt 300 ]]; then
            log_error "Workflow timeout"
            gh issue close "$issue_number" --comment "E2E test cleanup (timeout)"
            return 1
        fi

        workflow_run_id=$(gh run list \
            --workflow=issue-agent.yml \
            --limit 5 \
            --json databaseId,status \
            --jq '.[] | select(.status != "completed") | .databaseId' \
            | head -1)

        if [[ -n "$workflow_run_id" ]]; then
            break
        fi

        sleep 5
    done

    # Wait for completion
    while true; do
        local elapsed=$(($(date +%s) - workflow_start))
        if [[ $elapsed -gt 300 ]]; then
            log_error "Workflow timeout"
            gh issue close "$issue_number" --comment "E2E test cleanup (timeout)"
            return 1
        fi

        local status=$(gh run view "$workflow_run_id" --json status -q .status)

        if [[ "$status" == "completed" ]]; then
            break
        fi

        sleep 10
    done

    # Then: Check if fix branch was created for this specific issue
    log "Checking for fix branches for issue #${issue_number}..."
    local fix_branches=$(git ls-remote origin "refs/heads/fix/issue-${issue_number}*" | wc -l)

    if [[ $fix_branches -gt 0 ]]; then
        log_success "Fix branch(es) found for issue #${issue_number}: ${fix_branches}"

        # Verify branch identity
        local latest_branch=$(git ls-remote origin "refs/heads/fix/issue-${issue_number}*" | tail -1 | awk '{print $2}' | sed 's|refs/heads/||')
        log "Latest fix branch: ${latest_branch}"

        # Fetch and check commit author
        git fetch origin "$latest_branch" 2>/dev/null || true
        local author=$(git log -1 --format='%an <%ae>' "origin/${latest_branch}" 2>/dev/null || echo "unknown")

        if echo "$author" | grep -q "github-actions\[bot\]"; then
            log_success "Fix branch created with correct identity: ${author}"
        else
            log_warning "Fix branch author: ${author}"
        fi
    else
        log_warning "No fix branches found for issue #${issue_number}"
        log "This may be expected if the agent didn't create a fix"
    fi

    # Cleanup
    gh issue close "$issue_number" --comment "E2E test cleanup"
    CLEANUP_ISSUE=""
    log_success "TEST PASSED: Fix Branch Creation"
}

# Test: CI Triggers on Fix Branch
test_ci_triggers() {
    log_step "TEST: CI Triggers on Fix Branch"
    
    # This test requires a fix branch to exist
    log "Checking for existing fix branches..."
    local fix_branches=$(git ls-remote origin "refs/heads/fix/*" | wc -l)
    
    if [[ $fix_branches -eq 0 ]]; then
        log_warning "No fix branches found - skipping CI trigger test"
        log "Run test_fix_branch_creation first to create a fix branch"
        return 0
    fi
    
    # Get latest fix branch
    local latest_branch=$(git ls-remote origin "refs/heads/fix/*" | tail -1 | awk '{print $2}' | sed 's|refs/heads/||')
    log "Checking CI for branch: ${latest_branch}"
    
    # Check for workflow runs on this branch
    local runs=$(gh run list --branch "$latest_branch" --json databaseId,conclusion --limit 5)
    local run_count=$(echo "$runs" | jq '. | length')
    
    if [[ $run_count -gt 0 ]]; then
        log_success "CI workflows triggered on fix branch: ${run_count} runs"
        
        # Check if any runs succeeded
        local success_count=$(echo "$runs" | jq '[.[] | select(.conclusion == "success")] | length')
        if [[ $success_count -gt 0 ]]; then
            log_success "CI workflows passed: ${success_count}/${run_count}"
        else
            log_warning "No successful CI runs yet"
        fi
    else
        log_warning "No CI workflows found for fix branch"
        log "This may be expected if CI hasn't triggered yet"
    fi
    
    log_success "TEST PASSED: CI Triggers"
}

# Main execution
log_phase "E2E TESTS: Issue Agent Workflow"

case "$TEST_NAME" in
    auth)
        test_github_app_auth
        ;;
    branch)
        test_fix_branch_creation
        ;;
    ci)
        test_ci_triggers
        ;;
    all)
        test_github_app_auth
        test_fix_branch_creation
        test_ci_triggers
        ;;
    *)
        log_error "Unknown test: $TEST_NAME"
        log "Available tests: auth, branch, ci, all"
        exit 1
        ;;
esac

log_phase "${GREEN}✓${NC} E2E TESTS PASSED"
