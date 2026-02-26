# Crumbs v2 Design Companion

> Rationale, examples, and migration context for the [Crumbs v2 Specification](crumbs-v2-spec.md)

The spec defines *what*; this document explains *why*.

---

## 1. What Changed from v1

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

---

## 2. Two-Layer Architecture Rationale

### What the Core Does NOT Know About

The crumbs core engine is deliberately ignorant of project-specific concerns:

- Cook, serve, tidy, plate (Line Cook phases)
- Test-writer, test-review, execute (Capsule phases)
- TDD methodology, sous-chef, polisher (Line Cook agents)
- Writer/reviewer pairs (Capsule retry pattern)
- Kitchen signals, SERVE_RESULT blocks (Line Cook specifics)

### Why This Separation Matters

The two-layer split keeps the engine reusable across projects with fundamentally different workflows. Line Cook uses a cook→serve→tidy cycle with TDD gates and review agents. Capsule uses a test-writer→reviewer→executor pipeline with writer/reviewer pairs. Both are valid state machines, and the core engine treats them identically — as states, events, transitions, and guards.

If the core knew about "cook" or "sous-chef," every new project would need to either fit the Line Cook mold or fork the engine. The two-layer architecture means new projects only need to write a `config.yaml` and a context assembler hook.

---

## 3. Anti-Patterns Avoided

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

---

## 4. Storage Architecture Rationale

### Why JSONL + SQLite

| Alternative | Why not |
|---|---|
| DuckDB | Analytical engine optimized for columnar scans, wrong workload for point queries on individual issues |
| Native JSON per-file (one file per issue) | Great diffs, terrible query performance at scale; hundreds of files in a directory |
| Redis / embedded KV | Wrong paradigm — no git compatibility, requires running server |
| Vector DB | Wrong tool — structured queries on typed fields, not similarity search |
| JSONL-only (no SQLite) | Proven as sync format but poor as query engine; every query requires full file scan |
| SQLite-only (no JSONL) | Great queries but binary file produces unusable diffs in git |

The JSONL + SQLite hybrid is the proven architecture that beads already uses. It is not a new invention — it is a well-understood pattern applied to a new domain.

---

## 5. Example Workflows

### 5.1 Line Cook Task Workflow

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

### 5.2 Capsule Pipeline Workflow

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

### 5.3 Minimal 3-State Workflow

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

## 6. Typed Payload Examples

### Line Cook Payloads

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

### Capsule Payloads

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

---

## 7. Example Context Assemblers

### 7.1 Line Cook Context Assembler

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

### 7.2 Capsule Context Assembler

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

## 8. Interoperability Design

### 8.1 Checkpoint Compatibility

Capsule's checkpoint-based pause/resume pattern works naturally with crumbs:

1. Capsule saves a checkpoint after each phase completes (existing behavior)
2. The checkpoint references the issue ID and current workflow state
3. On resume, Capsule calls `cr workflow status <id>` to verify the checkpoint is consistent with crumbs state
4. If consistent: resume from checkpoint. If not: `cr next <id>` to get fresh context.

The crumbs engine does not manage checkpoints — that remains the orchestrator's responsibility. Crumbs provides the state that checkpoints reference.

### 8.2 How Projects Use Crumbs

Both Line Cook and Capsule would interact with crumbs through the same interface:

1. **Configure**: Define workflows in `.crumbs/config.yaml` with project-specific states, events, and guards
2. **Orchestrate**: The project's loop/campaign calls `cr next` to get the next action, then `cr transition` to record results
3. **Extend**: The context assembler hook injects project-specific context (tools, retry analysis, planning docs)
4. **Review**: Phase payloads carry structured data (verdicts, findings) that the project's review agents understand

The crumbs engine is the state machine; the project is the actor that drives it.

---

## 9. Migration Guide

### 9.1 From Beads

```
cr import-beads
```

One-time, non-destructive conversion:

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

### 9.2 Differences from Beads

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

### 9.3 From Crumbs v1 to v2

Additive, non-breaking migration:

1. Existing `.crumbs/` directories work unchanged
2. Add `workflows` section to `config.yaml` to enable v2 features
3. Existing PhaseRecords are preserved — WorkflowState is derived from them
4. Run `cr workflow validate` to verify config
5. Run `cr doctor --rebuild` to add SQLite indexes for new query patterns

If no `workflows` section exists in config, `cr` operates in v1 compatibility mode: phase records are accepted without workflow validation, and `cr next` / `cr transition` return errors indicating no workflow is configured.

---

## 10. State Machine Design Alignment

The workflow engine design maps to established state machine best practices. See [state-machine-bpap.md](../handoff/state-machine-bpap.md) for the full research document.

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
