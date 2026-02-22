# Loop Cycle: Autonomous Execution

**Hands-free multi-task execution.**

The Loop Cycle repeats Run Cycles (prep → cook → serve → tidy) autonomously until no ready tasks remain or a stopping condition is met. It uses the same quality gates as manual `/line:run` — nothing is relaxed.

## Prerequisites

Before using Loop:
- You're comfortable with `/line:run` and understand each phase
- Tasks are well-scoped (single-session, clear acceptance criteria)
- Your project has strong tests that reliably catch regressions
- Dependencies between tasks are set up correctly

## What It Does

```
┌─────────────────────────────┐
│  Loop                       │
│  ┌───────────────────────┐  │
│  │  Run Cycle            │  │
│  │  prep→cook→serve→tidy │──┼──→ Task complete, pushed
│  └───────────────────────┘  │
│           ↓                 │
│     More ready tasks?       │
│      yes → repeat           │
│      no  → stop             │
└─────────────────────────────┘
```

Each iteration is a full Run Cycle with all quality gates. Loop just automates the "pick next task and go" decision.

## When to Use

**Good fit:**
- Batch of well-defined, independent tasks
- After Mise created a clean set of work
- Overnight or background execution
- Tasks that follow a proven pattern (e.g., "add command X" repeated for several commands)

**Bad fit:**
- Exploratory or ambiguous tasks
- Tasks requiring human design decisions
- First time working with a new codebase
- Tasks with complex interdependencies you haven't validated

## How to Start

```
/line:loop                    # Run until no ready tasks
/line:loop max-iterations=5   # Stop after 5 cycles
/line:loop start --cli kiro   # Use Kiro as the AI backend
```

The Loop supports both Claude Code (default) and Kiro as AI backends.

Loop will:
1. Run `/line:prep` to find the next ready task
2. Execute a full Run Cycle
3. If task completes and more tasks are ready, repeat
4. Stop when no ready tasks remain or max iterations reached

## Monitoring and Stopping

Loop logs each cycle's outcome. Watch for:
- **Task completion** — each pushed task is reported
- **Serve rejections** — Cook → Serve loops are normal, but repeated failures may indicate a problem
- **Blocked tasks** — if all remaining tasks are blocked, Loop stops

**To stop early:** Cancel the running command (Ctrl+C or equivalent).

## Safety

Loop uses the exact same quality gates as `/line:run`:
- Taster reviews tests during Cook
- Sous-chef reviews code during Serve
- Serve rejection sends back to Cook (not skipped)
- Each cycle ends with a push (checkpoint)

**If Serve repeatedly rejects:** Loop will stop rather than loop infinitely on a failing task.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Loop stops immediately | No ready tasks | Check `bd ready`, resolve blockers |
| Loop keeps failing on same task | Task is ambiguous or too large | Cancel, split the task, retry |
| Serve rejection loop | Code quality issues | Cancel, fix manually, retry |
| Wrong task picked | Priority or dependency issue | Use `bd update` to adjust, retry |
