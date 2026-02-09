#!/usr/bin/env bash
# onboard.sh - Narrative 1: New Developer Orientation
#
# Tests: getting-started, prep
# Fixture: demo-simple
# Expected: Read-only — no source files created, no bead state changes
#
# This is the cheapest narrative, used as the stop-gate to validate
# that prompt injection of command markdown works across providers.

NARRATIVE_FIXTURE="demo-simple"

NARRATIVE_STEPS=(
    "getting-started"
    "prep"
)

# Step 1: getting-started (read-only guide)
STEP_COMMAND[0]="getting-started"
STEP_CONTEXT[0]="You are a new developer joining this project. Read the getting-started guide to understand the workflow."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=60
STEP_MAX_TURNS[0]=5
STEP_TYPE[0]="readonly"

# Step 2: prep (sync + show ready tasks)
# Prep runs git pull/bd sync, so it needs mutating tools even though it's read-only in intent
STEP_COMMAND[1]="prep"
STEP_CONTEXT[1]="Now run the prep phase to see what tasks are available to work on."
STEP_ARGUMENT[1]=""
STEP_TIMEOUT[1]=60
STEP_MAX_TURNS[1]=5
STEP_TYPE[1]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Explain the Line Cook workflow phases (prep, cook, serve, tidy)"
STEP_GOAL[1]="Show the next ready task (demo-001.1.1) after syncing state"

# ============================================================
# Per-Step Validation
# ============================================================

narrative_validate_step_2() {
    # prep should mention the correct task ID
    if echo "$STEP_RESULT_TEXT" | grep -qi "demo-001.1.1"; then
        add_check "prep_correct_task" true "Prep identifies demo-001.1.1"
    else
        add_check "prep_correct_task" false "Prep does not mention demo-001.1.1"
    fi
}

# ============================================================
# Final Validation
# ============================================================

narrative_validate_final() {
    # No source files should exist (read-only narrative)
    if [[ ! -f "src/todo.js" && ! -f "src/todo.test.js" ]]; then
        add_check "no_source_files" true "No source files created (read-only)"
    else
        add_check "no_source_files" false "Source files were created during read-only narrative"
    fi

    # Bead state should be unchanged
    local bead_status
    bead_status=$(get_bead_status demo-001.1.1)
    if [[ "$bead_status" == "open" ]]; then
        add_check "bead_unchanged" true "demo-001.1.1 still open (unchanged)"
    else
        add_check "bead_unchanged" false "demo-001.1.1 status changed to: $bead_status"
    fi
}
