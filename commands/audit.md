---
description: Audit beads structure, dependencies, and quality with auto-fix
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

## Summary

**Validate bead content quality and structure.** Complements `bd doctor` (system-level) with content-level validation.

**STOP after completing.** Show audit report and wait for user.

---

## Arguments

```
/line:audit [scope] [--fix] [--interactive]

scope:
  active    - Open/in_progress beads only (default)
  full      - All beads including closed, with work verification
  <id>      - Specific bead and hierarchy

--fix          - Auto-fix safe issues
--interactive  - Prompt for each fix (requires --fix)
```

### Scope Behavior

| Scope | Focus | Includes |
|-------|-------|----------|
| `active` | Current work hygiene | Open/in_progress beads only |
| `full` | Comprehensive + work verification | All beads, validates closed work |
| `<id>` | Specific bead hierarchy | Bead + parents + children |

---

## Process

### Step 1: Parse Arguments

Extract scope and flags from command:

```bash
# Default: active scope
SCOPE="active"
FIX_MODE=false
INTERACTIVE=false

# Parse arguments (scope is first non-flag arg)
# --fix enables auto-fix for safe issues
# --interactive prompts for each fix (requires --fix)
```

### Step 2: Gather Beads

Based on scope, gather beads to audit:

**Active scope (default):**
```bash
# Get open and in_progress beads
bd list --status=open --json > /tmp/open.json
bd list --status=in_progress --json > /tmp/progress.json
# Merge results
```

**Full scope:**
```bash
# Get all beads including closed
bd list --all --json > /tmp/all.json
```

**Specific bead:**
```bash
# Get the bead and its hierarchy
bd show <id> --json > /tmp/target.json
# Walk parent chain
# Get all children recursively
```

### Step 3: Structural Validation

Run structural checks on gathered beads:

#### 3a: Hierarchy Depth Check (Critical)

Max 3 levels: epic -> feature -> task

```bash
# For each bead, walk parent chain
for bead in $BEADS; do
  current=$bead
  depth=0
  while parent=$(bd show $current --json | jq -r '.[0].parent // empty'); do
    [ -z "$parent" ] && break
    depth=$((depth + 1))
    if [ $depth -gt 3 ]; then
      echo "CRITICAL: DEPTH_EXCEEDED $bead (depth: $depth)"
    fi
    current=$parent
  done
done
```

#### 3b: Orphan Check (Critical)

Parent reference must exist:

```bash
for bead in $BEADS; do
  parent=$(bd show $bead --json | jq -r '.[0].parent // empty')
  if [ -n "$parent" ]; then
    # Check if parent exists
    if ! bd show $parent >/dev/null 2>&1; then
      echo "CRITICAL: ORPHAN $bead references non-existent parent $parent"
    fi
  fi
done
```

#### 3c: Type Consistency Check (Warning)

Children should match parent tier:

| Parent Type | Expected Children |
|-------------|-------------------|
| epic | feature or task |
| feature | task |
| task | (no children) |

```bash
for bead in $BEADS; do
  type=$(bd show $bead --json | jq -r '.[0].issue_type // empty')
  children=$(bd list --parent=$bead --json | jq -r '.[].id')

  if [ "$type" = "task" ] && [ -n "$children" ]; then
    echo "WARNING: TYPE_CONSISTENCY $bead (task) has children"
  fi
done
```

### Step 4: Content Quality Checks

Run content quality validation:

#### 4a: Acceptance Criteria (Warning - Features)

Features should have 3-5 acceptance criteria:

```bash
for feature in $FEATURES; do
  desc=$(bd show $feature --json | jq -r '.[0].description')
  # Count numbered items (1. 2. 3. etc) or bullet items under "Acceptance"
  criteria_count=$(echo "$desc" | grep -cE "^[0-9]+\.|^- " || echo 0)

  if [ $criteria_count -lt 3 ]; then
    echo "WARNING: CRITERIA $feature has $criteria_count acceptance criteria (expected 3-5)"
  fi
done
```

