# Crumbs v2 Specification

> Git-native issue tracking with configurable state machine workflows

## 1. Overview

Crumbs is a git-native issue tracker that stores work items as append-only JSONL in the repository. It syncs via normal git operations, survives session boundaries, and natively tracks the trail of phase execution history — the crumbs an agent leaves as it works.

### 1.1 Design Principles

- **Git-native**: JSONL files in-repo under `.crumbs/`, synced with normal git operations
- **Event-sourced state**: Phase records are append-only immutable events; current state is a projection
- **Machine-driven prompting**: `cr next` tells the consumer what to do; the consumer doesn't decide workflow sequence
- **Project-agnostic**: The core engine knows states, events, transitions, and guards — not project-specific phase names
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

#### Layer 2: Project Integration

Each project provides:
- **Workflow definition** in `.crumbs/config.yaml`
- **Context assembler hook** (script/binary that `cr next` calls to fill the ContextBundle)
- **Phase payload schemas** (what data each phase produces)
- **Orchestrator** that calls `cr next` / `cr transition`

> See [crumbs-v2-design.md](crumbs-v2-design.md) for rationale on this separation and what the core intentionally does NOT know about.

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

The `phase` field is validated against the workflow config. The core engine validates that the phase name exists in the issue's workflow definition.

### 2.3 Typed Payloads (Extensible)

Payloads are project-defined JSON objects attached to completed PhaseRecords. The core engine stores and returns them verbatim — it does not interpret payload contents.

Projects register payload schemas in their workflow config (Section 3.1). The core validates payloads against registered schemas when provided, but schema registration is optional. Unregistered payloads are accepted as raw JSON.

> See [crumbs-v2-design.md](crumbs-v2-design.md) for project-specific payload examples (Line Cook, Capsule).

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
    attempt:        int             # Which attempt this is (convenience copy of workflow_state.attempt)
    max_attempts:   int?            # Max attempts configured for this transition (null if unlimited)

    # From context assembler hook (project-specific, empty if no hook configured)
    context:        object          # Project-specific context (tools, planning docs, retry analysis, etc.)
}
```

**Note:** `ContextBundle.attempt` is a convenience copy of `workflow_state.attempt`, provided so consumers can access the attempt number without navigating into the workflow state object.

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

parking:                                # Optional: exclude non-actionable items from cr ready / cr next
  epics: [<title>, ...]                 # Issues under epics with these titles excluded
  priority_threshold: <int>             # Issues at or above this priority excluded (default: none)

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
- `parking.priority_threshold` must be 0-4 if specified
- `parking.epics` entries are validated at runtime against existing epic titles (not at config load)

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

> See [crumbs-v2-design.md](crumbs-v2-design.md) for example workflows showing cascading in context.

---

## 4. Derived State (Read Projections)

Computed in-memory from Issues + PhaseRecords + Workflow definitions on load. Never persisted — rebuilt from JSONL on every read.

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

- **Git layer** (JSONL): Source of truth. Git-tracked, append-only, human-readable diffs. Syncs between collaborators via `git clone`/`git pull`.
- **Local layer** (SQLite): Query engine. Gitignored, rebuilt from JSONL. Indexed lookups and sub-millisecond queries.
- **Access layer** (cr CLI): Interface. Reads from SQLite for queries. Appends to JSONL for writes, then updates SQLite in the same logical operation.

> See [crumbs-v2-design.md](crumbs-v2-design.md) for the rationale behind this architecture and alternatives evaluated.

### 5.2 Directory Structure

```
.crumbs/
├── redirect            # Optional: path to canonical .crumbs/ (for worktrees)
├── issues.jsonl        # Issue events (append-only, git-tracked)
├── phases.jsonl        # Phase execution records (append-only, git-tracked)
├── deps.jsonl          # Dependency records (git-tracked)
├── config.yaml         # Workflows, hooks, project settings (git-tracked)
├── crumbs.db           # SQLite query cache (gitignored, auto-rebuilt)
└── crumbs.lock         # PID file for single-writer guarantee
```

**JSONL files** (git-tracked):

- `issues.jsonl`: Issue mutations appended as events with full Issue state. Latest event per `id` is the current state.
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
- Never read from JSONL for queries

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
- Conflict resolution for `issues.jsonl` mutations to the same issue: latest timestamp wins

### 5.4 Full Config Example

Complete `config.yaml` showing all sections (see Section 3.1 for the schema).

```yaml
prefix: "lc"
sync_branch: "crumbs-sync"

