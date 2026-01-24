# Scope Management

> Adapt the plan when reality doesn't match expectations.

Plans change during execution. Menu changes document how to handle scope adjustments, discovered work, and requirement shifts without losing focus.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Found a bug while working | Create bead, continue current task |
| Task bigger than expected | Split into subtasks |
| Requirement changed | Update bead, adjust scope |
| Blocked by external | Create dependency, work on something else |

## The Kitchen Analogy

During service, the menu adapts:

1. **86'd item** - Ingredient ran out, substitute or remove
2. **Special request** - Customer needs modification
3. **VIP table** - Reprioritize the queue
4. **Equipment failure** - Work around the broken station

Line Cook handles these gracefully.

## File, Don't Block

The core principle: **Discoveries become beads, not interruptions.**

```bash
# While working on auth feature, found a bug in user service
# DON'T: Stop and fix the bug now
# DO: Create a bead and continue

bd create --title="Fix null check in user service" --type=bug --priority=1
# Continue with auth feature
```

Why this works:
- Maintains focus on current task
- Bug is tracked, won't be forgotten
- Context stays clean
- Can prioritize bug after current task

## Handling Scope Changes

### Task Bigger Than Expected

When a task expands beyond one session:

```bash
# Original task
bd show lc-042
# "Implement user authentication"

# Realized this needs splitting
bd create --title="Add password hashing" --type=task --parent=lc-042
bd create --title="Add session management" --type=task --parent=lc-042
bd create --title="Add login endpoint" --type=task --parent=lc-042

# Close original as parent, work children
bd close lc-042 --reason="Split into subtasks"
```

### Task Smaller Than Expected

When something is trivial:

```bash
# Just do it and close
# No need to split or create subtasks
bd close lc-042
```

### Task Blocked

When you can't proceed:

```bash
# Identify what's blocking
bd create --title="Get API credentials from ops team" --type=task

# Add dependency
bd dep add lc-042 lc-043  # 042 depends on 043

# Work on something else
bd ready  # See what's not blocked
/line:cook lc-044
```

## Requirement Changes

### Minor Clarification

Update the bead and continue:

```bash
bd update lc-042 --description "$(cat <<EOF
Original: Implement user auth
Clarified: Use JWT tokens, not sessions
- Token expiry: 1 hour
- Refresh token: 7 days
EOF
)"
```

### Major Pivot

If requirements change significantly:

```bash
# Close current task as won't-do
bd close lc-042 --reason="Requirements changed to OAuth-only"

# Create new task with new requirements
bd create --title="Implement OAuth authentication" --type=feature --priority=2
```

## Adding Discovered Work

### Found Bug

```bash
bd create --title="Fix: Null check missing in user lookup" \
    --type=bug \
    --priority=1

# If urgent, add note to current task
bd update lc-042 --description "$(cat <<EOF
...existing description...

Note: Found bug in user lookup (lc-045), should fix before merge
EOF
)"
```

### Found Tech Debt

```bash
bd create --title="Refactor: Extract auth logic to separate package" \
    --type=task \
    --priority=3  # Lower priority, not blocking
```

### Found Missing Feature

```bash
bd create --title="Add password reset flow" \
    --type=feature \
    --priority=2

# If blocking current work
bd dep add lc-042 lc-046  # Current depends on new
```

## Priority Adjustments

### Escalation

```bash
# Bug became critical
bd update lc-045 --priority=0  # P0: Critical

# Move to front of queue (will appear first in bd ready)
```

### De-escalation

```bash
# Feature can wait
bd update lc-042 --priority=3  # P3: Nice to have
```

### Parking Lot

For work that's not immediate priority:

```bash
# Create or find parking lot epic
bd create --title="Backlog" --type=epic

# Move tasks there
bd update lc-042 --parent=lc-backlog

# Tasks under parking lot epics are excluded from /prep auto-selection
```

## Mid-Task Pivots

Sometimes you realize mid-task that the approach is wrong:

### Approach Not Working

```bash
# Document what you learned
bd update lc-042 --description "$(cat <<EOF
...existing description...

## Attempt 1: JWT in cookies
- Tried: Store JWT in httpOnly cookie
- Problem: CORS issues with subdomain
- Learned: Need bearer token in header instead
EOF
)"

# Reset to clean state
git checkout .  # Discard changes

# Continue with new approach
# (keep same task, you're still solving the same problem)
```

### Wrong Task Entirely

```bash
# Close current as wrong approach
bd close lc-042 --reason="Wrong approach, see lc-047 for correct solution"

# Create correct task
bd create --title="Implement OAuth with bearer tokens" \
    --type=task \
    --description="Previous attempt (lc-042) used cookies, had CORS issues"
```

## Communication

### Updating Stakeholders

When significant changes happen:

```bash
# Update the epic with status
bd update lc-epic --description "$(cat <<EOF
...existing description...

## Status Update (2024-01-15)
- Completed: Auth middleware, token validation
- Changed: Switched from cookies to bearer tokens (CORS issues)
- Added: Password reset feature (lc-046)
- Blocked: Waiting on OAuth credentials
- ETA impact: +2 sessions due to scope additions
EOF
)"
```

### Commit Messages

Reflect changes in commits:

```bash
git commit -m "feat(auth): switch to bearer token auth

Previous approach using httpOnly cookies had CORS issues with
subdomain API calls. Bearer tokens in Authorization header
work consistently across all deployment configs.

Refs: lc-042"
```

## Anti-patterns

### Scope Creep Without Tracking

> "While I'm here, let me also add caching..."

Problem: Untracked work, task never completes.

Fix: Create a bead for the additional work.

### Blocking on Perfection

> "I can't close this until the error messages are perfect."

Problem: Task drags on forever.

Fix: Close when requirements met, file polish work separately.

### Hidden Pivots

> Changing approach without documenting why.

Problem: Future confusion about decisions.

Fix: Update bead description with rationale.

### Over-Filing

> Creating beads for every tiny observation.

Problem: Bead list becomes noise.

Fix: Only file actionable work items.

## Related

- [Priority and Dependencies](./priorities.md) - Deciding what to work on
- [Workflow](./workflow.md) - Standard execution flow
- [Context Management](./context-management.md) - Managing context during changes
