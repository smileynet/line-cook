# OpenCode Session Management and Compaction Research

Research conducted: 2026-01-19
Related bead: lc-xhu

## Summary

OpenCode provides **significantly more programmatic control** than Claude Code, including a client-server architecture with SDK, plugin system with 25+ event hooks, and full TUI control via HTTP API.

## Research Questions Answered

### 1. Can OpenCode start new sessions programmatically?

**Yes.** Multiple methods available:

- **CLI non-interactive mode**: `opencode -p "your prompt"` runs a single prompt without TUI
- **SDK**: `client.session.create({ body: { title: "..." } })`
- **Server API**: HTTP endpoints for session management

### 2. Does OpenCode support context compaction? Can it be triggered programmatically?

**Yes, both automatic and programmatic.**

**Automatic compaction:**
- Triggers at ~95% context window capacity (`effective_context_window_percent`)
- Configurable via `compaction.auto: true/false` in config
- Can disable via `OPENCODE_DISABLE_AUTOCOMPACT` env var

**Programmatic:**
- `/compact` command in TUI
- SDK: Send compaction request through session API
- Plugin event: `session.compacted` fires after compaction

**Compaction process:**
1. Detects overflow via `SessionCompaction.isOverflow()`
2. Creates assistant message marked `summary: true`
3. Sends conversation to LLM with compaction prompt
4. Stores summary, truncates older messages

**Pruning:**
- Separate from compaction
- Removes old tool outputs to save tokens
- Configurable: `compaction.prune: true/false`
- Protected threshold: 40,000 tokens retained
- Minimum trigger: 20,000+ tokens saveable

### 3. TUI Control: Can OpenCode's TUI be controlled externally?

**Yes - this is a key differentiator from Claude Code.**

**Client-server architecture:**
- TUI is a client connecting to local server (default `localhost:4096`)
- Server exposes OpenAPI 3.1 spec
- Multiple clients can connect to same server

**TUI control endpoints (`/tui/*`):**
- `/tui/append-prompt` - Add text to prompt input
- `/tui/submit-prompt` - Execute current prompt
- `/tui/execute-command` - Run slash commands
- `/tui/open-sessions` - Open session selector
- `/tui/open-models` - Open model selector
- `/tui/show-toast` - Display notifications
- `/tui/control/next`, `/tui/control/response` - Bidirectional control

**SDK methods:**
```javascript
tui.appendPrompt("text")
tui.submitPrompt()
tui.showToast("message")
tui.openSessions()
tui.openModels()
```

**This enables:**
- IDE plugins (VS Code) controlling OpenCode
- External automation driving TUI
- Programmatic workflows with visual feedback

### 4. What hooks or APIs exist for session lifecycle?

**Plugin system with 25+ event hooks:**

**Session events:**
- `session.created`, `session.updated`, `session.deleted`
- `session.compacted`, `session.error`, `session.idle`
- `session.status`, `session.diff`

**Tool events:**
- `tool.execute.before` - Pre-execution hook (can intercept)
- `tool.execute.after` - Post-execution hook

**File/LSP events:**
- `file.edited`, `file.watcher.updated`
- `lsp.client.diagnostics`, `lsp.updated`

**Message events:**
- `message.part.removed`, `message.part.updated`
- `message.removed`, `message.updated`

**Other:**
- `command.executed`, `permission.replied`, `server.connected`

**Plugin context provides:**
- Current project info
- Git worktree
- Working directory
- SDK client for AI interactions

### 5. Can a single command start a new session AND begin new work?

**Yes.**

```bash
# Non-interactive single prompt
opencode -p "implement feature X"

# With specific model
opencode -p "implement feature X" -m <model-name>

# JSON output for parsing
opencode -p "implement feature X" -f json
```

Or via SDK:
```javascript
const session = await client.session.create({ body: { title: "Feature X" } })
await client.session.prompt({
  path: { id: session.id },
  body: { parts: [{ type: "text", text: "implement feature X" }] }
})
```

## Comparison: OpenCode vs Claude Code

| Capability | Claude Code | OpenCode |
|------------|-------------|----------|
| **Session creation** | `claude "prompt"` or `-p` flag | `opencode -p "prompt"` or SDK |
| **Session resume** | `--continue`, `--resume <id>` | SDK session management |
| **Auto-compaction** | Yes - at context limit | Yes - 95% threshold trigger |
| **Programmatic compact** | No (hooks observe only) | Yes - SDK/API |
| **TUI control** | None - intentionally separated | Full HTTP API + SDK |
| **External IPC** | None | Client-server architecture |
| **Plugin/hook system** | Hooks (can observe/block, not trigger) | Plugins (25+ events, can intercept) |
| **IDE integration** | VS Code extension | Server API for any IDE |

## Key Architectural Differences

### Claude Code
- **Separation of concerns**: Interactive TUI vs programmatic `-p` mode are distinct
- **Hooks are reactive**: Can observe and block, but can't trigger commands
- **No external TUI control**: Design choice for simplicity/security
- **Pattern**: Chain `-p` + `--resume` for programmatic workflows

### OpenCode
- **Unified server**: TUI is just one client to the server
- **Full programmatic control**: SDK can do anything TUI can do
- **Plugin system**: Can intercept and modify behavior
- **Pattern**: SDK/API for complex automation, TUI for interactive use

## Implications for Line Cook

1. **OpenCode integration would be more capable** - Could control TUI directly, trigger compaction programmatically, and hook into more events

2. **Claude Code requires workarounds** - Must use `-p` mode for automation, can't control running TUI, compaction is manual only

3. **Cross-tool strategy** - line-cook's current architecture works with both:
   - Claude Code: Hook events + separate `-p` invocations
   - OpenCode: Could use full SDK for deeper integration

4. **Future consideration** - If migrating to OpenCode/Crush, could leverage:
   - `session.compacted` event for automatic workflow triggers
   - TUI control for hybrid interactive/automated workflows
   - Plugin system for deep integration

## Sources

- [OpenCode GitHub](https://github.com/opencode-ai/opencode)
- [OpenCode SDK Documentation](https://opencode.ai/docs/sdk/)
- [OpenCode Server Documentation](https://opencode.ai/docs/server/)
- [OpenCode Plugins Documentation](https://opencode.ai/docs/plugins/)
- [OpenCode CLI Documentation](https://opencode.ai/docs/cli/)
- [OpenCode Configuration](https://opencode.ai/docs/config/)
- [Context Management Deep Dive](https://deepwiki.com/sst/opencode/2.4-context-management-and-compaction)
