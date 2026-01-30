---
description: Create structured work breakdown (convergent thinking)
---

## Summary

**Convergent thinking phase: structure, scope, decompose.** Second phase of mise en place.

This phase transforms exploration into a structured, reviewable plan. Output is a YAML menu plan that can be converted to beads.

**Input:** Brainstorm document (optional) or direct requirements
**Output:** `docs/planning/menu-plan.yaml`

**STOP after creating menu plan.** Wait for user approval before committing.

---

## Process

### Step 1: Load Context

Check for existing brainstorm document:

```bash
ls docs/planning/brainstorm-*.md 2>/dev/null
```

**If brainstorm exists:** Read it and use as input for planning.
**If no brainstorm:** Ask user for requirements directly.

### Step 2: Determine Scope

| Scope | Sessions | When to use |
|-------|----------|-------------|
| **Task** | <1 | Simple, clear deliverable |
| **Feature** | 1-3 | User-observable capability |
| **Epic** | 3+ | Multiple features, large effort |

### Step 3: Create Menu Plan

**Create `docs/planning/menu-plan.yaml`:**

```yaml
phases:
  - id: phase-1
    title: "Phase 1: Foundation"
    description: "Core infrastructure"

    features:
      - id: feature-1.1
        title: "Feature 1.1: <user-facing capability>"
        priority: 2
        user_story: "As a <role>, I want to <action> so that <benefit>"
        acceptance_criteria:
          - "Can do X"
          - "Can do Y"
          - "Handles error Z"

        tasks:
          - title: "<implementation step>"
            priority: 1
            tracer: "<what this proves>"
            description: |
              - Detail 1
              - Detail 2
            deliverable: "<what is created>"
            tdd: true
```

### Step 4: Hierarchy Structure

```
Epic (Phase)
├── Feature 1 (User-observable outcome)
│   ├── Task 1.1 (Implementation step)
│   ├── Task 1.2 (Implementation step)
│   └── Task 1.3 (Implementation step)
└── Feature 2 (User-observable outcome)
    ├── Task 2.1 (Implementation step)
    └── Task 2.2 (Implementation step)
```

### Step 5: Output Menu Plan Summary

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

Phases: <N>
Features: <M>
Tasks: <L>

Breakdown:
  Phase 1: <title>
    - Feature 1.1: <title>
      - <N> tasks
    - Feature 1.2: <title>
      - <N> tasks

REVIEW THE PLAN:
  1. Check hierarchy makes sense
  2. Verify each feature has:
     [ ] User story
     [ ] Acceptance criteria (3-5)
  3. Verify each task has:
     [ ] Tracer explanation
     [ ] Clear deliverable

NEXT STEP: Run /line-mise-commit to convert to beads and create test specs
```

---

## Task Sizing Guidelines

**Too Small** (combine):
- "Add import statement"
- "Create empty file"

**Just Right** (single session):
- "Implement session management"
- "Add command execution"
- "Create CLI wrapper"

**Too Large** (break down):
- "Implement entire lifecycle"
- "Add all monitoring features"

---

## Example Usage

```
/line-mise-plan
```

**NEXT STEP: @line-mise-commit (after plan approval)**
