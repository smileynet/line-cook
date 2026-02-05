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

Look for planning context:

1. Check for context folders:
   ```bash
   ls docs/planning/context-*/README.md 2>/dev/null
   ```

2. **If context folder(s) found:**
   - Read README.md files, find non-archived ones
   - If multiple, ask the user which one to use
   - Read context README for problem, approach, key decisions
   - Read `decisions.log` for rationale history

3. **If no context folder but brainstorm exists:**
   ```bash
   ls docs/planning/brainstorm-*.md 2>/dev/null
   ```
   - Read the brainstorm document and use as input
   - Create a context folder from brainstorm content

4. **If neither exists:**
   - Ask user for requirements directly

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

### Step 4b: Update Planning Context

If a planning context folder exists (`docs/planning/context-<name>/`):

1. Update README.md: status -> `scoped`, add Scope section with counts and feature list
2. Update architecture.md with any new layer/constraint info
3. Append scope decisions to decisions.log

### Step 5: Handoff

Output the menu plan summary:

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
```

Then ask the user how they'd like to proceed:

- **Continue to /line-finalize** — Convert plan to beads and test specs
- **Review menu plan first** — Stop here, review docs/planning/menu-plan.yaml
- **Done for now** — End the planning session

Wait for the user's response before continuing. If user chooses to continue, run `/line-finalize`.

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
/line-scope
```
