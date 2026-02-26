# Crumbs v2 Specification

> Git-native issue tracking with configurable state machine workflows

## 1. Overview

Crumbs is a git-native issue tracker that stores work items as append-only JSONL in the repository. It syncs via normal git operations, survives session boundaries, and natively tracks the trail of phase execution history — the crumbs an agent leaves as it works.

### 1.1 Design Principles

- **Git-native**: JSONL files live in-repo under `.crumbs/`, sync with normal git operations
- **Event-sourced state**: Phase records are append-only immutable events; current state is a projection
- **Machine-driven prompting**: `cr next` tells the consumer what to do; the consumer doesn't decide workflow sequence
- **Project-agnostic**: The core engine knows states, events, transitions, and guards — not cook, serve, or test-writer
- **Hierarchical**: Strict 3-tier hierarchy (epic → feature → task) with precomputed ancestry and progress
- **Single tool**: One CLI (`cr`) for issue tracking, workflow state, and context assembly

### 1.2 Two-Layer Architecture

#### Layer 1: Crumbs Core (project-agnostic)

The generic state machine engine. Knows about:
- Issues, PhaseRecords, Dependencies (data model)
- Workflow definitions (states, events, transitions, guards)
- WorkflowState derivation (projection from PhaseRecords)
- Transition execution (validate, record, cascade)
- Context assembly protocol (calls external hook, returns structured result)

Does NOT know about:
- Cook, serve, tidy, plate (Line Cook phases)
- Test-writer, test-review, execute (Capsule phases)
- TDD methodology, sous-chef, polisher (Line Cook agents)
- Writer/reviewer pairs (Capsule retry pattern)
- Kitchen signals, SERVE_RESULT blocks (Line Cook specifics)

#### Layer 2: Project Integration (Line Cook, Capsule, etc.)

Each project provides:
- **Workflow definition** in `.crumbs/config.yaml`
- **Context assembler hook** (script/binary that `cr next` calls to fill the ContextBundle)
- **Phase payload schemas** (what data each phase produces)
- **Orchestrator** that calls `cr next` / `cr transition`

### 1.3 What Changed from v1

| Area | v1 | v2 |
|------|----|----|
| Phase names | Fixed enum (`prep \| cook \| serve \| tidy \| plate`) | Project-defined strings in workflow config |
| State machine | Implicit in orchestrator code | Explicit in `.crumbs/config.yaml` per issue type |
| Context assembly | Not specified (left to consumer) | Formal protocol with hook interface |
| Transitions | No concept — phases just recorded | `cr transition` with guards, effects, cascades |
| Storage | JSONL only | JSONL (git-friendly source of truth) + SQLite (local query cache) |
| Payload schemas | Fixed types (CookPayload, ServePayload, TidyPayload) | Extensible — projects register their own payload schemas |
| Workflow commands | None | `cr next`, `cr transition`, `cr workflow show/status/history/validate` |
| Data model | All fields retained | All fields retained + WorkflowState, ContextBundle, TransitionResult |

### 1.4 Anti-Patterns Avoided

| Anti-pattern | How crumbs avoids it |
|---|---|
| God Object | Work items and phase records are separate entity types with single responsibility each |
| Inner Platform | Workflows are declarative config, not a generic "build your own engine" framework |
| Golden Hammer | Phase payloads are typed per project; the core accepts any JSON payload |
| Mutable state | Phase records are append-only; current state derived from latest events |
| Denormalization drift | Derived fields (progress_pct, close_eligible, workflow_state) are computed projections, not stored copies |
| Missing concept | Execution state (verdicts, retry counts, findings) is a first-class entity, not text hidden in comments |
| God state | Distinct states per phase; no single "active" state with internal branching |
| Implicit state | All state in the machine config, not scattered across files/flags/comments |
| Fat nodes | Core emits ContextBundle structure; project-specific hooks fill the content |
| Boolean flags for state | States are an explicit enum from workflow config; no `is_reviewing`, `is_retrying` booleans |
| Stuck states | Stale detection for orphaned started-without-completed phases |
| Blind retry (BPAP AP-1) | Structured feedback persistence across retries via PhaseRecords |
| Context amnesia (BPAP AP-2) | WorkflowState carries attempt count and phase history; hooks inject relevant context |

### 1.5 State Machine Design Alignment

The workflow engine design maps to established state machine best practices:

| Principle | Design decision |
|---|---|
| Illegal states unrepresentable | States are an explicit enum from workflow config. No boolean flags. |
| Decide/evolve split | `cr transition` is the pure decision function. Consumer executor is separate. |
| Hierarchical states | Workflows can nest (task workflow inside feature lifecycle inside epic lifecycle). Cross-cutting error handling at parent level. |
| Entry/exit actions | `cr next` provides entry context. `cr transition` captures exit payload. Both extensible via hooks. |
| Pure guards | Guards evaluate PhaseRecord data only. No I/O. Declared as expressions in config. |
| Event-sourced state | WorkflowState derived from phases.jsonl (JSONL = source of truth, SQLite = query cache). Rebuildable by replay. |
| Checkpointing | Completed PhaseRecords serve as checkpoints. Recovery replays from last completed. |
| Actor model | Orchestrator (Line Cook loop / Capsule campaign) invokes worker per phase. Worker sends done event. |
| Context vs finite states | Attempt count, feedback history in context, not state names. No `cook_attempt_2` states. |
| Machine-driven prompting | `cr next` tells consumer what to do. Consumer doesn't decide workflow sequence. |
| Idempotent actions | PhaseRecords are append-only. Side effects tracked for safe replay. |
| Model error states explicitly | Explicit blocked/failed states with configurable max-retry guards. |
| Idempotent replay | JSONL is append-only; SQLite rebuild is deterministic from same JSONL. No duplicate side effects on replay. |

---

## 2. Data Model

### 2.1 Issue (Core Work Item)

The primary entity. Carries identity, hierarchy, content, and artifact links.

