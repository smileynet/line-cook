#!/usr/bin/env bash
# planning.sh - Narrative 5: Planning Cycle
#
# Tests: brainstorm, sample, scope, finalize
# Fixture: demo-planning (empty beads + pre-seeded artifacts)
# Expected: Beads created from the planning process, committed
#
# Note: brainstorm, sample, and scope are interactive commands (AskUserQuestion).
# The prompts pre-seed inputs so the LLM can proceed non-interactively.
# We test the abbreviated flow: brainstorm → sample → scope → finalize, each with
# pre-seeded context to bypass interactive prompts.

NARRATIVE_FIXTURE="demo-planning"

NARRATIVE_STEPS=(
    "brainstorm"
    "sample"
    "scope"
    "finalize"
)

# Step 1: brainstorm
# The brainstorm command normally asks interactive questions. We provide
# the brainstorm.md already exists as a pre-seeded artifact and tell the
# LLM to review/refine it rather than starting from scratch.
STEP_COMMAND[0]="brainstorm"
STEP_CONTEXT[0]="A brainstorm.md file already exists with initial ideas. Review it and refine if needed. The project is a vanilla JS TodoWebApp. Do NOT use AskUserQuestion — work with the existing brainstorm.md content. If the brainstorm looks complete, confirm it and move on."
STEP_ARGUMENT[0]=""
STEP_TIMEOUT[0]=120
STEP_MAX_TURNS[0]=10
STEP_TYPE[0]="mutating"

# Step 2: sample
# The sample command walks through UX experience beats. We tell the
# LLM to create a walkthrough non-interactively from brainstorm context.
STEP_COMMAND[1]="sample"
STEP_CONTEXT[1]="No walkthrough exists yet. Create one based on the brainstorm.md. The project is a vanilla JS TodoWebApp. Software type is Web. Do NOT use AskUserQuestion — infer a reasonable persona and walk through the 5 beats, creating interaction sketches. Write the walkthrough document and move on."
STEP_ARGUMENT[1]=""
STEP_TIMEOUT[1]=120
STEP_MAX_TURNS[1]=10
STEP_TYPE[1]="mutating"

# Step 3: scope
# The scope command normally asks interactive questions to build the work
# breakdown. We provide menu-plan.yaml as pre-seeded output.
STEP_COMMAND[2]="scope"
STEP_CONTEXT[2]="A menu-plan.yaml file already exists with the structured work breakdown. Review it and refine if needed. The brainstorm.md and walkthrough have been completed. Do NOT use AskUserQuestion — work with the existing menu-plan.yaml content. If the scope looks complete, confirm it and move on."
STEP_ARGUMENT[2]=""
STEP_TIMEOUT[2]=120
STEP_MAX_TURNS[2]=10
STEP_TYPE[2]="mutating"

# Step 4: finalize
# Finalize converts the plan to beads and creates test specs.
STEP_COMMAND[3]="finalize"
STEP_CONTEXT[3]="Convert the menu-plan.yaml into beads issues. The brainstorm.md, walkthrough, and menu-plan.yaml are all complete. Create the beads hierarchy: epic, features, and tasks with dependencies. Commit the results."
STEP_ARGUMENT[3]=""
STEP_TIMEOUT[3]=300
STEP_MAX_TURNS[3]=20
STEP_TYPE[3]="mutating"

# Step goals for agent-based validation
STEP_GOAL[0]="Review and refine the existing brainstorm.md for the TodoWebApp project"
STEP_GOAL[1]="Create a walkthrough document for the TodoWebApp project"
STEP_GOAL[2]="Review and refine the existing menu-plan.yaml work breakdown"
STEP_GOAL[3]="Convert the menu-plan.yaml into beads issues with epic, features, and tasks"

# ============================================================
# Per-Step Validation
# ============================================================

narrative_validate_step_1() {
    # Brainstorm should acknowledge/work with the existing brainstorm.md
    if [[ -f "brainstorm.md" ]]; then
        add_check "brainstorm_exists" true "brainstorm.md exists"
    else
        add_check "brainstorm_exists" false "brainstorm.md not found"
    fi
}

narrative_validate_step_2() {
    # Sample should acknowledge/work with the existing walkthrough
    local walkthrough_found=false
    if ls docs/planning/walkthrough-*.md 2>/dev/null | head -1 >/dev/null 2>&1; then
        walkthrough_found=true
    elif [[ -f "walkthrough.md" ]]; then
        walkthrough_found=true
    fi
    if [[ "$walkthrough_found" == "true" ]]; then
        add_check "walkthrough_exists" true "walkthrough document exists"
    else
        add_check "walkthrough_exists" false "walkthrough document not found"
    fi
}

narrative_validate_step_3() {
    # Scope should acknowledge/work with the existing menu-plan.yaml
    if [[ -f "menu-plan.yaml" ]]; then
        add_check "scope_exists" true "menu-plan.yaml exists"
    else
        add_check "scope_exists" false "menu-plan.yaml not found"
    fi
}

narrative_validate_step_4() {
    # Finalize should create beads
    local bead_count
    bead_count=$(bd list --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    if [[ "$bead_count" -gt 0 ]]; then
        add_check "beads_created" true "Finalize created $bead_count beads"
    else
        add_check "beads_created" false "No beads created by finalize"
    fi
}

# ============================================================
# Final Validation
# ============================================================

narrative_validate_final() {
    # Beads should exist (created by finalize)
    local bead_count
    bead_count=$(bd list --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    if [[ "$bead_count" -gt 0 ]]; then
        add_check "final_beads_exist" true "$bead_count beads created"
    else
        add_check "final_beads_exist" false "No beads exist after planning"
    fi

    # Check that at least an epic exists
    local epic_count
    epic_count=$(bd list --json 2>/dev/null | jq '[.[] | select(.issue_type == "epic")] | length' 2>/dev/null || echo "0")
    if [[ "$epic_count" -gt 0 ]]; then
        add_check "epic_exists" true "$epic_count epic(s) created"
    else
        add_check "epic_exists" false "No epics created"
    fi

    # Planning artifacts should still be present
    if [[ -f "brainstorm.md" ]]; then
        add_check "brainstorm_preserved" true "brainstorm.md preserved"
    else
        add_check "brainstorm_preserved" false "brainstorm.md missing"
    fi

    if [[ -f "menu-plan.yaml" ]]; then
        add_check "scope_preserved" true "menu-plan.yaml preserved"
    else
        add_check "scope_preserved" false "menu-plan.yaml missing"
    fi
}