parking:
  epics: ["Backlog", "Retrospective"]
  priority_threshold: 4

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

### 5.5 Worktree Support (Redirect Files)

Workers operating in git worktrees can share a single `.crumbs/` database via redirect files.

**Redirect file:** `.crumbs/redirect` contains a single line — the path (relative or absolute) to the canonical `.crumbs/` directory. When present, all `cr` commands resolve through the redirect before accessing data.

**Resolution protocol:**

1. `cr` checks for `.crumbs/redirect` in the current working directory
2. If found, reads the path (one line, trimmed)
3. Resolves the path relative to the current working directory
4. Follows chains up to 3 levels (with circular detection)
5. All reads/writes target the resolved canonical `.crumbs/`

**Shared resources in the canonical `.crumbs/`:**

- Lock file (`crumbs.lock`) — workers in worktrees contend for the same lock, serializing writes
- SQLite cache (`crumbs.db`) — shared across all worktrees
- JSONL files — shared source of truth

**Setup:** The orchestrator creates worktrees and redirect files. Workers use `cr` commands normally — redirect resolution is transparent. See `cr redirect` in Section 6.1 for the admin command.

This enables the Gas Town pattern: a bare repo with multiple worktrees, each with `.crumbs/redirect` pointing to a shared `.crumbs/` directory. It also supports Claude Code's `EnterWorktree` tool — worktrees created via that mechanism can use `cr redirect` to share the main repo's database.

---

## 6. CLI Surface (`cr`)

The `cr` CLI serves three distinct roles at runtime. Organizing commands by role — rather than by category — clarifies who calls what and prevents interface leakage between layers.

- **Administration** (6.1): Project setup, issue lifecycle, health checks. Used by humans, CI, and planning agents.
- **Orchestrator** (6.2): Work selection and state transitions. Used by the loop/campaign that drives workflow.
- **Worker** (6.3): Context reading and execution checkpoints. Used by phase agents during execution.
- **Shared** (6.4): Reference, inspection, and collaboration. Used by both orchestrators and workers.

### 6.1 Setup & Administration

Commands for humans, CI, and planning agents — project setup, issue lifecycle, and health checks.

```
cr init                              # Create .crumbs/ directory, config, and SQLite db
cr doctor                            # Check for issues (hooks, sync, data integrity)
cr doctor --rebuild                  # Regenerate SQLite from JSONL
cr sync                              # Sync with git remote
cr sync --status                     # Check sync status without syncing
```

**Issue lifecycle:**

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

**Note on `cr update --status`:** Sets the issue's `status` field directly (open/in_progress/closed), which is independent of the workflow state machine. The workflow state is driven by transitions and PhaseRecords, while `status` is an administrative field. Use `cr transition` to advance the workflow; use `cr update --status` only for administrative corrections.

**Workflow administration:**

```
cr workflow show <type>              # Display the workflow definition for an issue type
cr workflow validate                 # Check config for errors (unreachable states, guard syntax, etc.)
```

**Project health:**

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

**Worktree setup:**

```
cr redirect <target-path>            # Create .crumbs/redirect pointing to target
cr redirect --show                   # Show resolved .crumbs/ path
```

Sets up `.crumbs/redirect` for workers operating in git worktrees (see Section 5.5).

### 6.2 Orchestrator Interface

Commands for the loop or campaign that drives workflow. The orchestrator's job is to repeatedly call `cr next`, dispatch work to a phase agent, then call `cr transition` with the result. It never executes phase work itself.

| Command | Purpose |
|---|---|
| `cr next [<id>] [--epic=<id>]` | Get next work + context bundle |
| `cr transition <id> <event> [--payload-file]` | Record outcome + advance state |
| `cr ready [--epic=<id>] [--all]` | List all actionable work (batch planning) |
| `cr workflow status <id>` | Verify state consistency |
| `cr close-eligible [--type=X]` | Check cascade readiness |
| `cr progress <id>` | Track completion progress |

