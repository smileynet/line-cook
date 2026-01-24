---
description: Prime planning session with bead hierarchy guidance
---

**Output this guidance to help structure planning.** Do not act - display for reference.

---

## Mise en Place: Planning Session Primer

*"Mise en place" (French: everything in its place) - the kitchen discipline of preparing and organizing ingredients before cooking begins.*

This guide helps structure work properly before execution. Use it when:
- Starting a new project or major feature
- Breaking down a large piece of work
- Onboarding to an existing project's issue structure

---

## The 3-Tier Hierarchy

```
Epic (capability area)
├── Feature (user-verifiable outcome)
│   └── Task (implementation step)
└── Feature
    ├── Task
    └── Task
```

| Tier | When to Use | Scope | Naming Style |
|------|-------------|-------|--------------|
| Epic | 3+ sessions, multiple features | Capability area | Noun phrase ("Authentication System") |
| Feature | User can verify "it works" | Deliverable outcome | Outcome statement ("User can reset password") |
| Task | Single session implementation | Code change | Action phrase ("Add email validation to reset form") |

**Key insight:** Epics are containers, Features are promises, Tasks are work.

---

## Naming Conventions

| Tier | Pattern | Good Example | Bad Example |
|------|---------|--------------|-------------|
| Epic | `<Noun> <System/Area>` | "User Authentication" | "Implement login stuff" |
| Feature | `<Actor> can <outcome>` | "User can export data as CSV" | "CSV export feature" |
| Task | `<Verb> <specific thing>` | "Add date picker to filter form" | "Work on filtering" |

**Feature naming test:** Can you demo this to a stakeholder? If yes, it's a feature.

---

## The "Who" Test

When deciding Feature vs Task, ask: **Who benefits directly?**

| Beneficiary | Classification | Example |
|-------------|----------------|---------|
| End user | Feature | "User sees loading indicator" |
| Developer/system | Task | "Add loading state to API hook" |
| Both equally | Usually Feature | "App shows helpful error messages" |

**Guideline:** If you'd mention it in release notes → Feature. If not → Task.

---

## Priority Levels

| Level | Meaning | When to Use |
|-------|---------|-------------|
| P0 | Critical | Production down, data loss, security breach |
| P1 | High | Blocking other work, major functionality broken |
| P2 | Medium | Normal priority (default for new features) |
| P3 | Low | Nice to have, when time permits |
| P4 | Backlog | Someday/maybe, parking lot items |

**Tips:**
- Most new work starts at P2
- P0/P1 should be rare - if everything is urgent, nothing is
- Use P4 for retrospective items and ideas

---

## The Parking Lot Pattern

For ideas, suggestions, and "nice to haves", use parking lot epics:

```bash
# Create parking lot epics (one-time setup)
bd create --title="Retrospective" --type=epic --priority=4
bd create --title="Backlog" --type=epic --priority=4
```

**Usage:**
- "Retrospective" = Items noticed during code review or work
- "Backlog" = Ideas for future consideration

**Auto-exclusion:** Tasks under these epics are automatically excluded from `/line-prep` and `/line-cook` selection. They're preserved for later review but won't interrupt current work.

**Direct tasks allowed:** Parking lot epics can have tasks directly (no feature layer needed).

---

## Planning Checklist

When breaking down work:

1. **Identify the capability area** → Epic (if large enough)
2. **List user-facing outcomes** → Features
3. **Break features into implementation steps** → Tasks
4. **Add dependencies** → `bd dep add <blocked> <blocker>`
5. **Set priorities** → P2 default, adjust as needed
6. **Park tangential ideas** → Under Retrospective/Backlog

**Rule of thumb:**
- 1-2 sessions of work? Skip the epic, just use features/tasks
- Single session? Just tasks, maybe no feature
- Large initiative? Full hierarchy

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Giant monolithic tasks | Can't track progress | Break into smaller tasks |
| Every task is an epic | Hierarchy loses meaning | Reserve epics for multi-feature work |
| Vague task names | Unclear when "done" | Use specific action + target |
| All P1 priorities | Nothing is prioritized | Use P2 as default, reserve P1 |
| Tasks with no parent | Orphan work, hard to navigate | Group under features or epics |
| Creating beads during planning | Mixes planning with execution | Plan first, create beads after |

---

## Example Breakdown

**Goal:** "Add dark mode to the application"

### Step 1: Identify Scope
- Multiple features (toggle, persistence, styling)
- Multi-session work
- → Create an Epic

### Step 2: Break into Features
```
Epic: Dark Mode Support
├── Feature: User can toggle between light/dark mode
├── Feature: Theme preference persists across sessions
└── Feature: App respects system theme preference
```

### Step 3: Break Features into Tasks
```
Feature: User can toggle between light/dark mode
├── Task: Add theme toggle component to settings
├── Task: Create dark theme CSS variables
├── Task: Apply theme class to root element
└── Task: Add transition animation for theme switch
```

### Step 4: Add Dependencies
```bash
# Theme toggle depends on CSS variables existing
bd dep add <toggle-task> <css-vars-task>
```

### Step 5: Set Priorities
- P2 for core functionality
- P3 for animation polish
- P4 for "nice to have" enhancements

---

## Session Boundary Reminder

**Planning is NOT execution.**

This session should result in:
- A clear hierarchy sketched out
- Agreement on scope and priorities
- Understanding of dependencies

After planning is complete:

1. **Create the beads** - `bd create` for each item
2. **Sync** - `bd sync`
3. **Clear context** - New session or `/line-compact`
4. **Begin execution** - `/line-prep` in fresh session

**Why clear context?** Planning accumulates exploration context that isn't needed for execution. Starting fresh lets you focus on the work itself.

---

**Ready to structure your work?** Share your goal and I'll help break it down using this framework.
