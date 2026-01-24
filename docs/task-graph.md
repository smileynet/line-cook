# Line Cook Task Graph

This document provides a comprehensive breakdown of the line-cook workflow as a task graph, showing all phases, sub-tasks, decision points, and guardrails.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LINE COOK WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌─────────────────┐
                          │      PREP       │  ← Mechanical
                          │  Sync & Identify│     CLI-only
                          └────────┬────────┘
                                   │ Ready tasks?
                                   │ Yes ▼
                          ┌─────────────────┐
                          │      COOK       │  ← AI-Assisted
                          │  Execute with    │     TUI required
                          │  Guardrails      │
                          └────────┬────────┘
                                   │ Complete?
                                   │ Yes ▼
                          ┌─────────────────┐
                          │     SERVE       │  ← AI-Assisted
                          │  Peer Review    │     TUI required
                          └────────┬────────┘
                                   │ Approved?
                                   │ Yes ▼
                          ┌─────────────────┐
                          │      TIDY       │  ← Mechanical
                          │  Commit & Push   │     CLI-only
                          └────────┬────────┘
                                   │
                                   └─▶ Work Complete
```

## Phase 1: PREP - Sync and Identify

**Purpose**: Mechanical phase to synchronize repository state and identify ready work items.

### Task Graph

```
PREP Phase
│
├─▶ Check prerequisites
│   ├─▶ Verify git repo exists
│   └─▶ Verify beads installed
│
├─▶ Sync git repository
│   ├─▶ git pull --rebase
│   └─▶ git fetch origin
│
├─▶ Sync beads tracker
│   ├─▶ bd sync
│   └─▶ Verify .beads/ directory
│
├─▶ Load session state
│   ├─▶ Check for existing session file
│   │   ├─▶ Found → Load state
│   │   └─▶ Not found → Create new session
│   └─▶ Verify current directory
│
├─▶ Query ready tasks
│   ├─▶ bd ready
│   │   ├─▶ Tasks found → List them
│   │   └─▶ No tasks → Show message
│   └─▶ Parse task IDs
│
└─▶ Output results
    ├─▶ Show ready tasks table
    ├─▶ Show current session info
    └─▶ Return exit code
        ├─▶ 0 = Success with tasks
        └─▶ 1 = No tasks ready
```

### Component Interactions

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    GIT      │───▶│    BEADS    │───▶│   SESSION   │
│  (cli.go)   │    │ (beads.go)  │    │ (session.go)│
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ git pull          │ bd ready           │ save state
       │                   │                    │
       └───────────────────┴────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   OUTPUT        │
                      │ (format ready   │
                      │  task list)     │
                      └─────────────────┘
```

### Guardrails

| Check | Description | Action if Failed |
|-------|-------------|------------------|
| Git repo exists | Must be in git repository | Exit with error |
| Beads installed | `bd` command available | Exit with error |
| Git sync success | `git pull` must succeed | Exit with error |
| Beads sync success | `bd sync` must succeed | Exit with error |

### Error Handling

```
Error State
│
├─▶ Git pull failed
│   ├─▶ Show error message
│   └─▶ Exit code 1
│
├─▶ Beads sync failed
│   ├─▶ Show error message
│   └─▶ Exit code 2
│
├─▶ No git repo
│   ├─▶ Show error message
│   └─▶ Exit code 3
│
└─▶ Beads not installed
    ├─▶ Show error message
    └─▶ Exit code 4
```

---

## Phase 2: COOK - Execute with Guardrails

**Purpose**: AI-assisted phase to claim a task and execute it with guardrails.

### Task Graph