**`cr next`** returns a ContextBundle (Section 2.7) for the next action. If `<id>` is provided, returns context for that specific issue. If omitted, selects the highest-priority ready issue (optionally filtered by `--epic`).

`cr next` performs:
1. Derive WorkflowState from PhaseRecords
2. Determine the next action from the workflow definition
3. Run the `prep` hook if configured
4. Call the project context assembler hook if configured
5. Return the ContextBundle

**`cr transition`** fires an event on an issue's workflow. Records a PhaseRecord, validates against guards, executes side effects, and returns a TransitionResult (Section 2.8). If `--payload-file` is provided, the file contents are attached as the PhaseRecord payload.

**Mapping to PhaseRecords:** `cr transition` creates a PhaseRecord with `status: completed` (on success) or `status: failed` (on guard rejection). The PhaseRecord's `phase` field is set to the `to_state` of the transition.

**`cr ready`** shows unblocked actionable items (tasks, features, bugs — excludes epics). Respects the `parking` config (Section 3.1): children of parking epics and issues at or above the configured priority threshold are excluded by default. Use `--all` to bypass filtering and show everything including parking items.

**`cr close-eligible`** lists issues where `close_eligible=true` and `status!=closed`. Use `--type=epic` to filter to epics only.

**`cr progress`** shows completion progress (bar + counts) for a parent issue.

#### `cr transition` vs `cr phase`

These commands serve different roles and should not be confused:

- **`cr transition`** is the **orchestrator command**. It fires a workflow event, validates guards, records a PhaseRecord, executes effects, and cascades to parents. This is the workflow driver.
- **`cr phase start/complete/fail`** are **worker commands** (Section 6.3). They record execution checkpoints for crash recovery and audit. They do NOT fire workflow events or check guards.
- **Typical flow:** Worker calls `cr phase start` → executes work → orchestrator calls `cr transition` (which implicitly records a PhaseRecord). The worker's `cr phase start` is optional but recommended for stale detection.

### 6.3 Worker Interface

Commands for phase agents during execution. The worker receives a ContextBundle (from the orchestrator, which got it from `cr next`), executes its phase, and records the result via `cr phase`. Workers do not select work or drive transitions — the orchestrator does that.

| Command | Purpose |
|---|---|
| `cr show <id> [--json]` | Read issue details |
| `cr phase start <id> <phase>` | Checkpoint: "I'm starting" |
| `cr phase complete <id> <phase> [--payload-file]` | Checkpoint: "I'm done" + payload |
| `cr phase fail <id> <phase> [--payload-file]` | Checkpoint: "I failed" + reason |
| `cr phase last-verdict <id>` | Read previous review verdict |
| `cr comment add <id> "..."` | Leave notes for next phase |

**`cr show`** returns the full IssueView (Section 4). Use `--json` for structured output.

**`cr phase start/complete/fail`** record execution checkpoints. These are lower-level than `cr transition` — they record what happened during a phase without driving the workflow state machine. The orchestrator decides when and how to transition based on the worker's result.

**`cr phase last-verdict`** returns the most recent review verdict from phase payloads. Workers use this to understand what went wrong on a previous attempt.

**`cr comment add`** leaves freeform notes on issues for context that doesn't fit into typed phase records. Comments are stored in `issues.jsonl` as events with `"event_type": "comment"`.

### 6.4 Shared Commands

Commands used by both orchestrators and workers for reference, inspection, and collaboration.

| Command | Purpose |
|---|---|
| `cr show <id>` | Reference lookup |
| `cr list [--status=X] [--type=X] [--parent=X] [--limit=N] [--all]` | Query related work |
| `cr children <id>` / `cr tree <id>` | Hierarchy inspection |
| `cr comment add/list <id>` | Collaboration |
| `cr phase history <id>` | Execution history |
| `cr workflow history <id>` | Transition audit trail |
| `cr blocked` | Show blocked issues |
| `cr dep add <issue> <depends-on>` | Add dependency |
| `cr dep remove <issue> <depends-on>` | Remove dependency |

### 6.5 Orchestrator Loop Protocol