```
Issue {
    # Identity
    id:             string      # PK, immutable (e.g. "lc-abc.1.3")
    title:          string      # Required
    issue_type:     enum        # epic | feature | task | bug
    status:         enum        # open | in_progress | closed
    priority:       int         # 0-4 (0=critical, 4=backlog)

    # Hierarchy
    parent:         string?     # FK → Issue.id
    epic_ancestor:  string?     # Precomputed root epic ID (set on create, updated on reparent)
    depth:          int         # 0=epic, 1=feature, 2=task (computed from parent chain)

    # Content
    description:    string?     # Full markdown
    close_reason:   string?     # Why closed (completion note or cancellation)

    # Structured content (queryable, extracted from description at creation)
    acceptance_criteria: list[string]  # Feature-only: "Given/When/Then" or checklist items
    deliverables:        list[string]  # Task-only: what this task produces
    user_story:          string?       # Feature-only: "As a X, I want Y, so that Z"

    # Artifact links
    test_spec:        string?   # Path to TDD spec
    feature_spec:     string?   # Path to BDD feature
    acceptance_doc:   string?   # Path to acceptance document
    planning_context: string?   # Path to planning context directory
    epic_branch:      string?   # Git branch name for this epic

    # Timestamps
    created_at:     datetime    # Auto-set on creation
    updated_at:     datetime    # Auto-set on every mutation
}
```

### 2.2 PhaseRecord (Execution Event)

Append-only record of workflow phase execution. One record per phase invocation per issue. Phase names are project-defined strings from the workflow config — not a fixed enum.

```
PhaseRecord {
    id:         string      # Auto-generated unique ID
    issue_id:   string      # FK → Issue.id
    phase:      string      # Project-defined phase name (e.g. "cook", "test-writer")
    status:     enum        # started | completed | failed
    attempt:    int         # Retry counter per (issue_id, phase) pair (starts at 1)
    timestamp:  datetime    # When this record was created
    payload:    object?     # Phase-specific typed payload (project-defined JSON), null if none
}
```

**Key difference from v1:** The `phase` field is a free-form string validated against the workflow config, not a fixed enum. "cook" is a valid phase name in a Line Cook project; "test-writer" is a valid phase name in a Capsule project. The core engine validates that the phase name exists in the issue's workflow definition.

### 2.3 Typed Payloads (Extensible)

Payloads are project-defined JSON objects attached to completed PhaseRecords. The core engine stores and returns them verbatim — it does not interpret payload contents.

Projects register payload schemas in their workflow config (Section 3.1). The core validates payloads against registered schemas when provided, but schema registration is optional. Unregistered payloads are accepted as raw JSON.

**Example: Line Cook payloads**

```
CookPayload {
    intent:         string          # What the task set out to do
    approach:       string?         # How it was implemented
    files_changed:  list[string]    # File paths modified
    tests_written:  list[string]    # Test file paths
    findings:       list[Finding]   # Issues discovered during cook
}

ServePayload {
    verdict:          enum          # approved | needs_changes | blocked
    blocking_issues:  int           # Count of blocking issues
    summary:          string        # Brief review assessment
    issues:           list[ReviewIssue]
}

TidyPayload {
    commit_sha:     string?         # Git commit hash
    issues_filed:   list[string]    # IDs of newly created issues (from findings)
    issues_closed:  list[string]    # IDs closed during tidy
    epic_merged:    bool            # Whether an epic branch was merged
    push_status:    enum            # success | failed | skipped
}
```

**Example: Capsule payloads**

```
TestWriterPayload {
    test_files:     list[string]    # Test file paths created/modified
    test_count:     int             # Number of test cases
    coverage_delta: float?          # Coverage change if measurable
}

ExecutePayload {
    files_changed:  list[string]    # Implementation file paths
    approach:       string          # How the implementation works
    test_results:   TestResults     # Pass/fail counts
}

ReviewPayload {
    verdict:        enum            # pass | needs_work | error
    feedback:       string          # Reviewer assessment
    findings:       list[Finding]   # Specific issues found
}
```

### 2.4 Finding

Shared type for discoveries during any phase. Project-agnostic.

```
Finding {
    category:    enum       # code | project | process
    severity:    enum       # critical | high | medium | low
    title:       string
    description: string
    file:        string?    # File path if applicable
    filed_as:    string?    # Issue ID if filed as separate issue
}
```

### 2.5 Dependency

Tracks blocking relationships between issues.

```
Dependency {
    from_id:    string      # FK → Issue.id (the blocked item)
    to_id:      string      # FK → Issue.id (the blocker)
    type:       enum        # blocks | relates_to
    created_at: datetime
}
```

### 2.6 WorkflowState (Derived Projection)

Computed from the issue's PhaseRecords and the workflow definition. Never persisted — rebuilt on read.

```
WorkflowState {
    current_state:      string          # Current state in the workflow (e.g. "cook", "test_reviewing")
    available_events:   list[string]    # Events valid from current state
    attempt:            int             # Current attempt number for the active phase
    phase_history:      list[PhaseRecord]  # All PhaseRecords for this issue, ordered by timestamp
    is_terminal:        bool            # Whether current_state is a terminal state
    stale:              bool            # True if a phase was started but never completed/failed
    stale_since:        datetime?       # Timestamp of the stale started record
}
```

**Derivation algorithm:**

1. Load all PhaseRecords for the issue, ordered by timestamp
2. Replay transitions: each completed/failed PhaseRecord maps to an event in the workflow definition
3. The state after replaying all transitions is `current_state`
4. If no PhaseRecords exist, `current_state` is the workflow's `initial` state
5. `available_events` are the events defined for transitions from `current_state`
6. `stale` is true if the most recent PhaseRecord has `status: started` and no subsequent `completed` or `failed` record exists for the same `(issue_id, phase, attempt)` tuple

### 2.7 ContextBundle (cr next Response)

The structured response from `cr next`. Contains everything a consumer needs to execute the next phase.

```
ContextBundle {
    issue:          Issue           # Full issue data
    workflow_state: WorkflowState   # Current state + available events
    next_action:    string          # The event the consumer should work toward producing
    next_state:     string          # The state the issue will move to on success
    attempt:        int             # Which attempt this is (for retry-aware context)
    max_attempts:   int?            # Max attempts configured for this transition (null if unlimited)

    # From context assembler hook (project-specific, empty if no hook configured)
    context:        object          # Project-specific context (tools, planning docs, retry analysis, etc.)
}
```

