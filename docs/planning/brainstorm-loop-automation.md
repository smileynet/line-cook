# Brainstorm: Loop Automation (Ralph Wiggum-style)

> Exploration document from `/line:brainstorm` phase.

**Created:** 2026-01-31
**Status:** Ready for Planning

---

## Problem Statement

### What pain point are we solving?
Line Cook currently executes one task per `/line:run` invocation. Users must manually restart the workflow after each task completes, which breaks flow and prevents overnight/background execution of well-defined work.

### Who experiences this pain?
Developers using Line Cook for:
- Large refactoring across many files (hundreds of similar changes)
- Test coverage expansion (file-by-file coverage improvement)
- Documentation generation (systematic docstring additions)
- Migration work (framework/API version bumps)

### What happens if we don't solve it?
- Manual intervention required between each task
- Cannot leverage "overnight coding" patterns
- Competitive disadvantage vs. tools with loop support (Ralph Wiggum, Continuous Claude)
- Context switching interrupts developer focus

---

## User Perspective

### Primary User
Developer running Line Cook for batch/mechanical tasks with clear success criteria.

### User Context
- Already familiar with Line Cook's planning and execution phases
- Has a set of well-scoped tasks in beads (created via `/line:scope` and `/line:finalize`)
- Wants to execute multiple tasks without babysitting each one
- Trusts the quality gates (tests, reviews) to catch issues

