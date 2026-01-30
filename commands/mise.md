---
description: Create work breakdown before starting implementation (orchestrates brainstorm→plan→finalize)
allowed-tools: Bash, Write, Read, Glob, Grep, Task, AskUserQuestion, Skill, WebFetch, WebSearch
---

## Summary

**Mise en place orchestrator: brainstorm → plan → finalize.** Primary entry point for planning work.

Like `/line:run` orchestrates the execution cycle (prep→cook→serve→tidy), `/line:mise` orchestrates the planning cycle (brainstorm→plan→finalize).

**Phases:**
1. **Brainstorm** - Divergent thinking: explore, question, research
2. **Plan** - Convergent thinking: structure, scope, decompose
3. **Finalize** - Execution: create beads, write test specs, persist

**Arguments:** `$ARGUMENTS` (optional)
- `skip-brainstorm` - Skip directly to planning (when requirements are clear)
- `<brainstorm-name>` - Use specific brainstorm document

---

## Process

### Step 1: Run /brainstorm

**Unless user provides `skip-brainstorm` or requirements are crystal clear:**

Invoke the brainstorm command to explore the problem space:

```
Skill(skill="line:brainstorm")
```

Wait for brainstorm to complete. Output is `docs/planning/brainstorm-<name>.md`.

**Pause for review.** Ask user if they want to proceed to planning:

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/brainstorm-<name>.md

<summary of exploration>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to proceed to planning phase?
- Review the brainstorm document
- Resolve any open questions
- Then continue to create structured plan

Continue to /line:plan? [Y/n]
```

Wait for user confirmation before proceeding.

### Step 2: Run /plan

Invoke the plan command to create structured breakdown:

```
Skill(skill="line:plan")
```

Wait for plan to complete. Output is `docs/planning/menu-plan.yaml`.

**Pause for review.** Ask user if they want to proceed to finalizing:

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

<summary of plan>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to finalize beads and create test specs?
- Review the menu plan
- Make any edits to the YAML file
- Then continue to create beads

Continue to /line:finalize? [Y/n]
```

Wait for user confirmation before proceeding.

### Step 3: Run /finalize

Invoke the finalize command to create beads and test specs:

```
Skill(skill="line:finalize")
```

Wait for finalize to complete. Beads and test specs are created.

### Step 4: Mise Complete Summary

After all steps complete, output summary:

```
╔══════════════════════════════════════════════════════════════╗
║  MISE EN PLACE COMPLETE                                      ║
╚══════════════════════════════════════════════════════════════╝

PLANNING CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/3] BRAINSTORM  ✓ explored
[2/3] PLAN        ✓ structured
[3/3] FINALIZE    ✓ beads + specs created

Artifacts:
  - docs/planning/brainstorm-<name>.md
  - docs/planning/menu-plan.yaml
  - .beads/ (<N> beads)
  - tests/features/ (<N> .feature files)
  - tests/specs/ (<N> .md files)

──────────────────────────────────────────

READY TO WORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Available tasks:
  <id> - <title>
  <id> - <title>

NEXT STEP: Run /line:prep to start working on tasks
  (or /line:run for full execution cycle)
```

---

## Using Individual Phases

Users can run phases individually for more control:

| Command | Purpose |
|---------|---------|
| `/line:brainstorm` | Just explore and create brainstorm.md |
| `/line:plan` | Just create menu-plan.yaml from brainstorm |
| `/line:finalize` | Just convert existing menu-plan to beads + specs |
| `/line:mise` | Run all three phases with review pauses |

**Example workflows:**

```
# Full orchestrated flow
/line:mise

# Skip brainstorm (clear requirements)
/line:mise skip-brainstorm

# Individual phases for maximum control
/line:brainstorm
# ... review and refine ...
/line:plan
# ... review and refine ...
/line:finalize
```

---

## Error Handling

If any step fails:

1. **Brainstorm fails** - Report what went wrong, offer to skip to plan
2. **Plan fails** - Report error, suggest running brainstorm first
3. **Finalize fails** - Report error, suggest reviewing menu-plan.yaml

```
PLANNING CYCLE: Incomplete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/3] BRAINSTORM  ✓
[2/3] PLAN        ✓
[3/3] FINALIZE    ✗ (error: <reason>)

Failed at: FINALIZE
Error: <description>

──────────────────────────────────────────

Run /line:finalize to retry after fixing the issue.
```

---

## Relationship to Execution Cycle

```
PLANNING CYCLE              EXECUTION CYCLE
━━━━━━━━━━━━━━━             ━━━━━━━━━━━━━━━━
/brainstorm                 /prep
      ↓                           ↓
/plan                       /cook
      ↓                           ↓
/finalize                   /serve
                                  ↓
                            /tidy
                                  ↓
                            /plate

/mise (orchestrator)        /run (orchestrator)
```

Planning creates the work. Execution completes the work.

---

## Design Notes

The `/line:mise` command separates planning into natural cognitive phases:

1. **Brainstorm** (divergent) - Expand possibilities, explore freely
2. **Plan** (convergent) - Narrow to structure, make decisions
3. **Finalize** (execution) - Persist to trackable artifacts

This matches the "Planning vs Execution" mental model from `docs/mental-models.md`.

**Benefits:**
- Natural pause points for review
- Context-efficient (can run phases in separate sessions)
- Progressive commitment (ideas → structure → tracked work)
- Test-first enforcement (specs created before implementation)

---

## Example Usage

```
/line:mise                    # Full planning cycle with pauses
/line:mise skip-brainstorm    # Skip brainstorm, start at plan
```

This command is the recommended entry point for planning new work.
