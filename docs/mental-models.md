# Mental Models for AI-Assisted Development

This document defines the core mental models that inform how Line Cook works. Understanding these concepts will help you get the most out of AI-assisted development workflows.

---

## 1. Sessions, Not Streams

**The insight:** AI context is finite. Treat AI interactions as bounded work sessions, not continuous conversations.

### The Problem

AI coding assistants don't have unlimited memory. Every message adds to the context window until it fills up, then older content gets dropped or summarized. If you treat an AI conversation like an endless stream of consciousness, you'll hit these problems:

- Important decisions made early get forgotten
- The AI loses track of what's been done vs what's planned
- Context fills with exploratory discussion instead of actionable work
- You can't pick up where you left off tomorrow

### The Solution

Work in **sessions**—bounded units of work with clear start and end points.

```
Session = Prep → Work → Verify → Commit → Push
```

Each session:
- **Starts clean** - Fresh context, synced with remote
- **Has one goal** - A single task or small set of related tasks
- **Ends with artifact** - Code pushed, issues filed, progress recorded
- **Leaves breadcrumbs** - Beads capture what was done and discovered

### How Beads Help

Beads are your memory between sessions. They persist:
- What needs to be done (open issues)
- What's blocked and why (dependencies)
- What was discovered along the way (filed findings)
- What's been completed (closed issues with context)

When you start a new session, `bd ready` shows you exactly where to pick up.

### Practical Implications

- **Clear context between tasks** - Start fresh for focused execution
- **One task per session** - Don't let scope creep fill your context
- **Push before stopping** - Work isn't done until it's on the remote
- **File discoveries as beads** - Don't trust your memory (or the AI's)

---

## 2. Planning vs Execution

**The insight:** Creative divergence and disciplined execution are different modes. Don't mix them.

### The Two Phases

**Planning phase (You + AI brainstorm):**
- Explore possibilities
- Ask clarifying questions
- Define scope and boundaries
- Create the work breakdown (beads)
- *This is where human judgment matters most*

**Execution phase (AI executes systematically):**
- Follow the plan
- One task at a time
- Verify before marking done
- File discoveries, don't act on them
- *This is where AI discipline shines*

### Why Separation Matters

Mixing planning and execution causes problems:

| Mixing Problem | What Happens |
|----------------|--------------|
| Mid-task scope changes | "While I'm here, let me also..." |
| Lost focus | Context fills with tangents |
| Incomplete verification | Rushing to the next idea |
| Unpushed work | Session ends without commit |

Keeping them separate provides:
- Clear handoff point between creative and mechanical work
- Fresh context for focused execution
- Natural checkpoints for review

### The Handoff

```
PLANNING                           EXECUTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Brainstorm ideas                   /prep - sync and survey
  ↓                                  ↓
Scope and prioritize               /cook - execute one task
  ↓                                  ↓
Create beads                       /serve - verify and review
  ↓                                  ↓
Clear context ─────────────────→   /tidy - commit and push
```

The `/mise` command helps with planning. Line Cook commands handle execution.

### Practical Implications

- **Brainstorm before beads** - Take multiple turns to clarify scope
- **Clear context after planning** - Start execution fresh
- **Don't redesign mid-cook** - File ideas as new beads instead
- **Complete the cycle** - Execution ends with push, not "good enough"

---

## 3. Progressive Trust

**The insight:** Start manual, add automation as confidence grows. Trust is earned through successful cycles.

### The Trust Ladder

```
MANUAL          You direct every action
   ↓
BEADS           Track work in issues, execute manually
   ↓
INDIVIDUAL      Run /prep, /cook, /serve, /tidy separately
   ↓
SERVICE         Run /service for full automated cycle
   ↓
AUTONOMOUS      Gas Town - goal-oriented agents
```

### Graduation Signals

Move up the ladder when you can answer "yes" to these questions:

**Beads → Individual Commands:**
- Have you successfully completed several beads manually?
- Do you understand what each Line Cook phase does?
- Can you recognize when something goes wrong?

**Individual → Service:**
- Have you run each command separately multiple times?
- Do you trust the review phase to catch issues?
- Are your beads well-scoped (single-session work)?