### 2.8 TransitionResult (cr transition Response)

The result of executing a transition via `cr transition`.

```
TransitionResult {
    success:        bool            # Whether the transition was valid
    from_state:     string          # State before transition
    to_state:       string          # State after transition (same as from_state if success=false)
    event:          string          # The event that was fired
    effects:        list[string]    # Side effects that were triggered
    error:          string?         # Why the transition failed (guard not met, invalid event, etc.)
    cascade:        CascadeResult?  # Result of parent cascade evaluation, if any
}

CascadeResult {
    parent_id:      string          # Parent issue ID
    evaluated:      bool            # Whether the parent was evaluated for state change
    transitioned:   bool            # Whether the parent actually changed state
    from_state:     string?         # Parent's previous state (if transitioned)
    to_state:       string?         # Parent's new state (if transitioned)
}
```

---

## 3. Workflow Definition

Workflows are declared in `.crumbs/config.yaml`, not hardcoded in the engine. Each issue type can have its own workflow. Different projects define different workflows.

### 3.1 Workflow Config Schema

```yaml
prefix: "lc"                          # Issue ID prefix

workflows:
  <issue_type>:                       # e.g. "task", "feature", "epic"
    states:                           # List of valid states
      - <state_name>                  # Strings, project-defined
    initial: <state_name>             # Starting state for new issues
    terminal:                         # States that represent completion
      - <state_name>
    transitions:                      # State machine edges
      - from: <state_name>
        event: <event_name>           # What triggers this transition
        to: <state_name>
        guard: <expression>?          # Optional condition (must be true to fire)
        effects:                      # Optional side effects
          - <effect_name>
    max_attempts: <int>?              # Default max attempts (overridable per transition)
    hooks:                            # Optional lifecycle hooks
      context_assembler: <path>       # Script/binary for cr next context
      prep: <command>?                # Command to run before cr next returns
      <phase>.<hook_point>:           # Phase-specific hooks
        agent: <agent_name>?          # Agent to invoke
        command: <command>?           # Command to run
    payload_schemas:                  # Optional payload validation
      <phase_name>: <json_schema>     # JSON Schema for phase payloads
```

**Config validation rules:**
- Every state referenced in `transitions`, `initial`, and `terminal` must appear in `states`
- `initial` must be exactly one state
- `terminal` must contain at least one state
- Transitions must form a connected graph from `initial` to at least one `terminal` state
- Guard expressions must be syntactically valid (see 3.2)
- Effect names must be recognized built-ins or registered hooks
- No duplicate `(from, event)` pairs unless distinguished by guards

### 3.2 Built-in Guards

Guards are pure boolean expressions evaluated against the WorkflowState and issue data. They perform no I/O.

| Guard expression | Meaning |
|---|---|
| `attempt < N` | Current attempt count is below N |
| `attempt >= N` | Current attempt count is at or above N |
| `attempt < max_attempts` | Current attempt is below the workflow's configured max |
| `close_eligible` | All children of this issue are closed (or issue has no children) |
| `all_children_closed` | Synonym for `close_eligible` |
| `status == "X"` | Issue status matches X |
| `has_phase("X")` | Issue has at least one completed PhaseRecord for phase X |
| `last_verdict("X") == "Y"` | Most recent payload from phase X has verdict field equal to Y |

Guards are evaluated in declaration order. When multiple transitions share the same `(from, event)` pair, the first transition whose guard evaluates to true (or has no guard) is selected. If no transition matches, the event is rejected.

**Custom guard expressions:** Projects may register custom guard functions in the context assembler hook. Custom guards receive the full WorkflowState and issue data as input and return a boolean. They are referenced by name in the config:

```yaml
guard: "custom:my_project_guard"
```

### 3.3 Built-in Side Effects

Side effects run after a transition is validated and the PhaseRecord is written. They are not guards — they do not influence whether the transition fires.

| Effect | Behavior |
|---|---|
| `record_phase` | Append a PhaseRecord (implicit — always happens on transition) |
| `set_in_progress` | Set `issue.status = in_progress` |
| `set_closed` | Set `issue.status = closed` |
| `check_parent` | Evaluate parent issue for cascading transition (see 3.4) |
| `fire_prep_hook` | Execute the workflow's `prep` hook command |

Effects execute in declaration order. If an effect fails, the transition still completes (the PhaseRecord is already written), but the failure is reported in the TransitionResult.

### 3.4 Cascading Transitions

When a transition includes the `check_parent` effect, the engine evaluates whether the parent issue should transition:

1. Load the parent issue and its workflow definition
2. Check if `close_eligible` is true (all children now closed)
3. If so, fire the appropriate event on the parent (e.g., `all_children_closed`)
4. The parent's transition may itself cascade to its parent (recursive)

Cascading is bounded by hierarchy depth (max 3 levels: task → feature → epic). The CascadeResult in the TransitionResult reports what happened at each level.

### 3.5 Example: Line Cook Task Workflow

```yaml
prefix: "lc"
workflows:
  task:
    states: [open, cook, serve, tidy, closed, blocked]
    initial: open
    terminal: [closed]
    transitions:
      - from: open
        event: assign
        to: cook
        effects: [set_in_progress, fire_prep_hook]
      - from: cook
        event: cook_complete
        to: serve
      - from: serve
        event: approved
        to: tidy
      - from: serve
        event: needs_changes
        to: cook
        guard: "attempt < max_attempts"
      - from: serve
        event: needs_changes
        to: blocked
        guard: "attempt >= max_attempts"
      - from: serve
        event: blocked
        to: blocked
      - from: tidy
        event: tidy_complete
        to: closed
        effects: [set_closed, check_parent]
      - from: blocked
        event: unblock
        to: cook
    max_attempts: 2
    hooks:
      prep: "cr sync && git fetch"
      context_assembler: "./plugins/claude-code/scripts/crumbs-context.py"
      cook.after_red: { agent: "taster" }
      serve.review: { agent: "sous-chef" }
      serve.after_approved: { agent: "polisher" }

  feature:
    states: [open, plate, closed]
    initial: open
    terminal: [closed]
    transitions:
      - from: open
        event: all_children_closed
        to: plate
      - from: plate
        event: plate_complete
        to: closed
        effects: [set_closed, check_parent]
    hooks:
      plate.review: { agent: "maitre" }

  epic:
    states: [open, close_service, closed]
    initial: open
    terminal: [closed]
    transitions:
      - from: open
        event: all_children_closed
        to: close_service
      - from: close_service
        event: complete
        to: closed
        effects: [set_closed]
    hooks:
      close_service.review: { agent: "critic" }
```

