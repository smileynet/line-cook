# Research: Beads Go CLI Architecture

**Issue**: lc-cvo
**Date**: 2026-01-18
**Purpose**: Study how beads implements its Go CLI tool as the foundation for line-cook CLI design.

## Executive Summary

Beads is a mature Go CLI built with:
- **spf13/cobra** for command structure and CLI framework
- **spf13/viper** for configuration management
- **GoReleaser** for cross-platform builds and distribution
- Platform-specific code via Go build tags
- SQLite for storage with optional daemon mode
- Claude Code plugin integration via hooks and skills

## 1. CLI Structure and Command Organization

### Framework: spf13/cobra

Beads uses Cobra, the de facto standard for Go CLIs. Key patterns:

```
cmd/bd/
├── main.go          # Root command, persistent flags, init
├── create.go        # bd create command
├── update.go        # bd update command
├── list.go          # bd list command
├── sync.go          # bd sync command
├── daemon*.go       # Background daemon functionality
└── ...              # ~180+ Go files for commands
```

### Root Command Pattern

```go
var rootCmd = &cobra.Command{
    Use:   "bd",
    Short: "bd - Dependency-aware issue tracker",
    Long:  `Issues chained together like beads...`,
    PersistentPreRun: func(cmd *cobra.Command, args []string) {
        // Initialize context, signals, config
        initCommandContext()
        rootCtx, rootCancel = signal.NotifyContext(...)
    },
}
```

### Command Groups (Tufte-inspired)

Beads organizes commands into semantic groups for better help output:

```go
rootCmd.AddGroup(
    &cobra.Group{ID: "issues", Title: "Working With Issues:"},
    &cobra.Group{ID: "views", Title: "Views & Reports:"},
    &cobra.Group{ID: "deps", Title: "Dependencies & Structure:"},
    &cobra.Group{ID: "sync", Title: "Sync & Data:"},
    &cobra.Group{ID: "setup", Title: "Setup & Configuration:"},
    &cobra.Group{ID: "maint", Title: "Maintenance:"},
    &cobra.Group{ID: "advanced", Title: "Integrations & Advanced:"},
)
```

### Persistent Flags

```go
rootCmd.PersistentFlags().StringVar(&dbPath, "db", "", "Database path")
rootCmd.PersistentFlags().StringVar(&actor, "actor", "", "Actor name")
rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "JSON output")
rootCmd.PersistentFlags().BoolVar(&noDaemon, "no-daemon", false, "Direct mode")
rootCmd.PersistentFlags().BoolVarP(&verboseFlag, "verbose", "v", false, "Debug")
rootCmd.PersistentFlags().BoolVarP(&quietFlag, "quiet", "q", false, "Quiet")
```

## 2. Claude Code Hooks Integration

### Plugin Manifest (plugin.json)

```json
{
  "name": "beads",
  "version": "0.47.2",
  "hooks": {
    "SessionStart": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "bd prime"}]
    }],
    "PreCompact": [{
      "matcher": "",
      "hooks": [{"type": "command", "command": "bd prime"}]
    }]
  }
}
```

### Hook Types Supported
- **SessionStart**: Load context when Claude Code starts
- **PreCompact**: Preserve context before conversation compaction

### Git Hooks Integration

Beads also installs git hooks (pre-commit, post-merge, pre-push, etc.):

```go
//go:embed templates/hooks/*
var hooksFS embed.FS
```

Git hooks delegate to the CLI: `bd hook <event>` instead of complex shell scripts.

## 3. Cross-Platform Concerns

### Build Tags Pattern

Platform-specific code uses Go build tags:

```go
// daemon_unix.go
//go:build unix || linux || darwin

// daemon_windows.go
//go:build windows

// daemon_wasm.go (for potential WASM support)
//go:build wasm
```

### Platform Abstractions

| Function | Unix | Windows |
|----------|------|---------|
| `configureDaemonProcess` | `Setsid: true` | `CREATE_NEW_PROCESS_GROUP` |
| `sendStopSignal` | `SIGTERM` | `SIGTERM` → `Kill()` |
| `isProcessRunning` | `syscall.Kill(pid, 0)` | `OpenProcess` + `GetExitCodeProcess` |
| Signal handling | `SIGTERM, SIGINT, SIGHUP` | `SIGTERM, Interrupt` |

### EPERM Handling (Sandboxed Environments)

```go
func isProcessRunning(pid int) bool {
    err := syscall.Kill(pid, 0)
    if err == nil { return true }
    if err == syscall.EPERM { return true }  // Permission denied = exists
    return false  // ESRCH = no such process
}
```

## 4. Configuration and State Management

