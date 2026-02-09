#!/usr/bin/env bash
# narrative-utils.sh - Utilities for narrative-based eval runs
#
# Provides:
#   load_command_content    - Load command markdown for a provider
#   build_step_prompt       - Build a self-contained prompt for one narrative step
#   agent_validate_step     - Use a lightweight LLM call to judge step completion
#   get_step_tools          - Get tool permissions for a step type

set -euo pipefail

NARRATIVE_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NARRATIVE_EVAL_DIR="$(cd "$NARRATIVE_LIB_DIR/.." && pwd)"
NARRATIVE_REPO_ROOT="$(cd "$NARRATIVE_EVAL_DIR/../.." && pwd)"

# Load command markdown content for a provider
#
# Args: provider, command_name
# Output: Command markdown content to stdout
# Returns: 0 on success, 1 if file not found
load_command_content() {
    local provider="$1"
    local command_name="$2"
    local command_file=""

    case "$provider" in
        claude)
            command_file="$NARRATIVE_REPO_ROOT/plugins/claude-code/commands/${command_name}.md"
            ;;
        opencode)
            command_file="$NARRATIVE_REPO_ROOT/plugins/opencode/commands/line-${command_name}.md"
            ;;
        kiro)
            command_file="$NARRATIVE_REPO_ROOT/plugins/kiro/prompts/line-${command_name}.md"
            ;;
        *)
            echo "Unknown provider: $provider" >&2
            return 1
            ;;
    esac

    if [[ ! -f "$command_file" ]]; then
        echo "Command file not found: $command_file" >&2
        return 1
    fi

    cat "$command_file"
}

# Build a self-contained prompt for one narrative step
#
# Injects the command markdown into a wrapper prompt that tells the LLM
# to follow the command instructions exactly. Headless mode lacks native
# slash commands, so we inject the command content directly.
#
# Args:
#   provider       - claude|opencode|kiro
#   command_name   - Command to execute (e.g., prep, cook, serve)
#   context        - Additional context/instructions for this step
#   [argument]     - Optional argument for the command (e.g., task ID)
#
# Output: Full prompt to stdout
build_step_prompt() {
    local provider="$1"
    local command_name="$2"
    local context="$3"
    local argument="${4:-}"

    local command_content
    command_content=$(load_command_content "$provider" "$command_name") || return 1

    local prompt="You are working in a Line Cook project with beads for issue tracking.
"

    if [[ -n "$context" ]]; then
        prompt+="
Context: $context
"
    fi

    if [[ -n "$argument" ]]; then
        prompt+="
The argument for this command is: $argument
"
    fi

    prompt+="
Follow these instructions exactly:

---
$command_content
---

Execute the process described above completely. When finished, summarize what you accomplished."

    echo "$prompt"
}

# Build a composite prompt that inlines multiple commands for a full cycle
#
# This is used by the full-run narrative. In headless mode, Skill() calls
# don't work, so we inline the actual command content for each phase.
#
# Args:
#   provider       - claude|opencode|kiro
#   context        - Additional context/instructions
#   [argument]     - Optional argument (e.g., task ID)
#
# Output: Full composite prompt to stdout
build_composite_prompt() {
    local provider="$1"
    local context="$2"
    local argument="${3:-}"

    local prep_content cook_content serve_content tidy_content
    prep_content=$(load_command_content "$provider" "prep") || return 1
    cook_content=$(load_command_content "$provider" "cook") || return 1
    serve_content=$(load_command_content "$provider" "serve") || return 1
    tidy_content=$(load_command_content "$provider" "tidy") || return 1

    local prompt="You are working in a Line Cook project with beads for issue tracking.

You must execute a FULL WORKFLOW CYCLE: prep → cook → serve → tidy, all in this single session.
Do NOT stop after prep. You must complete ALL FOUR phases.
"

    if [[ -n "$context" ]]; then
        prompt+="
Context: $context
"
    fi

    if [[ -n "$argument" ]]; then
        prompt+="
The task to work on is: $argument
"
    fi

    prompt+="
Execute these four phases IN ORDER. Do not skip any phase.

═══════════════════════════════════════════════
PHASE 1: PREP — Sync state and identify the next task
═══════════════════════════════════════════════

$prep_content

═══════════════════════════════════════════════
PHASE 2: COOK — Implement the task with TDD
═══════════════════════════════════════════════

$cook_content

═══════════════════════════════════════════════
PHASE 3: SERVE — Review code changes
═══════════════════════════════════════════════

$serve_content

═══════════════════════════════════════════════
PHASE 4: TIDY — Commit, sync beads, and push
═══════════════════════════════════════════════

$tidy_content

After completing ALL four phases, summarize what you accomplished in each phase.
IMPORTANT: You MUST complete all four phases. Do not stop after prep."

    echo "$prompt"
}

# Validate a step's output using a lightweight LLM call (haiku)
#
# The agent judges whether the provider output accomplishes the stated goal.
# Fast-path: if output is empty, returns failed without an API call.
#
# Args:
#   step_goal       - Human-readable description of what the step should accomplish
#   output_text     - Provider output text to evaluate
#   command_name    - Command name (for logging context)
#
# Output: JSON to stdout: {"passed": true/false, "reasoning": "..."}
agent_validate_step() {
    local step_goal="$1"
    local output_text="$2"
    local command_name="$3"

    # Fast path: empty output always fails
    if [[ -z "${output_text// /}" ]]; then
        echo '{"passed": false, "reasoning": "Output was empty"}'
        return
    fi

    # Truncate output to keep cost/latency low
    local truncated_output
    truncated_output=$(echo "$output_text" | head -c 4000)

    local validation_prompt="You are evaluating whether an AI coding assistant accomplished its goal.

GOAL: ${step_goal}
COMMAND: ${command_name}

=== OUTPUT START ===
${truncated_output}
=== OUTPUT END ===

Did the assistant accomplish the goal described above? Look at what was actually done, not just what was claimed.

Respond with ONLY a JSON object (no markdown, no code fences):
{\"passed\": true or false, \"reasoning\": \"one sentence explanation\"}"

    # Note: output_text is embedded directly in the prompt. This is acceptable for
    # internal eval use but not hardened against adversarial prompt injection.
    local agent_output agent_exit=0
    agent_output=$(timeout 30 claude -p "$validation_prompt" \
        --model haiku \
        --max-turns 1 \
        --no-session-persistence \
        --output-format text \
        2>/dev/null) || agent_exit=$?

    if [[ $agent_exit -ne 0 ]]; then
        echo "{\"passed\": false, \"reasoning\": \"Agent validation call failed (exit=$agent_exit)\"}"
        return
    fi

    # Parse JSON — try jq first (handles nested braces), fall back to regex
    local json_result
    json_result=$(echo "$agent_output" | jq -c 'select(.passed != null)' 2>/dev/null | head -1)
    if [[ -z "$json_result" ]]; then
        json_result=$(echo "$agent_output" | grep -oE '\{[^}]+\}' | head -1)
    fi

    if [[ -n "$json_result" ]] && echo "$json_result" | jq -e '.passed' >/dev/null 2>&1; then
        echo "$json_result"
    else
        echo '{"passed": false, "reasoning": "Agent validation response could not be parsed"}'
    fi
}

# Get tool permissions for a step type (claude --allowedTools)
#
# Args: step_type (readonly|mutating)
# Output: allowedTools string
get_step_tools() {
    local step_type="$1"

    case "$step_type" in
        readonly)
            echo "Bash(read-only:*),Read,Glob,Grep"
            ;;
        mutating|*)
            echo "Bash,Read,Edit,Glob,Grep,Write"
            ;;
    esac
}
