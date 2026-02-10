# Crumbs Specification

> Git-native issue tracking with built-in workflow execution state

## 1. Overview

Crumbs is a git-native issue tracker that stores work items as append-only JSONL in the repository. It syncs via normal git operations, survives session boundaries, and natively tracks the trail of phase execution history — the crumbs an agent leaves as it works.

Crumbs replaces both the `bd` CLI (beads) and the ad-hoc `.line-cook/` state files with a single tool that understands hierarchy, dependencies, and workflow phases as first-class concepts.

### Design Principles

- **Git-native**: JSONL files live in-repo under `.crumbs/`, sync with normal git operations
- **Event-sourced state**: Phase records are append-only immutable events; current state is a projection
- **Hierarchical**: Strict 3-tier hierarchy (epic → feature → task) with precomputed ancestry and progress
- **Single tool**: One CLI (`cr`) replaces both `bd` and `.line-cook/` state files
- **Graceful degradation**: Missing optional data never blocks the workflow

### Anti-Patterns Avoided

| Anti-pattern          | How crumbs avoids it                                                                                  |
|-----------------------|-------------------------------------------------------------------------------------------------------|
| God Object            | Work items and phase records are separate entity types with single responsibility each               |
| Inner Platform        | No generic "custom fields" framework — specific typed fields for known workflow needs                |
| Golden Hammer         | Phase payloads are typed per phase (CookPayload, ServePayload), not one generic event blob           |
| Mutable state         | Phase records are append-only; current state derived from latest events                              |
| Denormalization drift | Derived fields (progress_pct, close_eligible) are computed projections, not stored copies            |
| Missing concept       | Execution state (verdicts, retry counts, findings) is a first-class entity, not text hidden in comments |

---

## 2. Data Model

### 2.1 Issue (Core Work Item)

The primary entity. Carries forward everything beads provides (id, title, type, parent, priority, status) plus hierarchy acceleration fields and artifact links.

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
    test_spec:        string?   # Path to TDD spec (tests/specs/<slug>.md)
    feature_spec:     string?   # Path to BDD feature (tests/features/<slug>.feature)
    acceptance_doc:   string?   # Path to acceptance document
    planning_context: string?   # Path to planning context directory
    epic_branch:      string?   # Git branch name for this epic

    # Timestamps
    created_at:     datetime    # Auto-set on creation
    updated_at:     datetime    # Auto-set on every mutation
}
```

**Field notes:**

- `epic_ancestor` + `depth` eliminate parent-chain walks currently done by `find_epic_ancestor()` and `is_descendant_of_epic()` in iteration.py (lines 315-413), which make 1-3 subprocess calls per task
- `acceptance_criteria`, `deliverables`, `user_story` eliminate regex parsing of description text that menu-plan-to-beads.sh currently embeds as unstructured strings
- Artifact link fields (`test_spec`, `feature_spec`, etc.) eliminate filesystem path inference — paths are set at creation time by the plan converter

### 2.2 PhaseRecord (Execution Event)

Append-only record of workflow phase execution. One record per phase invocation per issue. This replaces the `bd comments add "PHASE: ..."` pattern and the `.line-cook/retry-context.json` file.

```
PhaseRecord {
    id:         string      # Auto-generated unique ID
    issue_id:   string      # FK → Issue.id
    phase:      enum        # prep | cook | serve | tidy | plate
    status:     enum        # started | completed | failed
    attempt:    int         # Retry counter per (issue_id, phase) pair (starts at 1, monotonically increasing)
    timestamp:  datetime    # When this record was created
    payload:    Payload?    # Phase-specific typed payload (see 2.3-2.6), null for prep/plate
}
```

Payload types are defined for phases that produce structured output: cook (2.3), serve (2.4), tidy (2.5). The `prep` and `plate` phases record start/complete/fail events but carry no typed payload (payload is null).

### 2.3 CookPayload

Records what happened during implementation.

```
CookPayload {
    intent:         string          # What the task set out to do
    approach:       string?         # How it was implemented
    files_changed:  list[string]    # File paths modified
    tests_written:  list[string]    # Test file paths
    findings:       list[Finding]   # Issues discovered during cook
}
```

### 2.4 ServePayload

Structured review results. Replaces the `SERVE_RESULT` text block currently parsed by line-loop, and the `.line-cook/retry-context.json` file written by `write_retry_context()` (iteration.py:997-1035).

```
ServePayload {
    verdict:          enum          # approved | needs_changes | blocked
    blocking_issues:  int           # Count of blocking issues
    summary:          string        # Brief review assessment
    issues:           list[ReviewIssue]
}

