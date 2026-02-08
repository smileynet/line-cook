---
name: hybrid-patterns
description: When to use scripts vs agent reasoning in command design. Use when designing new commands, extracting scripted steps from existing commands, reviewing token efficiency, or planning automation boundaries.
---

# Hybrid Agent + Script Patterns

Guidelines for splitting work between deterministic scripts and agent reasoning in Line Cook commands.

## When to Use

- Designing new commands (choosing what to script vs what needs judgment)
- Extracting mechanical steps from existing commands into companion scripts
- Reviewing commands for token efficiency
- Planning automation or orchestration boundaries
- Evaluating whether a task needs an agent or a subprocess

## Quick Reference

### Decision Table

| Situation | Use Script | Use Agent |
|-----------|-----------|-----------|
| Outcome identical every time | Yes | No |
| Requires judgment or adaptation | No | Yes |
| Fixed validation sequence | Yes | Agent at checkpoints only |
| Collecting data for decisions | Yes (produce JSON) | Yes (consume JSON) |
| Error recovery with known fix | Yes | No |
| Error recovery needing diagnosis | No | Yes |
| Git/bead state checks | Yes | No |
| Code review or implementation | No | Yes |

### Core Principles (One-liners)

| Principle | Meaning |
|-----------|---------|
| Scripts handle structure; agents handle judgment | Deterministic work belongs in scripts, ambiguous work belongs in agents |
| Defense in depth | Cheapest validators run first (static > deterministic > test > LLM > human) |
| Idempotent writes | Scripts should be safe to re-run without side effects |
| Structured output contracts | Agents and scripts communicate via defined signal formats, not prose parsing |
| Start simple | Begin with agent-only, extract scripts when mechanical patterns emerge |
| Sandwich pattern | Script pre-conditions → agent reasoning → script post-conditions |

## Topics

### The Hybrid Sandwich

<details><summary>Script → Agent → Script orchestration pattern</summary>

The most effective hybrid pattern sandwiches agent reasoning between scripted pre-conditions and post-conditions:

```
┌─────────────────────────────┐
│  1. Script: Pre-flight      │  Validate environment, collect state,
│     (deterministic)         │  produce structured snapshot
├─────────────────────────────┤
│  2. Agent: Reasoning        │  Analyze snapshot, make decisions,
│     (judgment)              │  implement changes, adapt to context
├─────────────────────────────┤
│  3. Script: Post-flight     │  Validate output, commit, sync,
│     (deterministic)         │  emit structured signals
└─────────────────────────────┘
```

**Existing example:** `line-loop.py` implements this pattern at the iteration level — it manages process lifecycle (script), delegates task work to Claude sessions (agent), then parses structured signals and decides next steps (script).

**Key insight:** The script layers don't need to be separate files. They can be sections of a command prompt that instruct the agent to run specific shell commands before and after its reasoning work. The distinction is about *what decides* — the script dictates the exact commands, the agent decides what to do with the results.

</details>

### Structured Output Contracts

<details><summary>Signal formats for script-agent communication</summary>

Scripts and agents communicate through defined signal formats. These contracts let scripts parse agent output reliably without fragile regex on prose.

**Active signals in Line Cook:**

| Signal | Format | Producer | Consumer | Purpose |
|--------|--------|----------|----------|---------|
| `SERVE_RESULT` | Key-value block | serve command | line-loop.py | Review verdict (APPROVED/NEEDS_CHANGES/BLOCKED/SKIPPED) |
| `KITCHEN_COMPLETE` | Plain text marker | cook command | line-loop.py | Cook confidence (supporting signal only) |
| `KITCHEN_IDLE` | Plain text marker | cook command | line-loop.py | No actionable work available |
| `INTENT` / `BEFORE → AFTER` | Labeled key-value block | cook command | line-loop.py | Intent declaration with before/after state |
| `<phase_complete>` | XML tag | any command | line-loop.py | Early phase termination |

**Contract rules:**
1. Signal format is the API — changing it is a breaking change
2. Agents produce signals; scripts consume them
3. Signals must be unambiguous (no context needed to parse)
4. Supporting signals (like KITCHEN_COMPLETE) are never sufficient alone for critical decisions — always require a definitive signal

</details>

### Defense-in-Depth Guardrails

<details><summary>Five-layer validation ordering by cost</summary>

Validate in order of increasing cost. Each layer catches problems before burning more expensive resources:

| Layer | Type | Cost | Example |
|-------|------|------|---------|
| 1 | Static checks | Near-zero | File exists, env var set, git clean |
| 2 | Deterministic validation | Low | JSON schema, dependency graph cycles, bead state |
| 3 | Test execution | Medium | Unit tests, smoke tests, type checks |
| 4 | LLM review | High | Code review (serve), architecture audit |
| 5 | Human review | Highest | PR review, manual testing |

**Application:** A command like `cook` should verify kitchen equipment (layer 1-2) before letting the agent write code (layer 4). The `plate` command runs tests (layer 3) before asking agents to evaluate acceptance criteria (layer 4).