#### 4b: User Story Format (Info - Features)

Features should have "As a...I want...so that" format:

```bash
for feature in $FEATURES; do
  desc=$(bd show $feature --json | jq -r '.[0].description')
  if ! echo "$desc" | grep -iqE "as a.*i want.*so that"; then
    echo "INFO: USER_STORY $feature missing user story format"
  fi
done
```

#### 4c: Task Deliverable (Info - Tasks)

Tasks should have "Deliverable:" in description:

```bash
for task in $TASKS; do
  desc=$(bd show $task --json | jq -r '.[0].description')
  if ! echo "$desc" | grep -iq "deliverable"; then
    echo "INFO: DELIVERABLE $task missing deliverable statement"
  fi
done
```

#### 4d: Missing Priority (Warning - Auto-fixable)

All beads should have priority set:

```bash
for bead in $BEADS; do
  priority=$(bd show $bead --json | jq -r '.[0].priority // empty')
  if [ -z "$priority" ]; then
    echo "WARNING: PRIORITY $bead missing priority (auto-fix: P2)"
    if $FIX_MODE; then
      bd update $bead --priority=2
      echo "  FIXED: Set priority to P2"
    fi
  fi
done
```

#### 4e: Missing Issue Type (Warning - Auto-fixable)

All beads should have issue_type:

```bash
for bead in $BEADS; do
  type=$(bd show $bead --json | jq -r '.[0].issue_type // empty')
  if [ -z "$type" ]; then
    # Infer from hierarchy
    parent=$(bd show $bead --json | jq -r '.[0].parent // empty')
    if [ -z "$parent" ]; then
      inferred="epic"
    else
      parent_type=$(bd show $parent --json | jq -r '.[0].issue_type // empty')
      case $parent_type in
        epic) inferred="feature" ;;
        feature) inferred="task" ;;
        *) inferred="task" ;;
      esac
    fi
    echo "WARNING: TYPE $bead missing issue_type (auto-fix: $inferred)"
    if $FIX_MODE; then
      bd update $bead --type=$inferred
      echo "  FIXED: Set issue_type to $inferred"
    fi
  fi
done
```

### Step 5: Health Checks

Run health validation:

#### 5a: Stale In-Progress (Warning)

In-progress beads older than 7 days:

```bash
for bead in $IN_PROGRESS; do
  updated=$(bd show $bead --json | jq -r '.[0].updated_at')
  days_old=$(( ($(date +%s) - $(date -d "$updated" +%s)) / 86400 ))

  if [ $days_old -gt 7 ]; then
    echo "WARNING: STALE $bead in_progress for $days_old days"
  fi
done
```

#### 5b: Old Open (Info)

Open beads with no activity for 30+ days:

```bash
for bead in $OPEN; do
  updated=$(bd show $bead --json | jq -r '.[0].updated_at')
  days_old=$(( ($(date +%s) - $(date -d "$updated" +%s)) / 86400 ))

  if [ $days_old -gt 30 ]; then
    echo "INFO: OLD_OPEN $bead open for $days_old days with no activity"
  fi
done
```

#### 5c: Nearly Complete Features (Info)

Features with >80% tasks complete:

```bash
for feature in $FEATURES; do
  total=$(bd list --parent=$feature | wc -l)
  closed=$(bd list --parent=$feature --status=closed | wc -l)

  if [ $total -gt 0 ]; then
    pct=$((closed * 100 / total))
    if [ $pct -ge 80 ] && [ $pct -lt 100 ]; then
      echo "INFO: NEARLY_COMPLETE $feature at $pct% ($closed/$total tasks)"
    fi
  fi
done
```

### Step 6: Work Verification (Full Scope Only)

Only run for `full` scope - validates closed work:

#### 6a: Acceptance Doc Check (Warning)

Closed features should have acceptance documentation:

```bash
if [ "$SCOPE" = "full" ]; then
  for feature in $CLOSED_FEATURES; do
    doc_path="docs/features/${feature}-acceptance.md"
    if [ ! -f "$doc_path" ]; then
      echo "WARNING: MISSING_DOC $feature (closed feature) has no acceptance doc"
      echo "  Expected: $doc_path"
      echo "  Action: Run /line:plate $feature or create manually"
    fi
  done
fi
```

#### 6b: Close Reason Check (Info)

Closed beads should have close_reason:

```bash
if [ "$SCOPE" = "full" ]; then
  for bead in $CLOSED; do
    reason=$(bd show $bead --json | jq -r '.[0].close_reason // empty')
    if [ -z "$reason" ]; then
      echo "INFO: NO_CLOSE_REASON $bead closed without explanation"
    fi
  done
fi
```

#### 6c: Orphan Parent Check (Warning)

If all children are closed, parent should be too:

```bash
if [ "$SCOPE" = "full" ]; then
  for parent in $FEATURES $EPICS; do
    status=$(bd show $parent --json | jq -r '.[0].status')
    if [ "$status" != "closed" ]; then
      children=$(bd list --parent=$parent --json)
      total=$(echo "$children" | jq length)
      closed=$(echo "$children" | jq '[.[] | select(.status == "closed")] | length')

      if [ "$total" -gt 0 ] && [ "$total" -eq "$closed" ]; then
        echo "WARNING: ORPHAN_PARENT $parent has all $total children closed but is still open"
        echo "  Action: bd close $parent"
      fi
    fi
  done
fi
```

### Step 7: Interactive Fixes (If --fix --interactive)

For issues that require user confirmation:

```bash
if $FIX_MODE && $INTERACTIVE; then
  # For orphan beads
  for orphan in $ORPHANS; do
    echo "ORPHAN: $orphan references non-existent parent"
    echo "Fix options:"
    echo "  1. Remove parent reference"
    echo "  2. Skip"
    # Use AskUserQuestion tool
  done
fi
```

### Step 8: Calculate Statistics

Gather summary statistics:

```bash
# Count by tier
epic_count=$(echo "$BEADS" | jq '[.[] | select(.issue_type == "epic")] | length')
feature_count=$(echo "$BEADS" | jq '[.[] | select(.issue_type == "feature")] | length')
task_count=$(echo "$BEADS" | jq '[.[] | select(.issue_type == "task")] | length')

# Count by status
open_count=$(echo "$BEADS" | jq '[.[] | select(.status == "open")] | length')
progress_count=$(echo "$BEADS" | jq '[.[] | select(.status == "in_progress")] | length')
closed_count=$(echo "$BEADS" | jq '[.[] | select(.status == "closed")] | length')

# Calculate overall progress
total_tasks=$task_count
closed_tasks=$(echo "$BEADS" | jq '[.[] | select(.issue_type == "task" and .status == "closed")] | length')
if [ $total_tasks -gt 0 ]; then
  progress_pct=$((closed_tasks * 100 / total_tasks))
fi
```

### Step 9: Output Report

Output the audit report with issues grouped by severity:

```
╔══════════════════════════════════════════════════════════════╗
║  AUDIT: Bead Health Check                                    ║
╚══════════════════════════════════════════════════════════════╝

Scope: <active|full|bead-id>
Beads scanned: <count>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL (must fix)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ORPHAN] <bead-id> references non-existent parent <parent-id>
  Fix: bd update <bead-id> --parent=""

[DEPTH] <bead-id> exceeds max hierarchy depth (4 levels)
  Fix: Restructure hierarchy to max 3 levels

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WARNINGS (should fix)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CRITERIA] <bead-id> (feature) has 1 acceptance criterion (expected 3-5)
  Suggestion: Add error handling and edge case criteria

[STALE] <bead-id> in_progress for 12 days
  Suggestion: Review or close

[PRIORITY] <bead-id> missing priority
  Auto-fix: bd update <bead-id> --priority=2

[TYPE] <bead-id> missing issue_type
  Auto-fix: bd update <bead-id> --type=<inferred>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INFO (suggestions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[USER_STORY] <bead-id> (feature) missing user story format
  Suggestion: Add "As a <user>, I want <goal> so that <benefit>"

[DELIVERABLE] <bead-id> (task) missing deliverable statement
  Suggestion: Add "Deliverable: <what will be produced>"

[BDD] <bead-id> (feature) missing BDD test file
  Expected: tests/features/*-<feature-slug>.feature

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCOPE HEALTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Work Breakdown:
  Epics: <count> (<active> active, <complete> complete)
  Features: <count> (<open> open, <closed> closed)
  Tasks: <count> (<open> open, <closed> closed)

Progress: [████████░░] <pct>% complete (<closed>/<total> tasks)

Stale Items: <count>
Nearly Complete Features: <count>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORK VERIFICATION (full scope only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[MISSING_DOC] <bead-id> (closed feature) has no acceptance doc
  Expected: docs/features/<bead-id>-acceptance.md
  Action: Run /line:plate <bead-id> or create manually

[ORPHAN_PARENT] <bead-id> (feature) has all tasks closed but is still open
  Children: <closed>/<total> closed
  Action: bd close <bead-id>

[NO_CLOSE_REASON] <bead-id> closed without explanation
  Action: Consider adding context with bd update <bead-id> --close-reason="..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Issues: <critical> critical, <warnings> warnings, <info> info
Work verification: <count> issues (full scope only)
Auto-fixable: <count> (run with --fix)

NEXT STEP: <action based on findings>
```

**NEXT STEP logic:**
- If critical issues: "Fix critical issues before proceeding"
- If auto-fixable + no --fix: "Run /line:audit --fix to auto-fix <count> issues"
- If warnings only: "Review warnings, then /line:prep"
- If clean: "/line:prep - workspace is healthy"

---

## Validation Rules Reference

### Structural (Critical/Warning)

| Check | Rule | Severity | Auto-fix |
|-------|------|----------|----------|
| Hierarchy depth | Max 3 levels (epic->feature->task) | Critical | No |
| Orphan child | Parent reference must exist | Critical | Interactive |
| Type consistency | Children match parent tier | Warning | Interactive |

### Content Quality (Warning/Info)

| Check | Applies To | Rule | Auto-fix |
|-------|------------|------|----------|
| Acceptance criteria | Features | 3-5 items in description | No (suggest) |
| User story | Features | "As a...I want...so that" format | No (suggest) |
| Deliverable | Tasks | "Deliverable:" in description | No (suggest) |
| Priority set | All | Should have priority (0-4) | Yes (default P2) |
| Issue type set | All | Should have issue_type | Yes (infer) |

### Health (Warning/Info)

| Check | Rule | Threshold |
|-------|------|-----------|
| Stale in_progress | in_progress too long | >7 days |
| Old open | Open with no activity | >30 days |
| Nearly complete | Feature with most tasks done | >80% |

### Work Verification (Full Scope)

| Check | Applies To | Rule | Severity |
|-------|------------|------|----------|
| Acceptance doc | Closed features | docs/features/<id>-acceptance.md | Warning |
| Close reason | Closed beads | Should explain outcome | Info |
| Parent complete | Closed children | Parent should also close | Warning |

---

## Integration

| Command | Relationship |
|---------|--------------|
| `bd doctor` | System checks (audit = content checks) |
| `/line:mise` | Creates beads -> audit validates after |
| `/line:prep` | Audit first for hygiene, prep for work |
| `/line:plate` | Audit can pre-validate features |

---

## Example Usage

```bash
# Check active work hygiene (default)
/line:audit

# Full audit with work verification
/line:audit full

# Audit specific bead hierarchy
/line:audit lc-abc.1

# Auto-fix safe issues
/line:audit --fix

# Interactive fixes (prompts for each)
/line:audit --fix --interactive

# Full audit with auto-fix
/line:audit full --fix
```