**State diagram (task):**
```
open ──assign──► cook ──cook_complete──► serve ──approved──► tidy ──tidy_complete──► closed
                  ▲                        │                                           │
                  │                        │ needs_changes                              │
                  │                        │ (attempt < max)                            │
                  └────────────────────────┘                                            │
                  ▲                        │                              check_parent ─┘
                  │                        │ needs_changes
                  │       unblock          │ (attempt >= max)
                  └───── blocked ◄─────────┘
```

### 3.6 Example: Capsule Pipeline Workflow

```yaml
prefix: "demo"
workflows:
  task:
    states: [open, test_writing, test_reviewing, executing, execute_reviewing, signing_off, merging, closed, failed]
    initial: open
    terminal: [closed, failed]
    transitions:
      - from: open
        event: start
        to: test_writing
        effects: [set_in_progress]
      - from: test_writing
        event: pass
        to: test_reviewing
      - from: test_writing
        event: error
        to: failed
      - from: test_reviewing
        event: pass
        to: executing
      - from: test_reviewing
        event: needs_work
        to: test_writing
        guard: "attempt < max_attempts"
      - from: test_reviewing
        event: needs_work
        to: failed
        guard: "attempt >= max_attempts"
      - from: executing
        event: pass
        to: execute_reviewing
      - from: executing
        event: error
        to: failed
      - from: execute_reviewing
        event: pass
        to: signing_off
      - from: execute_reviewing
        event: needs_work
        to: executing
        guard: "attempt < max_attempts"
      - from: execute_reviewing
        event: needs_work
        to: failed
        guard: "attempt >= max_attempts"
      - from: signing_off
        event: pass
        to: merging
      - from: signing_off
        event: fail
        to: failed
      - from: merging
        event: pass
        to: closed
        effects: [set_closed, check_parent]
      - from: merging
        event: error
        to: failed
    max_attempts: 3
    hooks:
      context_assembler: "./scripts/crumbs-context.sh"

  feature:
    states: [open, running, gating, closed]
    initial: open
    terminal: [closed]
    transitions:
      - from: open
        event: start_campaign
        to: running
      - from: running
        event: all_children_closed
        to: gating
      - from: gating
        event: gate_pass
        to: closed
        effects: [set_closed, check_parent]
      - from: gating
        event: gate_fail
        to: running
```

**State diagram (task):**
```
open ──start──► test_writing ──pass──► test_reviewing ──pass──► executing ──pass──► execute_reviewing
                     ▲                       │                      ▲                      │
                     │                       │ needs_work           │                      │ needs_work
                     │                       │ (attempt < max)      │                      │ (attempt < max)
                     └───────────────────────┘                      └──────────────────────┘
                     │                       │                      │                      │
                     │ error                 │ needs_work           │ error                │ needs_work
                     ▼                       │ (attempt >= max)     ▼                      │ (attempt >= max)
                   failed ◄──────────────────┘                    failed ◄────────────────┘

execute_reviewing ──pass──► signing_off ──pass──► merging ──pass──► closed
                                │                    │
                                │ fail               │ error
                                ▼                    ▼
                              failed               failed
```

### 3.7 Example: Minimal 3-State Workflow

The simplest valid workflow. Useful for projects that just need open/working/done tracking without complex transitions.

```yaml
prefix: "proj"
workflows:
  task:
    states: [open, working, done]
    initial: open
    terminal: [done]
    transitions:
      - from: open
        event: start
        to: working
        effects: [set_in_progress]
      - from: working
        event: complete
        to: done
        effects: [set_closed]
```

---

## 4. Derived State (Read Projections)

Computed in-memory from Issues + PhaseRecords + Workflow definitions on load. Never persisted — rebuilt from JSONL on every read. This avoids denormalization drift.

```
IssueView {
    # From Issue (all fields passed through)
    ... all Issue fields ...

    # Computed from child Issues
    children_total:     int         # Count of direct children
    children_closed:    int         # Count of closed children
    progress_pct:       int         # round(closed/total * 100), 0 if no children
    close_eligible:     bool        # All children closed (or no children for leaf tasks)

    # Computed from PhaseRecords + workflow definition
    workflow_state:     WorkflowState   # Full workflow state projection (see 2.6)
    current_phase:      string?     # Convenience: workflow_state.current_state
    attempt:            int         # Convenience: workflow_state.attempt
    last_verdict:       string?     # Most recent review verdict from payload (project-specific)
    verdict_summary:    string?     # Most recent review summary from payload (project-specific)
    has_rework:         bool        # last_verdict indicates rework needed
}
```

**WorkflowState derivation:** See Section 2.6 for the algorithm. The projection is computed from PhaseRecords that are already loaded into memory — no additional I/O is required.

**Verdict extraction:** `last_verdict` and `verdict_summary` are convenience fields extracted from the most recent PhaseRecord payload that contains a `verdict` field. Since payloads are project-defined, the core engine looks for a `verdict` key in the payload JSON. If absent, these fields are null.

---

## 5. Storage Architecture

### 5.1 Three-Layer Design

```
┌─────────────────────────────────────────────────┐
│  Access Layer: cr CLI                           │
│  Reads from SQLite, appends to JSONL, syncs     │
├─────────────────────────────────────────────────┤
│  Local Layer: SQLite (crumbs.db)                │
│  Indexed queries, sub-ms reads, gitignored      │
│  Rebuilt from JSONL on cr doctor --rebuild       │
├─────────────────────────────────────────────────┤
│  Git Layer: JSONL files                         │
│  Source of truth, git-tracked, human-readable   │
│  Append-only, merge-friendly diffs              │
└─────────────────────────────────────────────────┘
```

