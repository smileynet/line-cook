## Task

Configure Claude Code hooks for the line-cook workflow. Detects your project's languages and formatters, then generates tailored hooks.

**Arguments:** `$ARGUMENTS` (optional) - Setup mode: `minimal`, `tailored`, or `all`

## Process

### Step 1: Determine Mode

**If `$ARGUMENTS` provided:**
- Use that mode directly (`minimal`, `tailored`, or `all`)

**Otherwise:**
- Ask the user which mode they prefer

### Step 2: Explain Modes

Present the options to the user:

```
HOOKS SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

line-cook hooks automate workflow stages:
  • SessionStart  - Prime context with beads workflow info
  • PreToolUse    - Block dangerous commands (git push --force, rm -rf, etc.)
  • PostToolUse   - Auto-format edited files
  • Stop          - Warn about uncommitted/unpushed work

Setup modes:
  1) minimal   - Context + safety only (no auto-formatting)
  2) tailored  - Auto-format for YOUR project's languages
  3) all       - Enable all formatters (runs if installed)
```

Use AskUserQuestion if mode not provided:
- Question: "Which setup mode?"
- Options: minimal, tailored, all

### Step 3: Detect Project

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

### Step 4: Generate Hooks

Based on mode and detection, generate the post-tool-use hook:

**For `minimal` mode:**
- Skip PostToolUse hook generation
- Only enable SessionStart, PreToolUse, Stop

**For `tailored` mode:**
- Generate case statements only for detected language+formatter pairs
- Example: If Python detected and ruff available, add *.py case

**For `all` mode:**
- Generate case statements for all supported languages
- Each formatter checks `command -v` before running

Write the generated hook to `hooks/post-tool-use-edit.sh` (or create if hooks/ doesn't exist).

### Step 5: Generate Settings

Create the settings.json with enabled hooks:

```json
{
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],  // Only if not minimal
    "Stop": [...]
  }
}
```

Use absolute paths for the hook commands.

### Step 6: Offer Installation

Ask user how to install:

```
SETUP COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generated:
  ✓ hooks/post-tool-use-edit.sh (tailored for python, shell)
  ✓ hooks/settings.json

Install options:
  1) Project - Copy to .claude/settings.json (this project only)
  2) User    - Merge into ~/.claude/settings.json (all projects)
  3) Manual  - Show config, I'll install myself
```

Use AskUserQuestion:
- Question: "How should I install the hooks?"
- Options: Project, User, Manual

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

### Step 7: Verify

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
/line-setup              # Interactive mode selection
/line-setup minimal      # Quick setup, no formatting
/line-setup tailored     # Auto-detect and configure
/line-setup all          # Enable everything
```
