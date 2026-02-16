**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**One-time setup verification with guided fixes.** Checks that git, beads, and Line Cook are properly configured.

**Arguments:** `$ARGUMENTS` (none expected)

---

## Process

### Step 1: Run Diagnostic Checks

Discover and run the onboarding check script:

1. Find `onboarding-check.py` using Glob pattern `**/scripts/onboarding-check.py`
2. Run it with `--json` flag
3. Parse the JSON output

```bash
python3 <discovered-path>/onboarding-check.py --json
```

### Step 2: Display Results

**If all checks pass:**

Output the success banner:

```
KITCHEN INSPECTION: PASSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━

```

Then list each passing check with `✓` prefix, grouped by category (SYSTEM, PROJECT, PLUGIN).

Include the plugin version if detected.

End with:

```
Ready to cook. Next: @line-getting-started
```

**If any check fails:**

Output the inspection header:

```
KITCHEN INSPECTION
━━━━━━━━━━━━━━━━━━
```

List all checks with `✓` for pass and `✗` for fail. After the list, show the **first failure** with its fix hint:

```
FIX: <fix_hint from the failed check>

After fixing, run @line-init again.
```

**If checks have warnings but no failures:**

Show the success banner but note the warnings:

```
KITCHEN INSPECTION: PASSED (with warnings)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

List all checks. For warnings, use `⚠` prefix and include the fix hint.

End with:

```
Ready to cook. Next: @line-getting-started
```

---

## Example Output

```
KITCHEN INSPECTION: PASSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Git repository configured
✓ Git remote configured
✓ Beads CLI installed
✓ Beads initialized (.beads/)
✓ Line Cook v0.16.0
✓ Helper scripts available

Ready to cook. Next: @line-getting-started
```
