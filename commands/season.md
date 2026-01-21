---
description: Apply research findings to beads - add context and create new work
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, TodoWrite
---

## Summary

**Season your work with research findings - enrich existing beads with context and create new ones.**

In cooking, seasoning adds depth and flavor to a dish. Here, you season your beads with discoveries from research - adding context to existing work and creating new beads informed by what you've learned.

**STOP after completing.** Show summary and wait for user.

**Arguments:** `$ARGUMENTS` (optional)
- Path to research file (e.g., `docs/research/findings.md`)
- Or provide findings inline in the conversation

---

## Process

### Step 1: Identify Context Source

Check `$ARGUMENTS` for a file path or inline findings:

**If file path provided:**
```bash
# Read the research file
cat "$ARGUMENTS"
```

**If no arguments:**
- Look for recent research-related activity in the conversation
- Ask user to provide findings if none found

```
AskUserQuestion:
  question: "What research findings should I apply?"
  options:
    - Point me to a file (I'll provide the path)
    - Let me paste the findings here
    - Review recent conversation for findings
```

### Step 2: Analyze Findings

Parse the research content to identify:

| Category | Examples |
|----------|----------|
| **New tasks** | "We need to implement X", "Discovered we should add Y" |
| **Existing bead updates** | "This affects <bead-id>", "Now we know X about Y" |
| **Dependencies** | "X must happen before Y", "Blocked by Z" |
| **Scope changes** | "No longer need X", "Alternative approach is better" |
| **Priority adjustments** | "This is more urgent because...", "Can defer X" |

### Step 3: Load Current Beads Context

Gather relevant beads for cross-referencing:

```bash
# Get all open beads
bd list --status=open --json

# Get epic/feature structure for proper parenting
bd list --type=epic --json
bd list --type=feature --json
```

### Step 4: Match Findings to Beads

For each finding, determine the action:

| Finding Type | Action |
|--------------|--------|
| New work discovered | → CREATE new bead with context |
| Context for existing work | → UPDATE bead description |
| Work no longer needed | → CLOSE bead with reason |
| Priority change | → UPDATE bead priority |
| New dependency | → ADD dependency link |

### Step 5: Propose Changes

Present all proposed changes before executing:

```
SEASON: Applying Findings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: <research file or "conversation">

CREATES (<count>):
  + task: "Implement X approach"
    Parent: <epic-id> "<epic-title>"
    Priority: P2
    Context: "Research found X is preferred because..."

  + task: "Add Y validation"
    Parent: <feature-id> "<feature-title>"
    Priority: P1
    Context: "Discovered Y is required for Z to work"

UPDATES (<count>):
  ~ <bead-id>: "<bead-title>"
    Added context: "Now we know Y affects this because..."

  ~ <bead-id>: "<bead-title>"
    Priority: P3 → P1
    Reason: "Research shows this is critical path"

CLOSES (<count>):
  - <bead-id>: "<bead-title>"
    Reason: "Research shows alternative approach is better"

DEPENDENCIES (<count>):
  <bead-a> depends on <bead-b>
    Reason: "Cannot do A until B provides X"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 6: User Confirmation

Use AskUserQuestion to confirm changes:

```
AskUserQuestion:
  question: "Apply these changes to your beads?"
  options:
    - Yes, apply all changes (Recommended)
    - Let me review and adjust first
    - Cancel - don't make changes
```

**If "Let me review":**
- Present each change individually for approval
- Allow user to skip, modify, or approve each one

### Step 7: Execute Changes

Apply confirmed changes:

**Creating beads:**
```bash
# Create with rich context in description
bd create --title="<title>" --type=task --priority=<n> --parent=<parent-id> \
  --description="Context from research: <finding>"
```

**Updating beads:**
```bash
# Update description with new context
CURRENT=$(bd show <id> --json | jq -r '.description')
NEW_DESC="$CURRENT

---
Research findings (<date>):
<new context>"
bd update <id> --description="$NEW_DESC"

# Update priority
bd update <id> --priority=<n>
```

**Closing beads:**
```bash
bd close <id> --reason="<reason from research>"
```

**Adding dependencies:**
```bash
bd dep add <issue> <depends-on>
```

### Step 8: Output Summary

Show what was applied:

```
SEASONING COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Applied from: <source>

Created: <n> beads
Updated: <n> beads
Closed: <n> beads
Dependencies: <n> added

New beads:
  <id> [P<n>] <title>
  <id> [P<n>] <title>

NEXT STEP: /line:prep to see updated task queue
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Key Behaviors

### Context-Rich Descriptions

Every bead created or updated should explain WHY based on findings:

**Good:**
```
Context from research (2026-01-20):
API documentation shows rate limiting is 100 req/min, not 1000.
This requires implementing request queuing to stay under limits.
```

**Bad:**
```
Implement rate limiting.
```

### Link Back to Source

Reference where findings came from:
- File path: `Source: docs/research/api-analysis.md`
- URL: `Source: https://docs.example.com/api-limits`
- Conversation: `Source: Conversation research on 2026-01-20`

### Hierarchy-Aware

Suggest appropriate parent based on:
1. Existing epic/feature that relates to the finding
2. If no clear fit, suggest creating under a relevant epic or as orphan

### Priority Inference

Suggest priority based on finding urgency:
- "Critical", "blocking", "must have" → P1
- "Important", "should have" → P2
- "Nice to have", "consider" → P3
- "Future", "someday" → P4 (or Backlog epic)

---

## Example Usage

**With research file:**
```
/line:season docs/research/api-findings.md
```

**After conversation research:**
```
/line:season
(Claude will look for findings in recent conversation)
```

**With inline context:**
```
/line:season
User provides: "After testing, I found that X doesn't work with Y, we need to add Z support"
```

---

## Related Commands

- `/line:prep` - See updated task queue after seasoning
- `/line:organize` - Audit hierarchy after adding beads
- `/beads:create` - Create beads manually without research context
