---
description: Create work breakdown before starting implementation (orchestrates brainstorm→sample→scope→finalize)
---


## Summary

**Mise en place orchestrator: brainstorm → sample → scope → finalize.** Primary entry point for planning work.

Like `/line-run` orchestrates the execution cycle (prep→cook→serve→tidy), `/line-mise` orchestrates the planning cycle (brainstorm→sample→scope→finalize).

**Phases:**
1. **Brainstorm** - Divergent thinking: explore, question, research
2. **Sample** - Experiential thinking: walk through, question, sketch
3. **Scope** - Convergent thinking: structure, scope, decompose
4. **Finalize** - Execution: create beads, write test specs, persist

**Arguments:** `$ARGUMENTS` (optional)
- `skip-brainstorm` - Skip directly to sample (when requirements are clear)
- `skip-sample` - Skip sample, brainstorm hands off directly to scope

---

## Process

### Step 1: Start Planning Chain

**If the user specified `skip-brainstorm` and `skip-sample`:**
  Run `/line-scope`.

**If the user specified `skip-brainstorm` (but not `skip-sample`):**
  Run `/line-sample`.

**Otherwise:**
  Run `/line-brainstorm`.

Each command will ask the user how to proceed and chain to the next command automatically if the user chooses to continue. The full chain is: brainstorm -> sample -> scope -> finalize.

**Note:** If the user specified `skip-sample`, brainstorm will hand off directly to scope instead of sample.

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

[1/4] BRAINSTORM  ✓ explored
[2/4] SAMPLE      ✓ walked through
[3/4] SCOPE       ✓ structured
[4/4] FINALIZE    ✓ beads + specs created

Artifacts:
  - docs/planning/brainstorm-<name>.md
  - docs/planning/walkthrough-<name>.md
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
| `/line-brainstorm` | Just explore and create brainstorm.md |
| `/line-sample` | Just walk through UX and create walkthrough.md |
| `/line-scope` | Just create menu-plan.yaml from brainstorm |
| `/line-finalize` | Just convert existing menu-plan to beads + specs |
| `/line-mise` | Run all four phases with review pauses |

---

## Relationship to Execution Cycle

```
PLANNING CYCLE              EXECUTION CYCLE
━━━━━━━━━━━━━━━             ━━━━━━━━━━━━━━━━
/brainstorm                 /prep
      ↓                           ↓
/sample                     /cook
      ↓                           ↓
/scope                      /serve
      ↓                           ↓
/finalize                   /tidy
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

