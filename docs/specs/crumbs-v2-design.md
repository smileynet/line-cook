# Crumbs v2 Design Companion

> Rationale and examples for the [Crumbs v2 Specification](crumbs-v2-spec.md)

The spec defines *what*; this document explains *why*.

---

## 1. Two-Layer Architecture Rationale

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

## 2. Anti-Patterns Avoided

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

## 3. Storage Architecture Rationale

### Why JSONL + SQLite

| Alternative | Why not |
|---|---|
| DuckDB | Analytical engine optimized for columnar scans, wrong workload for point queries on individual issues |
| Native JSON per-file (one file per issue) | Great diffs, terrible query performance at scale; hundreds of files in a directory |
| Redis / embedded KV | Wrong paradigm — no git compatibility, requires running server |
| Vector DB | Wrong tool — structured queries on typed fields, not similarity search |
| JSONL-only (no SQLite) | Proven as sync format but poor as query engine; every query requires full file scan |
| SQLite-only (no JSONL) | Great queries but binary file produces unusable diffs in git |

The JSONL + SQLite hybrid is a well-understood pattern. JSONL provides git-friendly append-only storage; SQLite provides indexed sub-millisecond queries. Neither alone covers both requirements.

---

## 4. Example Workflows

### 4.1 Line Cook Task Workflow

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

### 4.2 Capsule Pipeline Workflow

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

### 4.3 Minimal 3-State Workflow

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

## 5. Typed Payload Examples

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

## 6. Example Context Assemblers

### 6.1 Line Cook Context Assembler

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

### 6.2 Capsule Context Assembler

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

## 7. Interoperability Design

### 7.1 Checkpoint Compatibility

Capsule's checkpoint-based pause/resume pattern works naturally with crumbs:

1. Capsule saves a checkpoint after each phase completes (existing behavior)
2. The checkpoint references the issue ID and current workflow state
3. On resume, Capsule calls `cr workflow status <id>` to verify the checkpoint is consistent with crumbs state
4. If consistent: resume from checkpoint. If not: `cr next <id>` to get fresh context.

The crumbs engine does not manage checkpoints — that remains the orchestrator's responsibility. Crumbs provides the state that checkpoints reference.

### 7.2 How Projects Use Crumbs

Both Line Cook and Capsule would interact with crumbs through the same interface:

1. **Configure**: Define workflows in `.crumbs/config.yaml` with project-specific states, events, and guards
2. **Orchestrate**: The project's loop/campaign calls `cr next` to get the next action, then `cr transition` to record results
3. **Extend**: The context assembler hook injects project-specific context (tools, retry analysis, planning docs)
4. **Review**: Phase payloads carry structured data (verdicts, findings) that the project's review agents understand

The crumbs engine is the state machine; the project is the actor that drives it.

---

## 8. Orchestrator vs Worker Design

### 8.1 Why the Distinction Matters

Line Cook evolved multiple ad-hoc channels for orchestrator↔worker communication because the predecessor tracker didn't have workflow commands:

- **Stdout signals**: Workers emit `KITCHEN_COMPLETE`, `SERVE_RESULT` as parseable lines. The orchestrator regex-matches stdout to detect completion.
- **File-based retry context**: Workers read/write `.line-cook/retry-context.json`. The serve agent writes it; the cook agent reads it on retry.
- **Snapshot diffs**: The orchestrator captures tracker state before/after worker invocation and diffs to detect what changed.
- **Tracker comments**: Workers write structured comments (`PHASE: cook completed`) that the orchestrator parses for status.

Each channel evolved independently to solve a real problem, but together they create a fragile, hard-to-debug protocol. A new project (Capsule) would need to learn and reimplement all of these patterns.

### 8.2 The Clean Boundary

Capsule's design (the Capsule Pipeline Workflow in Section 4.2 above) achieves the same outcomes with two commands:

- **`cr next`** → ContextBundle (everything the worker needs)
- **`cr transition`** → TransitionResult (everything the orchestrator needs to know)

This eliminates all ad-hoc channels:

| Ad-hoc channel | Replaced by |
|---|---|
| Stdout signal parsing | `cr transition` return value |
| File-based retry context | `ContextBundle.context.retry_analysis` |
| Snapshot diffs | `TransitionResult.cascade` |
| Tracker comment parsing | `PhaseRecord.payload` (typed, queryable) |

### 8.3 Why Workers Don't Drive Transitions

A tempting alternative: let workers call `cr transition` directly when they finish. This fails for several reasons:

1. **Retry logic is policy, not execution.** Whether to retry or escalate depends on attempt counts, guard expressions, and max_attempts config. Workers shouldn't embed this logic.
2. **Cascade evaluation requires hierarchy context.** When a task closes, the engine checks whether the parent feature should transition. Workers don't have (and shouldn't need) this context.
3. **Crash recovery.** If the worker crashes after doing work but before calling `cr transition`, the orchestrator can detect the stale `cr phase start` and retry. If the worker owned the transition, a crash would leave the workflow in an inconsistent state.
4. **Observability.** The orchestrator can log, meter, and circuit-break transitions centrally. Distributed transition calls are harder to monitor.

### 8.4 Why Planning Doesn't Need Its Own Interface

Line Cook has an explicit planning workflow (brainstorm → scope → finalize) orchestrated by `/line:mise`. Planning agents:
- Create issues in bulk via `cr create`
- Link planning context via `cr update --planning-context=<path>`
- Link test/feature specs via `cr update --test-spec=<path>`
- Validate completeness via `cr audit`

These are all admin commands (Section 6.1 of the spec). Planning agents act like humans creating and organizing work — they don't need orchestrator or worker interfaces. The `cr create` + `cr update` + `cr audit` surface is sufficient.

### 8.5 Parking Epics and Filtering

Line Cook creates "parking" epics (Backlog, Retrospective) for non-actionable work:
- `[DEFER]` findings → filed under Backlog epic (P4)
- `[RETRO]` findings → filed under Retrospective epic (P4)
- `[FIX]` findings → filed as siblings under parent feature (actionable)

Without config-driven filtering, every orchestrator must reimplement the same exclusion logic. Line Cook has `EXCLUDED_EPIC_TITLES` (hardcoded frozenset) and `BACKLOG_PRIORITY_THRESHOLD >= 4` in application code. Capsule would need its own equivalent.

The `parking` config (Section 3.1 of the spec) moves this into the tracker:
- `cr ready` and `cr next` exclude parking items by default
- `cr list` is unfiltered (admin command, shows everything)
- `cr ready --all` bypasses the filter when needed
- Orchestrators call `cr next` without filtering logic — the tracker handles it

### 8.6 Isolation Models

Two proven models for agent isolation during concurrent work:

**Epic branches (Line Cook):** Single working directory, branch switching per epic. Simple but limits concurrency — only one epic can be active at a time in a given checkout.

**Git worktrees (Gas Town):** Each worker gets its own worktree with an isolated filesystem. All worktrees share a single `.crumbs/` database via redirect files (Section 5.5 of the spec). Workers operate concurrently on different tasks without branch conflicts.

The crumbs spec supports both models. Epic branches work without any special configuration — `.crumbs/` lives in the repo root and is shared across branches. Worktrees use `.crumbs/redirect` to point at the canonical database, so `cr` commands resolve transparently.

| Aspect | Epic branches | Worktrees |
|---|---|---|
| Concurrency | One active at a time | Multiple concurrent |
| File isolation | None (shared working dir) | Full (separate filesystem) |
| Setup complexity | Low (just git branch) | Medium (worktree + redirect) |
| Crumbs integration | Automatic | Via `.crumbs/redirect` |
| Used by | Line Cook | Gas Town (beads equivalent) |

---

## 9. State Machine Design Alignment

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
