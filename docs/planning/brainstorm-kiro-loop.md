# Brainstorm: Kiro Loop Support

> Exploration document from `/line:brainstorm` phase.

**Created:** 2026-02-18
**Status:** Ready for Planning

---

## Problem Statement

### What pain point are we solving?
The autonomous `line:loop` only works with Claude Code CLI. The `run_phase()` function in `phase.py` hardcodes `["claude", "-p", skill, "--dangerously-skip-permissions", "--output-format", "stream-json", "--verbose"]`. Users of Kiro CLI cannot use the autonomous loop even though Line Cook already has a complete Kiro plugin with prompts, agents, and steering files.

### Who experiences this pain?
Line Cook users who use Kiro CLI as their primary AI coding tool. Kiro is the third supported platform (alongside Claude Code and OpenCode), but it's the only one with a full plugin that can't use the loop.

### What happens if we don't solve it?
Kiro users are limited to manual `@line-prep` → `@line-cook` → `@line-serve` → `@line-tidy` cycles. They miss the productivity gains of autonomous batch execution, which is Line Cook's most differentiating feature.

---

## User Perspective

### Primary User
Line Cook users running Kiro CLI (`kiro-cli`) who want autonomous loop execution.

### User Context
- Already have Kiro CLI installed and configured
- Already have the Line Cook Kiro plugin set up (`plugins/kiro/`)
- Familiar with `@line-prep`, `@line-cook`, `@line-serve`, `@line-tidy` prompts
- May have run manual cycles via `@line-run`
- Want to run `@line-loop start` and have it work

### Success Criteria (User's View)
- `@line-loop start` launches the autonomous loop using `kiro-cli` instead of `claude`
- All phases (cook, serve, tidy, plate, close-service) execute via Kiro
- Signal detection works (KITCHEN_COMPLETE, SERVE_RESULT, KITCHEN_IDLE)
- Status monitoring works (`@line-loop watch`, `status`, `tail`)
- Retry, skip list, and circuit breaker work identically

---

## Technical Exploration

### Existing Patterns in Codebase

| Pattern | Location | Relevance |
|---------|----------|-----------|
| Phase execution (Claude-specific) | `core/line_loop/phase.py:181-190` | Hardcodes `claude` binary and flags — needs abstraction |
| Streaming JSON parsing | `core/line_loop/parsing.py` | Parses `stream-json` format — Kiro may not have this |
| Signal detection (text-based) | `core/line_loop/phase.py:233-257` | Scans text for KITCHEN_COMPLETE, SERVE_RESULT etc. — format-agnostic |
| Idle detection | `core/line_loop/phase.py:262-278` | Based on `last_action_time` from tool_use events — needs fallback |
| Kiro prompts | `plugins/kiro/prompts/*.md` | 17 prompts already mapped to `@line-*` pattern |
| Kiro agents | `plugins/kiro/agents/*.json` | 6 agent configs (line-cook, taster, sous-chef, etc.) |
| Platform conditionals | `dev/sync-commands.sh` | `@IF_KIRO@` / `@IF_NOT_KIRO@` template markers |
| Config constants | `core/line_loop/config.py` | Centralized configuration — good place for CLI config |

### External Approaches Researched

| Approach | Source | Trade-offs |
|----------|--------|------------|
| Kiro non-interactive mode | `kiro-cli chat --no-interactive --trust-all-tools "prompt"` | Works but no `--output-format stream-json` equivalent |
| Kiro prompt invocation | Use `@line-cook` as the prompt argument | Maps directly to existing Kiro prompts |
| Kiro hooks | AgentSpawn, PreToolUse, PostToolUse, Stop events | Could provide action tracking, but adds complexity |

### Constraints from Architecture

1. **No streaming JSON in Kiro CLI**: Kiro's `--no-interactive` mode outputs plain text to stdout. There is no `--output-format stream-json` equivalent documented.

2. **Prompt syntax differs**: Claude uses `/line:cook`, Kiro uses `@line-cook`. The prompt must be the full text, not a flag value.

3. **Permission flags differ**: Claude uses `--dangerously-skip-permissions`, Kiro uses `--trust-all-tools`.

