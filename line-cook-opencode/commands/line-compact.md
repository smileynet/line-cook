---
description: Compact context with Line Cook workflow state preserved
---

## Summary

**Trigger context compaction while preserving Line Cook workflow state.**

Use this when context is getting long and you want to compact while ensuring the current task, phase, and key findings are preserved.

---

## Process

### Step 1: Gather Current Workflow State

Before triggering compaction, capture the current state:

```bash
bd list --status=in_progress --json
```

Also identify:
- Current workflow phase (prep/cook/serve/tidy)
- Any key findings noted but not yet filed
- Recent file changes: `git status --short`

### Step 2: Build Compaction Instructions

Construct instructions that tell the compaction to preserve Line Cook context:

**Template:**
```
PRESERVE LINE COOK WORKFLOW STATE:

Active Task:
  <bead-id>: <title>
  Phase: <prep|cook|serve|tidy>
  Status: <what has been done so far>

Key Context:
  - <important finding 1>
  - <important finding 2>

Pending Changes:
  <git status summary>

After compaction, continue with the current workflow phase.
If cook was in progress, resume from where we left off.
```

### Step 3: Output Compaction Guidance

**Note:** OpenCode does not currently have a manual `/compact` command. Compaction happens automatically when context reaches ~95% capacity.

Output guidance for the user:

```
COMPACT: Line Cook context preservation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OpenCode does not support manual compaction commands.
Context compacts automatically at ~95% capacity.

Current workflow state to preserve:

---
<constructed instructions from step 2>
---

Options:
1. Continue working - auto-compaction will trigger when needed
2. Use /clear to start fresh, then /line-prep to reload context
3. If using experimental.session.compacting hook, this state
   will be injected automatically before compaction

The session.compacted hook can re-inject context after compaction.
See line-cook-opencode README for hook configuration.
```

## Platform Differences

| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| Manual compact | `/compact <instructions>` | Not available |
| Auto-compact | At context limit | At ~95% capacity |
| Pre-compact hook | PreCompact | experimental.session.compacting |
| Post-compact hook | SessionStart (compact) | session.compacted |

## Hook Configuration (Optional)

OpenCode can use hooks to preserve context automatically:

```json
{
  "experimental.session.compacting": {
    "command": "bd list --status=in_progress --json | head -1"
  }
}
```

This injects the current task context into the compaction prompt automatically.

## Alternative: Manual Fresh Start

If you need a clean context immediately:

1. Run `/clear` to reset the session
2. Run `/line-prep` to reload workflow context
3. Continue with `/line-cook <task-id>` for your active task

## Example Output

```
COMPACT: Line Cook context preservation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OpenCode does not support manual compaction commands.
Context compacts automatically at ~95% capacity.

Current workflow state to preserve:

---
PRESERVE LINE COOK WORKFLOW STATE:

Active Task:
  lc-0g6: Add /line:compact command with workflow-specific instructions
  Phase: cook
  Status: Command file created, testing in progress

Key Context:
  - Research showed /compact accepts custom instructions (Claude Code)
  - OpenCode uses experimental.session.compacting hook

Pending Changes:
  A commands/compact.md

---

Options:
1. Continue working - auto-compaction will trigger when needed
2. Use /clear to start fresh, then /line-prep to reload context
3. The session.compacted hook will re-inject context automatically

Session will continue with cook phase.
```

## Example Usage

```
/line-compact
```

This command takes no arguments.
