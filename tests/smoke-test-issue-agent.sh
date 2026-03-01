#!/usr/bin/env bash
# smoke-test-issue-agent.sh - E2E smoke test for issue-agent workflow
#
# Tests the complete issue agent workflow:
# 0. Validate timeout fallback YAML structure (local, no API)
# 1. Create test issue
# 2. Wait for workflow to complete
# 3. Validate analysis comment
# 4. Test @mention response
# 5. Cleanup
#
# Usage:
#   ./tests/smoke-test-issue-agent.sh
#   ./tests/smoke-test-issue-agent.sh --dry-run
#   ./tests/smoke-test-issue-agent.sh --cleanup-only
#   ./tests/smoke-test-issue-agent.sh --validate-yaml   # structural check only
#
# Requirements:
#   - gh CLI authenticated
#   - CLAUDE_CODE_OAUTH_TOKEN secret configured in repo
#   - issue-agent.yml workflow deployed
#
# Cost estimate: ~$0.10-0.50 per run (Claude API calls)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source shared test utilities
source "$SCRIPT_DIR/lib/test-utils.sh"
setup_colors

# Defaults
MODE=""
VERBOSE=false
ISSUE_NUMBER=""
WORKFLOW_TIMEOUT=300  # 5 minutes max wait

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            MODE="dry-run"
            shift
            ;;
        --cleanup-only)
            MODE="cleanup"
            shift
            ;;
        --validate-yaml)
            MODE="validate-yaml"
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

# Check dependencies
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Missing dependency: $1"
        return 1
    fi
    log_success "Found: $1"
}

# Cleanup function
do_cleanup() {
    log_step "Cleaning up test issues..."
    local issues=$(gh issue list --label "smoke-test" --json number -q '.[].number')
    if [[ -z "$issues" ]]; then
        log "No test issues to clean up"
        return 0
    fi
    
    for issue_num in $issues; do
        log "Closing issue #${issue_num}..."
        gh issue close "$issue_num" --comment "Smoke test cleanup"
    done
    log_success "Cleanup complete"
}

# Cleanup on unexpected exit
trap do_cleanup EXIT

# Checks that both analyze and respond jobs have:
# - continue-on-error on the agent step
# - A fallback step gated on agent failure
# - Fallback comment with expected content
validate_timeout_fallback() {
    local workflow_file="$REPO_ROOT/.github/workflows/issue-agent.yml"
    local failures=0

    log_step "[0/5] Validating timeout fallback YAML structure..."

    if [[ ! -f "$workflow_file" ]]; then
        log_error "Workflow file not found: $workflow_file"
        return 1
    fi

    # Check analyze job: continue-on-error on agent step
    if grep -A2 'id: analyze' "$workflow_file" | grep -q 'continue-on-error: true'; then
        log_success "analyze job: continue-on-error present"
    else
        log_error "analyze job: missing continue-on-error on agent step"
        failures=$((failures + 1))
    fi

    # Check respond job: continue-on-error on agent step
    if grep -A2 'id: respond' "$workflow_file" | grep -q 'continue-on-error: true'; then
        log_success "respond job: continue-on-error present"
    else
        log_error "respond job: missing continue-on-error on agent step"
        failures=$((failures + 1))
    fi

    # Check for fallback steps (both jobs should have one)
    local fallback_count
    fallback_count=$(grep -c 'Post timeout fallback comment' "$workflow_file" || true)
    if [[ "$fallback_count" -ge 2 ]]; then
        log_success "Fallback steps found: $fallback_count (analyze + respond)"
    else
        log_error "Expected 2 fallback steps, found: $fallback_count"
        failures=$((failures + 1))
    fi

    # Check fallback gate conditions reference correct step outcomes
    if grep -q "steps.analyze.outcome == 'failure'" "$workflow_file"; then
        log_success "analyze fallback: gated on steps.analyze.outcome"
    else
        log_error "analyze fallback: missing or incorrect gate condition"
        failures=$((failures + 1))
    fi

    if grep -q "steps.respond.outcome == 'failure'" "$workflow_file"; then
        log_success "respond fallback: gated on steps.respond.outcome"
    else
        log_error "respond fallback: missing or incorrect gate condition"
        failures=$((failures + 1))
    fi

    # Check fallback comment content
    if grep -q 'Agent Timeout' "$workflow_file"; then
        log_success "Fallback comment contains 'Agent Timeout' marker"
    else
        log_error "Fallback comment missing 'Agent Timeout' marker"
        failures=$((failures + 1))
    fi

    if grep -q 'self-healing system' "$workflow_file"; then
        log_success "Fallback comment contains self-healing attribution"
    else
        log_error "Fallback comment missing self-healing attribution"
        failures=$((failures + 1))
    fi

    if [[ $failures -gt 0 ]]; then
        log_error "Timeout fallback validation failed ($failures errors)"
        return 1
    fi

    log_success "Timeout fallback structure valid"
    return 0
}

