---
description: Create work breakdown before starting implementation (orchestrates brainstorm→plan→commit)
---

## Summary

**Mise en place orchestrator: brainstorm → plan → commit.** Primary entry point for planning work.

Like `/line-run` orchestrates the execution cycle (prep→cook→serve→tidy), `/line-mise` orchestrates the planning cycle (brainstorm→plan→finalize).

**Phases:**
1. **Brainstorm** - Divergent thinking: explore, question, research
2. **Plan** - Convergent thinking: structure, scope, decompose
3. **Finalize** - Execution: create beads, write test specs, persist

---

## Process

### Step 1: Run /brainstorm

**Unless requirements are crystal clear:**

Run the brainstorm phase to explore the problem space.

Output is `docs/planning/brainstorm-<name>.md`.

**Pause for review.** Ask user if they want to proceed to planning.

### Step 2: Run /plan

Run the plan phase to create structured breakdown.

Output is `docs/planning/menu-plan.yaml`.

**Pause for review.** Ask user if they want to proceed to committing.

### Step 3: Run /finalize

Run the finalize phase to create beads and test specs.

Beads and test specs are created.

### Step 4: Mise Complete Summary

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

Available tasks:
  <id> - <title>

NEXT STEP: Run /line-prep to start working on tasks
```

---

## Using Individual Phases

Users can run phases individually for more control:

| Command | Purpose |
|---------|---------|
| `/line-brainstorm` | Just explore and create brainstorm.md |
| `/line-plan` | Just create menu-plan.yaml from brainstorm |
| `/line-finalize` | Just convert existing menu-plan to beads + specs |
| `/line-mise` | Run all three phases with review pauses |

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

## Example Usage

```
/line-mise                    # Full planning cycle with pauses
```

**NEXT STEP: @line-prep (after beads created)**
