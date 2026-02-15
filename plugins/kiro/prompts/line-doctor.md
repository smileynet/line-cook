**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Comprehensive health diagnostics and interactive troubleshooting.** Runs all setup checks plus project-specific analysis, then offers targeted help.

**Arguments:** `$ARGUMENTS` (optional) - Describe a specific problem to jump to targeted troubleshooting

---

## Process

### Step 1: Run Onboarding Checks

Discover and run the onboarding check script:

1. Find `onboarding-check.py` using Glob pattern `**/scripts/onboarding-check.py`
2. Run it with `--json` flag
3. Parse the JSON output

```bash
python3 <discovered-path>/onboarding-check.py --json
```

### Step 2: Run Additional Diagnostics

If beads is configured (`.beads/` exists), run additional project health checks:

```bash
# Project statistics
bd stats

# Beads' own doctor
bd doctor

# Check for stale in-progress tasks (in_progress for >7 days)
bd list --status=in_progress --json

# Check for orphaned beads (open tasks with no parent)
bd list --status=open --json
```

For stale task detection: parse the JSON output, check for tasks whose `updated_at` timestamp is more than 7 days old.

For orphan detection: check for open tasks/features that have no parent epic.

### Step 3: Format Full Report

Output the complete diagnostic report:

```
DOCTOR'S REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM
  ✓ Git repository (<branch>, <clean|dirty>)
  ✓ Beads CLI <version>
  ✓ Line Cook v<version>

PROJECT
  ✓ Beads initialized
  ✓ <N> issues (<open> open, <in_progress> in-progress, <closed> closed)
  ⚠ <N> stale in-progress tasks (>7 days)  [if any]
  ✓ No orphaned issues  [or: ⚠ <N> orphaned tasks (no parent)]

PLUGIN
  ✓ Scripts discoverable
  ✓ <N> commands available

SPICE RACK
  ✓ <name> (installed)  [for each installed spice]
  ○ <name> (available, not installed)  [for each uninstalled spice]

Overall: <HEALTHY|NEEDS ATTENTION> (<N> warnings)
```

Use these icons:
- `✓` = pass
- `⚠` = warning
- `✗` = failure
- `○` = informational (available but not installed)

### Step 4: Interactive Troubleshooting

**If the user passed a problem description as an argument:**

Skip the question and go directly to targeted troubleshooting for the described problem.

**Otherwise:**

Ask the user: **"Are you experiencing a specific problem?"**

1. No, just checking
2. Yes, something is wrong (please describe)
3. Tasks seem stuck
4. Commands aren't working
Ask the user: **"Are you experiencing a specific problem?"**

1. No, just checking
2. Yes, something is wrong (please describe)
3. Tasks seem stuck
4. Commands aren't working

### Step 5: Targeted Troubleshooting

Based on the problem category:

**Tasks seem stuck:**
- Check `bd blocked` for dependency issues
- Check for circular dependencies
- Show stale in-progress tasks with age
- Suggest: `bd close <id>` for done tasks, `bd update <id> --status=open` to unclaim

**Commands aren't working:**
- Re-run `onboarding-check.py` for script availability
- Check plugin version matches expectations
- Suggest: `/plugin update line` then start a new session

**General problem:**
- Read relevant docs based on keywords in the problem description
- Check recent git log for related changes
- Suggest fixes based on findings

### Step 6: Resolution or Escalation

**If the problem was resolved:**
- Summarize what was found and fixed

**If the problem persists:**
- Help create a tracking bead: `bd create --title="<problem summary>" --type=bug --priority=2`
- Suggest filing at `github.com/smileynet/line-cook/issues` with the doctor report output

---

## Example Output

```
DOCTOR'S REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM
  ✓ Git repository (main, clean)
  ✓ Beads CLI (3032c622)
  ✓ Line Cook v0.15.0

PROJECT
  ✓ Beads initialized
  ✓ 12 issues (4 open, 3 in-progress, 5 closed)
  ⚠ 2 stale in-progress tasks (>7 days)
  ✓ No orphaned issues

PLUGIN
  ✓ Scripts discoverable
  ✓ 21 commands available

SPICE RACK
  ✓ game-spice (installed)

Overall: HEALTHY (1 warning)
```

---

## Example Usage

```
@line-doctor                          # Full diagnostic report
@line-doctor tasks seem blocked       # Targeted troubleshooting
```