### Framework: spf13/viper

Configuration priority (highest to lowest):
1. Command-line flags
2. Environment variables (BD_*, BEADS_*)
3. Config file (config.yaml)
4. Defaults

### Config File Locations

Search order:
1. Project `.beads/config.yaml` (walks up from CWD)
2. User `~/.config/bd/config.yaml`
3. Home `~/.beads/config.yaml`

### Environment Variable Mapping

```go
v.SetEnvPrefix("BD")
v.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_"))
// BD_NO_DAEMON → "no-daemon"
// BD_LOCK_TIMEOUT → "lock-timeout"
```

### Storage Architecture

```
internal/storage/
├── storage.go      # Interface definitions
├── sqlite/         # Primary storage backend
├── memory/         # In-memory (testing)
├── factory/        # Factory pattern
└── dolt/           # Dolt backend (experimental)
```

Key interface:
```go
type Storage interface {
    CreateIssue(ctx, issue, actor) error
    GetIssue(ctx, id) (*Issue, error)
    UpdateIssue(ctx, id, updates, actor) error
    SearchIssues(ctx, query, filter) ([]*Issue, error)
    AddDependency(ctx, dep, actor) error
    // ...
}
```

### Daemon Mode

Beads supports a background daemon for performance:
- RPC client/server for CLI-daemon communication
- Auto-start on first command if enabled
- File system watcher for JSONL changes
- Graceful shutdown handling

## 5. Plugin/Extension Architecture

### Claude Code Plugin Structure

```
claude-plugin/
├── .claude-plugin/
│   └── plugin.json     # Manifest with hooks
├── agents/             # Agent definitions
├── commands/           # Slash command .md files
└── skills/
    └── beads/
        ├── SKILL.md    # Main skill definition
        ├── CLAUDE.md   # AI instructions
        └── resources/  # Additional documentation
```

### Skill Definition Pattern (SKILL.md)

```markdown
---
name: beads
description: >
  Git-backed issue tracker for multi-session work...
allowed-tools: "Read,Bash(bd:*)"
version: "0.47.1"
---
```

### Internal Hooks System

Beads has its own hook system for issue events:

```go
const (
    EventCreate = "create"
    EventUpdate = "update"
    EventClose  = "close"
)
```

Hooks live in `.beads/hooks/` and are executed async.

## 6. Build and Distribution

### GoReleaser Configuration

Targets:
- linux/amd64, linux/arm64
- darwin/amd64, darwin/arm64 (CGO_ENABLED=1)
- windows/amd64 (CGO_ENABLED=1, code-signed), windows/arm64
- android/arm64
- freebsd/amd64

### Distribution Channels

1. **GitHub Releases** - Pre-built binaries
2. **Homebrew** - `brew install steveyegge/beads/bd`
3. **npm** - `npm install @beads/bd` (native binary download)
4. **curl installer** - `curl -fsSL .../install.sh | bash`
5. **PowerShell installer** - `irm .../install.ps1 | iex`

### Version Injection

```go
var Version string  // Set via ldflags
var Build string    // Git short commit
var Commit string   // Full commit hash
var Branch string   // Branch name

// Build command:
go build -ldflags="-X main.Version={{.Version}} -X main.Build={{.ShortCommit}}"
```

### macOS Code Signing

Post-install re-signing to avoid Gatekeeper slowdown:
```bash
codesign --remove-signature "$binary_path"
codesign --force --sign - "$binary_path"
```

## Key Takeaways for line-cook

### Recommended Stack
- **CLI Framework**: spf13/cobra (mature, well-documented)
- **Config**: spf13/viper (seamless env/file/flag integration)
- **Build**: GoReleaser (handles cross-compilation, releases)

### Architecture Patterns to Adopt
1. **Command groups** for organized help
2. **Build tags** for platform-specific code
3. **Persistent flags** on root command
4. **Plugin manifest** (plugin.json) for Claude Code integration
5. **Skill.md format** for AI tool discovery

### Differences from beads
- line-cook doesn't need SQLite (uses beads for storage)
- Focus on workflow orchestration, not data management
- Simpler command set initially (prep, cook, serve, tidy)

### Migration Path
1. Port Python hooks to Go CLI subcommands
2. Hooks call `lc hook session-start` instead of Python
3. Slash commands invoke CLI or are generated from CLI
4. Git hooks delegate to CLI (thin shims)

## References

- Beads source: `~/.claude/plugins/marketplaces/beads-marketplace/`
- Cobra docs: https://cobra.dev/
- Viper docs: https://github.com/spf13/viper
- GoReleaser docs: https://goreleaser.com/