4. **Bundling is Claude Code only**: The bundled `line-loop.py` lives in `plugins/claude-code/scripts/`. For Kiro, the loop runs from `core/line_loop/` package directly (or a separate bundle).

5. **Action tracking depends on streaming JSON**: Without it, we lose per-tool-call visibility but can still track output activity.

---

## Technical Approaches Considered

### Option A: CLI Driver Abstraction
**Description:** Create a driver abstraction that encapsulates all CLI-specific behavior: command construction, output format, parsing strategy, and signal detection. Each supported CLI implements the driver interface.

**Pros:**
- Clean separation of concerns
- Easy to add more CLIs (OpenCode, future tools)
- Each driver handles its own output parsing quirks
- Testable in isolation

**Cons:**
- More code and complexity than needed for two CLIs
- Over-engineering risk if Kiro is the only addition
- Requires refactoring existing phase.py significantly

**Effort:** High

### Option B: Config-Driven CLI Selection
**Description:** Add CLI configuration to `config.py` that specifies the binary name, prompt format, permission flags, and output mode. `phase.py` reads these config values instead of hardcoded strings. Output parsing degrades gracefully when streaming JSON is unavailable.

**Pros:**
- Minimal code changes — config values replace hardcoded strings
- Graceful degradation: signal detection works on plain text, action tracking becomes best-effort
- Easy to understand and maintain
- Config can be set via CLI flag (`--cli kiro`) or environment variable

**Cons:**
- Doesn't cleanly handle fundamentally different output formats
- May accumulate if-else branches for CLI-specific behavior
- Less composable than driver pattern

**Effort:** Medium

### Option C: Kiro-Specific Fork of phase.py
**Description:** Create `phase_kiro.py` alongside `phase.py` with Kiro-specific subprocess invocation. Loop selects which module to use based on config.

**Pros:**
- No risk of breaking existing Claude loop
- Can optimize each implementation independently
- Simple mental model

**Cons:**
- Code duplication — most of phase.py is CLI-agnostic (idle detection, timeout handling, signal scanning)
- Maintenance burden: changes must be applied to both files
- Violates DRY

**Effort:** Medium (but ongoing cost is high)

---

## Risks and Unknowns

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Kiro non-interactive output format unknown | M | H | Test `kiro-cli chat --no-interactive` locally to see actual output |
| No streaming JSON = no action tracking | H | M | Use line-based output scanning as fallback; track "any output" for idle detection |
| Kiro `@prompt` syntax may not work as CLI argument | M | H | Test `kiro-cli chat --no-interactive "@line-cook"` vs passing prompt text directly |
| Kiro agent context not loading in non-interactive mode | M | H | Test if `--agent line-cook` flag works with non-interactive |

### Dependency Risks
- Kiro CLI must be installed and authenticated (`kiro-cli login`)
- Kiro CLI behavior in non-interactive mode is not extensively documented
- Kiro CLI is newer and may have breaking changes between versions

### Scope Risks
- Tempting to also add OpenCode loop support — defer that
- Tempting to add Kiro hooks integration for action tracking — defer to future enhancement
- Loop prompt dispatch is the real Kiro-specific adaptation

### Open Questions (Resolved)

- [x] Does Kiro CLI have streaming JSON output? **No** — not documented, not available
- [x] What does `kiro-cli chat --no-interactive` output? **Parseable plain text** — tool actions show `(using tool: name)` with `✓`/`✗` result and timing. Agent text prefixed with `> `. ANSI codes present but strippable. stderr has banner/chrome (redirect to DEVNULL).
- [x] Does `--agent line-cook` work with `--no-interactive`? **Yes** — confirmed working, agent loads steering files and tools.
- [x] Can Kiro load steering files in non-interactive mode? **Yes** — confirmed, steering context loads.
- [x] Does `@prompt-name` work as input argument? **Yes** — `@line-prep` as the input argument executed the full prep workflow.
- [ ] Does Kiro `--resume` work for session continuity within loop iterations? Flag exists but untested for chaining.

### Kiro Output Format (from testing)

