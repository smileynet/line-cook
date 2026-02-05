Create structured work breakdown (convergent thinking). Second phase of mise en place.

This phase transforms exploration into a structured, reviewable plan.

**Input:** Brainstorm document (optional) or direct requirements
**Output:** `docs/planning/menu-plan.yaml`

**STOP after creating menu plan.** Wait for user approval before committing.

---

## Process

### Step 1: Load Context

Look for planning context:

1. Check for context folders: `ls docs/planning/context-*/README.md`
2. If found, read non-archived README(s) for problem, approach, decisions
3. If no context folder, check for brainstorm: `ls docs/planning/brainstorm-*.md`
4. If neither exists, ask for requirements

### Step 2: Determine Scope

| Scope | Sessions | When to use |
|-------|----------|-------------|
| Task | <1 | Simple, clear deliverable |
| Feature | 1-3 | User-observable capability |
| Epic | 3+ | Multiple features |

### Step 3: Create Menu Plan

**Create `docs/planning/menu-plan.yaml`:**

```yaml
phases:
  - id: phase-1
    title: "Phase 1: Foundation"
    description: "Core infrastructure"

    features:
      - id: feature-1.1
        title: "Feature 1.1: <capability>"
        priority: 2
        user_story: "As a <role>, I want <action> so that <benefit>"
        acceptance_criteria:
          - "Can do X"
          - "Can do Y"

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
│   └── Task 1.2 (Implementation step)
└── Feature 2 (User-observable outcome)
    └── Task 2.1 (Implementation step)
```

### Step 4b: Update Planning Context

If a planning context folder exists:

1. Update README.md: status -> `scoped`, add Scope section
2. Update architecture.md with new constraints
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

REVIEW THE PLAN before proceeding.
```

Then ask the user how they'd like to proceed:

- **Continue to @line-finalize** — Convert plan to beads and test specs
- **Review menu plan first** — Stop here, review docs/planning/menu-plan.yaml
- **Done for now** — End the planning session

Wait for the user's response before continuing. If user chooses to continue, run `@line-finalize`.

## Task Sizing

**Too Small:** "Add import statement"
**Just Right:** "Implement session management"
**Too Large:** "Implement entire lifecycle"