**Service → Autonomous:**
- Have you run many `/service` cycles successfully?
- Do your tests reliably catch regressions?
- Is your codebase well-structured and predictable?

### Why Not Start at the Top?

Skipping steps causes problems:
- You won't recognize failure modes
- You can't debug when things go wrong
- You may trust output that shouldn't be trusted
- Recovery is harder without understanding the parts

### Practical Implications

- **Start at the beginning** - Run commands separately first
- **Stay at a level until confident** - Don't rush to automate
- **Drop down when debugging** - Isolate problems by running phases separately
- **Trust verification, not vibes** - Tests pass, code compiles, then merge

---

## 4. Guardrails as Recovery

**The insight:** Each checkpoint is a recovery point. Nothing is irreversible until push.

### The Safety Net

Line Cook's phases aren't just workflow steps—they're checkpoints you can return to:

```
/prep      ← Safe to re-run anytime (just reads state)
    ↓
/cook      ← Changes are local, can discard and retry
    ↓
/serve     ← Review can reject, send back to cook
    ↓
/tidy      ← Last chance before push
    ↓
git push   ← Point of no return (but still recoverable via git)
```

### Recovery Paths

| Situation | Recovery |
|-----------|----------|
| Cook went wrong | `git checkout .` and re-run cook |
| Serve rejected | Fix issues, re-run serve |
| Forgot to file something | Run cook again with new findings |
| Pushed but found bug | New bead, new cycle |
| Context got messy | Clear context, start fresh with prep |

### The "File, Don't Block" Principle

When you discover something during execution:
1. **Don't stop** - Keep working on the current task
2. **Don't act** - The discovery is a new task, not a tangent
3. **Note it** - Capture in findings for tidy to file
4. **Continue** - Complete the current work

This prevents:
- Scope creep from good intentions
- Half-finished work from context switches
- Lost discoveries that never get tracked

### Why Checkpoints Matter

Traditional development has implicit checkpoints (save, commit, push). AI-assisted development needs explicit ones because:
- AI can make many changes quickly
- It's easy to lose track of what changed
- Verification is more important when output is generated
- Recovery is faster when you know where to roll back to

### Practical Implications

- **Run prep even if you think state is clean** - Verify assumptions
- **Review cook output before serve** - Catch obvious issues early
- **Treat serve rejection as normal** - It's doing its job
- **Push is the commitment** - Everything before is reversible

---

## Putting It Together

These mental models reinforce each other:

1. **Sessions** provide natural boundaries for work
2. **Planning vs Execution** defines what happens within sessions
3. **Progressive Trust** determines how much automation to use
4. **Guardrails** make it safe to experiment and recover

The workflow embodies all four:

```
You plan (creative) → You create beads (persistent memory)
    ↓
Clear context (session boundary)
    ↓
AI executes (disciplined) → Checkpoints at each phase
    ↓
Push (commitment) → Session complete, memory updated
```

### Common Patterns

**Starting a new project:**
1. Brainstorm with AI (planning mode)
2. Create epic and tasks as beads
3. Clear context
4. Run `/prep` → `/cook` → `/serve` → `/tidy` for each task
5. Graduate to `/service` when confident

**Picking up existing work:**
1. Run `bd ready` to see what's unblocked
2. Run `/prep` to sync and survey
3. Continue the cycle

**Recovering from problems:**
1. Identify which phase failed
2. Drop down to manual commands
3. Fix the issue
4. Resume from that checkpoint

---

## Summary

| Mental Model | Key Insight | Practical Implication |
|--------------|-------------|----------------------|
| Sessions, Not Streams | Context is finite | Clear between tasks, push before stop |
| Planning vs Execution | Different modes need separation | Brainstorm then execute, don't mix |
| Progressive Trust | Automation is earned | Start manual, add automation gradually |
| Guardrails as Recovery | Checkpoints enable safety | Each phase is a recovery point |

Understanding these models helps you:
- Work effectively within AI context limitations
- Know when to plan vs when to execute
- Build confidence in automation incrementally
- Recover quickly when things go wrong
