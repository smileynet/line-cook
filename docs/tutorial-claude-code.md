# Tutorial: From Brainstorm to First Work Cycle

This tutorial walks you through the complete journey from initial brainstorming with an LLM to confident use of the full `/line:run` command. By the end, you'll understand each phase of the workflow and what to watch for as it runs.

**Prerequisites:**
- [beads](https://github.com/steveyegge/beads) installed (`bd` command available)
- line-cook installed (see [README.md](../README.md))
- A Git repository to work in
- Familiarity with Git basics

---

## Part 1: Understanding the Mental Models

Before diving into commands, understand the ideas that make Line Cook work.

> **Full reference:** [Mental Models](mental-models.md) covers these concepts in depth.

### Sessions, Not Streams

AI coding assistants have limited context windows. Treat interactions as bounded **sessions**, not endless conversations.

```
Session = Prep → Cook → Serve → Tidy → Push
```

Each session:
- Starts clean (fresh context, synced repo)
- Has one goal (a single task)
- Ends with artifact (code pushed, issues filed)
- Leaves memory (beads capture what happened)

**Why this matters:** When you clear context or start a new conversation, beads remember what was done. `bd ready` shows exactly where to pick up.

### Planning vs Execution

These are different modes. Don't mix them.

| Planning (You + AI brainstorm) | Execution (AI follows the plan) |
|-------------------------------|--------------------------------|
| Explore possibilities | Follow the recipe |
| Ask clarifying questions | One task at a time |
| Define scope | Verify before done |
| Create beads | File discoveries, don't act on them |

**The handoff:** After creating beads, clear your context. Start fresh with `/line:prep` for focused execution.

### Progressive Trust

Build confidence gradually:

```
MANUAL      →  BEADS      →  INDIVIDUAL  →  SERVICE
(you type)     (bd ready)    (/prep,/cook)  (/service)
```

Start by running commands separately. Graduate to `/line:run` once you understand each phase and trust the output.

### Guardrails as Recovery Points

Each command is a checkpoint. Nothing is permanent until `git push`.

| If this goes wrong... | Recovery |
|----------------------|----------|
| Cook made bad changes | `git checkout .` and retry |
| Serve rejected the code | Fix issues, run serve again |
| Forgot something | Run cook again, add to findings |
| Context got messy | Clear context, start fresh with prep |

**Key insight:** Line Cook's phases aren't just workflow—they're safe points to return to.

---

## Part 2: Planning with /mise

Before any code is written, you need a plan. Line Cook provides the `/line:mise` command to guide you through structured planning with three phases: brainstorm, plan, and finalize.

### The Three-Phase Planning Workflow

```
/line:brainstorm → /line:plan → /line:finalize
   (divergent)      (convergent)    (execution prep)
```

Each phase produces a reviewable artifact:
- **Brainstorm** outputs `docs/planning/brainstorm-<name>.md`
- **Plan** outputs `docs/planning/menu-plan.yaml`
- **Finalize** creates beads + test specifications

Between each phase, `/mise` pauses for your review. This prevents premature commitment and lets you iterate at each level.

### Example: Building a Reading List CLI

Let's say you want to build a simple CLI tool to track books you're reading. Instead of manually brainstorming, we'll use `/line:mise` to structure the planning.

### Step 1: Run /line:brainstorm

Start the planning cycle:

```
/line:mise
```

Or run brainstorm directly for more control:

```
/line:brainstorm
```

Claude will ask clarifying questions:

```
BRAINSTORM: Reading List CLI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Understanding the problem...

Questions:
  1. What info do you want to track per book? (title, author, pages, etc.)
  2. Where should data live? (local file, database, cloud?)
  3. Is this just for you, or will others use it?
```

You answer:

```
You: Just for me. I want title, author, and whether I've finished it.
     Local file is fine - keep it simple.
```

Claude explores approaches, identifies risks, and creates the brainstorm document:

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/brainstorm-reading-cli.md

Problem: Personal CLI to track reading list (title, author, finished)
User: Developer (you)
Recommended approach: JSON file storage with simple CRUD commands

Key decisions:
  - JSON file for simplicity (no database overhead)
  - Four core commands: add, list, done, remove
  - Search deferred to later iteration

Open questions: 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to proceed to planning phase?
- Review the brainstorm document
- Resolve any open questions
- Then continue to create structured plan

Continue to /line:plan? [Y/n]
```

### Step 2: Review the Brainstorm

Before proceeding, you can review `docs/planning/brainstorm-reading-cli.md`. This document captures:
- Problem statement and user context
- Technical approaches explored
- Risks and unknowns identified
- Recommended direction with rationale

If anything looks wrong, edit the document or ask Claude to adjust before continuing.

### Step 3: Run /line:plan

After confirming, Claude runs the plan phase:

```
MENU PLAN CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/menu-plan.yaml

Phases: 1
Features: 1
Tasks: 4

Breakdown:
  Phase 1: Core CLI
    - Feature 1.1: Basic reading list management
      - 4 tasks (storage + 3 commands)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to commit to beads and create test specs?
- Review the menu plan
- Make any edits to the YAML file
- Then continue to create beads

Continue to /line:finalize? [Y/n]
```

### Step 4: Review the Menu Plan

The menu plan is a YAML file you can edit:

```yaml
# docs/planning/menu-plan.yaml
phases:
  - id: phase-1
    title: "Phase 1: Core CLI"
    features:
      - id: feature-1.1
        title: "Basic reading list management"
        user_story: "As a reader, I want to track books so I know what I've read"
        acceptance_criteria:
          - "Can add books with title and author"
          - "Can list all books with finished status"
          - "Can mark books as finished"
        tasks:
          - title: "Implement JSON file storage"
            priority: 1
            tdd: true
          - title: "Add 'add book' command"
            priority: 2
            depends_on: ["Implement JSON file storage"]
          - title: "Add 'list books' command"
            priority: 2
            depends_on: ["Implement JSON file storage"]
          - title: "Add 'done' command"
            priority: 2
            depends_on: ["Implement JSON file storage"]
```

This is your chance to:
- Adjust task priorities
- Add or remove tasks
- Refine acceptance criteria
- Change dependencies

### Step 5: Run /line:finalize

After confirming, Claude converts the plan to beads:

```
MISE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Menu plan committed to beads and test specs created.

Beads Created:
  Epics: 1
  Features: 1
  Tasks: 4

Test Specs Created:
  BDD (features/): 1 .feature file
  TDD (specs/): 4 .md files

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

READY TO WORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Available tasks:
  lc-002 [P1] Implement JSON file storage

NEXT STEP: Run /line:prep to start working on tasks
```

### What Was Created

The finalize phase created:

**Beads** (in `.beads/`):
```
lc-001: Core CLI (epic)
├── lc-001.1: Basic reading list management (feature)
│   ├── lc-002: Implement JSON file storage [P1]
│   ├── lc-003: Add 'add book' command [P2] (blocked by lc-002)
│   ├── lc-004: Add 'list books' command [P2] (blocked by lc-002)
│   └── lc-005: Add 'done' command [P2] (blocked by lc-002)
```

**Test specs** (in `tests/`):
- `tests/features/feature-1.1-basic-reading-list.feature` (BDD)
- `tests/specs/implement-json-storage.md` (TDD)

### When to Skip Brainstorm

If requirements are already clear, skip directly to planning:

```
/line:mise skip-brainstorm
```

Or run phases individually for maximum control:

```bash
# Just explore
/line:brainstorm

# Already have brainstorm, need structure
/line:plan

# Already have menu plan, need beads
/line:finalize
```

### Clear Context Before Execution

Planning is done. Before starting execution, **clear your context** (new conversation or compact). This ensures:
- Fresh context for focused execution
- No confusion between planning discussion and task work
- Clean session boundaries

Then start fresh with `/line:prep`.

---

## Part 4: Starting Your First Session

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

## Part 5: Cooking Your First Task

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

## Part 6: Serving - Getting a Second Opinion

Before committing, `/line:serve` invokes a separate Claude instance to review your changes. This is AI peer review.

### What is Headless Claude?

**Headless Claude** means Claude running without an interactive terminal—a background process that receives a prompt, does work, and returns results. Think of it like running a script vs typing commands interactively.

Serve spawns a headless Claude with:
- A focused review prompt
- The diff of your changes
- Instructions to categorize findings

**Why fresh context matters:** The Claude that wrote the code has sunk cost—it made decisions and might rationalize them. A separate instance has no stake in defending those choices. It's more objective and more likely to "tell on itself" rather than gloss over problems to misrepresent success.

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

## Part 7: Tidy - Closing the Loop

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

## Part 8: Graduating to Full Automation

Now that you understand each phase, you can use `/line:run` to run them all together.

### The Full Cycle

```
/line:run
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

Notice that `/line:run` ends with a push. This is a **session boundary**—the natural point to clear context and start fresh.

For the next task, start a new conversation or use the `/compact` command. Each work cycle is designed to complete independently, preventing context bloat and keeping execution focused.

### When to Use Individual Commands

| Situation | Command |
|-----------|---------|
| Exploring what's available | `/line:prep` |
| Debugging cook issues | `/line:cook` alone |
| Skipping review for trivial changes | prep → cook → tidy |
| Understanding the review process | `/line:serve` alone |
| Just committing and pushing | `/line:tidy` |

### When to Use /line:run

- You're confident in the workflow
- You want focused execution without interruption
- The task is well-defined and ready

---

## Building Your Rhythm

Here's how to develop a sustainable workflow with Line Cook.

### Daily Pattern

**Start of day:**
```
/line:prep
```
See what's ready. Get oriented. Check if anything is blocked.

**During work:**
```
/line:run
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

## Recovery Paths

Things go wrong. Each phase of the workflow is a checkpoint—a known-good state you can return to. Understanding what happens at each phase helps you recover when something breaks.

### During Prep

Prep is about getting oriented. You're syncing with remote, surveying what's available, and picking a task. Problems here are usually about state—your local view doesn't match reality.

The good news: prep is read-only. Nothing you do here changes code. If something looks wrong, sync again or override the auto-selection.

| Problem | Solution |
|---------|----------|
| Beads out of sync | `bd sync` to pull latest |
| Merge conflicts | Ask Claude to help resolve, then `bd sync` |
| Wrong task selected | Specify task explicitly: `/line:cook lc-xxx` |

### During Cook

Cook is where code changes happen. This is the highest-risk phase because you're modifying files. But it's also the most recoverable—nothing is committed yet. All changes are local.

If cook produces bad output, you can always discard and retry. The key question is whether to fix forward (adjust the code) or reset (discard and try again). Small fixes: fix forward. Fundamentally wrong approach: reset.

| Problem | Solution |
|---------|----------|
| Code is wrong | `git checkout .` to discard changes, retry |
| Task too big | Stop, break into smaller beads, start fresh |
| Discovered blocking issue | Note in findings, file as blocker in tidy |
| Tests failing | Fix the tests before proceeding to serve |
| Context getting large | Finish cook, run tidy, clear context before next task |

### During Serve

Serve is the review checkpoint. A fresh Claude instance examines your changes with no memory of writing them—more objective, more likely to catch issues the original author would rationalize away.

Rejection here is normal and healthy. It means the safety net caught something. Don't skip serve just because it sometimes rejects code—that's the point.

| Problem | Solution |
|---------|----------|
| Review rejected | Fix issues, run `/line:serve` again |
| Reviewer found critical bug | Return to cook, fix, re-run serve |
| Auto-fix made wrong change | `git diff` to review, `git checkout <file>` to undo |

### During Tidy

Tidy is the commitment phase. You're filing discoveries as beads, committing code, and pushing to remote. Problems here are usually git-related—conflicts with remote, or issues with the commit itself.

Once push succeeds, the session is complete. Before that, you can still adjust.

| Problem | Solution |
|---------|----------|
| Commit failed | Check error, fix, retry tidy |
| Push failed | Check remote status, resolve conflicts, retry |
| Forgot to file something | Create bead manually with `bd create` |

### Session-Level Recovery

Sometimes you lose track of where you are. Maybe context got too long, maybe you got interrupted, maybe things just feel confused. The beads system is your anchor—it remembers state even when you don't.

| Problem | Solution |
|---------|----------|
| Confused about state | `bd show <task-id>` to see task details |
| Lost track of progress | `bd stats` and `bd ready` to survey |
| Context too long | Clear context, run `/line:prep` to resume |
| Need to abandon session | `git checkout .` to discard, task stays open |

### The Nuclear Option

If everything is confused and you want to start completely fresh:

```bash
git checkout .              # Discard local changes
git pull                    # Sync with remote
bd sync                     # Sync beads
```

Then start fresh with `/line:prep`. Your beads are still there—the work tracking survives even a full reset. You haven't lost your place, just your uncommitted changes.

---

## What's Next?

You now understand the complete Line Cook workflow. Here are your next steps:

1. **Try it** - Run through this tutorial with a real project
2. **Build trust** - Start with individual commands, graduate to `/line:run`
3. **Develop rhythm** - Use the daily pattern to build sustainable habits

The goal is confident, focused execution. Line Cook handles the discipline so you can focus on the work.

---

## Quick Reference

| Planning Commands | Purpose |
|-------------------|---------|
| `/line:mise` | Full planning cycle with pause points |
| `/line:brainstorm` | Explore problem space (divergent) |
| `/line:plan` | Create structured breakdown (convergent) |
| `/line:finalize` | Convert plan to beads + test specs |

| Execution Commands | Purpose |
|--------------------|---------|
| `/line:getting-started` | Quick workflow guide |
| `/line:prep` | Sync and show ready work |
| `/line:cook` | Execute a task with guardrails |
| `/line:serve` | AI peer review |
| `/line:tidy` | Commit, file findings, push |
| `/line:run` | Full execution cycle |

| Beads Command | Purpose |
|---------------|---------|
| `bd create --title="..." --type=task` | Create a task |
| `bd dep add <task> <depends-on>` | Add dependency |
| `bd ready` | Show unblocked tasks |
| `bd blocked` | Show blocked tasks |
| `bd stats` | Project overview |
| `bd sync` | Sync with remote |
