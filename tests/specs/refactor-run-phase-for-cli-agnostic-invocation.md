# Test Specification: Refactor run_phase for CLI-agnostic invocation

## Tracer
Core abstraction — proves phase execution works with any CLI profile

## Context
- Add build_phase_command() to phase.py
- Add process_output_line() to phase.py
- Modify run_phase() to accept cli_profile parameter
- Backward compatible: existing calls work unchanged
- Deliverable: CLI-agnostic run_phase() with unit tests

## Test Cases

### build_phase_command()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| phase="cook", args="", claude_profile | ["claude", "-p", "/line:cook", "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"] | Claude command |
| phase="cook", args="lc-abc", claude_profile | ["claude", "-p", "/line:cook lc-abc", "--dangerously-skip-permissions", ...] | Claude with args |
| phase="cook", args="", kiro_profile | ["kiro-cli", "chat", "--no-interactive", "--trust-all-tools", "--wrap", "never", "--agent", "line-cook", "@line-cook"] | Kiro command |
| phase="serve", args="lc-abc", kiro_profile | ["kiro-cli", "chat", ..., "@line-serve lc-abc"] | Kiro with args |
| phase="tidy", args="", kiro_profile | [..., "@line-tidy"] | Kiro tidy |

### process_output_line() — streaming JSON mode

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Valid JSON event line, claude_profile | (actions, text) | Delegates to existing parser |
| Invalid JSON line, claude_profile | ([], line) | Graceful fallback |
| Empty line, claude_profile | ([], "") | No-op |

### process_output_line() — plain text mode (Kiro)

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| "Reading file (using tool: read)", kiro_profile | ([], cleaned_line) with pending action | Tool action detected |
| " ✓ Success", kiro_profile, with pending | ([completed_action], cleaned_line) | Action resolved |
| "KITCHEN_COMPLETE", kiro_profile | ([], "KITCHEN_COMPLETE") | Signal passes through |
| "\x1b[32mtext\x1b[0m", kiro_profile | ([], "text") | ANSI stripped |

### run_phase() backward compatibility

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| run_phase("cook", cwd) — no cli_profile | Uses claude profile | Backward compatible |
| run_phase("cook", cwd, cli_profile=claude) | Same as default | Explicit claude |
| run_phase("cook", cwd, cli_profile=kiro) | Uses kiro command | Kiro invocation |

## Edge Cases
- [ ] run_phase() with None cli_profile defaults to claude
- [ ] Kiro output with mixed ANSI and signal text
- [ ] Idle detection updates last_action_time on any Kiro stdout

## Implementation Notes
Tests should mock subprocess.Popen to avoid real CLI invocations.
Verify that existing test_line_loop.py tests still pass unchanged.