ReviewIssue {
    severity:    enum       # critical | major | minor | nit
    category:    string     # correctness | security | style | completeness
    file:        string?    # File path if applicable
    description: string
    suggestion:  string?    # How to fix
}
```

### 2.5 TidyPayload

Records commit and cleanup outcomes.

```
TidyPayload {
    commit_sha:     string?         # Git commit hash
    issues_filed:   list[string]    # IDs of newly created issues (from findings)
    issues_closed:  list[string]    # IDs closed during tidy
    epic_merged:    bool            # Whether an epic branch was merged
    push_status:    enum            # success | failed | skipped
}
```

### 2.6 Finding

Shared type for discoveries during cook, serve, or audit phases.

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

### 2.7 Dependency

Tracks blocking relationships between issues.

```
Dependency {
    from_id:    string      # FK → Issue.id (the blocked item)
    to_id:      string      # FK → Issue.id (the blocker)
    type:       enum        # blocks | relates_to
    created_at: datetime
}
```

---

## 3. Derived State (Read Projections)

Computed in-memory from Issues + PhaseRecords on load. Never persisted — rebuilt from JSONL on every read. This avoids denormalization drift.

```
IssueView {
    # From Issue (all fields passed through)
    ... all Issue fields ...

    # Computed from child Issues
    children_total:     int         # Count of direct children
    children_closed:    int         # Count of closed children
    progress_pct:       int         # round(closed/total * 100), 0 if no children
    close_eligible:     bool        # All children closed (or no children for leaf tasks)

    # Computed from PhaseRecords
    current_phase:      enum?       # Phase from the most recent PhaseRecord by timestamp (regardless of status)
    attempt:            int         # Latest attempt number
    last_verdict:       enum?       # Most recent serve verdict
    verdict_summary:    string?     # Most recent serve summary
    has_rework:         bool        # last_verdict == needs_changes
}
```

`close_eligible` replaces the logic in `check_feature_completion()` and `check_epic_completion_after_feature()` (iteration.py:776-824), which currently make 3 subprocess calls each.

---

## 4. Storage Format

All data lives under `.crumbs/` in the repository root:

```
.crumbs/
├── issues.jsonl        # Issue events (append-only)
├── phases.jsonl        # Phase execution records (append-only)
├── deps.jsonl          # Dependency records
├── config.yaml         # Project settings
└── crumbs.lock         # PID file for single-writer guarantee
```

### 4.1 JSONL Conventions

Each `.jsonl` file contains one JSON object per line, representing the full event history.

**Issues** (`issues.jsonl`): Issue mutations (status change, reparent, field update) are appended as new events with the full Issue state. The latest event per `id` is the current state. This means:

- History is preserved — state at any point in time can be reconstructed
- Sync conflicts resolve by timestamp (latest wins)
- File is append-only — safe for concurrent readers

**Phase records** (`phases.jsonl`): All records are kept (not just latest). Each record is an immutable event with a unique `id`. Records for the same `issue_id` are ordered by `timestamp`.

**Dependencies** (`deps.jsonl`): One record per dependency relationship. Removal is recorded as a new event with a `removed: true` flag.

### 4.2 Config

`.crumbs/config.yaml` stores project-level settings:

```yaml
prefix: "lc"              # Issue ID prefix
sync_branch: "crumbs-sync"  # Git branch for sync operations
```

### 4.3 Lock File

`.crumbs/crumbs.lock` contains a PID and is held during write operations. Prevents concurrent writers from corrupting append-only files. Stale locks (process no longer running) are automatically cleaned up.

---

## 5. CLI Surface (`cr`)

### 5.1 Setup

```
cr init                              # Create .crumbs/ directory and config
cr doctor                            # Check for issues (hooks, sync, data integrity)
```

### 5.2 Finding Work

```
cr ready                             # Show unblocked actionable items (tasks, features, bugs — excludes epics)
cr ready --epic=<id>                 # Ready items within a specific epic
cr list [--status=X] [--type=X] [--parent=X] [--limit=N] [--all]
cr show <id>                         # Full issue detail (human-readable)
cr show <id> --json                  # Full IssueView as JSON
```

### 5.3 Creating & Updating

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

### 5.4 Hierarchy

```
cr children <id>                     # List direct children (convenience for cr list --parent=<id>)
cr tree <id>                         # Show full hierarchy tree
cr progress <id>                     # Show completion progress (bar + counts)
cr close-eligible                    # List all issues where close_eligible=true and status!=closed
cr close-eligible --type=epic        # Filter to epics only
```

### 5.5 Dependencies

```
cr dep add <issue> <depends-on>      # issue depends on depends-on
cr dep remove <issue> <depends-on>
cr blocked                           # Show all blocked issues
```

### 5.6 Comments

Freeform notes on issues for human-readable context that doesn't fit into typed phase records.

```
cr comment add <id> "note text"      # Add a freeform comment
cr comment list <id>                 # List comments on an issue
```

Comments are stored in `issues.jsonl` as events with `"event_type": "comment"` (distinct from `"event_type": "mutation"` used for issue state changes). Comment events are not phase records — use `cr phase` for structured execution state.

### 5.7 Phase Records

New — no beads equivalent. Replaces comment-based phase tracking and `.line-cook/` state files.

```
cr phase start <issue-id> <phase>                      # Record phase start
cr phase complete <issue-id> <phase> [--payload-file=<path>]  # Record phase completion with typed payload
cr phase fail <issue-id> <phase> [--payload-file=<path>]      # Record phase failure
cr phase history <issue-id>                             # Show phase execution history
cr phase last-verdict <issue-id>                        # Quick lookup of last serve verdict
```

### 5.8 Sync

```
cr sync                              # Sync with git remote
cr sync --status                     # Check sync status without syncing
```

### 5.9 Project Health

```
cr stats                             # Counts by type, status, progress
cr audit [active|full|<id>]          # Structural/content validation
```

`cr audit` replaces the standalone `plan-validator.py` script, performing:
- Hierarchy depth validation (max 3 tiers)
- Orphan detection (children referencing missing parents)
- Dependency cycle detection
- Content completeness checks (features have acceptance criteria, tasks have deliverables)
- Artifact link validation (referenced files exist)

### 5.10 Migration

```
cr import-beads                      # One-time migration from .beads/
```

Non-destructive: reads `.beads/issues.jsonl`, writes `.crumbs/issues.jsonl`. See the [integration spec](crumbs-line-cook-integration.md) for migration details.

### 5.11 Differences from Beads

| Capability               | `bd` (beads)                       | `cr` (crumbs)                                         |
|--------------------------|---------------------------------------|-------------------------------------------------------|
| Epic filtering           | Client-side ancestor walks            | `cr ready --epic=<id>` (native)                       |
| Hierarchy display        | No equivalent                         | `cr tree`, `cr children`, `cr progress`               |
| Close eligibility        | `bd epic close-eligible` (epic-only)  | `cr close-eligible [--type=X]` (any parent type)      |
| Phase tracking           | `bd comments add "PHASE: ..."`        | `cr phase complete <id> <phase>` with typed payload   |
| Freeform comments        | `bd comments add/list`                | `cr comment add/list` (separate from phase records)   |
| Validation               | External `plan-validator.py`          | `cr audit` (built-in, single pass)                    |
| Batch close              | Supported but unused                  | `cr close <id1> <id2> ...`                            |
| Retry context            | `.line-cook/retry-context.json`       | `cr phase last-verdict <id>`                          |
| Description update       | `bd update --body-file=<path>`        | `cr update --description-file=<path>`                 |
| Interactive edit         | `bd edit` (opens $EDITOR)             | Not supported — agents can't use interactive editors; use `cr update --description-file=<path>` for bulk edits |

---

## 6. Constraints & Validation

### 6.1 Structural

- **Max hierarchy depth**: 3 levels (depth values 0, 1, 2) — epic=0, feature=1, task=2
- **Parent must exist**: Creating an issue with `--parent=<id>` fails if that ID doesn't exist
- **Tasks and bugs cannot have children**: Exception: research epics may contain tasks directly (per ADR 0005)
- **Bugs behave like tasks**: Bugs occupy the same hierarchy level as tasks (depth 2), must have a parent feature or be orphaned (parentless)
- **Epics cannot be children**: An epic's `parent` must be null
- **Depth consistency**: `depth` must match actual parent chain length
- **Epic ancestor consistency**: `epic_ancestor` must match actual root ancestor (recomputed on reparent)

### 6.2 Content

- `id` is immutable after creation
- `issue_type` is immutable after creation (prevents type confusion)
- `priority` must be 0-4 (integer)
- PhaseRecords are immutable — append-only, no updates or deletes
- `attempt` is monotonically increasing per `(issue_id, phase)` pair within PhaseRecords (starts at 1)

### 6.3 Sync

- **Single writer**: `.crumbs/crumbs.lock` PID file prevents concurrent writes
- **Conflict resolution**: Latest timestamp wins for Issues; PhaseRecords never conflict (unique IDs, append-only)
- **Sync branch**: Configurable in `.crumbs/config.yaml` (default: `crumbs-sync`)

---

## 7. JSON Output Convention

All `cr` commands support `--json` for structured output. Human-readable format is the default.

### Example: `cr show <id> --json`

Returns the full IssueView — Issue fields + derived state + latest phase state:

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
    "current_phase": "cook",
    "attempt": 2,
    "last_verdict": "needs_changes",
    "verdict_summary": "Missing edge case for empty string",
    "has_rework": true,
    "created_at": "2026-02-08T10:00:00Z",
    "updated_at": "2026-02-09T14:30:00Z"
}
```

### Example: `cr ready --json`

Returns an array of IssueView objects for all ready work items.

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
