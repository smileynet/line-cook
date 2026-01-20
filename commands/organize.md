---
description: Audit and organize beads hierarchy
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, TodoWrite
---

## Summary

**Validate beads follow consistent hierarchy, fix violations, or restructure interactively.**

**Arguments:** `$ARGUMENTS` (optional)
- `audit` (default) - Report hierarchy issues
- `fix` - Fix validation errors interactively
- `reorganize` - Guided restructuring based on user goals
- `<epic-id>` - Scope audit to specific epic

---

## Process

### Step 1: Load Current Structure

Gather all beads and build hierarchy data:

```bash
# Count by type
EPIC_COUNT=$(bd list --type=epic --status=open --json | jq 'length')
FEATURE_COUNT=$(bd list --type=feature --status=open --json | jq 'length')
TASK_COUNT=$(bd list --type=task --status=open --json | jq 'length')

# Get all open issues with full data
ALL_ISSUES=$(bd list --status=open --json)
```

Build a parent-child tree using `bd list --parent=<id>` for each epic/feature.

### Step 2: Detect Project Mode

Determine hierarchy mode based on what exists:

| Condition | Mode |
|-----------|------|
| Has epics (epic count > 0) | **3-tier** (Epic → Feature → Task) |
| Has features but no epics | **2-tier** (Feature → Task) |
| Tasks only | **flat** (no hierarchy validation) |

### Step 3: Identify Parking-Lot Epics

Certain epics use relaxed hierarchy rules (direct tasks allowed):

```bash
# Find parking-lot epics by title keywords
PARKING_LOT_EPICS=$(bd list --type=epic --json | jq '[.[] | select(
  .title | test("Retrospective|Backlog|Research|Exploration"; "i")
) | .id]')
```

Parking-lot epic titles contain: "Retrospective", "Backlog", "Research", or "Exploration"

### Step 4: Parse Arguments

**If `$ARGUMENTS` is empty or `audit`:**
- Run validation and report (default)

**If `$ARGUMENTS` is `fix`:**
- Run validation, then interactively fix each issue

**If `$ARGUMENTS` is `reorganize`:**
- Skip to reorganize flow (Step 8)

**If `$ARGUMENTS` looks like an issue ID (e.g., `lc-xxx`):**
- Scope validation to that epic and its descendants only

### Step 5: Run Validations

#### 3-Tier Mode Validations

| Rule | Check | Severity |
|------|-------|----------|
| Task under epic | Task's parent is epic (not feature) | ERROR |
| Orphan task | Task with no parent (not in parking-lot) | WARNING |
| Deep nesting | Issue depth > 3 | ERROR |
| Feature with verb name | Title starts with "Add", "Fix", "Implement", etc. | WARNING |
| Single-child epic | Epic has exactly 1 child | INFO |

**Task under epic detection:**
```bash
# For each task, check if parent is an epic (not a feature)
bd show <parent-id> --json | jq '.issue_type'
# If "epic", this is a violation (task should be under feature)
```

**Orphan task detection:**
```bash
# Get all tasks
ALL_TASKS=$(bd list --type=task --status=open --json | jq -r '.[].id')

# For each task, check if it appears as child of any feature or epic
# A task is orphan if no --parent query returns it
for task in $ALL_TASKS; do
  # Check if task is child of any issue
  # Orphan if not found in any parent's children list
done
```

**Deep nesting detection:**
```bash
# Walk parent chain, count depth
# Epic (depth 1) → Feature (depth 2) → Task (depth 3)
# Anything beyond depth 3 is invalid
```

**Verb-name feature detection:**
```bash
# Check if feature title starts with common verbs
VERB_PATTERN="^(Add|Fix|Implement|Create|Build|Update|Refactor|Remove|Delete) "
bd list --type=feature --json | jq '[.[] | select(.title | test($VERB_PATTERN))]'
```

#### 2-Tier Mode Validations

| Rule | Check | Severity |
|------|-------|----------|
| Orphan task | Task with no parent feature | WARNING |
| Feature with verb name | Title starts with verb | WARNING |
| Task with outcome name | Task looks like a feature | INFO |

#### Flat Mode

No structural validation. Report summary counts only.

### Step 6: Generate Report (Audit Mode)

Output formatted report:

**3-tier project:**
```
HIERARCHY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: 3-tier (Epic → Feature → Task)
Structure: <n> epics, <n> features, <n> tasks

ERRORS (<count>):
  ✗ <id> [task] is child of EPIC (missing feature layer)
    Parent: <epic-id> "<epic-title>"
    Suggested: Create feature and reparent

WARNINGS (<count>):
  ⚠ <id> [feature] starts with verb "Implement"
    Consider: Rename to outcome-focused title

  ⚠ <id> [task] has no parent (orphan)
    Consider: Group under a feature

INFO (<count>):
  ℹ <epic-id> "<title>" has <n> direct tasks (parking-lot, OK)
  ℹ <epic-id> "<title>" has only 1 child

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run /line:organize fix to apply fixes interactively.
```

