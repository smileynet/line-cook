# ADR 0016: Trunk-Based Loop Development

**Status:** Accepted
**Date:** 2026-02-24

## Context

The line loop's epic branch pattern (`epic/{id}`) has caused stranded commits in every Kiro loop run. Despite three fixes (parse bug, decoupled merge, return-to-main), the fundamental problem persists:

- Partial epics never merge during a loop run
- Branches diverge from main between sessions
- Manual squash-merges are always needed to recover stranded work

The branching pattern was designed for isolation, but the autonomous loop doesn't benefit from isolation — it creates problems instead.

## Decision

Default to trunk-based development (all work on main) for the autonomous loop and manual `/line:run`.

- **Default**: Work directly on main, no branch switching
- **Opt-in**: `--epic-branch` flag preserves the branching workflow for cases where isolation is genuinely needed
- **Pre-start warning**: Loop warns if it starts on an epic branch in trunk-based mode
- **Merge guards**: `merge_completed_epic` calls are guarded by branch checks — only merge when actually on an epic branch
- **Epic completion**: Close-service still runs for epic documentation; merge step is skipped when on main

## Consequences

### Positive

- Loop work lands directly on main — no stranded commits
- Epic completion runs close-service only (no merge needed when on main)
- Simpler mental model for operators
- Existing epic branch functions retained but not called by default

### Negative

- Work from different epics intermixes on main (no isolation)
- Users who want isolation must remember `--epic-branch`

### Neutral

- `ensure_epic_branch`, `merge_epic_on_close`, `merge_completed_epic`, `auto_commit_wip` are retained for opt-in use
- Template instructions simplified (Step 1.5 branch check, Step 5 merge blocks removed)