- **Git layer** (JSONL): The source of truth. Git-tracked, append-only, human-readable diffs. This is what syncs between collaborators and what survives `git clone`.
- **Local layer** (SQLite): The query engine. Gitignored, rebuilt from JSONL. Provides indexed lookups, sub-millisecond queries, and complex filtering that JSONL alone cannot efficiently support.
- **Access layer** (cr CLI): The interface. Reads from SQLite for all queries. Appends to JSONL for all writes, then updates SQLite in the same logical operation.

### 5.2 Directory Structure

```
.crumbs/
├── issues.jsonl        # Issue events (append-only, git-tracked)
├── phases.jsonl        # Phase execution records (append-only, git-tracked)
├── deps.jsonl          # Dependency records (git-tracked)
├── config.yaml         # Workflows, hooks, project settings (git-tracked)
├── crumbs.db           # SQLite query cache (gitignored, auto-rebuilt)
└── crumbs.lock         # PID file for single-writer guarantee
```

**JSONL files** (git-tracked):

- `issues.jsonl`: Issue mutations appended as events with full Issue state. Latest event per `id` is the current state. History is preserved for reconstruction at any point in time.
- `phases.jsonl`: All PhaseRecords kept (not just latest). Each record is an immutable event with a unique `id`. Records for the same `issue_id` are ordered by `timestamp`.
- `deps.jsonl`: One record per dependency relationship. Removal recorded as a new event with `removed: true`.

**SQLite database** (gitignored):

- `crumbs.db`: Indexed tables mirroring JSONL content. Rebuilt deterministically from JSONL by `cr doctor --rebuild`. Contains indexes on `issue_id`, `status`, `parent`, `epic_ancestor`, `phase`, and `timestamp`.

**Config** (git-tracked):

- `config.yaml`: Project settings including prefix, workflow definitions, hooks, and payload schemas.

**Lock file**:

- `crumbs.lock`: Contains a PID. Held during write operations. Prevents concurrent writers from corrupting append-only files. Stale locks (process no longer running) are automatically cleaned up.

### 5.3 Sync Protocol

**Write path:**
1. Acquire `crumbs.lock`
2. Append record to the appropriate JSONL file
3. Insert/update the corresponding SQLite row
4. Release `crumbs.lock`

Steps 2 and 3 form a single logical operation. If the process crashes between them, `cr doctor --rebuild` recovers by regenerating SQLite from JSONL.

**Read path:**
- All queries read from SQLite (indexed, sub-ms)
- Never read from JSONL for queries (too slow for filtered lookups at scale)

**Rebuild:**
- `cr doctor --rebuild` regenerates `crumbs.db` from JSONL files
- Deterministic: same JSONL produces same SQLite content
- Safe to delete `crumbs.db` at any time — it will be rebuilt on next `cr` invocation

**Git pull:**
- When JSONL files change (after `git pull`), the SQLite cache may be stale
- `cr sync` detects JSONL changes (by comparing file modification times or checksums) and rebuilds affected SQLite tables
- Auto-rebuild on first `cr` command after detecting stale cache

**Git merge conflicts:**
- JSONL is append-only, so most merges are conflict-free (both sides append different lines)
- For the rare case where both sides append to the same JSONL file: standard git merge concatenates both additions (correct for append-only files)
- Conflict resolution for `issues.jsonl` mutations to the same issue: latest timestamp wins (same as v1)

### 5.4 Why This Architecture

| Alternative | Why not |
|---|---|
| DuckDB | Analytical engine optimized for columnar scans, wrong workload for point queries on individual issues |
| Native JSON per-file (one file per issue) | Great diffs, terrible query performance at scale; hundreds of files in a directory |
| Redis / embedded KV | Wrong paradigm — no git compatibility, requires running server |
| Vector DB | Wrong tool — structured queries on typed fields, not similarity search |
| JSONL-only (no SQLite) | Proven as sync format but poor as query engine; every query requires full file scan |
| SQLite-only (no JSONL) | Great queries but binary file produces unusable diffs in git |

The JSONL + SQLite hybrid is the proven architecture that beads already uses. It is not a new invention — it is a well-understood pattern applied to a new domain.

### 5.5 Config Extension: Workflows Section

The `config.yaml` gains a `workflows` section (see Section 3.1 for the full schema). The v1 config fields (`prefix`, `sync_branch`) remain unchanged.

```yaml
# v1 fields (unchanged)
prefix: "lc"
sync_branch: "crumbs-sync"

# v2 additions
workflows:
  task:
    states: [open, cook, serve, tidy, closed, blocked]
    initial: open
    terminal: [closed]
    transitions:
      # ... (see Section 3 for full examples)
    hooks:
      context_assembler: "./scripts/crumbs-context.py"
  feature:
    # ...
  epic:
    # ...
```

---

## 6. CLI Surface (`cr`)

### 6.1 Setup

```
cr init                              # Create .crumbs/ directory, config, and SQLite db
cr doctor                            # Check for issues (hooks, sync, data integrity)
cr doctor --rebuild                  # Regenerate SQLite from JSONL
```

### 6.2 Finding Work

```
cr ready                             # Show unblocked actionable items (tasks, features, bugs — excludes epics)
cr ready --epic=<id>                 # Ready items within a specific epic
cr list [--status=X] [--type=X] [--parent=X] [--limit=N] [--all]
cr show <id>                         # Full issue detail (human-readable)
cr show <id> --json                  # Full IssueView as JSON
```

### 6.3 Creating & Updating

```
cr create --title="..." --type=task --priority=2 [--parent=<id>] [--description="..."]
cr create --title="..." --type=feature --parent=<id> \
    [--user-story="..."] [--acceptance-criteria="AC1" --acceptance-criteria="AC2"]
cr create --title="..." --type=task --parent=<id> \
    [--deliverables="D1" --deliverables="D2"] [--test-spec=<path>]

cr update <id> [--status=X] [--priority=X] [--title="..."] [--parent=X]
cr update <id> [--description="..."] [--description-file=<path>]
cr update <id> [--test-spec=<path>] [--feature-spec=<path>] [--epic-branch=<branch>]

cr close <id> [<id2> ...] [--reason="..."]
```

