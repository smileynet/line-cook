# Git Hooks Integration Patterns Research

Research for line-cook CLI git hooks integration.

## Git Hook Types Relevant to Line-Cook

Based on research, these are the most relevant git hooks:

### Client-Side Hooks

| Hook | Trigger | Use Case for Line-Cook |
|------|---------|------------------------|
| `pre-commit` | Before commit message editor opens | Validate session state, check for uncommitted work |
| `prepare-commit-msg` | After default message created | Add metadata (session ID, task ID) to commit messages |
| `post-commit` | After commit completes | Log commits, update session tracking |
| `pre-push` | Before push to remote | Enforce session completion, verify all work committed |
| `post-checkout` | After git checkout | Detect context switch, suggest session recovery |
| `post-merge` | After git merge/pull | Sync state after receiving remote changes |

### Recommended Hooks for Line-Cook

**Primary (implement first):**
1. `pre-push` - Enforce session completion before push (highest value)
2. `pre-commit` - Validate state before commit
3. `post-checkout` - Context recovery after branch switch

**Secondary:**
4. `prepare-commit-msg` - Add session/task metadata to commits
5. `post-merge` - Sync after pull operations

## CLI Tool Hook Management Patterns

### Pattern 1: Husky (Node.js ecosystem)

**Installation:**
- Uses `prepare` npm script to auto-install on `npm install`
- Creates `.husky/` directory with shell scripts sourcing a common `husky.sh`
- Modern Husky (v9+) uses directory convention rather than git config

**Hook Structure:**
```bash
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"
npm test
```

**Pros:**
- Simple setup, widely adopted
- Shell scripts are version-controlled
- Auto-installs via npm

**Cons:**
- Requires Node.js runtime
- Sequential execution (slower)

### Pattern 2: Lefthook (Go-based)

**Installation:**
- `lefthook install` command
- YAML configuration (`lefthook.yml`)
- Single static binary, no runtime dependencies

**Hook Structure:**
```yaml
pre-commit:
  parallel: true
  jobs:
    - name: lint
      run: golangci-lint run
    - name: test
      run: go test ./...
```

**Pros:**
- Fast (Go binary, parallel execution)
- Language-agnostic
- Rich configuration (globs, parallel, tags)

**Cons:**
- More complex configuration
- Less ecosystem adoption than Husky

### Pattern 3: Beads (Go CLI)

Beads uses a **thin shim pattern** - the most elegant approach I've found.

**Installation:**
- `bd hooks install` command
- Embeds hook templates via Go's `embed` package
- Supports multiple install locations:
  - `.git/hooks/` (default, local-only, not versioned)
  - `.beads-hooks/` (versioned, shareable via `--shared` - commit to share with team)
  - `.beads/hooks/` (Dolt backend via `--beads` - hooks integrate with database)

**Hook Structure (Thin Shim):**
```bash
#!/usr/bin/env sh
# bd-shim v1
# bd-hooks-version: 0.48.0
#
# This shim delegates to 'bd hook pre-commit' which contains
# the actual hook logic.

if ! command -v bd >/dev/null 2>&1; then
    echo "Warning: bd command not found" >&2
    exit 0
fi

exec bd hook pre-commit "$@"
```

**Key Features:**
1. **Thin shims** - Hooks call `bd hook <hook-name>` (singular), logic lives in CLI binary
2. **Version tracking** - Shims have version comments for outdated detection
3. **Hook chaining** - `--chain` flag preserves existing hooks (renamed to `.old`)
4. **Hook status** - `bd hooks list` shows installed/outdated status
5. **Embedded templates** - Go `embed` package bundles templates in binary
6. **Cobra subcommands** - `bd hooks install/uninstall/list/run` for management, `bd hook <name>` for shim execution

**Implementation in Beads:**

