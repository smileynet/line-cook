# ADR 0017: Deferred Findings Triage

**Status:** Accepted
**Date:** 2026-02-24

## Context

During loop/run, tidy files ALL findings from cook/serve as sibling beads under the parent feature. This causes two problems:

1. **Disruptive loop iterations** — ambiguous findings ("consider refactoring X") get picked up by the loop, wasting iterations on work that needs user judgment.
2. **Feature closure blocking** — `check_feature_completion()` requires ALL children closed. Any unfixed finding under a feature permanently blocks plating and epic closure.

Additionally, findings often lack sufficient context to be actionable when picked up later — descriptions use a minimal template, and `--notes`/`--design` fields are unused.

## Decision

Introduce three-destination triage with markers applied during serve and routed during tidy:

| Marker | Destination | Loop picks up? | Blocks feature? |
|--------|-------------|----------------|-----------------|
| `[FIX]` | Sibling under parent feature | Yes | Yes |
| `[DEFER]` | Child of **Backlog** epic | No (excluded) | No |
| `[RETRO]` | Child of **Retrospective** epic | No (excluded) | No |

Two existing mechanisms do the heavy lifting with no Python changes:

- `EXCLUDED_EPIC_TITLES = frozenset({"Retrospective", "Backlog"})` — loop auto-selection already ignores children of these epics.
- Filing deferred findings under Backlog (not the parent feature) means they don't block `check_feature_completion()`.

All findings get enriched descriptions (problem, location, impact, context, verification) and `--notes` with structured metadata (source_task, source_phase, serve_severity, location, original_parent).

Cook findings without serve markers default to `[DEFER]` as the safe choice.

## Consequences

### Positive

- Feature closure unblocked — `[DEFER]` items are under Backlog, not parent feature
- Loop iterations focused — only `[FIX]` items get auto-selected
- Findings are actionable — enriched descriptions + notes survive across sessions
- Users can promote — `bd update <id> --parent=<feature-id>` moves deferred items into scope
- No Python changes — existing exclusion and completion checks handle routing

### Negative

- Deferred items may accumulate in Backlog if not periodically reviewed
- Serve reviewers must apply triage markers (extra cognitive step)

### Neutral

- Cook findings default to `[DEFER]` — conservative but may need manual promotion
- Retrospective epic continues to serve the same role as before
