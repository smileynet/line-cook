# Test Specification: Re-bundle and verify backward compatibility

## Tracer
Verification — proves bundled artifact works and nothing is broken

## Context
- Re-bundle line-loop.py via ./dev/release.py --bundle
- Run full test suite
- Verify backward compatibility
- Deliverable: Bundled line-loop.py with --cli support, all tests passing

## Test Cases

### Bundle verification

| Check | Expected | Notes |
|-------|----------|-------|
| ./dev/release.py --bundle exits 0 | Yes | Bundle succeeds |
| Syntax check passes | Yes | Valid Python |
| Size guard passes | Yes | Within limits |
| Smoke test passes | Yes | Imports work |

### --help output

| Check | Expected | Notes |
|-------|----------|-------|
| --cli flag shown | Yes | New flag visible |
| --cli choices include 'claude' | Yes | Default option |
| --cli choices include 'kiro' | Yes | New option |

### Backward compatibility

| Check | Expected | Notes |
|-------|----------|-------|
| line-loop.py (no --cli) defaults to claude | Yes | No behavior change |
| line-loop.py --cli kiro --max-iterations 0 exits cleanly | Yes | No crash |
| All existing tests pass | Yes | No regressions |

### Full test suite

| Check | Expected | Notes |
|-------|----------|-------|
| python3 -m unittest tests.test_line_loop -v | All pass | No regressions |

## Edge Cases
- [ ] Bundle includes new CLI_PROFILES from config.py
- [ ] Bundle includes new Kiro parsers from parsing.py
- [ ] Bundle includes modified run_phase() from phase.py

## Implementation Notes
This is primarily a verification task. Run commands and check outputs.