```go
// Embed templates at compile time
//go:embed templates/hooks/*
var hooksFS embed.FS

// Install command with options
func installHooksWithOptions(embeddedHooks map[string]string, force, shared, chain, beadsHooks bool) error {
    // Determine target directory
    var hooksDir string
    if beadsHooks {
        hooksDir = filepath.Join(beadsDir, "hooks")
    } else if shared {
        hooksDir = ".beads-hooks"
    } else {
        hooksDir, _ = git.GetGitHooksDir()
    }

    // Handle existing hooks
    for hookName, hookContent := range embeddedHooks {
        hookPath := filepath.Join(hooksDir, hookName)
        if _, err := os.Stat(hookPath); err == nil {
            if chain {
                os.Rename(hookPath, hookPath + ".old")
            } else if !force {
                os.Rename(hookPath, hookPath + ".backup")
            }
        }
        os.WriteFile(hookPath, []byte(hookContent), 0755)
    }

    // Configure git if using shared hooks
    if shared {
        exec.Command("git", "config", "core.hooksPath", ".beads-hooks").Run()
    }
}

// Run command - called by shims
var hooksRunCmd = &cobra.Command{
    Use:   "run <hook-name> [args...]",
    Short: "Execute a git hook (called by thin shims)",
    Run: func(cmd *cobra.Command, args []string) {
        hookName := args[0]
        hookArgs := args[1:]

        switch hookName {
        case "pre-commit":
            exitCode = runPreCommitHook()
        case "pre-push":
            exitCode = runPrePushHook(hookArgs)
        // ... other hooks
        }
        os.Exit(exitCode)
    },
}
```

## Recommended Approach for Line-Cook

Based on this research, I recommend the **Beads thin shim pattern** for line-cook:

> **Note:** This architecture applies to a future `lc` Go CLI binary. Line-cook currently
> uses shell-based Claude Code hooks (`hooks/*.sh`). The Go CLI would provide the full
> hook management capabilities described below.

### Architecture

```
line-cook/
├── cmd/
│   └── hooks.go              # Hook management commands
├── internal/
│   └── hooks/
│       ├── hooks.go          # Hook logic implementations
│       └── templates/        # Embedded hook templates
│           ├── pre-commit
│           ├── pre-push
│           └── post-checkout
```

### Commands

```bash
lc hooks install [--shared] [--chain] [--force]  # Install hooks
lc hooks uninstall                                # Remove hooks
lc hooks list                                     # Show status
lc hooks run <hook-name> [args...]               # Execute hook (for shims)
```

### Hook Template Example (pre-push)

```bash
#!/usr/bin/env sh
# lc-shim v1
# lc-hooks-version: 0.1.0
#
# line-cook pre-push hook
# Enforces session completion before push

if ! command -v lc >/dev/null 2>&1; then
    echo "Warning: lc not found, skipping session check" >&2
    exit 0
fi

exec lc hooks run pre-push "$@"
```

### Hook Logic (pre-push)

```go
func runPrePushHook(args []string) int {
    // 1. Check for active session
    if hasActiveSession() {
        // 2. Verify session is properly completed
        if !sessionIsComplete() {
            fmt.Fprintln(os.Stderr, "❌ Active session not completed")
            fmt.Fprintln(os.Stderr, "")
            fmt.Fprintln(os.Stderr, "Run: lc session end")
            fmt.Fprintln(os.Stderr, "Or:  lc session abort")
            return 1
        }
    }

    // 3. Check for uncommitted changes
    if hasUncommittedChanges() {
        fmt.Fprintln(os.Stderr, "❌ Uncommitted changes detected")
        return 1
    }

    return 0
}
```

### Why This Pattern

1. **Upgrades are seamless** - Hook logic in CLI binary, shims just delegate
2. **No runtime dependencies** - Go binary is self-contained
3. **Team sharing** - `--shared` flag for versioned hooks
4. **Hook chaining** - Preserves existing workflows (pre-commit framework, etc.)
5. **Version tracking** - Can detect and warn about outdated hooks
6. **Consistent with beads** - Users already familiar with pattern

### Implementation Priority

1. **Phase 1**: `lc hooks install/uninstall/list` commands
2. **Phase 2**: `pre-push` hook (session completion enforcement)
3. **Phase 3**: `post-checkout` hook (context recovery)
4. **Phase 4**: `pre-commit` and `prepare-commit-msg` hooks

## Sources

- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [Husky Documentation](https://typicode.github.io/husky/)
- [Lefthook vs Husky Comparison](https://www.edopedia.com/blog/lefthook-vs-husky/)
- [Beads source code](https://github.com/steveyegge/beads)
