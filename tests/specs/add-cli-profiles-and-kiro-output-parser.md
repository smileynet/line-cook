# Test Specification: Add CLI profiles and Kiro output parser

## Tracer
Foundation — proves config-driven CLI selection and Kiro output parsing work

## Context
- Add CLI_PROFILES dict to config.py with 'claude' and 'kiro' entries
- Add get_cli_profile() helper
- Add Kiro-specific parsers to parsing.py
- Leave all existing Claude parsing functions unchanged
- Deliverable: CLI profiles in config.py, Kiro parsers in parsing.py, with unit tests

## Test Cases

### config.py — CLI Profiles

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| get_cli_profile('claude') | Returns claude profile dict | Default CLI |
| get_cli_profile('kiro') | Returns kiro profile dict | Kiro CLI |
| get_cli_profile('unknown') | Raises KeyError | Unknown CLI |
| CLI_PROFILES['claude']['binary'] | 'claude' | Binary name |
| CLI_PROFILES['claude']['has_streaming_json'] | True | Claude has streaming JSON |
| CLI_PROFILES['kiro']['binary'] | 'kiro-cli' | Binary name |
| CLI_PROFILES['kiro']['has_streaming_json'] | False | Kiro has no streaming JSON |
| CLI_PROFILES['kiro']['subcommand'] | 'chat' | Kiro uses chat subcommand |
| DEFAULT_CLI | 'claude' | Backward compatible default |

### parsing.py — strip_ansi()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| "\x1b[32mhello\x1b[0m" | "hello" | Color codes removed |
| "no ansi here" | "no ansi here" | Plain text unchanged |
| "\x1b[1;31mERROR\x1b[0m: msg" | "ERROR: msg" | Bold+color removed |
| "" | "" | Empty string |

### parsing.py — parse_kiro_tool_action()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| "Reading file (using tool: read)" | "read" | Tool name extracted |
| "Running command (using tool: shell)" | "shell" | Tool name extracted |
| "Just some text" | None | No tool action |
| "> Agent thinking text" | None | Agent text, not tool |
| "(using tool: read_file)" | "read_file" | Underscored tool name |

### parsing.py — parse_kiro_tool_result()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| " ✓ Successfully read file" | ('success', 'Successfully read file') | Checkmark = success |
| " ✗ Failed to read file" | ('failure', 'Failed to read file') | Cross = failure |
| "Regular output" | None | No result marker |
| " - Completed in 0.4s" | None | Timing line, not result |

### parsing.py — extract_kiro_actions_from_line()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Tool action line + empty pending | Creates pending ActionRecord | New action started |
| Success result line + pending action | Completes action, returns it | Action resolved |
| Failure result line + pending action | Fails action, returns it | Action resolved |
| Plain text + empty pending | No actions | Nothing to track |

## Edge Cases
- [ ] ANSI codes wrapping tool action pattern
- [ ] Multiple tool actions on same line (should not happen, but handle)
- [ ] Unicode characters in tool output (checkmark is U+2713, cross is U+2717)
- [ ] Empty lines from Kiro output
- [ ] Lines with only whitespace

## Implementation Notes
These specs will be translated to Python unittest tests during /cook.
Existing tests in test_line_loop.py should remain passing.
