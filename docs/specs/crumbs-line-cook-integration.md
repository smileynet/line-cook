# Crumbs: Line Cook Integration

> Migration path from beads to crumbs, code changes, and performance gains

See [crumbs-spec.md](crumbs-spec.md) for the standalone crumbs specification.

## 1. Migration Overview

### Strategy

Beads → crumbs migration is **incremental and non-destructive**:

1. `cr import-beads` reads `.beads/issues.jsonl` and converts to `.crumbs/issues.jsonl`
2. Existing `bd comments` with `PHASE:` markers are parsed into PhaseRecords where possible
3. `.line-cook/retry-context.json` content becomes the latest ServePayload for the active task
4. Both `.beads/` and `.crumbs/` coexist during the transition period
5. Line Cook code migrates incrementally: dual-read period (check `.crumbs/` first, fall back to `.beads/`), then crumbs-only

### Migration Command

`cr import-beads` performs a one-time conversion:

- Reads all events from `.beads/issues.jsonl`
- Maps beads fields to crumbs Issue fields (id, title, description, issue_type, parent, priority, status, close_reason)
- Computes `epic_ancestor` and `depth` for each issue from the parent chain
- Parses `bd comments` for `PHASE: COOK`, `PHASE: SERVE`, `PHASE: TIDY` markers and creates PhaseRecords
- Reads `.line-cook/retry-context.json` if present and creates a ServePayload for the active task
- Extracts dependency records from `.beads/issues.jsonl` (beads stores blocking relationships inline in issue events) and writes them to `.crumbs/deps.jsonl`
- Sets `created_at` and `updated_at` from the original beads event timestamps (not the import time)
- Writes everything to `.crumbs/issues.jsonl`, `.crumbs/phases.jsonl`, `.crumbs/deps.jsonl`
- Does **not** modify or remove `.beads/`

**Fields left empty during import** (populated going forward by `cr create`):
- `acceptance_criteria`, `deliverables`, `user_story` — these are currently embedded as unstructured text in `description`; the importer does not attempt to parse them out. They remain empty for legacy issues and are populated for new issues created via `cr create`.
- Artifact link fields (`test_spec`, `feature_spec`, `acceptance_doc`, `planning_context`, `epic_branch`) — not stored in beads; left null. Can be backfilled manually via `cr update` if needed.

**Beads fields intentionally dropped** (not present in crumbs Issue model):
- `owner`, `created_by` — crumbs does not track authorship (single-user workflow)
- `closed_at` — crumbs uses `updated_at` timestamp on the close event instead of a separate field

---

## 2. Code Changes by File

### 2.1 `core/line_loop/models.py`

**Current state**: `BeadInfo` (lines 252-264) has 6 fields. `BeadSnapshot` (lines 268-311) stores lists by status with `get_by_id()` linear scan.

**Changes**:

- `BeadInfo` → `CrumbIssue`: Add `epic_ancestor`, `depth`, `deliverables`, `acceptance_criteria`, artifact link fields matching the crumbs Issue spec
- `BeadSnapshot` → `CrumbSnapshot`: Replace flat lists with indexed lookups
  - `parent_map: dict[str, str]` — child_id → parent_id
  - `epic_map: dict[str, str]` — issue_id → epic_ancestor_id
  - `children_map: dict[str, list[str]]` — parent_id → [child_ids]
  - `progress_map: dict[str, tuple[int,int]]` — parent_id → (closed_count, total_count)
  - One bulk `cr list --all --json` populates everything (replaces current 3 separate `bd` queries at lines 455, 471, 487)
  - `get_by_id()` becomes O(1) dict lookup instead of O(n) list scan
- Add `PhaseRecord` dataclass matching the crumbs spec
- Add `CrumbStore` class for reading/writing `.crumbs/phases.jsonl`
- `ServeResult` (lines 336-341) and `ServeFeedbackIssue` (lines 345-350) remain as internal models but map to/from `ServePayload` and `ReviewIssue`
- `BeadDelta.compute()` (lines 319-332) — logic unchanged but operates on `CrumbSnapshot`

### 2.2 `core/line_loop/iteration.py`

**Hierarchy walks eliminated** (currently lines 288-413):

