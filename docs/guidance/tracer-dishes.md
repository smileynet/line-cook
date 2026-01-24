# Tracer Dishes

> Build vertical slices through all layers, then expand incrementally.

The tracer bullet methodology proves an approach works before investing in full implementation. Like a tracer round showing where bullets will land, a tracer dish validates the complete path from user action to result.

## Quick Reference

| Approach | When to Use | Output |
|----------|-------------|--------|
| **Tracer** | Building feature foundation | Production code |
| **Prototype** | Testing ideas for stakeholders | Demo/throwaway |
| **Spike** | Learning new technology | Research notes |

**Most Line Cook tasks should be tracers** - production code that builds incrementally.

## The Kitchen Analogy

Before cooking a 12-course tasting menu:

1. **Mise en place** - Validate ingredients and equipment work
2. **First course** - Prove the complete plating → service → guest experience flow
3. **Expand** - Add courses using the proven pattern

Don't prep all 12 courses, then discover your oven is broken.

## Tracer Strategy

Every feature needs a tracer strategy:

```yaml
tracer_strategy:
  minimal_flow: "Step 1 → Step 2 → Step 3"
  layers: "Layer 1 → Layer 2 → Layer 3"
  expansion: "Items deferred to later tasks"
```

### minimal_flow

The simplest end-to-end path that proves the feature works:

```
# Example: Authentication feature
minimal_flow: "Config → Middleware → Single endpoint"
```

This proves: config loading works, middleware intercepts requests, endpoint validates correctly.

### layers

The architectural layers touched by this feature:

```
# Example: Database feature
layers: "CLI → Service → Repository → Database"
```

Each layer must be touched in the tracer. If you skip layers, you're not proving the full path.

### expansion

What gets added after the tracer works:

```
# Example: Authentication feature
expansion: "Additional endpoints, token refresh, rate limiting"
```

These are deferred intentionally - they use the proven pattern.

## When to Use What

### Tracer (Production Task)

Use when building feature foundation:

- You know the approach will work
- Building production-quality code
- Feature needs end-to-end validation

```yaml
- title: "Implement minimal auth flow"
  tracer: "Proves authentication pattern works"
  description: |
    - Config loading for auth settings
    - Middleware for JWT validation
    - Single protected endpoint
  tdd: true
```

### Spike (Research Task)

Use for learning and exploration:

- Unfamiliar technology
- Multiple approaches to evaluate
- Need to understand constraints

```yaml
- title: "Research webhook delivery patterns"
  type: task  # or spike
  description: |
    - Compare at-least-once vs at-most-once
    - Evaluate retry strategies
    - Document findings in research/ directory
```

### Prototype (Demo/Throwaway)

Use sparingly - only when:

- Stakeholder needs to see something before committing
- Visual/UX validation required
- Explicitly throwaway (will not become production code)

**Warning:** Prototypes rarely get rewritten. If you might use the code, make it a tracer.

## Horizontal vs Vertical Slicing

```
Horizontal (bad):
  Task 1: Build database layer
  Task 2: Build API layer
  Task 3: Build UI layer

Vertical (good):
  Task 1: Minimal flow through all layers (tracer)
  Task 2: Second feature using same layers
  Task 3: Enhancement to proven pattern
```

### Why Horizontal Fails

- Discover integration issues late
- Can't demo to users until all layers done
- Large batch = large risk

### Why Vertical Works

- Integration proven in first task
- Can demo after each task
- Small batch = small risk

## Tracer Anti-patterns

### All Prep, No Integration

> "Let's build the entire data layer first, then worry about the API."

Result: Integration issues discovered at the end.

Fix: Each task must touch all layers.

### Skipping Tests Until Done

> "I'll write the tests after the implementation is complete."

Result: Tests don't drive design; edge cases missed.

Fix: Write failing test first (see [TDD/BDD Workflow](./tdd-bdd.md)).

### Scope Creep in Tracer

> "The tracer should also handle caching, logging, and metrics."

Result: Tracer proves too much; takes too long.

Fix: Keep tracer minimal. Add features in expansion tasks.

### Prototype That Became Production

> "We just need a quick prototype... okay let's ship it."

Result: Fragile code, technical debt.

Fix: If code might ship, build it as a tracer from the start.

## Example: Auth Feature

**Bad (horizontal):**

```yaml
tasks:
  - title: "Build auth database schema"
  - title: "Build auth API endpoints"
  - title: "Build auth UI"
```

**Good (tracer):**

```yaml
tracer_strategy:
  minimal_flow: "Login form → API → Session → Protected page"
  layers: "UI → API → Auth service → Database"
  expansion: "Registration, password reset, OAuth"

tasks:
  - title: "Minimal login flow (tracer)"
    tracer: "Proves auth pattern works end-to-end"
    description: |
      - Basic login form (username/password)
      - Single API endpoint for auth
      - Session creation in database
      - One protected page
  - title: "Add registration"
    depends_on: ["Minimal login flow"]
    description: "Apply proven auth pattern to registration"
  - title: "Add OAuth providers"
    depends_on: ["Add registration"]
    description: "Extend pattern for external auth"
```

## Validation Checklist

Before starting a task, verify:

- [ ] Tracer touches all architectural layers
- [ ] Minimal flow is truly minimal (can't remove anything)
- [ ] Expansion list is defined (what comes later)
- [ ] TDD is enabled (test proves the tracer works)

## Related

- [TDD/BDD Workflow](./tdd-bdd.md) - How tests prove tracers work
- [Menu Changes](./menu-changes.md) - Restructuring work during execution
- [Order Priorities](./order-priorities.md) - Sequencing tracer tasks