### 6.4 Hierarchy

```
cr children <id>                     # List direct children
cr tree <id>                         # Show full hierarchy tree
cr progress <id>                     # Show completion progress (bar + counts)
cr close-eligible                    # List all issues where close_eligible=true and status!=closed
cr close-eligible --type=epic        # Filter to epics only
```

### 6.5 Dependencies

```
cr dep add <issue> <depends-on>      # issue depends on depends-on
cr dep remove <issue> <depends-on>
cr blocked                           # Show all blocked issues
```

### 6.6 Comments

Freeform notes on issues for human-readable context that doesn't fit into typed phase records.

```
cr comment add <id> "note text"      # Add a freeform comment
cr comment list <id>                 # List comments on an issue
```

Comments are stored in `issues.jsonl` as events with `"event_type": "comment"` (distinct from `"event_type": "mutation"` used for issue state changes). Comment events are not phase records — use `cr phase` or `cr transition` for structured execution state.

### 6.7 Workflow Commands

New in v2. These commands interact with the configurable state machine.

```
cr next [<id>] [--epic=<id>] [--json]
```

Returns a ContextBundle for the next action. If `<id>` is provided, returns context for that specific issue. If omitted, selects the highest-priority ready issue (optionally filtered by `--epic`).

`cr next` performs:
1. Derive WorkflowState from PhaseRecords
2. Determine the next action from the workflow definition
3. Run the `prep` hook if configured
4. Call the project context assembler hook if configured
5. Return the ContextBundle

```
cr transition <id> <event> [--payload-file=<path>]
```

Fire an event on an issue's workflow. Records a PhaseRecord, validates against guards, executes side effects, and returns a TransitionResult. If `--payload-file` is provided, the file contents are attached as the PhaseRecord payload.

```
cr workflow show <type>              # Display the workflow definition for an issue type
cr workflow status <id>              # Show current workflow state for an issue
cr workflow history <id>             # Show transition history (events fired, states visited)
cr workflow validate                 # Check config for errors (unreachable states, guard syntax, etc.)
```

### 6.8 Phase Records

Direct phase record manipulation. Lower-level than `cr transition` — useful for recording phase starts and for projects that manage transitions externally.

```
cr phase start <issue-id> <phase>                      # Record phase start
cr phase complete <issue-id> <phase> [--payload-file=<path>]  # Record phase completion
cr phase fail <issue-id> <phase> [--payload-file=<path>]      # Record phase failure
cr phase history <issue-id>                             # Show phase execution history
cr phase last-verdict <issue-id>                        # Quick lookup of last review verdict
```

**Relationship to `cr transition`:** `cr transition` is the high-level command that validates against the workflow definition, checks guards, and executes side effects. `cr phase` is the low-level command that directly appends PhaseRecords. Projects that use `cr transition` for all state changes do not need `cr phase` — but `cr phase start` is still useful for recording when work begins (before a transition fires).

### 6.9 Sync

```
cr sync                              # Sync with git remote
cr sync --status                     # Check sync status without syncing
```

### 6.10 Project Health

```
cr stats                             # Counts by type, status, progress
cr audit [active|full|<id>]          # Structural/content validation + workflow validation
```

`cr audit` performs:
- Hierarchy depth validation (max 3 tiers)
- Orphan detection (children referencing missing parents)
- Dependency cycle detection
- Content completeness checks (features have acceptance criteria, tasks have deliverables)
- Artifact link validation (referenced files exist)
- Workflow state consistency (WorkflowState matches issue status)
- Stale phase detection (started without completed)

### 6.11 Migration

```
cr import-beads                      # One-time migration from .beads/
```

Non-destructive: reads `.beads/issues.jsonl`, writes `.crumbs/` files. Builds SQLite index after import.

**From crumbs v1 to v2:** Additive migration. v1 `.crumbs/` directories continue to work. The `workflows` section in `config.yaml` is optional — if absent, `cr` operates in v1 mode (phase records without workflow validation). Adding a `workflows` section enables v2 features (transitions, guards, context assembly).

### 6.12 Differences from Beads

| Capability | `bd` (beads) | `cr` (crumbs) |
|---|---|---|
| Epic filtering | Client-side ancestor walks | `cr ready --epic=<id>` (native) |
| Hierarchy display | No equivalent | `cr tree`, `cr children`, `cr progress` |
| Close eligibility | `bd epic close-eligible` (epic-only) | `cr close-eligible [--type=X]` (any parent type) |
| Phase tracking | `bd comments add "PHASE: ..."` | `cr phase complete <id> <phase>` with typed payload |
| Workflow state | Not tracked | `cr workflow status <id>` (derived from phases + config) |
| State transitions | Manual status updates | `cr transition <id> <event>` with guards and effects |
| Context assembly | Not supported | `cr next <id>` calls project hook, returns ContextBundle |
| Freeform comments | `bd comments add/list` | `cr comment add/list` (separate from phase records) |
| Validation | External `plan-validator.py` | `cr audit` (built-in, single pass) |
| Batch close | Supported | `cr close <id1> <id2> ...` |
| Retry context | `.line-cook/retry-context.json` | `cr phase last-verdict <id>` (indexed lookup) |
| Storage | JSONL only | JSONL (source of truth) + SQLite (query cache) |
| Config validation | None | `cr workflow validate` |

---

## 7. Context Assembly Protocol

### 7.1 How `cr next` Works

```
┌──────────────┐
│  cr next <id>│
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ 1. Load issue from SQLite│
│ 2. Derive WorkflowState  │
│ 3. Determine next action │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 4. Run prep hook         │
│    (if configured)       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ 5. Call context assembler hook       │
│    Input:  JSON (issue, state, etc.) │
│    Output: JSON (project context)    │
│    (if configured; empty if not)     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 6. Return ContextBundle  │
│    (issue + state +      │
│     hook context)        │
└──────────────────────────┘
```

### 7.2 Context Assembler Interface

The context assembler is an external script or binary. The core engine invokes it as a subprocess.

**Input** (JSON on stdin):