```
COOK Phase
│
├─▶ Verify session exists
│   ├─▶ Found → Load session state
│   └─▶ Not found → Exit with error
│
├─▶ Parse task ID argument
│   ├─▶ Provided → Use it
│   └─▶ Not provided → Prompt user
│
├─▶ Claim task in beads
│   ├─▶ bd update <id> --status in_progress
│   ├─▶ Success → Continue
│   └─▶ Failed → Exit with error
│
├─▶ Generate AI context
│   ├─▶ Load task details: bd show <id>
│   ├─▶ Load parent context (if any)
│   ├─▶ Load related issues (dependencies)
│   ├─▶ Load relevant files from repo
│   └─▶ Compile task context
│
├─▶ Output execution context
│   ├─▶ Show task title and description
│   ├─▶ Show parent issue (if any)
│   ├─▶ Show dependencies
│   ├─▶ Show related files
│   └─▶ Show guardrails checklist
│
├─▶ Launch AI assistant
│   ├─▶ Provide context to AI
│   └─▶ Wait for AI completion
│
└─▶ Handle AI result
    ├─▶ Success → Update session state
    ├─▶ Failed → Exit with error
    └─▶ Interrupted → Leave task in_progress
```

### Component Interactions

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SESSION   │───▶│    BEADS    │───▶│    GIT      │
│ (session.go)│    │ (beads.go)  │    │  (cli.go)   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ load state        │ bd update/show    │ load files
       │                   │                    │
       └───────────────────┴────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │    AI TUI       │
                      │  (context &     │
                      │  execution)     │
                      └─────────────────┘
```

### Guardrails Checklist

| Check | Description | Timing |
|-------|-------------|--------|
| Task exists | Task ID must be valid | Before claim |
| Not already claimed | Task must be `ready` | Before claim |
| Session active | Must have valid session | Start |
| Dependencies ready | Parent tasks complete | Before claim |
| Clean git state | No uncommitted changes | Before AI start |

### Error Handling

```
Error State
│
├─▶ Invalid task ID
│   ├─▶ Show error message
│   └─▶ Exit code 1
│
├─▶ Task already in_progress
│   ├─▶ Show warning
│   └─▶ Prompt user to continue or select different task
│
├─▶ Dependencies not met
│   ├─▶ Show blocking issues
│   └─▶ Exit with error
│
├─▶ Git not clean
│   ├─▶ Show uncommitted files
│   └─▶ Exit with error
│
└─▶ AI execution failed
    ├─▶ Show error message
    └─▶ Leave task in_progress (manual recovery required)
```

---

## Phase 3: SERVE - AI Peer Review

**Purpose**: AI-assisted phase to review completed work before committing.

### Task Graph

```
SERVE Phase
│
├─▶ Verify session exists
│   ├─▶ Found → Load session state
│   └─▶ Not found → Exit with error
│
├─▶ Parse task ID argument
│   ├─▶ Provided → Use it
│   ├─▶ Not provided → Use session.current_task
│   └─▶ No current task → Exit with error
│
├─▶ Generate git diff
│   ├─▶ git diff HEAD
│   ├─▶ Parse changed files
│   └─▶ Extract diff content
│
├─▶ Generate review context
│   ├─▶ Load task details: bd show <id>
│   ├─▶ Load acceptance criteria
│   ├─▶ Load related code context
│   └─▶ Compile review checklist
│
├─▶ Output review context
│   ├─▶ Show task title and acceptance criteria
│   ├─▶ Show changed files summary
│   ├─▶ Show diff (truncated if large)
│   └─▶ Show review checklist
│
├─▶ Launch AI reviewer
│   ├─▶ Provide diff and context to AI
│   ├─▶ Request review against checklist
│   └─▶ Wait for AI review
│
└─▶ Handle review result
    ├─▶ Approved → Continue to TIDY
    ├─▶ Changes requested → Return to COOK
    └─▶ Failed → Exit with error
```

### Component Interactions

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SESSION   │───▶│    GIT      │───▶│    BEADS    │
│ (session.go)│    │  (cli.go)   │    │ (beads.go)  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ load state        │ git diff          │ bd show
       │                   │                    │
       └───────────────────┴────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   AI REVIEWER   │
                      │  (diff analysis  │
                      │  & checklist)   │
                      └─────────────────┘
```

### Review Checklist

