---
description: Create work breakdown before starting implementation (orchestrates brainstorm→scope→finalize)
allowed-tools: Bash, Write, Read, Glob, Grep, Task, AskUserQuestion, Skill, WebFetch, WebSearch
---

## Summary

**Mise en place orchestrator: brainstorm → scope → finalize.** Primary entry point for planning work.

Like `/line:run` orchestrates the execution cycle (prep→cook→serve→tidy), `/line:mise` orchestrates the planning cycle (brainstorm→scope→finalize).

**Phases:**
1. **Brainstorm** - Divergent thinking: explore, question, research
2. **Scope** - Convergent thinking: structure, scope, decompose
3. **Finalize** - Execution: create beads, write test specs, persist

**Arguments:** `$ARGUMENTS` (optional)
- `skip-brainstorm` - Skip directly to planning (when requirements are clear)
- `<brainstorm-name>` - Use specific brainstorm document

---

## Process

### Step 1: Start Planning Chain

**If `skip-brainstorm` in $ARGUMENTS or requirements are crystal clear:**
  Invoke `Skill(skill="line:scope")`.

**Otherwise:**
  Invoke `Skill(skill="line:brainstorm", args="$ARGUMENTS")`.

Each command will ask the user how to proceed and chain to the next command automatically if the user chooses to continue. The full chain is: brainstorm -> scope -> finalize.

If the chain completes (finalize runs), proceed to Step 2.
If the user stopped at any phase, output what was completed and stop.

### Step 2: Mise Complete Summary

After all phases complete, output summary:

```
╔══════════════════════════════════════════════════════════════╗
║  MISE EN PLACE COMPLETE                                      ║
╚══════════════════════════════════════════════════════════════╝

PLANNING CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/3] BRAINSTORM  ✓ explored
[2/3] SCOPE       ✓ structured
[3/3] FINALIZE    ✓ beads + specs created

Artifacts:
  - docs/planning/brainstorm-<name>.md
  - docs/planning/menu-plan.yaml
  - docs/planning/context-<name>/ (planning context)
  - .beads/ (<N> beads)
  - tests/features/ (<N> .feature files)
  - tests/specs/ (<N> .md files)
```

---

## Using Individual Phases

Users can run phases individually for more control:

| Command | Purpose |
|---------|---------|
| `/line:brainstorm` | Just explore and create brainstorm.md |
| `/line:scope` | Just create menu-plan.yaml from brainstorm |
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
/line:scope
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
[2/3] SCOPE       ✓
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
/scope                      /cook
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
2. **Scope** (convergent) - Narrow to structure, make decisions
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