```json
{
    "issue": { /* full Issue object */ },
    "workflow_state": { /* full WorkflowState object */ },
    "attempt": 2,
    "phase_history": [ /* PhaseRecord array */ ],
    "config": { /* workflow config for this issue type */ }
}
```

**Output** (JSON on stdout):

```json
{
    "tools": ["python3", "pytest", "git"],
    "planning_context": { "architecture": "...", "constraints": "..." },
    "retry_analysis": { "persistent_issues": [...], "strategy_change": "..." },
    "custom_field": "any project-specific data"
}
```

The core engine does not interpret the output — it is passed through verbatim as the `context` field of the ContextBundle. The consumer (Line Cook's loop, Capsule's campaign) understands its own context format.

**Error handling:** If the hook exits with a non-zero status, `cr next` returns the ContextBundle with an empty `context` field and a warning. The consumer decides whether to proceed without context or abort.

**Hook path:** Configured in `.crumbs/config.yaml` under `hooks.context_assembler`. Resolved relative to the repository root. Can be any executable (Python script, shell script, Go binary, etc.).

### 7.3 Default Behavior (No Hook)

If no `context_assembler` hook is configured, `cr next` returns:

```json
{
    "issue": { /* ... */ },
    "workflow_state": { /* ... */ },
    "next_action": "cook_complete",
    "next_state": "serve",
    "attempt": 1,
    "max_attempts": 2,
    "context": {}
}
```

This is sufficient for simple projects that don't need project-specific context injection.

### 7.4 Example: Line Cook Context Assembler

A Line Cook project's `crumbs-context.py` might produce:

```json
{
    "tools": {
        "test_runner": "python3 -m unittest",
        "build": null,
        "lint": null,
        "formatter": null
    },
    "planning_context": {
        "path": "docs/planning/lc-abc/",
        "architecture": "Three-zone plugin architecture...",
        "constraints": ["No pytest dependency", "Bundle after package changes"]
    },
    "retry_analysis": {
        "attempt": 2,
        "persistent_issues": [
            {
                "description": "Missing edge case for empty string",
                "seen_in_attempts": [1, 2],
                "strategy": "Previous regex approach failed; switching to explicit validation"
            }
        ],
        "prior_verdicts": [
            {"attempt": 1, "verdict": "needs_changes", "summary": "Missing edge case"}
        ]
    },
    "sibling_context": {
        "completed_siblings": ["lc-abc.1.1", "lc-abc.1.2"],
        "patterns_established": ["Input validation uses validator module"]
    }
}
```

### 7.5 Example: Capsule Context Assembler

A Capsule project's `crumbs-context.sh` might produce:

```json
{
    "acceptance_criteria": [
        "Given valid input, function returns expected output",
        "Given invalid input, function returns descriptive error"
    ],
    "test_results": {
        "pass": 5,
        "fail": 2,
        "skip": 0
    },
    "worklog_path": ".capsule/worklogs/demo-001.1.1.md",
    "worktree_path": ".capsule/worktrees/demo-001.1.1/",
    "phase_config": {
        "provider": "claude-sonnet-4-6",
        "max_retries": 3,
        "timeout": "10m"
    },
    "prior_feedback": "Test for negative numbers missing. Add edge case coverage."
}
```

---

## 8. Session Recovery

### 8.1 Stale Detection

A phase is stale when a `started` PhaseRecord exists without a corresponding `completed` or `failed` record for the same `(issue_id, phase, attempt)` tuple. This happens when a session crashes or is interrupted mid-phase.

`cr audit` reports stale phases. `cr workflow status <id>` shows stale state with the `stale_since` timestamp.

### 8.2 Resume Semantics