| Check | Description | Pass Criteria |
|-------|-------------|---------------|
| Acceptance criteria | Task requirements met | All criteria satisfied |
| Code quality | Follows project conventions | Style, patterns consistent |
| Tests | Tests added/updated | Tests cover changes |
| Build | Code compiles/builds | Build succeeds |
| No regressions | Existing tests pass | All tests pass |
| Documentation | Docs updated if needed | Changes documented |

### Error Handling

```
Error State
│
├─▶ No session found
│   ├─▶ Show error message
│   └─▶ Exit code 1
│
├─▶ No current task in session
│   ├─▶ Show error message
│   └─▶ Exit code 2
│
├─▶ No git changes
│   ├─▶ Show message "nothing to review"
│   └─▶ Exit code 3
│
└─▶ AI review failed
    ├─▶ Show error message
    └─▶ Exit code 4
```

---

## Phase 4: TIDY - Commit and Push

**Purpose**: Mechanical phase to finalize work, file findings, and push to remote.

### Task Graph

```
TIDY Phase
│
├─▶ Verify session exists
│   ├─▶ Found → Load session state
│   └─▶ Not found → Exit with error
│
├─▶ Parse task ID argument
│   ├─▶ Provided → Use it
│   ├─▶ Not provided → Use session.current_task
│   └─▶ No current task → Exit with error
│
├─▶ Generate commit message
│   ├─▶ Load task details: bd show <id>
│   ├─▶ Load git diff
│   ├─▶ Parse changes
│   └─▶ Generate message (or prompt user)
│
├─▶ Quality gates
│   ├─▶ Run tests (if configured)
│   │   ├─▶ Pass → Continue
│   │   └─▶ Fail → Prompt user to abort or continue
│   ├─▶ Run linter (if configured)
│   │   ├─▶ Pass → Continue
│   │   └─▶ Fail → Prompt user to abort or continue
│   └─▶ Run build (if configured)
│       ├─▶ Pass → Continue
│       └─▶ Fail → Prompt user to abort or continue
│
├─▶ Check for findings
│   ├─▶ Prompt user: "Any issues to file as beads?"
│   ├─▶ Yes → Create new bead issues
│   └─▶ No → Continue
│
├─▶ Update task status
│   ├─▶ bd close <id>
│   ├─▶ Success → Continue
│   └─▶ Failed → Exit with error
│
├─▶ Sync beads
│   ├─▶ bd sync
│   └─▶ Verify success
│
├─▶ Commit changes
│   ├─▶ git add .
│   ├─▶ git commit -m "<message>"
│   ├─▶ Success → Continue
│   └─▶ Failed → Exit with error
│
├─▶ Push to remote
│   ├─▶ git pull --rebase
│   ├─▶ git push
│   ├─▶ Success → Continue
│   └─▶ Failed → Prompt user to retry
│
├─▶ Update session state
│   ├─▶ Clear current_task
│   └─▶ Save session
│
└─▶ Output summary
    ├─▶ Show commit message
    ├─▶ Show remote URL
    └─▶ Exit with success
```

### Component Interactions

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SESSION   │───▶│    GIT      │───▶│    BEADS    │
│ (session.go)│    │  (cli.go)   │    │ (beads.go)  │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       │ load/save state   │ commit/push       │ close/sync
       │                   │                    │
       └───────────────────┴────────────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  QUALITY GATES  │
                      │  (tests, lint,  │
                      │   build)        │
                      └─────────────────┘
```

### Guardrails

| Check | Description | Action if Failed |
|-------|-------------|------------------|
| Session exists | Must have active session | Exit with error |
| Current task exists | Task must be claimed | Exit with error |
| Quality gates pass | Tests, lint, build | Prompt to abort or continue |
| Commit succeeds | git commit must work | Exit with error |
| Push succeeds | git push must work | Prompt to retry |
| Beads close succeeds | Task must close | Exit with error |

### Error Handling

```
Error State
│
├─▶ No session found
│   ├─▶ Show error message
│   └─▶ Exit code 1
│
├─▶ No current task
│   ├─▶ Show error message
│   └─▶ Exit code 2
│
├─▶ Quality gate failed
│   ├─▶ Show failure details
│   ├─▶ Prompt: "Continue anyway? (y/N)"
│   │   ├─▶ Yes → Continue
│   │   └─▶ No → Exit with code 3
│   └─▶ User decision
│
├─▶ Commit failed
│   ├─▶ Show error message
│   └─▶ Exit code 4
│
├─▶ Push failed
│   ├─▶ Show error message
│   ├─▶ Prompt: "Retry? (y/N)"
│   │   ├─▶ Yes → Retry push
│   │   └─▶ No → Exit with code 5
│   └─▶ User decision
│
└─▶ Beads close failed
    ├─▶ Show error message
    └─▶ Exit code 6
