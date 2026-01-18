# Line Cook Hooks

Hooks automate workflow stages in Claude Code and OpenCode. This document covers installation and configuration.

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

The PostToolUse hook auto-formats files using these tools. Install only what you need.

---

### Python: ruff

Fast Python linter and formatter. Replaces black, isort, flake8.

| | |
|---|---|
| Homepage | https://docs.astral.sh/ruff/ |
| GitHub | https://github.com/astral-sh/ruff |

**Installation:**

| Method | Command |
|--------|---------|
| pipx (recommended) | `pipx install ruff` |
| pip | `pip install ruff` |
| brew | `brew install ruff` |
| conda | `conda install -c conda-forge ruff` |
| cargo | `cargo install ruff` |

**Agent Install Instructions:**
```
Install ruff for Python formatting.
Preferred order: pipx, pip, brew (macOS), cargo.
Commands:
- pipx install ruff
- pip install ruff
- brew install ruff
- cargo install ruff
Verify: ruff --version
```

---

### JavaScript/TypeScript: prettier

Opinionated code formatter for JS, TS, JSON, YAML, Markdown.

| | |
|---|---|
| Homepage | https://prettier.io/ |
| GitHub | https://github.com/prettier/prettier |

**Installation:**

| Method | Command |
|--------|---------|
| npm (global) | `npm install -g prettier` |
| npm (local) | `npm install --save-dev prettier` |
| yarn | `yarn add --dev prettier` |
| pnpm | `pnpm add -D prettier` |
| brew | `brew install prettier` |

**Agent Install Instructions:**
```
Install prettier for JS/TS/JSON/YAML/MD formatting.
For projects with package.json: npm install --save-dev prettier
For global install: npm install -g prettier
Alternative: brew install prettier (macOS)
Verify: prettier --version
```

---

### JavaScript/TypeScript: biome

Fast formatter and linter. Alternative to prettier + eslint.

| | |
|---|---|
| Homepage | https://biomejs.dev/ |
| GitHub | https://github.com/biomejs/biome |

**Installation:**

| Method | Command |
|--------|---------|
| npm (global) | `npm install -g @biomejs/biome` |
| npm (local) | `npm install --save-dev @biomejs/biome` |
| brew | `brew install biome` |
| cargo | `cargo install biome` |

**Agent Install Instructions:**
```
Install biome as faster alternative to prettier.
For projects: npm install --save-dev @biomejs/biome
For global: npm install -g @biomejs/biome
Verify: biome --version
```

---

### Go: gofmt / goimports

Standard Go formatters. goimports also manages imports.

| | |
|---|---|
| gofmt docs | https://pkg.go.dev/cmd/gofmt |
| goimports docs | https://pkg.go.dev/golang.org/x/tools/cmd/goimports |

**Installation:**

| Tool | Command |
|------|---------|
| gofmt | Included with Go |
| goimports | `go install golang.org/x/tools/cmd/goimports@latest` |

**Go Installation:**

| Platform | Command |
|----------|---------|
| macOS | `brew install go` |
| Ubuntu/Debian | `sudo apt install golang-go` |
| Windows | `winget install GoLang.Go` |
| Arch | `sudo pacman -S go` |

**Agent Install Instructions:**
```
gofmt is included with Go. For goimports:
1. Ensure Go is installed
2. Ensure $GOPATH/bin or $HOME/go/bin is in PATH
3. Run: go install golang.org/x/tools/cmd/goimports@latest
Verify: goimports -h
```

---

### Rust: rustfmt

Standard Rust formatter, included with rustup.

| | |
|---|---|
| Homepage | https://rust-lang.github.io/rustfmt/ |
| GitHub | https://github.com/rust-lang/rustfmt |

**Installation:**

```bash
rustup component add rustfmt
```

**Rust Installation:**

| Platform | Command |
|----------|---------|
| Unix/macOS | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Windows | Download installer from https://rustup.rs |

**Agent Install Instructions:**
```
rustfmt is included with Rust via rustup.
If Rust installed but rustfmt missing:
  rustup component add rustfmt
If Rust not installed:
  Unix/macOS: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  Windows: Download from https://rustup.rs
Verify: rustfmt --version
```

---

### Shell: shfmt

Shell script formatter supporting bash, sh, mksh.

