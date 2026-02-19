# Planning Context: Kiro Loop Support

**Status:** finalized
**Feature:** lc-du3
**Created:** 2026-02-18

## Problem
The autonomous `line:loop` only works with Claude Code CLI because `phase.py` hardcodes the `claude` binary and its flags. Kiro CLI users have a complete plugin (prompts, agents, steering) but cannot use the loop — Line Cook's most differentiating feature.

## Approach
Config-driven CLI selection with graceful degradation. Add CLI profiles to `config.py` that specify binary, flags, and output format. `phase.py` reads these profiles instead of hardcoded values. When streaming JSON is unavailable (Kiro), fall back to line-based output scanning for idle detection and skip granular action tracking.

## Key Decisions
- Config-driven approach over driver abstraction (simpler, sufficient for two CLIs)
- Graceful degradation for action tracking (signals work on plain text; action tracking is best-effort)
- Line-based idle detection as fallback when streaming JSON unavailable
- Defer Kiro hooks integration, OpenCode loop support, and session resume to future work

## Artifacts
- Brainstorm: docs/planning/brainstorm-kiro-loop.md
- Menu plan: docs/planning/menu-plan.yaml
- Architecture: docs/planning/context-kiro-loop/architecture.md
- Decisions: docs/planning/context-kiro-loop/decisions.log

## Scope
Phases: 1, Features: 1, Tasks: 5

- Feature 1.1: Run autonomous loop with Kiro CLI
  1. Add CLI profiles and Kiro output parser (config.py, parsing.py)
  2. Refactor run_phase for CLI-agnostic invocation (phase.py)
  3. Wire --cli flag through loop and CLI entry point (iteration.py, loop.py, cli)
  4. Update loop command template to pass --cli flag (template, sync, background launch)
  5. Re-bundle and verify backward compatibility
