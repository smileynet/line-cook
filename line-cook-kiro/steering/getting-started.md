# Getting Started

When the user says "getting started", "tutorial", "help with line cook", or similar:

**Read and display the full Line Cook tutorial to the user.**

Use the Read tool to read the tutorial file at `docs/tutorial-kiro.md` (in the line-cook repository root).

After reading, output the entire contents to the user so they can follow along. Do not summarize or act on it - display it for reference.

If the file cannot be found, display this fallback quick reference:

---

## Line Cook - Quick Start

Line Cook provides structured workflow cycles for AI-assisted development.

### The Workflow

**Quick cycle (most common):**
```
prep → cook → serve → tidy
  ↓      ↓       ↓       ↓
sync  execute  review  commit
```
Use the quick cycle for individual tasks within a feature.

**Full service (feature delivery):**
```
mise → prep → cook → serve → tidy → plate
  ↓      ↓       ↓       ↓       ↓       ↓
plan   sync  execute  review  commit validate
```
Use full service when delivering a complete feature. The **plate** phase validates that all feature requirements are met before marking the feature complete.

### Get Started in 3 Steps

1. **Sync and see what's ready**
   ```bash
   git pull --rebase && bd sync && bd ready
   ```
   Shows available tasks and next step.

2. **Execute a task**
   ```bash
   bd update <id> --status in_progress
   bd show <id>
   ```
   Claims task and provides context for execution.

3. **Complete and push**
   ```bash
   bd close <id>
   git add . && git commit -m "..."
   bd sync && git push
   ```
   Commits, files issues, and pushes to remote.

### All Commands

| Command | Purpose |
|---------|---------|
| "mise" | Plan work breakdown before implementation |
| "prep" | Sync git, show ready tasks |
| "cook" | Claim and execute a task |
| "serve" | AI peer review of completed work |
| "tidy" | Commit, sync beads, push |
| "plate" | Validate completed feature |
| "service" | Full service (mise→prep→cook→serve→tidy→plate) |
| "work" | Quick cycle (prep→cook→serve→tidy) |

### Learn More

- **Full tutorial**: `docs/tutorial-kiro.md` in line-cook repository
- **User documentation**: [README.md](https://github.com/smileynet/line-cook/blob/main/README.md)
- **Technical details**: [AGENTS.md](https://github.com/smileynet/line-cook/blob/main/AGENTS.md)
- **Task tracking**: Line Cook uses [beads](https://github.com/steveyegge/beads) for git-native issue tracking

### Need Help?

Run `bd ready` at any time to see what's ready to work on.