| | |
|---|---|
| GitHub | https://github.com/mvdan/sh |

**Installation:**

| Platform | Command |
|----------|---------|
| brew | `brew install shfmt` |
| go | `go install mvdan.cc/sh/v3/cmd/shfmt@latest` |
| apt | `sudo apt install shfmt` |
| snap | `sudo snap install shfmt` |
| pacman | `sudo pacman -S shfmt` |

**Agent Install Instructions:**
```
Install shfmt for shell script formatting.
- macOS: brew install shfmt
- Ubuntu/Debian: sudo apt install shfmt
- Arch: sudo pacman -S shfmt
- Go: go install mvdan.cc/sh/v3/cmd/shfmt@latest
Verify: shfmt --version
```

---

### Shell: shellcheck

Shell script static analysis tool.

| | |
|---|---|
| Homepage | https://www.shellcheck.net/ |
| GitHub | https://github.com/koalaman/shellcheck |

**Installation:**

| Platform | Command |
|----------|---------|
| brew | `brew install shellcheck` |
| apt | `sudo apt install shellcheck` |
| dnf | `sudo dnf install ShellCheck` |
| pacman | `sudo pacman -S shellcheck` |
| Windows | `winget install koalaman.shellcheck` |

**Agent Install Instructions:**
```
Install shellcheck for shell script linting.
- macOS: brew install shellcheck
- Ubuntu/Debian: sudo apt install shellcheck
- Fedora: sudo dnf install ShellCheck
- Arch: sudo pacman -S shellcheck
- Windows: winget install koalaman.shellcheck
Verify: shellcheck --version
```

---

### Ruby: rubocop

Ruby static code analyzer and formatter.

| | |
|---|---|
| Homepage | https://rubocop.org/ |
| GitHub | https://github.com/rubocop/rubocop |

**Installation:**

| Method | Command |
|--------|---------|
| gem | `gem install rubocop` |
| bundler | Add `gem 'rubocop'` to Gemfile |

**Agent Install Instructions:**
```
Install rubocop for Ruby formatting.
Global: gem install rubocop
For projects with Gemfile: add gem 'rubocop', group: :development
Verify: rubocop --version
```

---

### GDScript: gdformat

Godot GDScript formatter (part of gdtoolkit).

| | |
|---|---|
| GitHub | https://github.com/Scony/godot-gdscript-toolkit |

**Installation:**

| Method | Command |
|--------|---------|
| pipx (recommended) | `pipx install gdtoolkit` |
| pip | `pip install gdtoolkit` |

**Agent Install Instructions:**
```
Install gdtoolkit for GDScript formatting.
Includes gdformat and gdlint.
- pipx install gdtoolkit
- pip install gdtoolkit
Requires Python 3.7+.
Verify: gdformat --version
```

---

## Agent Tool Installer

For Claude Code or OpenCode agents, use this workflow to install formatters:

### Step 1: Detect Project Languages

```python
# Check for language indicators
python_project = exists("*.py") or exists("pyproject.toml") or exists("setup.py")
js_project = exists("package.json") or exists("*.ts") or exists("*.js")
go_project = exists("go.mod") or exists("*.go")
rust_project = exists("Cargo.toml") or exists("*.rs")
shell_project = exists("*.sh")
ruby_project = exists("Gemfile") or exists("*.rb")
godot_project = exists("project.godot") or exists("*.gd")
```

### Step 2: Check Available Formatters

```bash
command -v ruff        # Python
command -v prettier    # JS/TS/JSON/YAML/MD
command -v biome       # JS/TS (alternative)
command -v gofmt       # Go (included with Go)
command -v goimports   # Go (imports)
command -v rustfmt     # Rust
command -v shfmt       # Shell
command -v shellcheck  # Shell (linter)
command -v rubocop     # Ruby
command -v gdformat    # GDScript
```

### Step 3: Install Missing Formatters

Based on detected languages, offer to install missing formatters:

```
Detected: Python, Shell
Missing formatters:
  - ruff (Python): pipx install ruff
  - shfmt (Shell): brew install shfmt
  - shellcheck (Shell): brew install shellcheck

Would you like me to install these?
```

### Step 4: Verify Installation

```bash
ruff --version
shfmt --version
shellcheck --version
```

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