| Function                              | Current (beads)                                   | After (crumbs)                                         |
|---------------------------------------|---------------------------------------------------|--------------------------------------------------------|
| `build_hierarchy_chain()` (line 288) | Walk parent chain, 0-3 `bd show` fallback calls  | Lookup `snapshot.parent_map` chain — 0 subprocess calls |
| `find_epic_ancestor()` (line 315)    | Walk parent chain, 0-3 `bd show` fallback calls  | Lookup `issue.epic_ancestor` — 0 subprocess calls      |
| `is_descendant_of_epic()` (line 367) | Walk parent chain, 0-3 `bd show` fallback calls  | Compare `issue.epic_ancestor == epic_id` — 0 subprocess calls |

**Completion checks eliminated** (currently lines 776-824):

| Function                                          | Current (beads)                                       | After (crumbs)                                         |
|---------------------------------------------------|-------------------------------------------------------|--------------------------------------------------------|
| `check_feature_completion()` (line 776)          | `get_task_info` × 2 + `get_children` = 3 subprocess calls | Read `snapshot.progress_map[parent_id]` — 0 subprocess calls |
| `check_epic_completion_after_feature()` (line 801) | `get_task_info` × 2 + `get_children` = 3 subprocess calls | Same pattern — 0 subprocess calls                      |

**Bead state queries replaced** (currently lines 434-553):

| Function                       | Current (beads)                                       | After (crumbs)                                         |
|--------------------------------|-------------------------------------------------------|--------------------------------------------------------|
| `get_bead_snapshot()` (line 434) | 3 separate `bd` queries (ready, in_progress, closed) | 1 bulk `cr list --all --json` populates CrumbSnapshot with indexes |
| `get_task_info()` (line 505)   | `bd show <id> --json` per call                       | Lookup in snapshot (already loaded)                    |
| `get_children()` (line 536)    | `bd list --parent=<id> --all --json` per call        | Lookup `snapshot.children_map[parent_id]`              |

**Retry context replaced** (currently lines 997-1046):

| Function                           | Current (beads)                                       | After (crumbs)                                         |
|------------------------------------|-------------------------------------------------------|--------------------------------------------------------|
| `write_retry_context()` (line 997) | Write `.line-cook/retry-context.json` filesystem file | `CrumbStore.append(PhaseRecord(phase="serve", payload=ServePayload(...)))` |
| `clear_retry_context()` (line 1038) | Delete `.line-cook/retry-context.json`               | No-op — crumbs is append-only; loop reads latest by issue_id |

**Task detection improved**:

| Function                          | Current (beads)                                | After (crumbs)                                         |
|-----------------------------------|------------------------------------------------|--------------------------------------------------------|
| `detect_worked_task()` (line 221) | Infer from snapshot diff (before vs after)     | Still works the same way, but the PhaseRecord's `issue_id` from the latest CookPayload provides a definitive answer when available |

### 2.3 `core/line_loop/loop.py`

**Subprocess calls updated**:

- `bd ready --json` (line 240) → `cr ready --json`
- Epic mode: client-side `is_descendant_of_epic()` filtering of ready tasks → `cr ready --epic=<id> --json` (server-side filter, single call)
- `bd sync` (line 623) → `cr sync`
- `get_next_ready_task()` — simplifies because epic filtering is now server-side

**No architectural changes**: Loop structure (prep→cook→serve→tidy→plate), circuit breaker, skip list, exponential backoff — all unchanged (per ADR 0009).

### 2.4 Helper Scripts

**`plugins/claude-code/scripts/preflight.py`**
- Replace `bd` existence/health checks with `cr` equivalents
- `cr doctor` replaces `bd doctor`

**`plugins/claude-code/scripts/state-snapshot.py`**
- `cr show --json` returns hierarchy + progress natively (IssueView includes `children_total`, `progress_pct`, `close_eligible`)
- Eliminates manual hierarchy walks to build display context

**`plugins/claude-code/scripts/kitchen-equipment.py`**
- `cr phase last-verdict <id>` replaces:
  - Comment parsing (`bd comments list <id>` + regex for `PHASE: SERVE`)
  - `.line-cook/retry-context.json` file reading
