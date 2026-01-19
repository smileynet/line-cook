## Summary

**Validate hook configurations and detect orphaned configs.** Useful after plugin updates or when hooks stop working.

**Arguments:** `$ARGUMENTS` (optional) - Path to check (defaults to current project)

---

## Process

### Step 1: Run Doctor Script

Execute the doctor validation:

```bash
python3 "$CLAUDE_PROJECT_DIR/hooks/line_doctor.py"
```

If `$ARGUMENTS` provided (specific path to check):
```bash
CLAUDE_PROJECT_DIR="$ARGUMENTS" python3 "$CLAUDE_PROJECT_DIR/hooks/line_doctor.py"
```

**Note:** The target project must have line_doctor.py in its hooks/ directory. If checking another project that uses line-cook hooks, copy line_doctor.py there first, or run the doctor from the target project.

### Step 2: Report Results

The script outputs a formatted report:

```
LINE DOCTOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Project: /path/to/project
  ✓ Python 3 available
  ✓ Valid JSON: settings.json
  ✓ Valid structure: settings.json
  ✓ Found: session_start.py
  ✓ Valid Python: session_start.py
  ✓ Imports OK: session_start.py
  ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ All checks passed
```

### Step 3: Handle Issues

If issues are found, the output shows:

```
LINE DOCTOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ Project: /path/to/project
  ✓ Python 3 available
  ✓ Valid JSON: settings.json
  ✓ Valid structure: settings.json
  ✗ Missing script: old_hook.py
      Event: PreToolUse
      Path: /path/to/hooks/old_hook.py
      File does not exist

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✗ 1 issue(s) found

To fix orphaned configs:
  1. Update paths in .claude/settings.json
  2. Or remove unused hook configurations
```

Offer to help fix the issue:

1. **Missing script** - Offer to update settings.json to remove the reference or point to correct file
2. **Invalid JSON** - Show the syntax error and offer to fix
3. **Structure issues** - Explain what's wrong and suggest corrections
4. **Import errors** - Check if hook_utils.py exists, offer to copy from plugin

## What Doctor Checks

1. **JSON validity** - Settings files parse correctly
2. **Structure validation** - Hook definitions have required fields (type, command)
3. **Script existence** - All referenced Python scripts exist
4. **Python syntax** - Scripts compile without syntax errors
5. **Import availability** - Local imports (hook_utils) are present
6. **Python availability** - Python 3 is in PATH

## Common Issues

### Orphaned References
After restructuring or renaming hook files:
```
✗ Missing script: session_start.py
    Path: /old/path/hooks/session_start.py
```
**Fix:** Update `.claude/settings.json` to point to the new location.

### Missing hook_utils
After copying hooks without utilities:
```
✗ Missing imports: pre_tool_use.py
    hook_utils (expected at /path/hooks/hook_utils.py)
```
**Fix:** Copy `hook_utils.py` from the line-cook plugin to your hooks directory.

### Syntax Errors
After editing hooks manually:
```
✗ Syntax error: post_tool_use.py
    Line 42: unexpected EOF while parsing
```
**Fix:** Check line 42 for missing brackets, quotes, or colons.

## Example Usage

```
/line:doctor              # Check current project
/line:doctor ~/other/proj # Check specific project
```

## Related Commands

- `/line:setup` - Configure hooks from scratch
- `/hooks` - View active hook configuration (built-in)