**Principle:** Never use an LLM to check something a script could check. If `git status` can tell you whether there are uncommitted changes, don't ask the agent to figure it out.

</details>

### Cost Control and Circuit Breakers

<details><summary>Preventing runaway token burn</summary>

Scripts provide hard boundaries that agents cannot override:

- **Timeouts:** `line-loop.py` enforces per-phase timeouts (configurable, default varies by phase). The agent cannot extend its own deadline.
- **Failure counters:** Circuit breaker trips after 5 consecutive failures in a 10-iteration window. Skip list activates after 3 failures per task.
- **Idle detection:** KITCHEN_IDLE signal triggers early loop termination when only parking-lot items remain.
- **Retry budgets:** Serve NEEDS_CHANGES allows max 2 cook retries within a single iteration before recording failure and moving on.

**Key insight:** These guardrails work because they're in the script layer, outside the agent's control. An agent inside a command cannot decide to ignore a timeout — the orchestrating script kills the process.

</details>

### When Scripts Should NOT Be Used

<details><summary>Tasks that require agent judgment</summary>

Not everything benefits from scripting. These tasks are fundamentally judgment-based:

| Task | Why It Needs an Agent |
|------|----------------------|
| Code implementation | Requirements are ambiguous; every codebase is different |
| Code review | Evaluating correctness requires understanding intent |
| Test design | Choosing what to test requires understanding risk |
| Error diagnosis | Root cause analysis needs contextual reasoning |
| Context presentation | Summarizing state for humans needs judgment about relevance |
| Adaptation to feedback | Serve NEEDS_CHANGES requires understanding *what* to change |

**Rule of thumb:** If you can write a deterministic spec for the output given the input, script it. If the output depends on judgment about the input's meaning, use an agent.

</details>

## Anti-Patterns

### Organized by Symptom

| Symptom | Name | Fix |
|---------|------|-----|
| Agent runs git/bd/file checks | Token Burn | Pre-flight script collects state |
| No scripts at all | Agent Maximalism | Extract mechanical steps |
| Script handles ambiguous cases | Script Maximalism | Let agent decide |
| Regex parsing agent prose | Regex Coupling | Structured signal contracts |
| Unbounded agent loop | No Circuit Breaker | Timeout + failure counter |
| Chose agents because fancy | Shiny Abstraction | Apply decision table |
| Validation in command AND script | Split Brain | Single source of truth |

### Anti-Pattern Deep Dives

<details><summary>Token Burn</summary>

**Symptom:** Agent spends tokens running `git status`, `bd show`, `bd ready`, file existence checks — operations with identical output every time.

**Cause:** Command prompt tells agent to "check the environment" without providing pre-collected state.

**Fix:** Add a pre-flight section that runs deterministic commands and feeds results to the agent as context. The agent reads the snapshot instead of running the commands itself.

**Example:**
```
# BAD: Agent burns tokens on git status
"First, check if there are uncommitted changes by running git status..."

# GOOD: Pre-flight collects state, agent reads it
"The current git state is: [pre-collected snapshot]
Based on this state, decide whether to..."
```

**Impact:** A typical `prep` command runs ~8 deterministic commands. At ~100 tokens per tool call overhead, that's 800 tokens per invocation that could be zero.

</details>

<details><summary>Agent Maximalism</summary>

**Symptom:** Every step of a workflow runs through agent reasoning, including steps that never vary. The command works but costs 10x more tokens than necessary.

**Cause:** It's easier to write "do X, then do Y" in a prompt than to build a companion script. The cost is invisible until you measure it.

**Fix:** Profile the command's mechanical ratio (see Line Cook Analysis below). Extract steps above 80% mechanical into a companion script or pre-flight section.

**Rule of thumb:** If you can predict the exact shell commands before reading any code, it's mechanical work.

</details>

<details><summary>Regex Coupling</summary>

**Symptom:** Scripts use fragile regex patterns to parse agent prose output. Breaks when agents rephrase slightly.

**Cause:** No structured signal contract between agent and script. The script tries to extract meaning from natural language.

**Fix:** Define explicit signal formats (like SERVE_RESULT). The agent emits the signal in a fixed format; the script parses the format, not the prose.

**Example:**
```
# BAD: Parsing prose
if re.search(r"(?:approved|looks good|lgtm)", output, re.I):
    verdict = "approved"

# GOOD: Parsing structured signal
serve_result = parse_serve_result(output)
if serve_result and serve_result.verdict == "APPROVED":
    ...
```

</details>

## Line Cook Analysis

### Existing Hybrid Patterns (What Works)

These patterns are already implemented and working:

- **`line-loop.py`** — Full sandwich pattern: script manages process lifecycle, delegates work to Claude sessions, parses structured signals to decide next steps
- **`menu-plan-to-beads.sh`** — Pure script for deterministic YAML→beads conversion, no agent needed
- **SERVE_RESULT contract** — Well-defined signal format with verdict, continue flag, and blocking issue count
- **Kitchen equipment verification** — Cook command checks tool availability before starting work
- **Multi-signal completion** — `check_task_completed()` requires definitive signals (bead closed, serve approved) rather than trusting supporting signals alone

### Mechanical Ratio by Command

Estimates of mechanical (scriptable) vs judgment work in each command. Higher mechanical ratio = greater script extraction opportunity.

| Command | Mechanical | Judgment | Script Opportunity |
|---------|-----------|----------|--------------------|
| prep | 85% | 15% | State snapshot producer (git, bd, file checks) |
| cook | 30% | 70% | Kitchen equipment runner (pre-flight tool checks) |
| serve | 20% | 80% | Diff collector (git diff, changed file list) |
| tidy | 75% | 25% | Git commit + bead sync sequence |
| plate | 70% | 30% | Test executor + artifact collector |
| plan-audit | 90% | 10% | Structural validator (dependency cycles, naming) |
| finalize | 85% | 15% | Already scripted (`menu-plan-to-beads.sh`) |
| architecture-audit | 80% | 20% | Metrics collector (file counts, complexity) |
| loop | 90% | 10% | Already a script (`line-loop.py`) |
| scope | 40% | 60% | Minimal — mostly judgment about work breakdown |
| brainstorm | 10% | 90% | Minimal — divergent thinking is fundamentally agent work |
| mise | 50% | 50% | Orchestration sequencing (brainstorm→scope→finalize) |
| decision | 60% | 40% | ADR file scaffolding + numbering |
| run | 95% | 5% | Already orchestration (prep→cook→serve→tidy→plate sequence) |
| help | 20% | 80% | Minimal — contextual help requires understanding intent |
| getting-started | 10% | 90% | Minimal — interactive guidance |
| smoke-test (dev) | 80% | 20% | Test execution sequence (project-local, not shipped) |

### Agents

| Agent | Mechanical | Judgment | Notes |
|-------|-----------|----------|-------|
| sous-chef | 10% | 90% | Code review is fundamentally judgment |
| taster | 15% | 85% | Test quality review requires understanding |
| maitre | 15% | 85% | Acceptance criteria review requires understanding |
| critic | 15% | 85% | E2E coverage review requires understanding |
| polisher | 20% | 80% | Code editing requires judgment, but follows patterns |

### Top Script Extraction Opportunities

Future work, ordered by impact (tokens saved × invocation frequency):

1. **Pre-flight environment validator** — Shared gate for cook/serve/tidy: git clean check, bd connectivity, tool availability
2. **State snapshot producer** (for prep) — Run all bd/git commands, produce JSON snapshot for agent to present
3. **Kitchen equipment runner** (for cook) — Verify tools, collect pre-conditions, produce readiness report
4. **Diff collector** (for serve) — Gather git diff, changed files, test results into structured bundle
5. **Structural plan validator** (for plan-audit) — Check dependency cycles, naming conventions, completeness
6. **Metrics collector** (for architecture-audit) — File counts, line counts, complexity metrics via static analysis

## Checklists

### New Command Design

- [ ] Estimate mechanical ratio — what percentage is deterministic?
- [ ] If mechanical ratio > 60%, design a companion script or pre-flight section
- [ ] Define pre-conditions the script collects before agent reasoning
- [ ] Define post-conditions the script validates after agent reasoning
- [ ] Specify signal contracts if the command produces output for other scripts
- [ ] Set timeouts appropriate to the command's expected duration
- [ ] Document the mechanical/judgment boundary in the command header

### Script Extraction Review

- [ ] Is the step truly deterministic? (Same input always produces same output)
- [ ] Does extracting it save meaningful tokens? (>100 tokens per invocation)
- [ ] Define the contract: what does the script produce, what does the agent consume?
- [ ] Can the script be tested independently from the agent?
- [ ] Is the script idempotent? (Safe to re-run without side effects)

### Cost Review

- [ ] Per-phase timeouts configured and appropriate
- [ ] Circuit breaker thresholds set (consecutive failures, window size)
- [ ] Idle detection enabled (KITCHEN_IDLE or equivalent)
- [ ] Retry budgets defined (max retries before skip/escalate)
- [ ] Escalation path defined (what happens when circuit breaker trips)

## See Also

- `core/line_loop/` — Reference implementation of script-agent orchestration
- `plugins/claude-code/scripts/menu-plan-to-beads.sh` — Pure script example
- `plugins/claude-code/scripts/line-loop.py` — Bundled loop script
- [Python Scripting skill](./../python-scripting/python-scripting.md) — HOW to write scripts (this skill covers WHEN)
- [Project Minimalism skill](./../project-minimalism/project-minimalism.md) — Complementary principles on avoiding over-engineering
- `docs/decisions/0009-autonomous-loop-as-external-package.md` — ADR on the script/agent split decision