```

---

## WORK - Full Cycle Orchestration

**Purpose**: Runs complete PREP → COOK → SERVE → TIDY cycle.

### Task Graph

```
WORK Cycle
│
├─▶ Run PREP
│   ├─▶ Success → Continue
│   └─▶ Failed → Exit with error
│
├─▶ Select task
│   ├─▶ Parse task ID (if provided)
│   ├─▶ Prompt user to select (if not provided)
│   └─▶ User selection
│
├─▶ Run COOK with selected task
│   ├─▶ Success → Continue
│   └─▶ Failed → Exit with error
│
├─▶ Run SERVE with completed task
│   ├─▶ Approved → Continue
│   ├─▶ Changes requested → Return to COOK
│   └─▶ Failed → Exit with error
│
└─▶ Run TIDY with reviewed task
    ├─▶ Success → Cycle complete
    └─▶ Failed → Exit with error
```

### Component Flow

```
    PREP         COOK          SERVE         TIDY
      │             │             │             │
      ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Sync &   │──▶│ Execute  │──▶│ Review   │──▶│ Commit   │
│ Identify │  │ with AI  │  │ with AI  │  │ & Push   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
      │             │             │             │
      └─────────────┴─────────────┴─────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   Session       │
                      │   State         │
                      │   (persists     │
                      │    across       │
                      │    phases)      │
                      └─────────────────┘