### Success Criteria (User's View)
1. Start a loop, walk away, return to completed work
2. All tasks executed follow the same quality standards as single runs
3. Clear progress tracking (which tasks completed, which failed)
4. Graceful handling of failures (don't blow through API credits on stuck work)
5. Easy to stop mid-loop if needed

---

## Technical Exploration

### Existing Patterns in Codebase

| Pattern | Location | Relevance |
|---------|----------|-----------|
| Single-task orchestration | `commands/run.md` | Foundation to build on - already chains prep→cook→serve→tidy |
| Phase chaining with Skill() | `commands/run.md:43-68` | Uses `Skill()` tool to invoke commands sequentially |
| Bead status tracking | `commands/prep.md:52-80` | Uses `bd ready` to find available tasks |
| Quality gates | `commands/cook.md:165-180` | Stops on test failures, build failures |
| Structured output signals | `commands/serve.md:95-110` | Parseable verdict blocks for decisions |
| Findings tracking | `commands/tidy.md:45-75` | Files new beads from discovered work |

### External Approaches Researched

| Approach | Source | Trade-offs |
|----------|--------|------------|
| **Ralph Wiggum (Stop Hook)** | [Anthropic Plugin](https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md) | Elegant (uses hooks), but requires prompt-level completion detection which is unreliable |
| **ralph-claude-code (Dual Gate)** | [frankbria/ralph-claude-code](https://github.com/frankbria/ralph-claude-code) | Robust (heuristic + explicit signal), but complex state tracking |
| **Continuous Claude (PR Loop)** | [AnandChowdhary/continuous-claude](https://github.com/AnandChowdhary/continuous-claude) | Git-native persistence, but designed for single-prompt iteration not task lists |
| **TDD Ralph Loop** | [MarioGiancini/ralph-loop-setup](https://github.com/MarioGiancini/ralph-loop-setup) | TDD focus aligns with cook phase, but overlaps with existing cook TDD cycle |

### Constraints from Architecture

1. **Commands are markdown files** - Loop logic must fit command/skill pattern
2. **Beads track tasks** - Natural stopping condition: `bd ready` returns empty
3. **Quality gates already exist** - Must preserve test/review/commit checks
4. **Session boundaries matter** - Context grows over iterations; may need clearing
5. **Git-native persistence** - Work persists via commits, not memory files

---

## Technical Approaches Considered

### Option A: `/line:loop` Command (Orchestrator Pattern)

**Description:** New command that wraps `/line:run` in a loop, checking for more ready tasks after each completion.

**Implementation:**
```markdown
## Process

1. Check `bd ready` for available tasks
2. If empty → output summary, exit
3. Call Skill("line:run")
4. Check result status (pass/fail)
5. If pass → goto 1
6. If fail → decide: continue or stop
7. Repeat until no tasks or max iterations
```

**Pros:**
- Uses existing building blocks (`/line:run` unchanged)
- Clean separation of concerns (loop logic separate from execution)
- Simple mental model ("run keeps running")
- Beads provide natural termination (no tasks = done)

**Cons:**
- Relies on prompt-level loop (Claude executing steps)
- Context accumulates over iterations (may hit limits)
- No external process to catch crashes

**Effort:** Low

### Option B: Shell Script Wrapper (External Loop)

**Description:** Bash script that calls `claude --skill line:run` in a while loop, parsing exit codes.

**Implementation:**
```bash
#!/bin/bash
while true; do
  ready=$(bd ready --count)
  [[ $ready -eq 0 ]] && break
  claude --skill line:run
  [[ $? -ne 0 ]] && break
done
```

**Pros:**
- External process survives Claude crashes
- Fresh context each iteration (no accumulation)
- Can add cost/time limits easily
- Follows Continuous Claude pattern

**Cons:**
- Breaks the "all-in-Claude" plugin model
- Requires shell setup, not just command invocation
- Harder to integrate with hooks system
- User must manage script separately

**Effort:** Medium

### Option C: Stop Hook Pattern (Ralph Wiggum Style)

**Description:** Implement a Claude Code Stop hook that intercepts exit and re-invokes `/line:run` if tasks remain.

**Implementation:**
- Hook at `hooks/stop.sh` intercepts Claude exit
- Checks `bd ready --count`
- If tasks remain, re-prompts with original task
- If empty, allows exit

**Pros:**
- Truly autonomous (no user intervention)
- Matches popular Ralph Wiggum pattern
- Fresh session each iteration (context reset)
- Leverages Claude Code's hook system

**Cons:**
- Hooks are shell scripts (platform concerns)
- Less visible what's happening (magic feeling)
- Harder to add guardrails (max iterations, cost limits)
- Exit detection is implicit, not explicit

**Effort:** Medium

### Option D: Hybrid (Command + Optional Hook)

**Description:** `/line:loop` command for in-session chaining, with optional stop hook for multi-session persistence.

**Pros:**
- Flexibility: use command for quick loops, hook for overnight runs
- Progressive disclosure: start simple, add power later
- Best of both worlds

**Cons:**
- More to document and maintain
- User confusion about which to use when

**Effort:** Medium-High

---

## Risks and Unknowns

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Context overflow in long loops | Medium | High | Max iterations limit; clear session between cycles |
| API cost runaway | Medium | High | Cost limit flag; iteration limit; warnings |
| Stuck loop (task keeps failing) | Medium | Medium | Consecutive failure limit; skip-and-continue option |
| Completion false positive | Low | Medium | Rely on test results, not self-assessment |

### Dependency Risks
- Beads (`bd` commands) must be reliable for task counting
- Claude Code hooks API must be stable (if using Option C)

### Scope Risks
- Feature creep: adding scheduling, parallel execution, distributed loops
- Should start minimal (just iterate on `/line:run`) and expand

### Open Questions

- [x] How does context accumulation affect long loops? → Mitigate with iteration limits, consider fresh sessions
- [x] Can we detect "stuck" loops? → Consecutive failure counting
- [x] Should we support "skip on failure" vs "stop on failure"? → **Stop on failure** (safer, investigate issues)
- [ ] What's the right default max-iterations? (10? 25? 50?)
- [x] Should loop show real-time progress or just final summary? → **Task-by-task progress** (shows momentum)

---

## Recommended Direction

### Chosen Approach
**Option A: `/line:loop` Command** - Start with the simplest viable approach.

### Rationale
1. **Minimal new code** - Wraps existing `/line:run`, doesn't duplicate logic
2. **Beads as termination** - Natural completion when `bd ready` is empty
3. **Preserves quality gates** - Every iteration runs full prep→cook→serve→tidy
4. **Fits mental model** - "Loop keeps running until done" is intuitive
5. **Easy to enhance** - Can add max-iterations, failure handling, progress tracking
6. **Avoids magic** - No hidden hooks, explicit command invocation

Later phases can add:
- Stop hook for true overnight automation (Option C add-on)
- Shell wrapper for enterprise/CI scenarios (Option B add-on)

### Suggested Scope

| Scope | Recommendation |
|-------|----------------|
| MVP | `/line:loop` command that calls `/line:run` until no tasks ready |
| Full Feature | Add `--max-iterations`, stop-on-failure behavior (default), task-by-task progress output |
| Epic | Add stop hook, cost tracking, parallel execution, scheduling |

### Deferred Items
- Stop hook automation (Phase 2)
- Shell script wrapper (if needed for CI)
- Cost/budget limits (requires API integration)
- Parallel task execution (complex, different paradigm)
- Scheduling/cron integration

---

## Next Steps

- [x] Resolve open questions (key ones answered)
- [ ] Proceed to `/line:scope` to create structured breakdown
- [ ] Decide on MVP vs Full Feature scope

---

## Sources

Research sources consulted:

- [Anthropic Ralph Wiggum Plugin](https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md)
- [ralph-claude-code by frankbria](https://github.com/frankbria/ralph-claude-code)
- [Continuous Claude by AnandChowdhary](https://github.com/AnandChowdhary/continuous-claude)
- [Ralph Wiggum Technique Explained - Paddo.dev](https://paddo.dev/blog/ralph-wiggum-autonomous-loops/)
- [The Register - Ralph Wiggum Coverage](https://www.theregister.com/2026/01/27/ralph_wiggum_claude_loops/)
- [Awesome Claude Code](https://awesomeclaude.ai/ralph-wiggum)
