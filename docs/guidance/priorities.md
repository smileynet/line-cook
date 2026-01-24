# Priority and Dependencies

> Work on the right things in the right order.

Priority and dependency management ensures important work happens first and blocking work gets resolved before dependent work begins.

## Quick Reference

| Priority | Level | When to Use |
|----------|-------|-------------|
| **P0** | Critical | Production broken, security issue |
| **P1** | High | Blocks other work, time-sensitive |
| **P2** | Medium | Standard work, not blocking |
| **P3** | Low | Nice to have, can wait |
| **P4** | Backlog | Maybe someday |

## The Kitchen Analogy

Order priority in a restaurant:

1. **Fire tickets** - Tables waiting, need food now
2. **VIP orders** - Important guests, prioritize
3. **Normal flow** - Standard tickets in order
4. **Prep work** - When there's a lull

Line Cook follows the same principle: urgent first, then important, then everything else.

## Priority Levels

### P0: Critical

**Use for:**
- Production outages
- Security vulnerabilities
- Data corruption risks
- Broken builds blocking all work

**Characteristics:**
- Drop everything to fix
- All hands if needed
- Immediate notification

```bash
bd create --title="CRITICAL: Auth bypass in API" --type=bug --priority=0
```

### P1: High

**Use for:**
- Blocking other work
- Customer-facing bugs
- Time-sensitive features
- Breaking changes in main

**Characteristics:**
- Top of the queue
- Work on today
- May need to pause other work

```bash
bd create --title="Fix: Login fails after password change" --type=bug --priority=1
```

### P2: Medium (Default)

**Use for:**
- Standard feature work
- Non-critical bugs
- Technical improvements
- Documentation updates

**Characteristics:**
- Normal priority
- Work in order
- Most tasks are P2

```bash
bd create --title="Add email verification" --type=feature --priority=2
```

### P3: Low

**Use for:**
- Polish and refinement
- Convenience features
- Optional improvements
- Tech debt (non-blocking)

**Characteristics:**
- When P2 queue is empty
- Can wait indefinitely
- Nice to have

```bash
bd create --title="Improve error messages" --type=task --priority=3
```

### P4: Backlog

**Use for:**
- Ideas for later
- Deferred decisions
- Maybe someday items

**Characteristics:**
- Rarely worked
- Review periodically
- May never happen

```bash
bd create --title="Consider GraphQL API" --type=feature --priority=4
```

## Dependencies

Dependencies define what must complete before something can start.

### Types of Dependencies

**Task depends on task:**

```bash
# Task B depends on Task A (A must complete before B starts)
bd dep add lc-B lc-A
```

**Feature depends on feature:**

```bash
# Feature uses parent blocking in menu plans
# See menu-plan-format.md for details
```

### Viewing Dependencies

```bash
# See what blocks this task
bd show lc-042
# Blocked by: lc-041

# See all blocked items
bd blocked

# See what this blocks
bd show lc-041
# Blocks: lc-042, lc-043
```

### Resolving Dependencies

When a blocking task completes:

```bash
bd close lc-041
# lc-042 and lc-043 are now unblocked

bd ready  # Will now show lc-042, lc-043
```

## Auto-Selection

Line Cook's `/prep` and `/cook` commands auto-select tasks based on:

1. **Not blocked** - No open dependencies
2. **Highest priority** - P0 > P1 > P2 > P3 > P4
3. **Epic focus** - Prefers tasks in current epic
4. **Creation order** - Earlier created first (tie-breaker)

### Manual Override

To work on a specific task:

```bash
/line:cook lc-042  # Explicit selection
```

### Parking Lot Exclusion

Tasks under "Backlog" or "Retrospective" epics are excluded from auto-selection:

```bash
# Create parking lot epic
bd create --title="Backlog" --type=epic

# Move task there
bd update lc-099 --parent=lc-backlog

# Task won't appear in /prep or auto-select
# But can still be worked explicitly
/line:cook lc-099
```

## Priority Guidelines

### Escalation Criteria

**Escalate to P0:**
- Production impact affecting users
- Security vulnerability
- Data integrity at risk

**Escalate to P1:**
- Blocking multiple people
- Customer escalation
- Deadline approaching

### De-escalation Criteria

**De-escalate to P3:**
- Found workaround
- Less impact than thought
- No immediate need

**Move to Backlog (P4):**
- Requirements changed
- May not ever do
- Nice to have, not need to have

### Example Escalation

```bash
# Original: P2 bug
bd show lc-042
# Priority: P2

# Customer reported same bug, escalate
bd update lc-042 --priority=1

# Becomes critical (production broken)
bd update lc-042 --priority=0
```

## Dependency Strategies

### Tracer-Based Dependencies

Order tasks as tracer bullets:

```bash
# Tracer proves pattern
bd create --title="Minimal auth flow" --type=task
# -> lc-041

# Expansion depends on tracer
bd create --title="Add OAuth providers" --type=task
bd dep add lc-042 lc-041
```

### Layer-Based Dependencies

When dependencies follow architectural layers:

```bash
# Database first
bd create --title="Add users table" --type=task
# -> lc-041

# Service depends on database
bd create --title="User service" --type=task
bd dep add lc-042 lc-041

# API depends on service
bd create --title="User API endpoints" --type=task
bd dep add lc-043 lc-042
```

### Avoiding Circular Dependencies

```bash
# BAD: A depends on B, B depends on A
bd dep add lc-A lc-B
bd dep add lc-B lc-A  # Error: would create cycle

# FIX: Break into smaller pieces
bd create --title="Shared interface" --type=task  # lc-C
bd dep add lc-A lc-C
bd dep add lc-B lc-C
```

## Anti-patterns

### Everything is P0

> "All my tasks are critical!"

Problem: If everything is critical, nothing is.

Fix: Reserve P0 for actual emergencies. Most work is P2.

### No Dependencies

> "I'll just remember the order."

Problem: Wrong order causes rework.

Fix: Explicitly add dependencies for ordering.

### Over-Dependencing

> "Everything depends on everything."

Problem: Nothing can start, queue is blocked.

Fix: Only add necessary dependencies. Use priority for soft ordering.

### Priority Inflation

> Starting all tasks at P1 "just in case."

Problem: Priority loses meaning.

Fix: Start at P2, escalate only when needed.

## Visualizing Priority Queue

```bash
# See what's ready to work (not blocked, sorted by priority)
bd ready

# Example output:
# P0: [lc-099] CRITICAL: Production auth broken
# P1: [lc-042] Fix login after password change
# P2: [lc-045] Add email verification
# P2: [lc-046] Improve error messages

# See what's blocked
bd blocked

# Example output:
# [lc-047] Add OAuth (blocked by lc-042)
# [lc-048] Add 2FA (blocked by lc-042, lc-046)
```

## Related

- [Workflow](./workflow.md) - How priorities fit in execution
- [Scope Management](./scope-management.md) - Adjusting priorities during work
- [Context Management](./context-management.md) - Managing what's in progress