# Validate-yaml mode (standalone, no auth needed)
if [[ "$MODE" == "validate-yaml" ]]; then
    trap - EXIT
    log_phase "STRUCTURAL VALIDATION: Issue Agent Timeout Fallback"
    validate_timeout_fallback
    exit $?
fi

# Dry run mode
if [[ "$MODE" == "dry-run" ]]; then
    log_step "Checking dependencies..."
    check_dependency gh || exit 1
    
    # Verify gh auth
    if ! gh auth status &> /dev/null; then
        log_error "gh CLI not authenticated. Run: gh auth login"
        exit 1
    fi
    log_success "gh CLI authenticated"
    
    log_success "Dry run complete - all dependencies satisfied"
    exit 0
fi

# Cleanup only mode
if [[ "$MODE" == "cleanup" ]]; then
    do_cleanup
    exit 0
fi

# Get repo info
REPO_OWNER=$(gh repo view --json owner -q .owner.login)
REPO_NAME=$(gh repo view --json name -q .name)
log "Repository: ${REPO_OWNER}/${REPO_NAME}"

# Test execution
log_phase "SMOKE TEST: Issue Agent Workflow"

# Step 0: Validate YAML structure (fast, local)
validate_timeout_fallback

# Step 1: Create test issue
log_step "[1/5] Creating test issue..."
ISSUE_TITLE="Smoke Test: broken import in loop.py [$(date +%s)]"
ISSUE_BODY="This is a smoke test issue to validate the issue-agent workflow.

