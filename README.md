# Line Cook

**You design. It ships.**

Focus on the what and why—Line Cook handles the how. Structured execution with guardrails that keeps you in deep work while AI runs the prep→cook→serve→tidy cycle.

## Quick Start

```bash
# 1. Initialize beads in your project
bd init

# 2. Create some tasks
bd create --title="Implement user auth" --type=feature --priority=1
bd create --title="Add login form" --type=task

# 3. Run the workflow
/line:work
```

That's it. Line Cook syncs your repo, picks a ready task, executes it with guardrails, reviews the work, and commits when done.

## What It Does

```mermaid
graph LR
    subgraph "You + AI"
        A[Brainstorm] --> B[Create beads]
    end
    subgraph "Line Cook"
        C[/prep] --> D[/cook] --> E[/serve] --> F[/tidy]
    end
    B --> C
    F --> |next task| C
```

| Command | What happens |
|---------|--------------|
| `/prep` | Sync git, load context, show ready work |
| `/cook` | Claim a task, execute with guardrails |
| `/serve` | Review completed work (AI peer review) |
| `/tidy` | Commit, sync beads, push |
| `/work` | Run the full cycle |

## Installation

> **Requires:** [beads](https://github.com/steveyegge/beads) for task tracking, Git, Claude Code or OpenCode

### Claude Code

```bash
/plugin marketplace add smileynet/line-cook
/plugin install line@line-cook
```

Commands: `/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`, `/line:work`

### OpenCode

```bash
opencode plugin install https://github.com/smileynet/line-cook
```

Commands: `/line-prep`, `/line-cook`, `/line-serve`, `/line-tidy`, `/line-work`

## The Guardrails

Line Cook enforces discipline so you don't have to:

- **Sync before work** - Always start with current state
- **One task at a time** - Focus prevents scope creep
- **Verify before done** - Tests pass, code compiles
- **File, don't block** - Discovered issues become new beads
- **Push before stop** - Work isn't done until it's pushed

> **Tip: The Retro Epic Pattern**
>
> Create a "Retro" epic for minor findings: refactoring ideas, doc gaps, "maybe we should..." thoughts. File them as low-priority beads as you work. Review when you have breathing room. Captures feedback without derailing focus.

## Hooks (Optional)

Auto-format code, block dangerous commands, warn about uncommitted work:

```bash
/line:setup  # Interactive configuration
```

See [HOOKS.md](HOOKS.md) for details.

---

## Why Line Cook?

Line Cook sits between manual prompting and full autonomy:

| Approach | Control | Automation |
|----------|---------|------------|
| Manual prompting | Full | None |
| Beads | High | Low |
| **Line Cook** | Medium | Medium |
| Gas Town | Low | High |

The goal: build confidence in AI workflows before going full YOLO mode.

### The Kitchen Metaphor

- **Chef** (you) plans the menu during brainstorming
- **Line cook** (this tool) executes orders systematically

A good line cook follows the recipe and calls out problems—but doesn't redesign the dish mid-service.

## Influences

Built on ideas from:

- **[beads](https://github.com/steveyegge/beads)** - Git-native issue tracking for AI development. Line Cook orchestrates beads execution.
- **[Gas Town](https://github.com/steveyegge/gastown)** - Autonomous agent framework. Line Cook is the stepping stone toward that level of trust.
- **[Vibe Coding](https://bookshop.org/p/books/vibe-coding-building-production-grade-software-with-genai-chat-agents-and-beyond-gene-kim/b6e53e37eeba8cac)** - Gene Kim & Steve Yegge's book on AI-assisted development. The "file, don't block" principle and checkpoint patterns come from here.

## Project Structure

```
line-cook/
├── commands/           # Slash commands
├── hooks/              # Claude Code hooks (Python)
├── line-cook-opencode/ # OpenCode plugin
├── HOOKS.md            # Hooks documentation
└── TESTING.md          # Testing guide
```

## License

MIT

## Related

- [beads](https://github.com/steveyegge/beads) - Git-native issue tracking
- [Gas Town](https://github.com/steveyegge/gastown) - Autonomous agent framework
- [meta-claude](https://github.com/smileynet/meta-claude) - Claude Code skills and documentation
