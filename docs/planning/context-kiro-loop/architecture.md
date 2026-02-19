# Architecture: Kiro Loop Support

> Technical patterns, constraints, and conventions discovered during planning.
> Loaded by `/cook` for design context (~800 tokens target).

## Layers
- **config.py** — CLI profiles (binary, flags, output format, prompt pattern)
- **phase.py** — Subprocess invocation, output parsing, signal/idle detection
- **iteration.py** — Unchanged (CLI-agnostic orchestration)
- **loop.py** — Passes CLI config through to phases, adds `--cli` arg
- **CLI wrapper** — Adds `--cli` argparse flag

## Patterns
- CLI profiles are dicts in `config.py`, keyed by name (`claude`, `kiro`)
- `run_phase()` accepts profile and builds command from it (no hardcoded strings)
- Output parsing has two modes: streaming JSON (Claude) and line-scanning (fallback)
- Signal detection is always text-based — works with any output format
- Idle detection: streaming JSON tracks `tool_use` events; fallback tracks any stdout activity

## Constraints
- Kiro CLI has no `--output-format stream-json` — plain text stdout with tool actions as `(using tool: name)`
- Kiro prompt syntax: `@line-cook` not `/line:cook` — works as positional input arg
- Kiro non-interactive: `kiro-cli chat --no-interactive --trust-all-tools --agent line-cook "@line-cook"`
- Kiro stdout includes ANSI escape codes — must strip for clean parsing
- Kiro stderr has banner/chrome — redirect to DEVNULL
- Bundled `line-loop.py` lives in `plugins/claude-code/` — Kiro runs from `core/line_loop/` directly
- Must not break existing Claude loop behavior (backward compatible)

## Conventions
- All line_loop modules import from `.config` — centralized constants
- After modifying `core/line_loop/`, re-bundle via `./dev/release.py --bundle`
- Tests: `python3 -m unittest tests.test_line_loop -v`
- No walrus operators in comprehensions