The canonical orchestrator loop. All orchestrators (Line Cook's `line_loop`, Capsule's campaign, etc.) follow this pattern:

```
while has_work:
    bundle = cr next [--epic=<id>]
    if bundle is empty: break

    # Optional: record that work is starting (for stale detection)
    cr phase start <bundle.issue.id> <bundle.next_state>

    # Dispatch to the appropriate phase agent
    result = invoke_worker(bundle)

    # Record the outcome — engine handles guards, effects, cascade
    if result.success:
        cr transition <id> <success_event> --payload-file=result.json
    else:
        cr transition <id> <failure_event> --payload-file=result.json
```

This replaces ad-hoc completion detection patterns (snapshot diffs, stdout signal parsing, file-based retry context) with a single protocol. The orchestrator's only responsibilities are calling `cr next` and `cr transition` — the engine handles guards, retry counting, cascade evaluation, and effect execution.

**Note:** The orchestrator calls `cr phase start` (a worker command, Section 6.3) before dispatching the worker. This is the one cross-boundary usage — the orchestrator records the start checkpoint for stale detection, then hands off to the worker.

**What the orchestrator does NOT do:**
- Parse phase-specific payloads (the engine evaluates guards against them)
- Track attempt counts (the engine derives these from PhaseRecords)
- Walk hierarchy for cascade (the `check_parent` effect handles this)
- Filter parking items from ready lists (the `parking` config handles this)

### 6.6 Worker Execution Protocol

The canonical worker lifecycle. All workers (cook agent, serve agent, test-writer, etc.) follow this pattern:

```
# Worker receives ContextBundle (from orchestrator)
issue = bundle.issue
state = bundle.workflow_state
context = bundle.context  # Project-specific (tools, retry analysis, etc.)

# Read retry context from the bundle (no file I/O needed)
if state.attempt > 1:
    prior_verdicts = state.phase_history  # Previous PhaseRecords
    retry_analysis = context.retry_analysis  # From context assembler

# Execute phase work
result = do_work(issue, context)

# Report result as structured payload
write_payload(result)  # → payload.json
# Orchestrator calls cr transition with this payload
```

**Key constraints:**
- Workers never call `cr next` or `cr transition` — the orchestrator does that
- Workers MAY call `cr phase start/complete/fail` for their own checkpointing
- Workers read retry context from `bundle.workflow_state.phase_history` and `bundle.context` — not from ad-hoc files
- Workers write structured payloads; the orchestrator decides what event to fire

---

## 7. Context Assembly Protocol

Context assembly is the **orchestrator's responsibility**. When the orchestrator calls `cr next`, the engine invokes the project's context assembler hook and assembles a ContextBundle — everything the worker needs in one structured object. The TransitionResult (returned by `cr transition`) is the **return contract** — how the orchestrator learns what happened.

The worker never calls `cr next` or assembles its own context. The orchestrator provides the ContextBundle; the worker executes its phase and produces a structured payload; the orchestrator records the outcome via `cr transition`.

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

The core engine does not interpret the output — it is passed through verbatim as the `context` field of the ContextBundle. The consumer understands its own context format.

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

This is sufficient for projects that don't need project-specific context injection.

> See [crumbs-v2-design.md](crumbs-v2-design.md) for example context assembler outputs from Line Cook and Capsule.

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

Returns the full IssueView:

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
    "workflow_state": {
        "current_state": "cook",
        "available_events": ["cook_complete"],
        "attempt": 2,
        "is_terminal": false,
        "stale": false,
        "stale_since": null
    },
    "current_phase": "cook",
    "attempt": 2,
    "last_verdict": "needs_changes",
    "has_rework": true
}
```

### Example: `cr transition <id> <event> --json` (success with cascade)

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

Firing an event for which no valid transition exists from the current state:

```json
{
    "success": false,
    "from_state": "open",
    "to_state": "open",
    "event": "approved",
    "effects": [],
    "error": "No transition from state 'open' for event 'approved'",
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
            "files_changed": ["src/validate.py"],
            "tests_written": ["tests/test_validate.py"]
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
            "summary": "Missing edge case for empty string"
        }
    }
]
```

