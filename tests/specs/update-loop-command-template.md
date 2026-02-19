# Test Specification: Update loop command template to pass --cli flag

## Tracer
Wrapper integration — proves @line-loop start invokes the correct CLI

## Context
- Update loop.md.template with --cli kiro in Kiro block
- Sync template to all plugin directories
- Verify background execution works for Kiro (nohup)
- Verify script discovery works for Kiro
- Deliverable: Updated template, synced, background launch verified

## Test Cases

### Template content

| Check | Expected | Notes |
|-------|----------|-------|
| @IF_KIRO@ block contains --cli kiro | Yes | Kiro launch uses correct flag |
| @IF_CLAUDECODE@ block has no --cli | Yes | Claude uses default |
| Kiro block uses nohup + & | Yes | Background execution |
| Kiro block captures PID | Yes | echo $! > loop.pid |

### Sync verification

| Check | Expected | Notes |
|-------|----------|-------|
| plugins/kiro/prompts/line-loop.md contains --cli kiro | Yes | Synced |
| plugins/claude-code/commands/loop.md has no --cli kiro | Yes | Claude default |
| plugins/opencode/prompts/line-loop.md is unaffected | Yes | No changes |

### Script discovery

| Check | Expected | Notes |
|-------|----------|-------|
| Kiro finds plugins/claude-code/scripts/line-loop.py | Yes | Shared bundle path |
| OR Kiro finds core/line-loop-cli.py | Yes | Development path |

## Edge Cases
- [ ] nohup process survives after Kiro shell tool returns
- [ ] Loop log captures both stdout and stderr
- [ ] PID file is created before nohup returns

## Implementation Notes
Template tests are manual/visual verification of generated output.
Sync test runs dev/sync-commands.sh and checks output files.
Background execution needs empirical testing with actual Kiro CLI.
