# Getting Started

When the user says "getting started", "tutorial", "help with line cook", or similar:

**Read and display the full Line Cook tutorial to the user.**

Use the Read tool to read the tutorial file at `docs/tutorial-kiro.md` (in the line-cook repository root).

After reading, output the entire contents to the user so they can follow along. Do not summarize or act on it - display it for reference.

If the file cannot be found, display this fallback quick reference:

---

## Line Cook - Quick Start

Line Cook provides structured workflow cycles for AI-assisted development. Sync → Execute → Review → Commit.

### The Workflow

```
prep → cook → serve → tidy
  ↓      ↓      ↓      ↓
sync  execute review commit
```

Or run the full cycle: `work`

### Get Started in 3 Steps

1. **Sync and see what's ready**
   ```
   prep
   ```
   Shows available tasks and next step.

2. **Execute a task**
   ```
   cook
   ```
   Works through a task with verification.

3. **Complete and push**
   ```
   tidy
   ```
   Commits, files issues, and pushes to remote.

### Learn More

- **Full tutorial**: `docs/tutorial-kiro.md` in line-cook repository
- **User documentation**: [README.md](https://github.com/smileynet/line-cook/blob/main/README.md)
- **Technical details**: [AGENTS.md](https://github.com/smileynet/line-cook/blob/main/AGENTS.md)
- **Task tracking**: Line Cook uses [beads](https://github.com/steveyegge/beads) for git-native issue tracking

### Need Help?

Run `prep` at any time to see what's ready to work on.

