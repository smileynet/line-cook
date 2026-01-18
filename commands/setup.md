## Task

Configure Claude Code hooks for the line-cook workflow. Detects your project's languages and formatters, then generates tailored hooks.

**Arguments:** `$ARGUMENTS` (optional) - Setup mode: `minimal`, `tailored`, or `all`

## Process

### Step 1: Gather User Preferences

**If `$ARGUMENTS` provided:**
- Use that mode directly (`minimal`, `tailored`, or `all`)
- Still ask about install scope

**Otherwise:**
- Ask BOTH questions at once using AskUserQuestion with multiple questions

Present the setup context first:

```
HOOKS SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

line-cook hooks automate workflow stages:
  • SessionStart  - Prime context with beads workflow info
  • PreToolUse    - Block dangerous commands (git push --force, rm -rf, etc.)
  • PostToolUse   - Auto-format edited files
  • Stop          - Warn about uncommitted/unpushed work
```

Use AskUserQuestion with TWO questions simultaneously:

**Question 1 - Mode:**
- Header: "Mode"
- Question: "Which setup mode?"
- Options:
  - `tailored (Recommended)` - Auto-format for YOUR project's languages
  - `minimal` - Context + safety only (no auto-formatting)
  - `all` - Enable all formatters (runs if installed)

**Question 2 - Scope:**
- Header: "Install"
- Question: "Where should hooks be installed?"
- Options:
  - `Project (Recommended)` - Copy to .claude/settings.json (this project only)
  - `User` - Merge into ~/.claude/settings.json (all projects)
  - `Manual` - Show config, I'll install myself

### Step 2: Detect Project

Run detection and show results:

```bash
# Detect languages
find . -name "*.py" -o -name "pyproject.toml" | head -1  # Python
find . -name "package.json" -o -name "*.ts" | head -1     # JS/TS
find . -name "go.mod" -o -name "*.go" | head -1           # Go
find . -name "Cargo.toml" -o -name "*.rs" | head -1       # Rust
find . -name "*.sh" | head -1                              # Shell
find . -name "Gemfile" -o -name "*.rb" | head -1          # Ruby

# Detect formatters
command -v ruff && echo "ruff"
command -v prettier && echo "prettier"
command -v gofmt && echo "gofmt"
command -v rustfmt && echo "rustfmt"
command -v shfmt && echo "shfmt"
command -v shellcheck && echo "shellcheck"
```

Output detection results:

```
Detected:
  Languages:  python, shell
  Formatters: ruff, shellcheck

Mode: tailored
```

### Step 3: Configure Hooks

Hooks are Python scripts for cross-platform compatibility.

**For `minimal` mode:**
- Skip PostToolUse hook
- Only enable SessionStart, PreToolUse, Stop

**For `tailored` mode:**
- Update `hooks/post_tool_use.py` FORMATTERS dict for detected languages only
- Example: If Python detected and ruff available, keep .py entries

**For `all` mode:**
- Use default `hooks/post_tool_use.py` with all formatters enabled
- Each formatter is checked with `shutil.which()` before running

Hook files:
- `hooks/session_start.py` - Context priming
- `hooks/pre_tool_use.py` - Command validation
- `hooks/post_tool_use.py` - Auto-formatting
- `hooks/stop_check.py` - Work verification

### Step 4: Generate Settings

Create the settings.json with enabled hooks:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [{
          "type": "command",
          "command": "python3 ./hooks/session_start.py",
          "timeout": 30
        }]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{
          "type": "command",
          "command": "python3 ./hooks/pre_tool_use.py",
          "timeout": 5
        }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{
          "type": "command",
          "command": "python3 ./hooks/post_tool_use.py",
          "timeout": 30
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python3 ./hooks/stop_check.py",
          "timeout": 10
        }]
      }
    ]
  }
}
```

Note: For `minimal` mode, omit the PostToolUse section.

### Step 5: Install Hooks

Based on user's scope selection from Step 1:

**If Project:**
```bash
mkdir -p .claude
cp hooks/settings.json .claude/settings.json
```

**If User:**
- Read existing ~/.claude/settings.json
- Merge hooks section
- Write back

**If Manual:**
- Output the settings.json content
- Explain where to put it

### Step 6: Verify

After installation, verify hooks are configured:

```
HOOKS INSTALLED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Active hooks:
  ✓ SessionStart  - Auto-prime workflow context
  ✓ PreToolUse    - Block dangerous commands
  ✓ PostToolUse   - Auto-format (python, shell)
  ✓ Stop          - Verify work is saved

Hooks take effect on next session start.
Run /hooks in Claude Code to verify configuration.
```

## Supported Languages & Formatters

| Language | Extensions | Formatters |
|----------|------------|------------|
| Python | .py, pyproject.toml | ruff, black, isort |
| JavaScript | .js, .jsx, .mjs, package.json | prettier, biome, eslint |
| TypeScript | .ts, .tsx, tsconfig.json | prettier, biome, eslint |
| Go | .go, go.mod | gofmt, goimports |
| Rust | .rs, Cargo.toml | rustfmt |
| Shell | .sh, .bash | shfmt, shellcheck |
| Ruby | .rb, Gemfile | rubocop |
| GDScript | .gd, project.godot | gdformat |
| JSON/YAML/MD | .json, .yaml, .yml, .md | prettier |

## Example Usage

```
/line:setup              # Interactive mode selection
/line:setup minimal      # Quick setup, no formatting
/line:setup tailored     # Auto-detect and configure
/line:setup all          # Enable everything
```
