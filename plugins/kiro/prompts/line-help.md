**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. The user's message following this prompt is your input.

## Summary

**Show available commands with contextual suggestions.** Helps users discover and navigate Line Cook commands.

**Arguments:** `$ARGUMENTS` (optional) - Command name for detailed help

---

## Process

### Step 1: Check for Detailed Help Request

**If `$ARGUMENTS` provided:**
- Show detailed help for that specific command
- Skip to Step 5

**Otherwise:**
- Continue to gather context and show quick reference

### Step 2: Gather Workspace Context

Detect current workspace state:

```bash
# Check if beads directory exists
BEADS_PRESENT=false
if [ -d ".beads" ]; then
  BEADS_PRESENT=true
fi

# Get task counts (if beads present)
if $BEADS_PRESENT; then
  READY_COUNT=$(bd ready 2>/dev/null | grep -c "^lc-" || echo 0)
  IN_PROGRESS_COUNT=$(bd list --status=in_progress 2>/dev/null | grep -c "^lc-" || echo 0)
  BLOCKED_COUNT=$(bd blocked 2>/dev/null | grep -c "^lc-" || echo 0)
fi

# Check git status
GIT_STATUS="clean"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  GIT_STATUS="dirty"
fi
```

### Step 3: Determine Suggested Command

Based on context, suggest the most relevant next action:

| Context | Suggested Command |
|---------|-------------------|
| No .beads directory | `@line-mise` (start planning) |
| Beads present, no ready tasks | `@line-mise` (create more work) |
| Ready tasks available | `@line-cook <first-ready-id>` |
| In-progress tasks | `@line-cook <in-progress-id>` |
| Dirty working tree + tasks done | `@line-tidy` |

### Step 4: Output Quick Reference

Output the contextual help display:

```
╔══════════════════════════════════════════════════════════════╗
║  LINE COOK - Quick Reference                                 ║
╚══════════════════════════════════════════════════════════════╝

YOUR CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready tasks: <count> | In progress: <count> | Blocked: <count>
Working tree: <clean|dirty>
Suggested: <command based on context>

PLANNING (create work)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@line-mise         Full planning cycle (brainstorm→scope→finalize)
@line-brainstorm   Explore problem space (divergent thinking)
@line-scope        Create work breakdown (convergent thinking)
@line-finalize     Convert plan to beads and test specs
@line-plan-audit   Check bead health and structure
@line-architecture-audit  Analyze code structure and smells
@line-decision     Record architecture decisions (ADRs)

EXECUTION (do work)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@line-run          Full cycle (prep→cook→serve→tidy)
@line-prep         Sync state, show ready tasks
@line-cook         Execute task with TDD guardrails
@line-serve        Review changes (sous-chef)
@line-tidy         Commit and push
@line-plate        Validate completed feature

REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@line-getting-started   Workflow guide with bead reference
@line-loop              Autonomous loop management
@line-help <command>    Detailed help for specific command

For detailed help: @line-help <command>
```

**Contextual variations:**

**If no .beads directory:**
```
YOUR CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
No beads directory found.
Suggested: @line-mise (start planning your work)

Tip: Line Cook uses beads to track work across sessions.
     Run @line-mise to create your first work breakdown.
```

**If dirty working tree:**
```
YOUR CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready tasks: <count> | In progress: <count> | Blocked: <count>
Working tree: dirty (uncommitted changes)
Suggested: @line-tidy (commit your changes)

Tip: Run @line-tidy to commit changes before starting new work.
```

### Step 5: Output Detailed Help (If Command Specified)

**If `$ARGUMENTS` is a command name:**

Read the command file and output detailed help:

```bash
COMMAND_FILE="commands/${ARGUMENTS#line-}.md"
if [ ! -f "$COMMAND_FILE" ]; then
  # Try without prefix
  COMMAND_FILE="commands/$ARGUMENTS.md"
fi
```

Output format for detailed help:

```
╔══════════════════════════════════════════════════════════════╗
║  @line-<command> - <description from frontmatter>      ║
╚══════════════════════════════════════════════════════════════╝

SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Summary section from command file>

USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Example usage from command file>

ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Arguments if any>

RELATED COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<Previous/Next in workflow>

Back to overview: @line-help
```

**Command not found:**

```
Command not found: <argument>

Available commands:
  Planning: mise, brainstorm, scope, finalize, plan-audit, architecture-audit, decision
  Execution: run, prep, cook, serve, tidy, plate
  Reference: getting-started, loop, help

Run @line-help for overview.
```

---

## Command Descriptions

Quick reference for all commands:

| Command | Phase | Description |
|---------|-------|-------------|
| `@line-mise` | Planning | Full planning cycle (orchestrates brainstorm→scope→finalize) |
| `@line-brainstorm` | Planning | Explore problem space (divergent thinking) |
| `@line-scope` | Planning | Create work breakdown (convergent thinking) |
| `@line-finalize` | Planning | Convert plan to beads and test specs |
| `@line-plan-audit` | Planning | Check bead health and structure |
| `@line-architecture-audit` | Planning | Analyze code structure and smells |
| `@line-decision` | Planning | Record, list, or supersede architecture decisions |
| `@line-run` | Execution | Full cycle (orchestrates prep→cook→serve→tidy) |
| `@line-prep` | Execution | Sync state, show ready tasks |
| `@line-cook` | Execution | Execute task with TDD guardrails |
| `@line-serve` | Execution | Review changes (sous-chef subagent) |
| `@line-tidy` | Execution | Commit and push |
| `@line-plate` | Execution | Validate completed feature (maître subagent) |
| `@line-getting-started` | Reference | Workflow guide with bead reference |
| `@line-loop` | Reference | Autonomous loop management |
| `@line-help` | Reference | Contextual help for Line Cook commands |

---

## Workflow Relationships

```
PLANNING CYCLE              EXECUTION CYCLE
━━━━━━━━━━━━━━━             ━━━━━━━━━━━━━━━━
/brainstorm                 /prep
      ↓                           ↓
/scope                      /cook
      ↓                           ↓
/finalize                   /serve
                                  ↓
                            /tidy
                                  ↓
                            /plate (if feature complete)

/mise (orchestrator)        /run (orchestrator)
```

Planning creates work. Execution completes work.

---

## Example Usage

```
@line-help              # Show quick reference with context
@line-help cook         # Detailed help for cook command
@line-help mise         # Detailed help for mise command
```