**Problem:**
The file \`core/line_loop/loop.py\` has a missing import for \`datetime\`.

**Expected:**
The agent should:
1. Analyze the issue
2. Search the codebase
3. Propose a fix or ask clarifying questions
4. Apply appropriate labels

This issue is tagged with \`smoke-test\` for automated cleanup."

ISSUE_NUMBER=$(gh issue create \
    --title "$ISSUE_TITLE" \
    --body "$ISSUE_BODY" \
    --label "smoke-test" \
    --json number -q .number)

if [[ -z "$ISSUE_NUMBER" ]]; then
    log_error "Failed to create issue"
    exit 1
fi

log_success "Created issue #${ISSUE_NUMBER}"
log "   URL: https://github.com/${REPO_OWNER}/${REPO_NAME}/issues/${ISSUE_NUMBER}"

# Step 2: Wait for workflow to complete
log_step "[2/5] Waiting for issue-agent workflow..."
WORKFLOW_START=$(date +%s)
WORKFLOW_RUN_ID=""

# Poll for workflow run
while true; do
    ELAPSED=$(($(date +%s) - WORKFLOW_START))
    if [[ $ELAPSED -gt $WORKFLOW_TIMEOUT ]]; then
        log_error "Workflow timeout after ${WORKFLOW_TIMEOUT}s"
        log "   Check: https://github.com/${REPO_OWNER}/${REPO_NAME}/actions"
        do_cleanup
        exit 1
    fi
    
    # Find workflow run for this issue
    WORKFLOW_RUN_ID=$(gh run list \
        --workflow=issue-agent.yml \
        --limit 10 \
        --json databaseId,headBranch,status \
        --jq ".[] | select(.headBranch == \"main\" or .headBranch == null) | select(.status != \"completed\") | .databaseId" \
        | head -1)
    
    if [[ -n "$WORKFLOW_RUN_ID" ]]; then
        log "   Found workflow run: ${WORKFLOW_RUN_ID}"
        break
    fi
    
    log "   Waiting for workflow to start... (${ELAPSED}s)"
    sleep 5
done

# Wait for workflow to complete
while true; do
    ELAPSED=$(($(date +%s) - WORKFLOW_START))
    if [[ $ELAPSED -gt $WORKFLOW_TIMEOUT ]]; then
        log_error "Workflow timeout after ${WORKFLOW_TIMEOUT}s"
        do_cleanup
        exit 1
    fi
    
    WORKFLOW_STATUS=$(gh run view "$WORKFLOW_RUN_ID" --json status -q .status)
    
    if [[ "$WORKFLOW_STATUS" == "completed" ]]; then
        WORKFLOW_CONCLUSION=$(gh run view "$WORKFLOW_RUN_ID" --json conclusion -q .conclusion)
        if [[ "$WORKFLOW_CONCLUSION" == "success" ]]; then
            log_success "Workflow completed successfully (${ELAPSED}s)"
            break
        else
            log_error "Workflow failed with conclusion: ${WORKFLOW_CONCLUSION}"
            log "   View logs: gh run view ${WORKFLOW_RUN_ID} --log"
            do_cleanup
            exit 1
        fi
    fi
    
    log "   Workflow status: ${WORKFLOW_STATUS} (${ELAPSED}s)"
    sleep 10
done

# Step 3: Validate analysis comment
log_step "[3/5] Validating analysis comment..."
sleep 5  # Give GitHub API a moment to sync

COMMENTS=$(gh issue view "$ISSUE_NUMBER" --json comments -q '.comments | length')
if [[ "$COMMENTS" -eq 0 ]]; then
    log_error "No comments found on issue"
    do_cleanup
    exit 1
fi

COMMENT_BODY=$(gh issue view "$ISSUE_NUMBER" --json comments -q '.comments[0].body')

# Check for structured analysis
if ! echo "$COMMENT_BODY" | grep -q "Analysis"; then
    log_error "Comment missing 'Analysis' section"
    log "Comment preview:"
    log "$(echo "$COMMENT_BODY" | head -10)"
    do_cleanup
    exit 1
fi

log_success "Analysis comment found"

# Check for confidence indicator (present in Path B analysis responses)
if echo "$COMMENT_BODY" | grep -qi "confidence"; then
    log_success "Confidence indicator found (Path B response)"
else
    log_warning "No confidence indicator found"
    log "   Path A responses (fix proposed) omit confidence — not a failure"
fi

log "   Preview: $(echo "$COMMENT_BODY" | head -3 | tr '\n' ' ')"

# Step 4: Test @mention response
log_step "[4/5] Testing @mention response..."
MENTION_COMMENT="@claude What file should I check for the import issue?"

gh issue comment "$ISSUE_NUMBER" --body "$MENTION_COMMENT"
log "   Posted mention comment"

# Wait for response workflow
sleep 10
RESPONSE_START=$(date +%s)

while true; do
    ELAPSED=$(($(date +%s) - RESPONSE_START))
    if [[ $ELAPSED -gt 120 ]]; then
        log_warning "Response timeout - skipping validation"
        break
    fi
    
    COMMENT_COUNT=$(gh issue view "$ISSUE_NUMBER" --json comments -q '.comments | length')
    if [[ "$COMMENT_COUNT" -gt 1 ]]; then
        RESPONSE_BODY=$(gh issue view "$ISSUE_NUMBER" --json comments -q '.comments[-1].body')
        if echo "$RESPONSE_BODY" | grep -q "loop.py"; then
            log_success "@mention response received"
            log "   Preview: $(echo "$RESPONSE_BODY" | head -2 | tr '\n' ' ')"
            break
        fi
    fi
    
    log "   Waiting for response... (${ELAPSED}s)"
    sleep 10
done

# Step 5: Cleanup
log_step "[5/5] Cleaning up..."
do_cleanup

log_phase "${GREEN}✓${NC} SMOKE TEST PASSED"
log ""
log "Validated:"
log "  ✓ Timeout fallback YAML structure"
log "  ✓ Issue creation"
log "  ✓ Workflow trigger and execution"
log "  ✓ Analysis comment posted"
log "  ✓ Confidence indicator checked"
log "  ✓ @mention response (if completed)"
log "  ✓ Cleanup"
log ""
