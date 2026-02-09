#!/usr/bin/env bash
# full-run.sh - Narrative 4: /run Orchestrator
#
# Tests: run (which orchestrates prep → cook → serve → tidy)
# Fixture: demo-simple
# Expected: At least demo-001.1.1 implemented, tested, committed, pushed
#
# The /run command uses Skill() calls internally which aren't available
# headlessly. The prompt concatenates the run command markdown which
# instructs the LLM to execute all four phases in sequence.

NARRATIVE_FIXTURE="demo-simple"

NARRATIVE_STEPS=(
    "run"
)

# Step 1: run (full cycle — composite prompt inlines all 4 phases)
STEP_COMMAND[0]="run"
STEP_CONTEXT[0]="Execute the full workflow cycle. This should automatically prep, cook, serve, and tidy. The project has ready task demo-001.1.1. Implement it with TDD (tests in src/todo.test.js, code in src/todo.js), run tests with 'node src/todo.test.js', review, commit referencing the task ID (include 'demo-001.1.1' in the commit message), and push."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=900
STEP_MAX_TURNS[0]=50
STEP_TYPE[0]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Complete all four workflow phases: prep (identify task), cook (implement with TDD), serve (review), tidy (commit and push)"

# Override prompt builder to inline all four phases
# (run.md uses Skill() calls which don't work in headless mode)
narrative_build_prompt() {
    local provider="$1"
    local _command="$2"
    local context="$3"
    local argument="${4:-}"
    build_composite_prompt "$provider" "$context" "$argument"
}

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
