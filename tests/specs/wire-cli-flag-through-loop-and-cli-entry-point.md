# Test Specification: Wire --cli flag through loop and CLI entry point

## Tracer
Integration — proves end-to-end loop works with --cli kiro

## Context
- Add cli_profile parameter to run_iteration()
- Add cli_name parameter to run_loop()
- Add --cli argument to CLI argparse
- Deliverable: --cli flag working end-to-end

## Test Cases

### iteration.py — run_iteration()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| run_iteration(..., cli_profile=kiro) | Passes kiro to all run_phase() calls | Kiro propagated |
| run_iteration(..., cli_profile=None) | Default behavior unchanged | Backward compatible |
| check_epic_completion(..., cli_profile=kiro) | Passes kiro to close-service | Epic close via Kiro |

### loop.py — run_loop()

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| run_loop(..., cli_name='kiro') | Resolves kiro profile, passes to iterations | Kiro mode |
| run_loop(..., cli_name=None) | Uses DEFAULT_CLI | Backward compatible |
| run_loop(..., cli_name='claude') | Resolves claude profile explicitly | Explicit claude |
| run_loop(..., cli_name='unknown') | Raises KeyError at loop start | Fail fast |

### CLI argparse — line-loop-cli.py

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| --cli kiro | args.cli == 'kiro' | Kiro selected |
| --cli claude | args.cli == 'claude' | Claude explicit |
| (no --cli) | args.cli == DEFAULT_CLI | Default |
| --cli invalid | argparse error | Invalid choice |

## Edge Cases
- [ ] cli_profile=None throughout the call chain
- [ ] --help output shows --cli with choices

## Implementation Notes
Use mock to verify run_phase() receives correct cli_profile.
CLI argparse tests can use parse_args() directly.