**2-tier project:**
```
HIERARCHY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: 2-tier (Feature → Task)
Structure: <n> features, <n> tasks

WARNINGS (<count>):
  ⚠ <id> [task] has no parent feature (orphan)
    Consider: Group under a feature

✓ No errors found
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Flat project:**
```
HIERARCHY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: flat (tasks only)
Structure: <n> tasks

ℹ No hierarchy validation for flat projects.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Clean audit (no issues):**
```
HIERARCHY AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: 3-tier (Epic → Feature → Task)
Structure: <n> epics, <n> features, <n> tasks

✓ All beads follow hierarchy conventions.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 7: Interactive Fix Mode

For each violation found, use AskUserQuestion to offer fix options:

**Task under epic (ERROR):**
```
AskUserQuestion:
  question: "<task-id> is directly under epic. How should we fix this?"
  options:
    - Create new feature and move task under it
    - Move to existing feature (select from list)
    - Skip (leave as-is)
```

**Orphan task (WARNING):**
```
AskUserQuestion:
  question: "<task-id> has no parent. How should we organize it?"
  options:
    - Create new feature for this task
    - Move to existing feature (select from list)
    - Move to parking-lot (Backlog/Research)
    - Skip (leave as orphan)
```

**Feature with verb name (WARNING):**
```
AskUserQuestion:
  question: "Feature '<title>' starts with verb. Rename to outcome?"
  options:
    - Suggest: "<outcome-focused rename>" (Recommended)
    - Keep current name
    - Enter custom name
```

**Applying fixes:**
```bash
# Create feature and move task
bd create --title="<feature-title>" --type=feature --parent=<epic-id>
bd update <task-id> --parent=<new-feature-id>

# Move to existing feature
bd update <task-id> --parent=<feature-id>

# Rename feature
bd update <feature-id> --title="<new-title>"
```

### Step 8: Reorganize Mode (Interactive Restructuring)

Guide user through restructuring their beads:

**Step 8a: Show current state**
```
REORGANIZE BEADS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current: <n> open issues (<n> tasks, <n> features, <n> epics)

Let's organize your work. I'll ask about your goals and
suggest a structure based on the feature-design-guide.
```

**Step 8b: Gather user intent**

Use AskUserQuestion for guided restructuring:

```
AskUserQuestion:
  question: "What capability or goal are you building toward?"
  (free text - this becomes the epic name)
```

```
AskUserQuestion:
  question: "What user-observable outcomes should this deliver?"
  multiSelect: true
  options:
    - (user provides outcomes - these become features)
```

**Step 8c: Map existing work**

Show existing tasks and ask which belong under each proposed feature:

```
AskUserQuestion:
  question: "Which existing tasks belong under '<feature-title>'?"
  multiSelect: true
  options:
    - <task-id>: <task-title>
    - <task-id>: <task-title>
    ...
```

**Step 8d: Preview changes**

Before applying:
```
PROPOSED STRUCTURE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Epic: "<epic-title>"
├── Feature: "<feature-1-title>"
│   ├── <task-id>: <task-title>
│   └── <task-id>: <task-title>
├── Feature: "<feature-2-title>"
│   └── <task-id>: <task-title>
└── Feature: "<feature-3-title>"
    └── (no tasks yet)

Changes to apply:
  CREATE epic: "<title>"
  CREATE feature: "<title>" under <epic-id>
  CREATE feature: "<title>" under <epic-id>
  MOVE <task-id> under <feature-id>
  MOVE <task-id> under <feature-id>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

```
AskUserQuestion:
  question: "Apply these changes?"
  options:
    - Yes, apply all changes (Recommended)
    - Edit structure first
    - Cancel
```

**Step 8e: Execute changes**

```bash
# Create epic
bd create --title="<epic-title>" --type=epic --priority=<p>

# Create features under epic
bd create --title="<feature-title>" --type=feature --parent=<epic-id>

# Move tasks under features
bd update <task-id> --parent=<feature-id>
```

**Step 8f: Show result**
```
REORGANIZATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created: 1 epic, 3 features
Moved: 5 tasks

New structure:
  bd show <epic-id> --tree

Next steps:
  - Review with: bd list --parent=<epic-id>
  - Run /line:organize to verify hierarchy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Reference: Hierarchy Conventions

See [feature-design-guide.md](../docs/feature-design-guide.md) for detailed hierarchy guidance.

**Quick reference:**

| Tier | Purpose | Naming Style |
|------|---------|--------------|
| **Epic** | Capability area (3+ sessions) | Noun phrase: "Hook System Hardening" |
| **Feature** | User-verifiable outcome | Outcome statement: "Hooks work in worktrees" |
| **Task** | Implementation step (1 session) | Action phrase: "Harden detection logic" |

**Parking-lot epics** (Retrospective, Backlog, Research): Direct tasks allowed, no feature layer required.

---

## Example Usage

```bash
/line:organize              # Audit all (default)
/line:organize audit        # Explicit audit mode
/line:organize fix          # Fix validation errors interactively
/line:organize reorganize   # Guided restructuring session
/line:organize lc-tp6       # Audit specific epic and children
```

---

## Related Commands

- `/line:prep` - Start session and show ready tasks
- `/line:cook` - Execute a task
- `/beads:create` - Create new beads manually
