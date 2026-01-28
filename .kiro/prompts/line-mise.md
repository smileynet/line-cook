Create work breakdown before starting implementation. Prep step before creating beads.

**STOP after creating menu plan.** Wait for user approval before converting to beads.

---

## Process

### Step 1: Understand the Order

Ask clarifying questions:

**What are we building?**
- What problem are we solving?
- What does success look like?
- Who is the user?

**What are the constraints?**
- Are there technical constraints?
- Time constraints (MVP vs full feature)?
- Dependencies on other work?

**What's the scope?**
- MVP (minimum viable product)
- Full feature
- Multi-session epic

**Ask questions if unclear.** Don't assume.

### Step 2: Create Menu Plan

Build a structured breakdown in YAML format:

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
            description: |
              - Detail 1
              - Detail 2
            deliverable: "<what is created>"
```

### Step 3: Hierarchy Structure

Use three-tier hierarchy:

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

**Mapping:**
- **Epic** = Phase (3+ sessions, multiple features)
- **Feature** = User-observable capability (1-3 sessions)
- **Task** = Single implementation unit (< 2 hours)

### Step 4: Output Menu Plan Summary

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
     ✓ User story
     ✓ Acceptance criteria (3-5)
  3. Verify each task has:
     ✓ Clear deliverable
     ✓ Dependencies listed

NEXT STEP: Approve plan, then convert to beads
```

### Step 5: Convert to Beads (After Approval)

**ONLY convert after user approves the menu plan.**

Create beads manually:
```bash
bd create --title="Phase 1: Foundation" --type=epic --priority=2
bd create --title="Feature 1.1: <title>" --type=feature --parent=<epic-id> --priority=2
bd create --title="<task>" --parent=<feature-id> --priority=1
bd dep add <new-task-id> <dependency-task-id>
```

### Step 6: Sync and Commit

```bash
bd sync
git add docs/planning/menu-plan.yaml .beads/
git commit -m "plan: Create menu plan for <phase>

- <N> phases planned
- <M> features with acceptance criteria
- <L> tasks with deliverables"
git push
```

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

## Common Mistakes

- Creating beads directly without plan review
- Tasks too vague: "Implement monitoring"
- Tasks too large: "Complete Phase 1"
- No deliverable: "Research X"
- "Internal features" with no user interface

**NEXT STEP: @line-prep (after beads created)**
