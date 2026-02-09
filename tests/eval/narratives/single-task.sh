#!/usr/bin/env bash
# single-task.sh - Narrative 2: One Task Execution Cycle
#
# Tests: prep, cook, serve, tidy
# Fixture: demo-simple
# Expected: demo-001.1.1 implemented, tested, reviewed, committed, pushed

NARRATIVE_FIXTURE="demo-simple"

NARRATIVE_STEPS=(
    "prep"
    "cook"
    "serve"
    "tidy"
)

# Step 1: prep
STEP_COMMAND[0]="prep"
STEP_CONTEXT[0]="Start by running the prep phase to sync and identify the next task."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=60
STEP_MAX_TURNS[0]=5
# Prep runs git pull/bd sync, needs mutating tools
STEP_TYPE[0]="mutating"

# Step 2: cook demo-001.1.1
STEP_COMMAND[1]="cook"
STEP_CONTEXT[1]="Implement the task identified in prep. Follow TDD: write failing tests first, then implement to make them pass. The project uses 'node src/todo.test.js' to run tests."
STEP_ARGUMENT[1]="demo-001.1.1"
STEP_TIMEOUT[1]=600
STEP_MAX_TURNS[1]=25
STEP_TYPE[1]="mutating"

# Step 3: serve (review)
STEP_COMMAND[2]="serve"
STEP_CONTEXT[2]="Review the code changes from the cook phase. Check that tests exist, pass, and the implementation meets the task requirements. The task was demo-001.1.1 (add todo item). Files to review: src/todo.js, src/todo.test.js."
STEP_ARGUMENT[2]=""
STEP_TIMEOUT[2]=120
STEP_MAX_TURNS[2]=10
STEP_TYPE[2]="mutating"

# Step 4: tidy (commit + push)
STEP_COMMAND[3]="tidy"
STEP_CONTEXT[3]="Commit all changes and push to remote. The task ID is demo-001.1.1. Include 'demo-001.1.1' in the commit message. Close the bead before committing."
STEP_ARGUMENT[3]=""
STEP_TIMEOUT[3]=120
STEP_MAX_TURNS[3]=10
STEP_TYPE[3]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Sync state and identify demo-001.1.1 as next ready task"
STEP_GOAL[1]="Implement demo-001.1.1 with TDD (tests and code)"
STEP_GOAL[2]="Review code changes and provide a verdict"
STEP_GOAL[3]="Commit changes, sync beads, and push to remote"

# ============================================================
# Final Validation
# ============================================================

narrative_validate_final() {
    # Source files exist
    if [[ -f "src/todo.js" ]]; then
        add_check "source_file_exists" true "src/todo.js exists"
    else
        add_check "source_file_exists" false "src/todo.js not found"
    fi

    if [[ -f "src/todo.test.js" ]]; then
        add_check "test_file_exists" true "src/todo.test.js exists"
    else
        add_check "test_file_exists" false "src/todo.test.js not found"
    fi

    # Tests pass
    if [[ -f "src/todo.test.js" ]]; then
        if node src/todo.test.js >/dev/null 2>&1; then
            add_check "tests_pass" true "Tests pass"
        else
            add_check "tests_pass" false "Tests fail"
        fi
    fi

    # Bead closed
    local bead_status
    bead_status=$(get_bead_status demo-001.1.1)
    if [[ "$bead_status" == "closed" ]]; then
        add_check "bead_closed" true "demo-001.1.1 is closed"
    else
        add_check "bead_closed" false "demo-001.1.1 status: $bead_status (expected: closed)"
    fi

    # Commit references task
    if git log --oneline -20 | grep -qi "demo-001.1.1"; then
        add_check "commit_references_task" true "Commit references demo-001.1.1"
    else
        add_check "commit_references_task" false "No commit references demo-001.1.1"
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

    # Clean working tree (exclude .beads/ metadata — multi-step narratives may
    # trigger sync artifacts beyond just the lock file — and scratch/)
    local uncommitted
    uncommitted=$(git status --porcelain 2>/dev/null | grep -v '\.beads/' | grep -v '^?? scratch/' || true)
    if [[ -z "$uncommitted" ]]; then
        add_check "clean_working_tree" true "Working tree is clean"
    else
        add_check "clean_working_tree" false "Uncommitted changes" "$uncommitted"
    fi
}
