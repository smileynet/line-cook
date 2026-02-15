**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Interactive hands-on walkthrough of Line Cook.** Teaches the two-cycle workflow (Mise + Run) through guided exploration — either with a demo project or the user's real project.

**Arguments:** `$ARGUMENTS` (optional) - `demo` to jump straight to demo project setup

---

## Process

### Step 1: Welcome and State Detection

Check workspace state to tailor the experience:

```bash
# Check beads
BEADS_PRESENT=false
if [ -d ".beads" ]; then
  BEADS_PRESENT=true
fi

# Check for existing tasks
if $BEADS_PRESENT; then
  TASK_COUNT=$(bd list 2>/dev/null | grep -c "^" || echo 0)
fi

# Check git
GIT_CLEAN=true
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  GIT_CLEAN=false
fi
```

Output welcome:

```
WELCOME TO LINE COOK
━━━━━━━━━━━━━━━━━━━━

Line Cook organizes AI coding into two cycles:
  Mise Cycle: Ideas → Tasks (brainstorm, scope, finalize)
  Run Cycle:  Tasks → Code  (prep, cook, serve, tidy)

Let's walk through both.
```

### Step 2: Choose Learning Path

Ask the user:

**"How would you like to explore Line Cook?"**

1. Walk me through with a demo project
2. Explain using my current project
3. Just show me the commands
Ask the user:

**"How would you like to explore Line Cook?"**

1. Walk me through with a demo project
2. Explain using my current project
3. Just show me the commands

**If "Just show me the commands"** — Skip to Step 6.

### Step 3: Demo Project Setup (Demo Path Only)

**Skip this step if the user chose "current project".**

Ask the user which demo:
1. Simple (6 tasks, JavaScript) — recommended for first time
2. Web (16 tasks, Go web dashboard)
Ask the user which demo:
1. Simple (6 tasks, JavaScript) — recommended for first time
2. Web (16 tasks, Go web dashboard)

Set up the demo:

```bash
# Fetch demo content from GitHub
DEMO_NAME="demo-simple"  # or demo-web
gh api repos/smileynet/line-cook/contents/docs/demos/${DEMO_NAME}/issues.jsonl \
  --jq '.content' | base64 -d > /tmp/line-cook-demo-issues.jsonl

# Create temp project
DEMO_DIR=$(mktemp -d -t line-cook-demo-XXXXXX)
cd "$DEMO_DIR"
git init
git commit --allow-empty -m "Initial commit"

# Initialize beads and import
bd init
bd import /tmp/line-cook-demo-issues.jsonl
```

Tell the user:

```
Demo project created at: <path>

This project has <N> tasks organized into features and epics.
Let's explore what the Mise Cycle produced, then try the Run Cycle.
```

### Step 4: Mise Cycle Tour

Explain the planning cycle using concrete examples:

**Demo path:** Show what mise already produced (the imported beads).

```bash
bd stats
bd list
```

**Current project path:** Show their existing beads.

Walk through each phase:

```
THE MISE CYCLE: Ideas → Tasks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. /brainstorm — Explore the problem space
   Asks questions, researches approaches, identifies risks.
   Output: docs/planning/brainstorm-<name>.md

2. /scope — Structure the work
   Decomposes into epics → features → tasks with dependencies.
   Output: docs/planning/menu-plan.yaml

3. /finalize — Create trackable work items
   Converts the plan into beads with test specifications.
   Output: .beads/ directory + test specs

Or use /mise to run all three with pauses between phases.
```

Show their actual task hierarchy:

```bash
bd list --status=open
bd ready
```

Explain how tasks relate to features and epics using their data.

### Step 5: Run Cycle Tour

Explain the execution cycle:

```
THE RUN CYCLE: Tasks → Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. /prep — Sync and see what's ready
   Pulls latest changes, shows unblocked tasks.

2. /cook — Execute one task
   Claims it, writes tests first (TDD), implements, closes.

3. /serve — AI peer review
   Polisher cleans code, sous-chef reviews for issues.

4. /tidy — Commit and push
   Files any discoveries as new beads, commits, pushes.

Or use /run to run all four phases in sequence.
```

**Demo path:** Show what prep would recommend:

```bash
bd ready
```

Point out the highest-priority unblocked task and explain how cook would claim and execute it.

**Current project path:** Run prep to show their actual ready tasks and explain the flow.

Ask: **"Want to try running /prep to see your ready tasks?"**
Ask: **"Want to try running /prep to see your ready tasks?"**

### Step 6: Summary

Output the complete command reference with workflow context:

```
LINE COOK COMMAND MAP
━━━━━━━━━━━━━━━━━━━━

PLANNING (Mise Cycle)          EXECUTION (Run Cycle)
  @line-brainstorm             @line-prep
        ↓                            ↓
  @line-scope                  @line-cook
        ↓                            ↓
  @line-finalize               @line-serve
                                     ↓
                                @line-tidy
                                     ↓
                                @line-plate (feature done)
                                     ↓
                                @line-close-service (epic done)

  @line-mise (all 3)           @line-run (all 4)

UTILITIES
  @line-help             Command reference + suggestions
  @line-plan-audit       Check bead health
  @line-decision         Record architecture decisions
  @line-loop             Autonomous execution
  @line-whats-new        Recent changes
  @line-doctor           Troubleshooting

GETTING STARTED
  @line-init             Verify your setup
  @line-getting-started  The mental model
  @line-onboarding       This walkthrough
```

End with contextual next step:

- If demo project: "To try the full workflow, run `@line-run` in this demo project."
- If current project with ready tasks: "You have <N> ready tasks. Run `@line-run` to start executing."
- If current project with no tasks: "Run `@line-mise` to plan your first batch of work."
- If no beads: "Run `bd init` then `@line-mise` to get started."

---

## Example Usage

```
@line-onboarding              # Interactive walkthrough
@line-onboarding demo         # Jump straight to demo setup
```