When `cr next` encounters a stale issue (the issue's WorkflowState has `stale: true`):

1. The issue remains in the state it was in when the phase started
2. `cr next` returns the same ContextBundle as if the phase hadn't started — the consumer re-enters the phase
3. The attempt counter is NOT incremented (this is a resume, not a retry)
4. The stale `started` record remains in the history for audit purposes

The consumer can explicitly fail the stale phase (`cr phase fail <id> <phase>`) to advance the attempt counter and trigger retry logic instead of resume.

### 8.3 Checkpoint Compatibility

Capsule's checkpoint-based pause/resume pattern works naturally with crumbs:

1. Capsule saves a checkpoint after each phase completes (existing behavior)
2. The checkpoint references the issue ID and current workflow state
3. On resume, Capsule calls `cr workflow status <id>` to verify the checkpoint is consistent with crumbs state
4. If consistent: resume from checkpoint. If not: `cr next <id>` to get fresh context.

The crumbs engine does not manage checkpoints — that remains the orchestrator's responsibility. Crumbs provides the state that checkpoints reference.

---

## 9. Constraints & Validation

### 9.1 Structural

- **Max hierarchy depth**: 3 levels (depth values 0, 1, 2) — epic=0, feature=1, task=2
- **Parent must exist**: Creating an issue with `--parent=<id>` fails if that ID doesn't exist
- **Tasks and bugs cannot have children**: Exception: research epics may contain tasks directly
- **Bugs behave like tasks**: Bugs occupy the same hierarchy level as tasks (depth 2)
- **Epics cannot be children**: An epic's `parent` must be null
- **Depth consistency**: `depth` must match actual parent chain length
- **Epic ancestor consistency**: `epic_ancestor` must match actual root ancestor

### 9.2 Content

- `id` is immutable after creation
- `issue_type` is immutable after creation
- `priority` must be 0-4 (integer)
- PhaseRecords are immutable — append-only, no updates or deletes
- `attempt` is monotonically increasing per `(issue_id, phase)` pair (starts at 1)

### 9.3 Workflow

- Transitions must form a valid graph from `initial` to at least one `terminal` state
- Every state in `transitions` must be declared in `states`
- Guard expressions must be syntactically valid and reference only available context
- Guards must be pure functions — no I/O, no side effects
- When multiple transitions share `(from, event)`, they must be distinguished by mutually exclusive guards
- `cr workflow validate` checks all of the above and reports errors

### 9.4 Sync

- **Single writer**: `.crumbs/crumbs.lock` PID file prevents concurrent writes
- **Conflict resolution**: Latest timestamp wins for Issues; PhaseRecords never conflict (unique IDs, append-only)
- **Sync branch**: Configurable in `.crumbs/config.yaml` (default: `crumbs-sync`)
- **SQLite consistency**: If SQLite is stale relative to JSONL, auto-rebuild before serving queries

---

## 10. JSON Output Convention

All `cr` commands support `--json` for structured output. Human-readable format is the default.

### Example: `cr show <id> --json`

Returns the full IssueView — Issue fields + derived state + workflow state:

```json
{
    "id": "lc-abc.1.3",
    "title": "Add input validation",
    "issue_type": "task",
    "status": "in_progress",
    "priority": 2,
    "parent": "lc-abc.1",
    "epic_ancestor": "lc-abc",
    "depth": 2,
    "description": "Validate all user inputs before processing",
    "close_reason": null,
    "acceptance_criteria": [],
    "deliverables": ["validate.py module", "test coverage >90%"],
    "user_story": null,
    "test_spec": "tests/specs/input-validation.md",
    "feature_spec": null,
    "acceptance_doc": null,
    "planning_context": null,
    "epic_branch": null,
    "children_total": 0,
    "children_closed": 0,
    "progress_pct": 0,
    "close_eligible": true,
    "workflow_state": {
        "current_state": "cook",
        "available_events": ["cook_complete"],
        "attempt": 2,
        "phase_history": ["(see cr phase history for full records)"],
        "is_terminal": false,
        "stale": false,
        "stale_since": null
    },
    "current_phase": "cook",
    "attempt": 2,
    "last_verdict": "needs_changes",
    "verdict_summary": "Missing edge case for empty string",
    "has_rework": true,
    "created_at": "2026-02-08T10:00:00Z",
    "updated_at": "2026-02-09T14:30:00Z"
}
```

Note: `workflow_state.phase_history` contains the full PhaseRecord array. It is abbreviated in this example — see `cr phase history <id> --json` for the full format.

### Example: `cr next <id> --json`

Returns a ContextBundle:

```json
{
    "issue": {
        "id": "lc-abc.1.3",
        "title": "Add input validation",
        "status": "in_progress"
    },
    "workflow_state": {
        "current_state": "cook",
        "available_events": ["cook_complete"],
        "attempt": 2,
        "is_terminal": false,
        "stale": false
    },
    "next_action": "cook_complete",
    "next_state": "serve",
    "attempt": 2,
    "max_attempts": 2,
    "context": {
        "tools": { "test_runner": "python3 -m unittest" },
        "retry_analysis": {
            "persistent_issues": [
                { "description": "Missing edge case for empty string" }
            ]
        }
    }
}
```

### Example: `cr transition <id> <event> --json`

Returns a TransitionResult:

```json
{
    "success": true,
    "from_state": "serve",
    "to_state": "tidy",
    "event": "approved",
    "effects": ["record_phase"],
    "error": null,
    "cascade": null
}
```

### Example: `cr transition <id> <event> --json` (with cascade)

```json
{
    "success": true,
    "from_state": "tidy",
    "to_state": "closed",
    "event": "tidy_complete",
    "effects": ["record_phase", "set_closed", "check_parent"],
    "error": null,
    "cascade": {
        "parent_id": "lc-abc.1",
        "evaluated": true,
        "transitioned": true,
        "from_state": "open",
        "to_state": "plate"
    }
}
```

### Example: `cr transition <id> <event> --json` (guard rejection)

```json
{
    "success": false,
    "from_state": "serve",
    "to_state": "serve",
    "event": "needs_changes",
    "effects": [],
    "error": "Guard 'attempt < max_attempts' failed: attempt 2 >= max_attempts 2",
    "cascade": null
}
```

### Example: `cr phase history <id> --json`

Returns an array of PhaseRecord objects ordered by timestamp:

```json
[
    {
        "id": "ph-001",
        "issue_id": "lc-abc.1.3",
        "phase": "cook",
        "status": "completed",
        "attempt": 1,
        "timestamp": "2026-02-08T11:00:00Z",
        "payload": {
            "intent": "Add input validation module",
            "approach": "Regex-based validation with custom error messages",
            "files_changed": ["src/validate.py", "src/models.py"],
            "tests_written": ["tests/test_validate.py"],
            "findings": []
        }
    },
    {
        "id": "ph-002",
        "issue_id": "lc-abc.1.3",
        "phase": "serve",
        "status": "completed",
        "attempt": 1,
        "timestamp": "2026-02-08T11:30:00Z",
        "payload": {
            "verdict": "needs_changes",
            "blocking_issues": 1,
            "summary": "Missing edge case for empty string",
            "issues": [
                {
                    "severity": "major",
                    "category": "correctness",
                    "file": "src/validate.py",
                    "description": "Empty string input not handled",
                    "suggestion": "Add check for empty/whitespace-only strings"
                }
            ]
        }
    }
]
```

---

## 11. Migration

### 11.1 From Beads

```
cr import-beads
```

One-time, non-destructive conversion. Reads `.beads/issues.jsonl`, writes `.crumbs/` files, builds SQLite index.

- Maps beads fields to crumbs Issue fields
- Computes `epic_ancestor` and `depth` from parent chains
- Parses `bd comments` for `PHASE:` markers and creates PhaseRecords
- Reads `.line-cook/retry-context.json` if present and creates a ServePayload
- Extracts dependency records
- Preserves original timestamps
- Does not modify or remove `.beads/`

**Fields left empty during import** (populated going forward by `cr create`):
- `acceptance_criteria`, `deliverables`, `user_story` — embedded as unstructured text in legacy descriptions
- Artifact link fields — not stored in beads; backfillable via `cr update`

### 11.2 From Crumbs v1 to v2

Additive, non-breaking migration:

1. Existing `.crumbs/` directories work unchanged
2. Add `workflows` section to `config.yaml` to enable v2 features
3. Existing PhaseRecords are preserved — WorkflowState is derived from them
4. Run `cr workflow validate` to verify config
5. Run `cr doctor --rebuild` to add SQLite indexes for new query patterns

If no `workflows` section exists in config, `cr` operates in v1 compatibility mode: phase records are accepted without workflow validation, and `cr next` / `cr transition` return errors indicating no workflow is configured.
