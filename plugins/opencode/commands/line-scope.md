---
description: Create structured work breakdown (convergent thinking)
---


## Summary

**Convergent thinking phase: structure, scope, decompose.** Second phase of mise en place.

This phase transforms exploration into a structured, reviewable plan. Output is a YAML menu plan that can be converted to beads.

**Input:** Brainstorm document (optional) or direct requirements
**Output:** `docs/planning/menu-plan.yaml`

**Arguments:** `$ARGUMENTS` (optional) - Path to brainstorm document or direct requirements

**STOP after creating menu plan.** Wait for user approval before committing.

---

## Process

### Step 1: Load Context

**If the user provided a path or requirements:**
- Use the input as the brainstorm document path or direct requirements
- If it's a file path, read it as the brainstorm document
- If it's descriptive text, use it as direct requirements

**Otherwise:**
- Look for planning context automatically (below)

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
   - Read the brainstorm document
   - Use it as input for planning
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
    description: "Core infrastructure for tmux integration and worktrees"

    features:
      - id: feature-1.1
        title: "Feature 1.1: Execute commands in tmux sessions"
        priority: 2
        user_story: "As a capsule orchestrator, I want to execute commands in tmux sessions so that I can programmatic control OpenCode TUI"
        acceptance_criteria:
          - "Can create/destroy tmux sessions"
          - "Can send commands with proper debouncing"
          - "Can capture session output"

        tasks:
          - title: "Port tmux wrapper from gastown"
            priority: 1
            tracer: "Foundation layer - proves tmux integration works"
            description: |
              - Copy internal/tmux/tmux.go structure
              - Adapt for Capsule needs
            deliverable: "internal/tmux/tmux.go skeleton"
            tdd: true

          - title: "Implement session creation/destruction"
            priority: 1
            depends_on: ["Port tmux wrapper from gastown"]
            tracer: "Session lifecycle - proves basic management works"
            description: |
              - NewSession(name, workDir) function
              - KillSession(name) function
              - SessionExists(name) check
            deliverable: "Session management with tests"
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

### Step 5b: Update Planning Context

If a planning context folder exists (`docs/planning/context-<name>/`):

1. **Update README.md:**
   - Set status to `scoped`
   - Add Scope section with phase/feature/task counts and feature list

2. **Update architecture.md:**
   - Add any new layer/constraint info discovered during scoping

3. **Append to decisions.log:**
   ```
   YYYY-MM-DD | scope | <decision> | <rationale>
   ```

### Step 6: Handoff

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

## Hierarchy Structure

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

