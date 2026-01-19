---
description: Compact context with Line Cook workflow state preserved
allowed-tools: Bash, Read
---

## Summary

**Trigger context compaction while preserving Line Cook workflow state.**

Use this when context is getting long and you want to compact while ensuring the current task, phase, and key findings are preserved.

**STOP after outputting.** Wait for user to run `/compact` manually.

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

### Step 3: Trigger Compaction

Output the compaction command for the user to run:

```
COMPACT: Line Cook context preservation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run this command to compact with workflow state preserved:

/compact <instructions>

Where <instructions> is:

---
<constructed instructions from step 2>
---

After compaction completes, the session will continue with your
current task and phase context restored.
```

**Important:** This command prepares the compaction instructions but the user must run `/compact` manually. Claude Code's `/compact` is a built-in CLI command that must be invoked directly by the user, not triggered from within another command's execution.

## Why Manual Invocation?

Claude Code's `/compact` command is a built-in that:
1. Cannot be triggered programmatically from plugin commands
2. Requires user confirmation before proceeding
3. Rewrites the entire conversation history

This command prepares the optimal instructions so the user can run `/compact` with confidence that their Line Cook workflow state will be preserved.

## Alternative: Let Auto-Compaction Handle It

If you prefer not to manually compact:
1. Continue working until auto-compaction triggers
2. The SessionStart hook will re-inject beads context automatically
3. You may need to remind Claude of the specific task details

Manual compaction with this command gives more control over what's preserved.

## Example Output

```
COMPACT: Line Cook context preservation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run this command to compact with workflow state preserved:

/compact PRESERVE LINE COOK WORKFLOW STATE:

Active Task:
  lc-0g6: Add /line:compact command with workflow-specific instructions
  Phase: cook
  Status: Command file created, testing in progress

Key Context:
  - Research showed /compact accepts custom instructions
  - SessionStart hook handles post-compaction context reload

Pending Changes:
  A commands/compact.md

After compaction completes, continue with cook phase testing.

---

After compaction, continue from the current phase.
```

## Example Usage

```
/line:compact
```

This command takes no arguments.
