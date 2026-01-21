# Kiro CLI Context Preservation Research

Research findings for context preservation events in Kiro CLI.

## Executive Summary

**Kiro CLI does NOT have a `session.compacting` event equivalent.** There are no hooks that fire before, during, or after compaction operations.

This means line-cook cannot automatically preserve workflow state when Kiro's context is compacted, unlike the implementation possible in Claude Code and OpenCode.

## Available Hook Types

Kiro CLI supports exactly 5 hook types:

| Hook | Trigger | Use Case |
|------|---------|----------|
| `AgentSpawn` | Agent initializes | Load initial context |
| `UserPromptSubmit` | User sends prompt | Inject context, validate |
| `PreToolUse` | Before tool runs | Block dangerous operations |
| `PostToolUse` | After tool runs | Auto-format, validate |
| `Stop` | Assistant finishes response | Post-processing tasks |

**None of these relate to context compaction.**

## Compaction Behavior

### Manual Compaction
- User runs `/compact` command
- Older messages summarized, recent ones retained

### Automatic Compaction
- Triggers when context window overflows
- No warning or hook before it happens

### Configuration
```bash
kiro-cli settings compaction.excludeMessages 4        # Message pairs to keep
kiro-cli settings compaction.excludeContextWindowPercent 5  # % to retain
```

### Post-Compaction State
- Creates a new session (original can be resumed via `/chat resume`)
- Context changes NOT preserved between sessions

## Impact on Line Cook

### What We Can't Do
- Automatically save workflow state before compaction
- Inject context recovery instructions into compacted session
- Detect when compaction is about to happen

### Workarounds

#### 1. User-Initiated Context Recovery

Add to steering file:
```markdown
## After Context Clear or Compaction

If you've lost workflow context (don't remember current task, can't see beads state):

1. Run `bd prime` to reload beads context
2. Run `bd list --status=in_progress` to find active work
3. Resume with `/cook` or start fresh with `/prep`
```

#### 2. AgentSpawn Hook for Priming

The `AgentSpawn` hook fires when agent initializes. Use it to prime context:

```json
{
  "hooks": {
    "AgentSpawn": {
      "command": "bash .kiro/scripts/session-start.sh",
      "timeout_ms": 30000
    }
  }
}
```

This won't help with compaction (which doesn't restart the agent), but it helps new sessions.

#### 3. Knowledge Base Integration (Experimental)

Kiro has experimental persistent context storage:
> "An experimental feature enables persistent context storage and retrieval across chat sessions with semantic search capabilities."

This could potentially be used for workflow state, but it's experimental and not documented.

#### 4. Manual /compact Awareness

Teach users to run recovery after compaction:
```
User: compact
Agent: [context summarized]
User: prep
Agent: [re-syncs state, shows ready tasks]
```

## Comparison with Other Platforms

| Feature | Claude Code | OpenCode | Kiro |
|---------|-------------|----------|------|
| Pre-compaction hook | ✓ `session.compacting` | ✓ plugin event | ✗ None |
| Auto-prime after compact | ✓ via hook | ✓ via plugin | ✗ Manual only |
| Context persistence | ✓ CLAUDE.md | ✓ AGENTS.md | ✓ steering/ |

## Recommendation for Line Cook

Accept the limitation and document the workaround:

1. **AgentSpawn hook** primes context for new sessions
2. **Steering file** instructs user to run `prep` after compaction
3. **No automatic recovery** - users must manually re-sync

Update steering file:
```markdown
## Context Recovery

After `/compact` or context clear:
1. Say "prep" to re-sync state
2. Or run `bd prime` for beads context only

Note: Unlike Claude Code, Kiro cannot auto-restore workflow state after compaction.
```

## Sources

- [Kiro Context Management](https://kiro.dev/docs/cli/chat/context/)
- [Kiro Hooks Documentation](https://kiro.dev/docs/cli/hooks/)
- [Kiro CLI Changelog](https://kiro.dev/changelog/cli/)
- [Kiro Experimental Features](https://kiro.dev/docs/cli/experimental/)
