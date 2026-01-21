# Tutorial: From Brainstorm to First Work Cycle

This tutorial walks you through the complete journey from initial brainstorming with an LLM to confident use of the full `/line-work` command. By the end, you'll understand each phase of the workflow and what to watch for as it runs.

**Prerequisites:**
- [beads](https://github.com/steveyegge/beads) installed (`bd` command available)
- line-cook installed (see [README.md](../README.md))
- A Git repository to work in
- Familiarity with Git basics

---

## Part 1: Why Line Cook?

Before diving into the workflow, let's understand why Line Cook exists and the problems it solves.

### The Problem: Unstructured Sessions Drift

Working with AI coding assistants without structure leads to predictable problems:

- **Scope creep** - "While I'm here, let me also fix this..."
- **Lost context** - "What were we working on again?"
- **Forgotten discoveries** - "I noticed a bug but didn't write it down"
- **Unbounded sessions** - No clear stopping points
- **Unpushed work** - Changes sitting locally, never committed

Sound familiar? These aren't AI problems—they're discipline problems. Line Cook provides the discipline so you can focus on the work.

### The Kitchen Metaphor

Think of a professional kitchen:

- **The Chef** (you) designs the menu, plans the service, decides what gets made
- **The Line Cook** (this tool) executes orders systematically, calls out problems, follows recipes precisely

A good line cook doesn't redesign the dish mid-service. They execute what's been planned, note issues for the chef's attention, and keep the kitchen running smoothly.

That's Line Cook: structured execution of your plans.

### The Trust Ladder

Line Cook sits at a specific point on the automation spectrum:

| Approach | Control | Automation | Trust Required |
|----------|---------|------------|----------------|
| Manual prompting | Full | None | Low |
| Beads only | High | Low | Low |
| **Line Cook** | Medium | Medium | Medium |
| Gas Town | Low | High | High |

**Manual prompting**: You direct every action. Maximum control, but tiring.

**Beads only**: Track work in issues, but execute manually. Good for learning.

**Line Cook**: Structured cycles with guardrails. You plan, it executes systematically.

**Gas Town**: Autonomous agent framework. You describe goals, it figures out how.

Most people should start with beads, graduate to Line Cook as trust builds, and consider Gas Town for well-understood, repeatable tasks.

### The Guardrails Philosophy

Line Cook enforces five principles:

1. **Sync before work** - Always start with current state from remote
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles, todos complete
4. **File, don't block** - Discovered issues become new beads, not interruptions
5. **Push before stop** - Work isn't done until it's remote

These aren't arbitrary rules. Each prevents a common failure mode in AI-assisted development.

---

## Part 2: Brainstorming with the LLM

Before any code is written, you need a plan. Line Cook works best when tasks are well-defined and properly sized. Here's how to collaborate with Claude to break down a project.

### Example: Building a Reading List CLI

Let's say you want to build a simple CLI tool to track books you're reading. Here's how the conversation might unfold over several turns.

**Turn 1 - Start broad:**

```
You: I want to build a CLI tool that tracks my reading list.

Claude: Good project! Before we dive in, a few questions to scope this:

        1. What info do you want to track per book? (title, author, pages, etc.)
        2. Where should data live? (local file, database, cloud?)
        3. Is this just for you, or will others use it?
```

**Turn 2 - Narrow the scope:**

```
You: Just for me. I want title, author, and whether I've finished it.
     Local file is fine - keep it simple.

Claude: Perfect. A JSON file will work well for that. Now, what operations
        do you need?

        - Add a book
        - List all books
        - Mark a book as finished
        - Remove a book

        Anything else? Search? Stats? Export?
```

**Turn 3 - Decide what's MVP vs later:**

```
You: Those four are the core. Search would be nice but not essential.
     Let's keep the first version minimal.

Claude: Smart. We can add search later. So for MVP:

        **Storage** (build first - everything depends on this):
        - JSON file with load/save operations
        - Simple schema: [{title, author, finished}]

        **Commands** (build after storage):
        - `add` - title and author required
        - `list` - show all books, maybe indicate finished ones
        - `done` - mark a book finished
        - `remove` - delete by title or ID

        Should I structure this as beads? One epic for "Core CLI",
        with storage as the first task, then the commands?
```

**Turn 4 - Confirm the structure:**

```
You: Yes, that makes sense. The commands can't work without storage,
     so that dependency is real.

Claude: Exactly. Here's the structure:

        Epic: "Core CLI Commands"
        ├── Task: "Implement JSON storage" (no blockers)
        ├── Task: "Add command" (blocked by storage)
        ├── Task: "List command" (blocked by storage)
        ├── Task: "Done command" (blocked by storage)
        └── Task: "Remove command" (blocked by storage)

        Ready to create these beads?
```

### Why Multiple Turns Matter

Notice what happened:
- **Turn 1**: Broad idea, Claude asks clarifying questions
- **Turn 2**: Scope narrows based on your answers
- **Turn 3**: MVP vs nice-to-have distinction emerges
- **Turn 4**: Structure confirmed, ready to execute

Rushing to create tasks from a vague idea leads to rework. Taking a few turns to clarify scope saves time later.

### What You're Building

Through this conversation, you've identified:

| Type | Name | Notes |
|------|------|-------|
| Epic | Core CLI Commands | Groups related work |
| Task | JSON file storage | No dependencies (do first) |
| Task | Add book command | Depends on storage |
| Task | List books command | Depends on storage |
| Task | Done command | Depends on storage |
| Task | Remove command | Depends on storage (cut in Part 3) |

This structure captures both the work and the order it should happen in. Dependencies ensure you don't start "add book" before storage exists.

---

## Part 3: Creating Your First Beads

Now let's turn that brainstorm into tracked issues. Beads are git-native issues that travel with your repository.

### Initialize Beads (if needed)

If this is a new project, initialize beads first:

```bash
bd init
```

This creates a `.beads/` directory in your project.

### Ask Claude to Create the Beads

Rather than typing commands yourself, ask Claude to propose them:

```
You: Go ahead and create those beads. Show me what you'll run first.

Claude: I'll create the epic and tasks with dependencies. Here's my plan:

        # 1. Create the epic (container for related work)
        bd create --title="Core CLI commands" --type=epic --priority=2

        # 2. Create tasks as children of the epic
        bd create --title="Implement JSON file storage" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'add book' command" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'list books' command" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'done' command" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'remove' command" --type=task --priority=2 --parent=<epic-id>

        # 3. Add dependencies (commands depend on storage)
        bd dep add <add-id> <storage-id>
        bd dep add <list-id> <storage-id>
        bd dep add <done-id> <storage-id>
        bd dep add <remove-id> <storage-id>

        Should I proceed?
```

### Review Before Approving

Take a moment to review. This is your chance to catch issues:

```
You: Actually, let's drop "remove" for MVP - 3 commands is enough to start.
     We can add it later. Also, make storage P1 since everything depends on it.

Claude: Good catch. Updated plan:

        # 1. Create epic
        bd create --title="Core CLI commands" --type=epic --priority=2

        # 2. Create storage first (P1 - critical path)
        bd create --title="Implement JSON file storage" --type=task --priority=1 --parent=<epic-id>

        # 3. Create command tasks (P2 - after storage)
        bd create --title="Add 'add book' command" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'list books' command" --type=task --priority=2 --parent=<epic-id>
        bd create --title="Add 'done' command" --type=task --priority=2 --parent=<epic-id>

        # 4. Dependencies
        bd dep add <add-id> <storage-id>
        bd dep add <list-id> <storage-id>
        bd dep add <done-id> <storage-id>

        Proceed?
```

### Approve and Execute

```
You: Looks good. Go ahead.

Claude: Creating beads...

        ✓ Created lc-001: Core CLI commands (epic)
        ✓ Created lc-002: Implement JSON file storage (P1, parent: lc-001)
        ✓ Created lc-003: Add 'add book' command (P2, parent: lc-001)
        ✓ Created lc-004: Add 'list books' command (P2, parent: lc-001)
        ✓ Created lc-005: Add 'done' command (P2, parent: lc-001)

        Adding dependencies...

        ✓ lc-003 now depends on lc-002
        ✓ lc-004 now depends on lc-002
        ✓ lc-005 now depends on lc-002

        Done. Here's the structure:
```

### Verify the Structure

Claude shows you the result:

```
lc-001: Core CLI commands
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type: epic
Priority: P2
Status: open

Children:
  ○ lc-002: Implement JSON file storage [P1]
  ○ lc-003: Add 'add book' command [P2] (blocked by lc-002)
  ○ lc-004: Add 'list books' command [P2] (blocked by lc-002)
  ○ lc-005: Add 'done' command [P2] (blocked by lc-002)

Project stats:
  Open: 5 | In Progress: 0 | Blocked: 3 | Ready: 1
```

### Why Review Matters

Notice what happened:
- Claude proposed 4 command tasks, but you trimmed scope further (dropped remove)
- You upgraded storage priority since it's the critical path
- The review took 30 seconds but prevented creating work you didn't want

The pattern: **Propose → Review → Approve → Execute**

This keeps you in control while letting Claude do the typing.

### Clear Context Before Execution

Planning is done. Before starting execution, **clear your context** (new conversation or compact). This ensures:
- Fresh context for focused execution
- No confusion between planning discussion and task work
- Clean session boundaries

Then start fresh with `/line-prep`.

---

## Part 4: Starting Your First Session

Now let's see how `/line-prep` shows you what's ready to work on.

### Run Prep

```
/line-prep
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

New to line-cook? Run /line-getting-started for workflow guide.

NEXT STEP: /line-cook lc-002
```

### What Prep Does

1. **Syncs** - Pulls latest from remote, syncs beads
2. **Surveys** - Counts ready, in-progress, and blocked tasks
3. **Picks** - Identifies the highest-priority unblocked task
4. **Reports** - Shows you the lay of the land

Prep will never recommend a blocked task. It respects your dependency structure.

---

## Part 5: Cooking Your First Task

This is where work happens. Run `/line-cook` to execute the recommended task.

### Run Cook

```
/line-cook
```

Or specify the task explicitly:

```
/line-cook lc-002
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

NEXT STEP: /line-serve (review) or /line-tidy (commit)
```

Cook won't mark a task complete if tests fail or code doesn't compile.

---

## Part 6: Serving - Getting a Second Opinion

Before committing, `/line-serve` invokes a separate Claude instance to review your changes. This is AI peer review.

### Run Serve

```
/line-serve
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

NEXT STEP: /line-tidy
```

### Verdicts

- **APPROVED** - Changes look good, proceed to tidy
- **NEEDS_CHANGES** - Issues found, may want to address before committing
- **BLOCKED** - Critical problems, should fix before proceeding

Serve is non-blocking. Even if review fails, you can continue to tidy.

---

## Part 7: Tidy - Closing the Loop

Tidy is where everything gets captured and pushed. Nothing is lost.

### Run Tidy

```
/line-tidy
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

## Part 8: Graduating to Full Automation

Now that you understand each phase, you can use `/line-work` to run them all together.

### The Full Cycle

```
/line-work
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

### The Session Boundary

Notice that `/line-work` ends with a push. This is a **session boundary**—the natural point to clear context and start fresh.

For the next task, start a new conversation or use the `/compact` command. Each work cycle is designed to complete independently, preventing context bloat and keeping execution focused.

### When to Use Individual Commands

| Situation | Command |
|-----------|---------|
| Exploring what's available | `/line-prep` |
| Debugging cook issues | `/line-cook` alone |
| Skipping review for trivial changes | prep → cook → tidy |
| Understanding the review process | `/line-serve` alone |
| Just committing and pushing | `/line-tidy` |

### When to Use /line-work

- You're confident in the workflow
- You want focused execution without interruption
- The task is well-defined and ready

---

## Building Your Rhythm

Here's how to develop a sustainable workflow with Line Cook.

### Daily Pattern

**Start of day:**
```
/line-prep
```
See what's ready. Get oriented. Check if anything is blocked.

**During work:**
```
/line-work
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
2. **Build trust** - Start with individual commands, graduate to `/line-work`
3. **Develop rhythm** - Use the daily pattern to build sustainable habits

The goal is confident, focused execution. Line Cook handles the discipline so you can focus on the work.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/line-getting-started` | Quick workflow guide |
| `/line-prep` | Sync and show ready work |
| `/line-cook` | Execute a task with guardrails |
| `/line-serve` | AI peer review |
| `/line-tidy` | Commit, file findings, push |
| `/line-work` | Full cycle (all four) |

| Beads Command | Purpose |
|---------------|---------|
| `bd create --title="..." --type=task` | Create a task |
| `bd dep add <task> <depends-on>` | Add dependency |
| `bd ready` | Show unblocked tasks |
| `bd blocked` | Show blocked tasks |
| `bd stats` | Project overview |
| `bd sync` | Sync with remote |
