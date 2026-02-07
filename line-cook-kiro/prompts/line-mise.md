## Summary

**Mise en place orchestrator: brainstorm → scope → finalize.** Primary entry point for planning work.

Like `@line-run` orchestrates the execution cycle (prep→cook→serve→tidy), `@line-mise` orchestrates the planning cycle (brainstorm→scope→finalize).

**Phases:**
1. **Brainstorm** - Divergent thinking: explore, question, research
2. **Scope** - Convergent thinking: structure, scope, decompose
3. **Finalize** - Execution: create beads, write test specs, persist

**Arguments:** `$ARGUMENTS` (optional)
- `skip-brainstorm` - Skip directly to scoping (when requirements are clear)

---

## Process

### Step 1: Start Planning Chain

**If `skip-brainstorm` in $ARGUMENTS or requirements are crystal clear:**
  Run `@line-scope`.

**Otherwise:**
  Run `@line-brainstorm`.

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
| `@line-brainstorm` | Just explore and create brainstorm.md |
| `@line-scope` | Just create menu-plan.yaml from brainstorm |
| `@line-finalize` | Just convert existing menu-plan to beads + specs |
| `@line-mise` | Run all three phases with review pauses |

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

## Example Usage

```
@line-mise                    # Full planning cycle with pauses
```