```

### Error Handling

Each phase follows its own error handling (see individual phases above).

**WORK-specific errors:**

```
Error State
│
├─▶ PREP failed
│   └─▶ Exit with error (don't start work)
│
├─▶ COOK failed
│   ├─▶ Task left in_progress
│   └─▶ Exit with error
│
├─▶ SERVE failed
│   ├─▶ Task left in_progress
│   └─▶ Exit with error
│
└─▶ TIDY failed
    ├─▶ Task left in_progress
    └─▶ Exit with error
```

---

## Session State Management

### State Lifecycle

```
Session Lifecycle
│
├─▶ Initialization (PREP)
│   ├─▶ Check for existing session
│   │   ├─▶ Found → Load state
│   │   └─▶ Not found → Create new session
│   └─▶ Session fields:
│       ├─▶ repo_path: Current directory
│       ├─▶ remote_url: Git remote URL
│       ├─▶ current_task: Task ID (null initially)
│       ├─▶ phase: "prep" | "cook" | "serve" | "tidy" | "complete"
│       ├─▶ start_time: Timestamp
│       └─▶ metadata: Additional info
│
├─▶ COOK phase
│   ├─▶ Set current_task = selected task ID
│   ├─▶ Set phase = "cook"
│   └─▶ Save session
│
├─▶ SERVE phase
│   ├─▶ Verify current_task matches
│   ├─▶ Set phase = "serve"
│   └─▶ Save session
│
├─▶ TIDY phase
│   ├─▶ Verify current_task matches
│   ├─▶ Set phase = "tidy"
│   └─▶ Save session
│
└─▶ Completion
    ├─▶ Set current_task = null
    ├─▶ Set phase = "complete"
    ├─▶ Save session
    └─▶ Session persists until next cycle starts
```

### Session File Location

```
Session Storage
│
├─▶ Location: .beads/session.json
│   ├─▶ In repository root
│   ├─▶ Git-ignored (in .gitignore)
│   └─▶ Machine-specific state
│
└─▶ Schema:
    {
      "repo_path": "/path/to/repo",
      "remote_url": "https://github.com/user/repo.git",
      "current_task": "lc-123",
      "phase": "cook",
      "start_time": "2026-01-21T10:00:00Z",
      "metadata": {
        "branch": "feature/lc-123",
        "original_branch": "main"
      }
    }
```

### Session Recovery

```
Recovery Scenarios
│
├─▶ After compaction
│   ├─▶ Session state preserved
│   ├─▶ Run `/line:prep` to continue
│   └─▶ Phases resume from saved state
│
├─▶ After interruption
│   ├─▶ Run `/line:serve` to review
│   ├─▶ Run `/line:tidy` to commit
│   └─▶ Or `/line:work` to restart cycle
│
└─▶ After COOK completion
    ├─▶ Session has current_task
    ├─▶ Run `/line:serve` to review
    └─▶ Then `/line:tidy` to finalize
```

---

## Component Data Flow

### Cross-Phase Data Sharing

```
Data Flow Diagram
│
┌─────────────────────────────────────────────────────────────────┐
│                         PREP                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │    GIT      │  │    BEADS    │  │   SESSION   │               │
│  │ - remote    │  │ - ready     │  │ - repo_path │               │
│  │ - branch    │  │   tasks     │  │ - remote    │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                      │
│                          ▼                                      │
│                    ┌─────────────┐                              │
│                    │   OUTPUT    │                              │
│                    │ - task list │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ (user selects task)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         COOK                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │   SESSION   │  │    BEADS    │  │    GIT      │               │
│  │ - current   │  │ - task      │  │ - files    │               │
│  │   task      │  │   details   │  │             │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                      │
│                          ▼                                      │
│                    ┌─────────────┐                              │
│                    │   AI TUI    │                              │
│                    │ - execution │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ (changes made)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SERVE                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │    GIT      │  │   SESSION   │  │    BEADS    │               │
│  │ - diff      │  │ - current   │  │ - task      │               │
│  │             │  │   task      │  │   criteria │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                      │
│                          ▼                                      │
│                    ┌─────────────┐                              │
│                    │ AI REVIEWER │                              │
│                    │ - approval  │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                          │
                          │ (approved)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TIDY                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │    GIT      │  │    BEADS    │  │   SESSION   │               │
│  │ - commit    │  │ - close     │  │ - clear     │               │
│  │ - push      │  │   task      │  │   task      │               │
│  └─────────────┘  └─────────────┘  └─────────────┘               │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                      │
│                          ▼                                      │
│                    ┌─────────────┐                              │
│                    │   OUTPUT    │                              │
│                    │ - summary   │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Guardrails Summary

### Phase-Specific Guardrails

| Phase | Guardrails | Enforcement |
|-------|-----------|-------------|
| **PREP** | Git repo exists, beads installed, sync success | Exit with error |
| **COOK** | Task valid, not claimed, dependencies met, git clean | Exit or prompt |
| **SERVE** | Session active, task exists, changes present | Exit with error |
| **TIDY** | Quality gates, commit success, push success, beads close | Exit or prompt |

### Global Guardrails

| Guardrail | Description | Enforcement |
|-----------|-------------|-------------|
| Always sync first | Never work on stale state | PREP checks git/beads sync |
| One task at a time | Prevent scope creep | Session tracks single task |
| Verify before done | Quality gates before commit | TIDY runs tests/lint/build |
| File, don't block | Discoveries become beads | TIDY prompts for findings |
| Push before stop | Work not done until pushed | TIDY verifies push success |

### Error Recovery Patterns

| Error Type | Recovery Strategy |
|------------|-------------------|
| Sync failure | Manual resolution, retry |
| Claim failure | Check task status, select different task |
| AI execution failure | Manual intervention, leave task in_progress |
| Review failure | Return to COOK, make changes |
| Quality gate failure | Fix issues or manually override |
| Commit failure | Resolve conflict, retry |
| Push failure | Resolve conflict, retry |

---

## Key Design Principles

### 1. Separation of Concerns

```
Mechanical Phases (CLI-only)
├── PREP: Sync and identify
└── TIDY: Commit and push

AI-Assisted Phases (TUI required)
├── COOK: Execute with AI
└── SERVE: Review with AI
```

### 2. State Persistence

```
Session state survives across:
├── Phase transitions (PREP → COOK → SERVE → TIDY)
├── Interruptions (user stops work)
└── Context compaction (AI session compacts)

Recovery:
├── Resume from saved session
├── Continue from current phase
└── Complete pending work
```

### 3. Guardrails at Every Phase

```
Input Validation → Process Execution → Output Verification
     PREP               COOK/SERVE           TIDY
     ↓                   ↓                    ↓
  Sync checks       Execution checks    Quality gates
  Task validation    Review validation   Push verification
```

### 4. Fail-Safe Design

```
Failure Modes:
├── Mechanical failures → Clear error, exit
├── AI failures → Leave state for manual recovery
├── Quality gate failures → Prompt user decision
└── Push failures → Allow retry without data loss
```

### 5. User Control

```
Decision Points:
├── PREP: User selects task from ready list
├── COOK: User provides task ID (optional)
├── SERVE: User reviews AI feedback
├── TIDY: User confirms findings, overrides gates (if needed)
└── WORK: User selects task or provides ID
```

---

## Exit Codes Reference

| Code | Phase | Meaning |
|------|-------|---------|
| 0 | All | Success |
| 1 | All | General error |
| 1 | PREP | No git repo |
| 2 | PREP | Beads sync failed |
| 3 | PREP | Git sync failed |
| 4 | PREP | Beads not installed |
| 1 | COOK | Invalid task ID |
| 2 | COOK | Task already claimed |
| 3 | COOK | Dependencies not met |
| 4 | COOK | Git not clean |
| 5 | COOK | AI execution failed |
| 1 | SERVE | No session found |
| 2 | SERVE | No current task |
| 3 | SERVE | No git changes |
| 4 | SERVE | AI review failed |
| 1 | TIDY | No session found |
| 2 | TIDY | No current task |
| 3 | TIDY | Quality gate failed (user aborted) |
| 4 | TIDY | Commit failed |
| 5 | TIDY | Push failed (user aborted) |
| 6 | TIDY | Beads close failed |

---

## Integration Points

### Git Integration

```
Git Operations:
├── PREP: pull --rebase, fetch origin
├── COOK: load files for context
├── SERVE: diff HEAD
└── TIDY: add, commit, pull --rebase, push
```

### Beads Integration

```
Beads Operations:
├── PREP: sync, ready
├── COOK: show, update --status in_progress
├── SERVE: show (acceptance criteria)
└── TIDY: close, sync, create new issues
```

### AI Integration

```
AI Interactions:
├── COOK: Provide task context, wait for execution
└── SERVE: Provide diff and criteria, wait for review
```

---

## Future Extensions

### Potential Enhancements

```
Enhanced Guardrails:
├── Automated testing with coverage thresholds
├── Static analysis integration
├── Security scanning
└── Performance benchmarking

Session Management:
├── Multi-task sessions (parallel work)
├── Session branching (try alternative approaches)
└── Session history (roll back to earlier state)

Collaboration:
├── Shared sessions (pair programming)
├── Session export/import (handoffs)
└── Integration with code review tools
```

---

## Appendix: File Structure Reference

```
line-cook/
├── commands/              # Claude Code command definitions
│   ├── prep.md
│   ├── cook.md
│   ├── serve.md
│   ├── tidy.md
│   └── work.md
├── internal/
│   ├── cli/              # CLI command implementations
│   │   ├── prep.go
│   │   ├── cook.go
│   │   ├── serve.go
│   │   ├── tidy.go
│   │   └── work.go
│   ├── beads/            # Beads integration
│   │   └── beads.go
│   ├── git/              # Git operations
│   │   └── git.go
│   ├── session/          # Session state management
│   │   └── session.go
│   └── output/           # Formatting and display
│       └── output.go
└── docs/
    ├── task-graph.md     # This file
    ├── tutorial-claude-code.md
    ├── tutorial-opencode.md
    └── tutorial-kiro.md
```
