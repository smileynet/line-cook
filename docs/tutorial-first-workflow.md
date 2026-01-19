# Tutorial: From Brainstorm to First Work Cycle

This tutorial walks you through the complete journey from initial brainstorming with an LLM to confident use of the full `/line:work` command. By the end, you'll understand each phase of the workflow and what to watch for as it runs.

**Prerequisites:**
- [beads](https://github.com/steveyegge/beads) installed (`bd` command available)
- line-cook installed (see [README.md](../README.md))
- A Git repository to work in
- Familiarity with Git basics

---

## Part 1: Brainstorming with the LLM

Before any code is written, you need a plan. Line Cook works best when tasks are well-defined and properly sized. Here's how to collaborate with Claude to break down a project.

### Example: Building a Reading List CLI

Let's say you want to build a simple CLI tool to track books you're reading.

**Start the conversation:**

```
You: I want to build a CLI tool that tracks my reading list. Help me
     break this down into manageable tasks.

Claude: Let's identify the core capabilities you need:

        1. **Data storage** - Where do books live? (JSON file is simplest)
        2. **Core commands** - What can users do?
           - Add a book
           - List all books
           - Mark a book as read
           - Remove a book
        3. **Nice-to-haves** - What could come later?
           - Search/filter
           - Reading stats
           - Export to other formats

        I'd group these into:
        - An epic for "Core CLI Commands"
        - A task for "JSON file storage" (needed first)
        - Individual tasks for each command

        The command tasks depend on storage existing first.
```

### What You're Building

Through this conversation, you've identified:

| Type | Name | Notes |
|------|------|-------|
| Epic | Core CLI Commands | Groups related work |
| Task | JSON file storage | No dependencies (do first) |
| Task | Add book command | Depends on storage |
| Task | List books command | Depends on storage |
| Task | Mark read command | Depends on storage |

This structure captures both the work and the order it should happen in. Dependencies ensure you don't start "add book" before storage exists.

---

## Part 2: Creating Your First Beads

Now let's turn that brainstorm into tracked issues. Beads are git-native issues that travel with your repository.

### Initialize Beads (if needed)

```bash
bd init
```

This creates a `.beads/` directory in your project.

### Create the Epic

```bash
bd create --title="Core CLI commands" --type=epic --priority=2
```

Output:
```
Created issue: lc-001
  Title: Core CLI commands
  Type: epic
  Priority: P2
```

### Create the Storage Task

```bash
bd create --title="Implement JSON file storage" --type=task --priority=2 --parent=lc-001
```

Output:
```
Created issue: lc-002
  Title: Implement JSON file storage
  Type: task
  Priority: P2
  Parent: lc-001 (Core CLI commands)
```

### Create Command Tasks

```bash
bd create --title="Add 'add book' command" --type=task --priority=2 --parent=lc-001
bd create --title="Add 'list books' command" --type=task --priority=2 --parent=lc-001
bd create --title="Add 'mark read' command" --type=task --priority=2 --parent=lc-001
```

### Add Dependencies

Commands need storage to exist first:

```bash
bd dep add lc-003 lc-002  # 'add book' depends on storage
bd dep add lc-004 lc-002  # 'list books' depends on storage
bd dep add lc-005 lc-002  # 'mark read' depends on storage
```

### Verify Your Structure

```bash
bd show lc-001
```

Output:
```
lc-001: Core CLI commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: epic
Priority: P2
Status: open

Children:
  ○ lc-002: Implement JSON file storage
  ○ lc-003: Add 'add book' command (blocked by lc-002)
  ○ lc-004: Add 'list books' command (blocked by lc-002)
  ○ lc-005: Add 'mark read' command (blocked by lc-002)
```

Check project stats:

```bash
bd stats
```

Output:
```
Project Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Open:        5
In Progress: 0
Closed:      0
Blocked:     3

Ready to work: 1
```

Notice: Only 1 task is ready (storage). The others are blocked until storage is done.

---

## Part 3: Starting Your First Session

Now let's see how `/line:prep` shows you what's ready to work on.

### Run Prep

```
/line:prep
```

Watch the output carefully:

```
SESSION: reading-cli @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sync: ✓ up to date                   ← Git is current with remote

Ready: 1 tasks                        ← Tasks with no blockers
In progress: 0                        ← Nothing claimed yet
Blocked: 3                            ← Waiting on dependencies

EPIC IN FOCUS:
  lc-001 [P2] Core CLI commands       ← Your epic
  Progress: 0/4 children complete

NEXT TASK (part of epic):
  lc-002 [P2] Implement JSON storage  ← Auto-selected (no blockers)

New to line-cook? Run /line:getting-started for workflow guide.

NEXT STEP: /line:cook lc-002
```

### What Prep Does

1. **Syncs** - Pulls latest from remote, syncs beads
2. **Surveys** - Counts ready, in-progress, and blocked tasks
3. **Picks** - Identifies the highest-priority unblocked task
4. **Reports** - Shows you the lay of the land

Prep will never recommend a blocked task. It respects your dependency structure.

---

## Part 4: Cooking Your First Task

This is where work happens. Run `/line:cook` to execute the recommended task.

### Run Cook

```
/line:cook
```

Or specify the task explicitly:

```
/line:cook lc-002
```

### What to Watch

Cook will produce output like this:

```
COOKING: lc-002 - Implement JSON file storage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] Design storage schema ... ✓
[2/4] Create storage module ... ✓
[3/4] Implement CRUD operations ... in progress
[4/4] Add unit tests ... pending

Progress: 2/4 complete
```

**Watch for:**
- **Task breakdown** - Did it decompose the work sensibly?
- **Progress markers** - `✓` means done, `in progress` is current
- **Verification steps** - Tests should be part of the plan

### Findings During Execution

As Claude works, it may discover issues or improvements. These are noted but NOT filed immediately:

```
Findings (to file in /tidy):
  New tasks:
    - "Add validation for book titles"
  Potential issues:
    - "Edge case: empty reading list"
  Improvements:
    - "Consider adding timestamps to entries"
```

This is the "file, don't block" principle. Discoveries are captured for later triage, not interruptions.

### Completion

When done, you'll see verification results:

```
DONE: lc-002 - Implement JSON file storage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Created storage.py with JSON-based persistence for book records.
  Includes load, save, add, remove, and update operations.

Files changed:
  A src/storage.py
  A tests/test_storage.py

Verification:
  [✓] All todos complete
  [✓] Code compiles
  [✓] Tests pass (4 passed)

Findings (to file in /tidy):
  New tasks:
    - "Add validation for book titles"
  Improvements:
    - "Consider adding timestamps to entries"

NEXT STEP: /line:serve (review) or /line:tidy (commit)
```

Cook won't mark a task complete if tests fail or code doesn't compile.

---

## Part 5: Serving - Getting a Second Opinion

Before committing, `/line:serve` invokes a separate Claude instance to review your changes. This is AI peer review.

### Run Serve

```
/line:serve
```

### What Serve Does

1. **Collects changes** - Gets the diff from cook
2. **Invokes reviewer** - Spawns headless Claude with review prompt
3. **Categorizes findings** - Sorts issues by severity
4. **Auto-fixes nits** - Applies obvious fixes (trailing newlines, typos)

### Review Output

```
REVIEW: lc-002 - Implement JSON file storage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verdict: APPROVED

Summary:
  Clean implementation of JSON storage. Good test coverage.
  Error handling is appropriate for the use case.

Auto-fixed:
  - src/storage.py:45 - Added missing trailing newline

Issues to file in /tidy:
  - [P3] "Add file locking for concurrent access"
  - [P4/retro] "Consider dataclass for Book type"

Positive notes:
  - Good separation of concerns
  - Comprehensive test coverage
  - Clear function naming

NEXT STEP: /line:tidy
```

### Verdicts

- **APPROVED** - Changes look good, proceed to tidy
- **NEEDS_CHANGES** - Issues found, may want to address before committing
- **BLOCKED** - Critical problems, should fix before proceeding

Serve is non-blocking. Even if review fails, you can continue to tidy.

---

## Part 6: Tidy - Closing the Loop

Tidy is where everything gets captured and pushed. Nothing is lost.

### Run Tidy

```
/line:tidy
```

### What Tidy Does

1. **Files beads** - Discoveries from cook/serve become tracked issues
2. **Checks epics** - Closes any epics with all children complete
3. **Commits** - Creates a conventional commit
4. **Syncs beads** - Pushes bead changes to git
5. **Pushes code** - Sends everything to remote

### Tidy Output

```
TIDY: Session cleanup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SESSION SUMMARY
━━━━━━━━━━━━━━━

Task completed:
  Task: lc-002 - Implement JSON file storage
  Created storage.py with JSON persistence for book records.

Files changed:
  A src/storage.py (+87)
  A tests/test_storage.py (+45)

Problems encountered:
  - (none)

Issues closed: 1
  ✓ lc-002: Implement JSON file storage

Epics completed: 0

Issues filed: 3
  + lc-006: Add validation for book titles [P3]
  + lc-007: Add file locking for concurrent access [P3]
  + lc-008: Consider dataclass for Book type [P4/retro]

Commit: a1b2c3d
  feat: implement JSON file storage for reading list

Push: ✓ origin/main

Session complete.
```

### What Just Happened

The task is done. The code is pushed. Discovered issues are tracked. Dependencies are updated - lc-003, lc-004, and lc-005 are now unblocked.

Run `bd ready` and you'll see your command tasks are now available:

```bash
bd ready
```

```
Ready Tasks (3):
  lc-003 [P2] Add 'add book' command
  lc-004 [P2] Add 'list books' command
  lc-005 [P2] Add 'mark read' command
```

---

## Part 7: Graduating to Full Automation

Now that you understand each phase, you can use `/line:work` to run them all together.

### The Full Cycle

```
/line:work
```

This runs: **prep → cook → serve → tidy**

Output shows each phase completing:

```
WORK CYCLE: Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/4] PREP    ✓ synced
[2/4] COOK    ✓ executed
[3/4] SERVE   ✓ reviewed (APPROVED)
[4/4] TIDY    ✓ committed, pushed

Files: 2 changed
Commit: b4c5d6e
Issues filed: 1

───────────────────────────────────────────

TASK: lc-003 - Add 'add book' command

SUMMARY: Implemented 'add' command with title and author arguments.
         Validates input and writes to JSON storage.
```

### When to Use Individual Commands

| Situation | Command |
|-----------|---------|
| Exploring what's available | `/line:prep` |
| Debugging cook issues | `/line:cook` alone |
| Skipping review for trivial changes | prep → cook → tidy |
| Understanding the review process | `/line:serve` alone |
| Just committing and pushing | `/line:tidy` |

### When to Use /line:work

- You're confident in the workflow
- You want focused execution without interruption
- The task is well-defined and ready

---

## Part 8: Building Your Rhythm

Here's how to develop a sustainable workflow with Line Cook.

### Daily Pattern

**Start of day:**
```
/line:prep
```
See what's ready. Get oriented. Check if anything is blocked.

**During work:**
```
/line:work
```
Run focused cycles. One task at a time. Trust the process.

**When distracted:**
Note ideas but don't act on them. They'll become beads in tidy.

**End of day:**
Make sure your last cycle finished with `git push`. Work isn't done until pushed.

### Health Checks

Periodically check your project health:

```bash
bd stats        # Overall counts
bd blocked      # What's waiting on what
bd ready        # What you can work on
```

### The Parking Lot

Minor ideas and "someday" items shouldn't clog your main backlog. Create a Retrospective epic:

```bash
bd create --title="Retrospective" --type=epic --priority=4
```

Items filed under Retrospective are automatically excluded from prep/cook auto-selection. They're parked until you explicitly work on them.

### The Key Principles

1. **Sync before work** - Always start current
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles
4. **File, don't block** - Discoveries become beads, not interruptions
5. **Push before stop** - Work isn't done until it's remote

---

## What's Next?

You now understand the complete Line Cook workflow. Here are your next steps:

1. **Try it** - Run through this tutorial with a real project
2. **Read the reference** - `/line:getting-started` has the full beads command reference
3. **Set up hooks** - `/line:setup` configures auto-formatting and safety checks
4. **Build trust** - Start with individual commands, graduate to `/line:work`

The goal is confident, focused execution. Line Cook handles the discipline so you can focus on the work.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/line:prep` | Sync and show ready work |
| `/line:cook` | Execute a task with guardrails |
| `/line:serve` | AI peer review |
| `/line:tidy` | Commit, file findings, push |
| `/line:work` | Full cycle (all four) |

| Beads Command | Purpose |
|---------------|---------|
| `bd create --title="..." --type=task` | Create a task |
| `bd dep add <task> <depends-on>` | Add dependency |
| `bd ready` | Show unblocked tasks |
| `bd blocked` | Show blocked tasks |
| `bd stats` | Project overview |
| `bd sync` | Sync with remote |
