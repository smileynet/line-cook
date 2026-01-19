# Line Cook Hooks

Hooks automate workflow stages in Claude Code and OpenCode. This document covers installation and configuration.

> **Note for OpenCode users:** OpenCode uses built-in TypeScript hooks (in `line-cook-opencode/src/`), not the Python hooks described here. See the OpenCode plugin source for details.

## Quick Start

Run the setup command in your Claude Code or OpenCode session:

```
/line:setup              # Interactive mode
/line:setup minimal      # Session context + safety only
/line:setup tailored     # Auto-format for detected languages
/line:setup all          # Enable all formatters
```

## Overview

| Hook | Trigger | Purpose |
|------|---------|---------|
| SessionStart | Session begins | Prime context with beads workflow |
| PreToolUse | Before Bash commands | Block dangerous commands |
| PostToolUse | After Edit/Write | Auto-format edited files |
| Stop | Agent stops | Warn about uncommitted work |

## Prerequisites

### Python 3.8+

Hooks are written in Python for cross-platform compatibility (Windows, Linux, macOS).

**Verify installation:**
```bash
python3 --version
```

**Installation:**

| Platform | Command |
|----------|---------|
| macOS | `brew install python3` |
| Ubuntu/Debian | `sudo apt install python3` |
| Fedora | `sudo dnf install python3` |
| Windows | `winget install Python.Python.3.12` |
| Arch | `sudo pacman -S python` |

**Agent Install Instructions:**
```
Check if python3 is available. If not:
- macOS: brew install python3
- Ubuntu/Debian: sudo apt install python3
- Windows: winget install Python.Python.3.12
- Arch: sudo pacman -S python
Verify with: python3 --version
```

---

## Formatter Tools

The PostToolUse hook auto-formats files using language-specific formatters:

| Language | Tool | Quick Install |
|----------|------|---------------|
| Python | ruff | `pipx install ruff` |
| JS/TS | prettier or biome | `npm install -g prettier` |
| Go | gofmt/goimports | Included with Go |
| Rust | rustfmt | `rustup component add rustfmt` |
| Shell | shfmt, shellcheck | `brew install shfmt shellcheck` |
| Ruby | rubocop | `gem install rubocop` |
| GDScript | gdformat | `pipx install gdtoolkit` |

**Detailed installation instructions**: See [docs/tool-installation.md](docs/tool-installation.md) for all installation methods, platform-specific commands, and agent install instructions.

---

## Hook Configuration

Hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./hooks/session_start.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./hooks/pre_tool_use.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./hooks/post_tool_use.py",
            "timeout": 30
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ./hooks/stop_check.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

Run `/line:setup` to configure hooks for your project.

---

## Hook Files

| File | Purpose |
|------|---------|
| `hooks/session_start.py` | Prime context with beads workflow |
| `hooks/pre_tool_use.py` | Block dangerous commands |
| `hooks/post_tool_use.py` | Auto-format edited files |
| `hooks/stop_check.py` | Warn about uncommitted work |
| `hooks/settings.json` | Hook configuration template |

---

## Testing

Run the test suite to verify hooks work on your platform:

```bash
python3 hooks/test_hooks.py
```

Expected output:
```
============================================================
Line Cook Hooks Test Suite
Platform: linux  # or win32, darwin
Python: 3.12.x
============================================================

Testing hook_utils.py...
  [PASS] Log path: ~/.claude/hooks.log
  [PASS] Logger setup works

Testing pre_tool_use.py...
  [PASS] Safe command allowed
  [PASS] Dangerous command blocked
  [PASS] Empty command handled

... (more tests) ...

============================================================
ALL TESTS PASSED!
============================================================
```

---

## Windows Compatibility

Hooks are written in Python for cross-platform support. Windows-specific notes:

**Python Command:**
- Use `python` or `python3` depending on your installation
- Settings may need adjustment: `"command": "python ./hooks/session_start.py"`

**Path Handling:**
- All hooks use `pathlib.Path` and `os.path` for cross-platform paths
- Forward slashes work in most contexts on Windows

**Environment Variables:**
- `$CLAUDE_PROJECT_DIR` is set by Claude Code on all platforms
- `%USERPROFILE%` patterns are blocked in pre_tool_use.py

**Testing on Windows:**
```powershell
python hooks\test_hooks.py
```

---

## Debugging

View hook execution with debug mode:

```bash
claude --debug
```

Check hook logs:

```bash
# Logs are written to .claude/hooks.log in project or ~/.claude/hooks.log
tail -f .claude/hooks.log
```

Test hooks manually:

```bash
echo '{"tool_input":{"command":"git status"}}' | python3 ./hooks/pre_tool_use.py
echo $?  # Should be 0

echo '{"tool_input":{"command":"git push --force"}}' | python3 ./hooks/pre_tool_use.py
echo $?  # Should be 2
```

---

## Security Notes

- Hooks run with your user permissions
- Always review hook code before installation
- Use absolute paths for user-level hooks
- Validate inputs in custom hooks
- Never commit secrets to hook files

---

## Git Hooks

Line Cook also provides git hooks for enforcing session discipline at the git level.

### Pre-Push Hook

The pre-push hook enforces "landing the plane" discipline before pushing:

- **Warns** if issues are still in `in_progress` status
- **Warns** if there are uncommitted `.beads/` changes
- **Runs** `bd sync --flush-only` to ensure database changes are flushed

**Installation:**

Copy the pre-push hook to your project:

```bash
# From the line-cook repository
cp hooks/git/pre-push /path/to/your/project/.git/hooks/pre-push
chmod +x /path/to/your/project/.git/hooks/pre-push
```

Or manually create `.git/hooks/pre-push` with the script content.

**Behavior:**

| Check | Action |
|-------|--------|
| Issues in_progress | Warning (allows push) |
| Uncommitted .beads/ | Warning (allows push) |
| bd sync fails | Warning (allows push) |

The hook issues warnings but does not block pushes by default. This encourages good habits without forcing strict enforcement.

**Bypass:**

```bash
SKIP_SESSION_CHECK=1 git push   # Skip session check only
git push --no-verify            # Skip all git hooks
```

**Strict Mode:**

To block pushes when issues are in_progress, edit the hook and change the final `exit 0` in the in_progress check block to `exit 1`.

### Existing Hooks

Line Cook projects typically have these hooks installed (via beads):

| Hook | Purpose |
|------|---------|
| `pre-commit` | Version check, `bd sync --flush-only` |
| `post-merge` | Import updated issues after pull |
| `pre-push` | Session completion warnings |

Run `bd doctor` to see which hooks are installed and which are missing.
