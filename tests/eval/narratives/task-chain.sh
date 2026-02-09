#!/usr/bin/env bash
# task-chain.sh - Narrative 3: Sequential Dependency Unlock
#
# Tests: prep, cook, serve, tidy (x2 cycles), plate
# Fixture: demo-simple
# Expected: Both demo-001.1.1 and demo-001.1.2 closed, feature validated

NARRATIVE_FIXTURE="demo-simple"

NARRATIVE_STEPS=(
    "prep-1"
    "cook-1"
    "serve-1"
    "tidy-1"
    "prep-2"
    "cook-2"
    "serve-2"
    "tidy-2"
    "plate"
)

# --- Cycle 1: demo-001.1.1 (add todo) ---

STEP_COMMAND[0]="prep"
STEP_CONTEXT[0]="Start the first cycle. Sync and identify the next ready task."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=60
STEP_MAX_TURNS[0]=5
# Prep runs git pull/bd sync, needs mutating tools
STEP_TYPE[0]="mutating"

STEP_COMMAND[1]="cook"
STEP_CONTEXT[1]="Implement the add-todo task. Follow TDD: write tests first in src/todo.test.js, then implement in src/todo.js. Run tests with 'node src/todo.test.js'."
STEP_ARGUMENT[1]="demo-001.1.1"
STEP_TIMEOUT[1]=600
STEP_MAX_TURNS[1]=25
STEP_TYPE[1]="mutating"

STEP_COMMAND[2]="serve"
STEP_CONTEXT[2]="Review the implementation of demo-001.1.1 (add todo). Check tests and code quality."
STEP_ARGUMENT[2]=""
STEP_TIMEOUT[2]=120
STEP_MAX_TURNS[2]=10
STEP_TYPE[2]="mutating"

STEP_COMMAND[3]="tidy"
STEP_CONTEXT[3]="Commit and push. Close bead demo-001.1.1. This will unblock demo-001.1.2."
STEP_ARGUMENT[3]=""
STEP_TIMEOUT[3]=120
STEP_MAX_TURNS[3]=10
STEP_TYPE[3]="mutating"

# --- Cycle 2: demo-001.1.2 (toggle complete) ---

STEP_COMMAND[4]="prep"
STEP_CONTEXT[4]="Start cycle 2. demo-001.1.2 (toggle complete) should now be unblocked."
STEP_ARGUMENT[4]=""
STEP_TIMEOUT[4]=60
STEP_MAX_TURNS[4]=5
# Prep runs git pull/bd sync, needs mutating tools
STEP_TYPE[4]="mutating"

STEP_COMMAND[5]="cook"
STEP_CONTEXT[5]="Implement toggle-complete functionality. Build on existing src/todo.js. Add tests for toggling completion state. Run tests with 'node src/todo.test.js'."
STEP_ARGUMENT[5]="demo-001.1.2"
STEP_TIMEOUT[5]=600
STEP_MAX_TURNS[5]=25
STEP_TYPE[5]="mutating"

STEP_COMMAND[6]="serve"
STEP_CONTEXT[6]="Review the implementation of demo-001.1.2 (toggle complete). Check tests and code quality."
STEP_ARGUMENT[6]=""
STEP_TIMEOUT[6]=120
STEP_MAX_TURNS[6]=10
STEP_TYPE[6]="mutating"

STEP_COMMAND[7]="tidy"
STEP_CONTEXT[7]="Commit and push. Close bead demo-001.1.2."
STEP_ARGUMENT[7]=""
STEP_TIMEOUT[7]=120
STEP_MAX_TURNS[7]=10
STEP_TYPE[7]="mutating"

# --- Feature validation ---

STEP_COMMAND[8]="plate"
STEP_CONTEXT[8]="Validate the completed feature demo-001.1 (User can manage todos). Both child tasks should be closed."
STEP_ARGUMENT[8]="demo-001.1"
STEP_TIMEOUT[8]=120
STEP_MAX_TURNS[8]=10
STEP_TYPE[8]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Sync state and identify demo-001.1.1 as the next ready task"
STEP_GOAL[1]="Implement demo-001.1.1 (add todo) with TDD"
STEP_GOAL[2]="Review the implementation of demo-001.1.1"
STEP_GOAL[3]="Commit changes for demo-001.1.1 and push to remote"
STEP_GOAL[4]="Sync state and identify demo-001.1.2 as the next ready task (unblocked by demo-001.1.1)"
STEP_GOAL[5]="Implement demo-001.1.2 (toggle complete) with TDD"
STEP_GOAL[6]="Review the implementation of demo-001.1.2"
STEP_GOAL[7]="Commit changes for demo-001.1.2 and push to remote"
STEP_GOAL[8]="Validate the completed feature demo-001.1 with both child tasks closed"

# ============================================================
# Per-Step Validation
# ============================================================

narrative_validate_step_1() {
    if echo "$STEP_RESULT_TEXT" | grep -qi "demo-001.1.1"; then
        add_check "prep1_task" true "Prep 1 identifies demo-001.1.1"
    else
        add_check "prep1_task" false "Prep 1 does not mention demo-001.1.1"
    fi
}

narrative_validate_step_5() {
    if echo "$STEP_RESULT_TEXT" | grep -qi "demo-001.1.2"; then
        add_check "prep2_task" true "Prep 2 identifies demo-001.1.2"
    else
        add_check "prep2_task" false "Prep 2 does not mention demo-001.1.2"
    fi
}

# ============================================================
# Final Validation
# ============================================================

narrative_validate_final() {
    # Both beads closed
    local status1 status2
    status1=$(get_bead_status demo-001.1.1)
    status2=$(get_bead_status demo-001.1.2)

    if [[ "$status1" == "closed" ]]; then
        add_check "bead1_closed" true "demo-001.1.1 is closed"
    else
        add_check "bead1_closed" false "demo-001.1.1 status: $status1"
    fi

    if [[ "$status2" == "closed" ]]; then
        add_check "bead2_closed" true "demo-001.1.2 is closed"
    else
        add_check "bead2_closed" false "demo-001.1.2 status: $status2"
    fi

    # Source files exist with toggle logic
    if [[ -f "src/todo.js" ]]; then
        add_check "source_exists" true "src/todo.js exists"
        if grep -qiE '(complete|toggle|done)' src/todo.js; then
            add_check "toggle_implemented" true "src/todo.js contains toggle/complete logic"
        else
            add_check "toggle_implemented" false "src/todo.js missing toggle/complete logic"
        fi
    else
        add_check "source_exists" false "src/todo.js not found"
    fi

    # Tests pass
    if [[ -f "src/todo.test.js" ]]; then
        if node src/todo.test.js >/dev/null 2>&1; then
            add_check "tests_pass" true "Tests pass"
        else
            add_check "tests_pass" false "Tests fail"
        fi
    fi

    # Pushed to remote
    git fetch origin >/dev/null 2>&1 || true
    local unpushed
    unpushed=$(git log origin/main..HEAD --oneline 2>/dev/null || echo "error")
    if [[ -z "$unpushed" ]]; then
        add_check "pushed_to_remote" true "All commits pushed"
    else
        add_check "pushed_to_remote" false "Unpushed commits exist" "$unpushed"
    fi
}