**Tool action pattern:**
```
<tool description> (using tool: <tool_name>)
 ✓ <success message>
 - Completed in <N>s
```

**Agent text:** Prefixed with `> `

**Example:**
```
> I'll read the file.
Reading file: /path/to/file.md, from line 1 to 5 (using tool: read)
 ✓ Successfully read 420 bytes from /path/to/file.md
 - Completed in 0.4s
I will run the following command: echo done (using tool: shell)
Purpose: Run echo command
done
 - Completed in 0.36s
> Done. Here are the results.
```

**Implications for action tracking:** We CAN parse tool names, success/failure, and timing from Kiro output — just need a different parser (regex-based on plain text vs JSON event parsing).

---

## Recommended Direction

### Chosen Approach
**Option B: Config-Driven CLI Selection** — with graceful degradation for output parsing.

### Rationale
1. **Minimum viable change**: The core loop logic (iteration, retry, skip list, circuit breaker, epic branches) is already CLI-agnostic. Only `phase.py`'s subprocess invocation and output parsing are Claude-specific.

2. **Signal detection is text-based**: The signals we care about (KITCHEN_COMPLETE, SERVE_RESULT, KITCHEN_IDLE, phase_complete) are embedded in the agent's text output by the prompts themselves. These work regardless of output format.

3. **Action tracking is possible**: Kiro outputs tool actions as `(using tool: name)` with `✓`/`✗` results and timing. A regex-based parser can extract this alongside Claude's JSON parser. Idle detection can track stdout activity (any output = not idle).

4. **Config is natural**: Adding `--cli kiro` to the CLI argparse is straightforward. The config propagates through `run_loop()` → `run_iteration()` → `run_phase()`.

### Implementation Sketch

**Config additions:**
```python
# CLI profiles
CLI_PROFILES = {
    'claude': {
        'binary': 'claude',
        'prompt_flag': '-p',
        'prompt_format': '/line:{phase}',  # /line:cook, /line:serve
        'permission_flags': ['--dangerously-skip-permissions'],
        'output_flags': ['--output-format', 'stream-json', '--verbose'],
        'has_streaming_json': True,
    },
    'kiro': {
        'binary': 'kiro-cli',
        'prompt_flag': None,  # prompt is positional in chat subcommand
        'prompt_format': '@line-{phase}',  # @line-cook, @line-serve
        'permission_flags': ['--trust-all-tools'],
        'output_flags': [],
        'has_streaming_json': False,
        'subcommand': 'chat',
        'extra_flags': ['--no-interactive'],
    },
}
```

**phase.py changes:**
- `run_phase()` accepts a `cli_profile` dict
- Constructs command from profile instead of hardcoded values
- When `has_streaming_json` is False, uses regex-based parser for `(using tool: name)` pattern
- Idle detection uses "time since last stdout line" as fallback

**parsing.py additions:**
- `parse_kiro_tool_action(line)` — extracts tool name from `(using tool: name)` pattern
- `parse_kiro_tool_result(line)` — extracts success/failure from `✓`/`✗`
- `strip_ansi(text)` — removes ANSI escape codes from Kiro output

### Suggested Scope
| Scope | Recommendation |
|-------|----------------|
| MVP | Config-driven CLI selection, phase execution with Kiro, text-based signal detection, line-based idle fallback |
| Full Feature | Kiro hooks integration for action tracking, `--agent` flag support, session resume |
| Epic | Multi-CLI support framework (Claude, Kiro, OpenCode), unified action tracking API |

### Deferred Items
- OpenCode loop support (similar problem, different CLI)
- Kiro hooks integration (AgentSpawn, PreToolUse, PostToolUse for richer integration)
- Session resume (`--resume`) between loop iterations for context continuity
- Bundling line-loop.py for Kiro plugin (currently only Claude Code has the bundle)
- ANSI stripping optimization (could use a library vs regex chain)

---

## Next Steps

- [ ] Resolve open questions via local testing of `kiro-cli chat --no-interactive`
- [ ] Proceed to `/line:scope` to create structured breakdown
- [ ] Test prototype with a single phase before full integration