- Single structured query instead of two unstructured sources

**`plugins/claude-code/scripts/diff-collector.py`**
- `cr show <id> --json` for issue context (same pattern, new CLI command)

**`plugins/claude-code/scripts/plan-validator.py`**
- Many validation checks move to `cr audit`:
  - Hierarchy depth enforcement
  - Orphan issue detection
  - Dependency cycle detection
  - Content completeness (acceptance criteria, deliverables)
- Script becomes a thin wrapper calling `cr audit` + any project-specific checks not in crumbs

**`plugins/claude-code/scripts/metrics-collector.py`**
- No changes — does not interact with issue tracking

### 2.5 `plugins/claude-code/scripts/menu-plan-to-beads.sh`

**Renamed to `menu-plan-to-crumbs.sh`**. Key changes:

- `bd create` → `cr create` with new structured fields:
  - `--user-story="As a..."` (features)
  - `--acceptance-criteria="AC1" --acceptance-criteria="AC2"` (features)
  - `--deliverables="D1" --deliverables="D2"` (tasks)
  - `--test-spec=tests/specs/<slug>.md` (tasks with TDD)
  - `--feature-spec=tests/features/<slug>.feature` (features with BDD)
- `bd dep add` → `cr dep add` (same semantics)
- `bd sync` → `cr sync`
- Artifact paths set at creation time instead of being inferred later by templates

### 2.6 Templates

All 16 command templates under `core/templates/commands/*.md.template` plus 3 agent templates under `core/templates/agents/*.md.template` need `bd` → `cr` command updates. The 14 distinct `bd` subcommands map to `cr` equivalents:

| beads command            | crumbs equivalent                      | Templates using it                                                          |
|--------------------------|----------------------------------------|-----------------------------------------------------------------------------|
| `bd ready`               | `cr ready`                             | help, cook, prep, finalize, getting-started, loop                           |
| `bd list`                | `cr list`                              | help, cook, prep, tidy, finalize, getting-started, plan-audit, plate, loop, serve |
| `bd show`                | `cr show`                              | run, cook, prep, tidy, finalize, plan-audit, serve, plate, loop; agents: critic, maitre, sous-chef |
| `bd blocked`             | `cr blocked`                           | help, loop, finalize, getting-started                                       |
| `bd create`              | `cr create`                            | cook, tidy, finalize, getting-started, prep, loop                           |
| `bd update`              | `cr update`                            | run, cook, plan-audit, tidy, getting-started, loop                          |
| `bd comments add`        | `cr phase complete` or `cr comment add` | cook, tidy, serve, getting-started (freeform notes use `cr comment add`)   |
| `bd comments list`       | `cr phase history` or `cr comment list` | cook (replaced by `cr phase last-verdict` for rework detection)            |
| `bd close`               | `cr close`                             | cook, tidy, finalize, getting-started, plate, plan-audit                    |
| `bd sync`                | `cr sync`                              | prep, tidy, finalize, getting-started, plate                                |
| `bd dep add`             | `cr dep add`                           | finalize, getting-started                                                   |
| `bd epic close-eligible` | `cr close-eligible --type=epic`        | tidy, iteration.py                                                          |
| `bd doctor`              | `cr doctor`                            | architecture-audit, plan-audit                                              |
| `bd stats`               | `cr stats`                             | getting-started                                                             |

**Phase recording changes in templates**:

- **Cook template**: `bd comments add "PHASE: COOK..."` → `cr phase complete <id> cook --payload-file=<path>` where the payload file contains a CookPayload JSON
- **Serve template**: `bd comments add "PHASE: SERVE..."` + SERVE_RESULT text block → `cr phase complete <id> serve --payload-file=<path>` with ServePayload JSON
- **Tidy template**: `bd comments add "PHASE: TIDY..."` → `cr phase complete <id> tidy --payload-file=<path>` with TidyPayload JSON
- **Rework detection**: `cr phase last-verdict <id>` replaces comment parsing in cook retry mode

Human-readable summaries are still valuable for browsability. Templates may continue writing brief comments alongside the structured phase records.

### 2.7 Agent Templates

Three agent templates under `core/templates/agents/` also reference `bd` commands:

- **`critic.md.template`**: `bd show`, `bd list --parent` → `cr show`, `cr children`
- **`maitre.md.template`**: `bd show` → `cr show`
- **`sous-chef.md.template`**: `bd show` → `cr show`

These are straightforward command renames with no behavioral changes.

---

## 3. Performance Comparison

Subprocess call counts for key operations:

| Operation                                | Beads (current)                                    | Crumbs (proposed)                                      | Source                     |
|------------------------------------------|----------------------------------------------------|--------------------------------------------------------|----------------------------|
| Build snapshot                           | 3 `bd` calls (ready + in_progress + closed)        | 1 `cr list --all --json`                               | iteration.py:434-502       |
| Find epic ancestor for 1 task            | 1-3 `bd show` calls                                | 0 (precomputed `epic_ancestor` field)                  | iteration.py:315-364       |
| Find epic ancestor for N ready tasks     | N × 1-3 calls                                      | 0 (field on every issue)                               | iteration.py:315-364       |
| Check feature completion on task close   | 3 calls (`get_task_info` × 2 + `get_children`)    | 0 (read `close_eligible` from snapshot)                | iteration.py:776-798       |
| Check epic completion after feature      | 3 calls (`get_task_info` × 2 + `get_children`)    | 0 (same pattern)                                       | iteration.py:801-824       |
| Get last serve verdict                   | `bd comments list` + regex parse                   | 1 `cr phase last-verdict <id>` (indexed lookup)        | kitchen-equipment.py       |
| Get retry context                        | Read `.line-cook/retry-context.json`               | Same as verdict lookup (from phase records)            | iteration.py:997-1035      |
| Filter ready tasks by epic               | Walk ancestors of every ready task (N × 1-3 calls) | `cr ready --epic=<id>` (server-side filter)            | loop.py + iteration.py:367-413 |
| Build hierarchy for display              | 1-3 `bd show` per task                             | 0 (parent_map built on snapshot load)                  | iteration.py:288-312       |
| Validate issue structure                 | Multiple `bd list`/`bd show` per check             | `cr audit` (built-in, single pass)                     | plan-validator.py          |

**Estimated savings per iteration**: A typical loop iteration working on a task under an epic currently makes ~10-15 subprocess calls for hierarchy/completion checks. With crumbs, this drops to ~2-3 calls (snapshot load + sync), with everything else resolved from in-memory indexes.

---

## 4. Backward Compatibility

### What stays the same

- `.beads/` directory is not modified or removed by crumbs
- `cr import-beads` is non-destructive (reads `.beads/`, writes `.crumbs/`)
- Git workflow (branches, commits, push) — unchanged
- Template phase structure (prep → cook → serve → tidy → plate) — unchanged
- 3-tier hierarchy semantics (ADR 0005) — unchanged, now enforced natively by `cr`
- JSONL + git sync storage model — same philosophy, different directory (`.crumbs/` vs `.beads/`)
- Loop architecture (external Python package, ADR 0009) — unchanged
- Safety mechanisms: Circuit breaker (5 consecutive failures), skip list (3 failures per task), exponential backoff with jitter — all unchanged
- Signal parsing: SERVE_RESULT, COOK_INTENT, KITCHEN_COMPLETE structured output blocks — unchanged (these are session-level signals, not persisted state)

### What changes

- Session close protocol: `bd sync` → `cr sync`
- Hook system: Auto-run `cr` init on session start (currently auto-runs `bd prime`)
- CLI tool invocations throughout templates: `bd` → `cr`
- State files: `.line-cook/retry-context.json` no longer written (replaced by phase records)
- Comment-based phase tracking: Replaced by `cr phase` commands (comments become optional human-readable extras)

### Dual-read migration period

During the transition, code that reads issue data can check for `.crumbs/` first and fall back to `.beads/`:

```python
def get_snapshot(cwd: Path) -> CrumbSnapshot:
    if (cwd / ".crumbs").exists():
        return get_crumb_snapshot(cwd)  # New path
    return get_bead_snapshot(cwd)       # Legacy fallback
```

This pattern allows incremental migration: convert one function at a time, test, then move to the next.
