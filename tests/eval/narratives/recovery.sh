#!/usr/bin/env bash
# recovery.sh - Narrative 6: Serve Rejection + Retry
#
# Tests: prep, cook (skip tests), serve (reject), cook (retry)
# Fixture: demo-simple
# Expected: First serve rejects (no tests), retry adds tests, final state passes
#
# This tests the review feedback loop: cook without tests → serve rejects →
# cook again with review findings → tests exist and pass.

NARRATIVE_FIXTURE="demo-simple"

NARRATIVE_STEPS=(
    "prep"
    "cook-skip-tests"
    "serve-reject"
    "cook-retry"
)

# Step 1: prep
STEP_COMMAND[0]="prep"
STEP_CONTEXT[0]="Start by running prep to identify the next task."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=60
STEP_MAX_TURNS[0]=5
# Prep runs git pull/bd sync, needs mutating tools
STEP_TYPE[0]="mutating"

# Step 2: cook (intentionally skip tests)
STEP_COMMAND[1]="cook"
STEP_CONTEXT[1]="Implement the task but SKIP writing tests. Only create src/todo.js with the implementation. Do NOT create src/todo.test.js. This is intentional — we want to test the review feedback loop."
STEP_ARGUMENT[1]="demo-001.1.1"
STEP_TIMEOUT[1]=600
STEP_MAX_TURNS[1]=25
STEP_TYPE[1]="mutating"

# Step 3: serve (expect rejection due to missing tests)
STEP_COMMAND[2]="serve"
STEP_CONTEXT[2]="Review the code changes. The implementation of demo-001.1.1 is in src/todo.js but there are no tests in src/todo.test.js. Review should identify missing tests as a critical issue."
STEP_ARGUMENT[2]=""
STEP_TIMEOUT[2]=120
STEP_MAX_TURNS[2]=10
STEP_TYPE[2]="mutating"

# Step 4: cook retry (fix the issues from review)
STEP_COMMAND[3]="cook"
STEP_CONTEXT[3]="The serve phase found critical issues: tests are missing. Retry the cook phase to add the missing tests. Create src/todo.test.js with proper tests for the add-todo functionality. Make sure tests pass with 'node src/todo.test.js'. Also close bead demo-001.1.1 when done."
STEP_ARGUMENT[3]="demo-001.1.1"
STEP_TIMEOUT[3]=600
STEP_MAX_TURNS[3]=25
STEP_TYPE[3]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Sync state and identify the next ready task"
STEP_GOAL[1]="Implement demo-001.1.1 without writing tests (implementation only)"
STEP_GOAL[2]="Review code and identify missing tests as a critical issue"
STEP_GOAL[3]="Add missing tests for demo-001.1.1 and verify they pass"

# ============================================================
# Per-Step Validation
# ============================================================

narrative_validate_step_3() {
    # Check for rejection indicators — serve should flag missing tests
    if echo "$STEP_RESULT_TEXT" | grep -qiE "needs_changes|NEEDS_CHANGES|blocked|BLOCKED|critical|missing.*test|no.*test|reject"; then
        add_check "serve_rejects" true "Serve identifies issues with missing tests"
    else
        add_check "serve_rejects" false "Serve did not flag missing tests as an issue"
    fi
}

# ============================================================
# Final Validation
# ============================================================

narrative_validate_final() {
    # After retry, tests should exist and pass
    if [[ -f "src/todo.test.js" ]]; then
        add_check "test_file_exists" true "src/todo.test.js exists after retry"
    else
        add_check "test_file_exists" false "src/todo.test.js not found after retry"
    fi

    if [[ -f "src/todo.test.js" ]]; then
        if node src/todo.test.js >/dev/null 2>&1; then
            add_check "tests_pass" true "Tests pass after retry"
        else
            add_check "tests_pass" false "Tests fail after retry"
        fi
    fi

    # Source file should exist
    if [[ -f "src/todo.js" ]]; then
        add_check "source_file_exists" true "src/todo.js exists"
    else
        add_check "source_file_exists" false "src/todo.js not found"
    fi
}
