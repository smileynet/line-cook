# Planning Context: demo-web

**Status:** finalized
**Epic:** demo-001
**Created:** 2026-02-04

## Problem
The existing demo template (demo-simple) is a minimal TodoWebApp that only exercises 2 tasks. Users need a realistic multi-feature project to properly test line-cook's loop, plate, and epic completion capabilities.

## Approach
Build a Go + Templ + SQLite web dashboard that monitors line-cook workflows. The dashboard reads loop status files and receives hook events, providing real-time visibility into loop execution. Modeled on ~/code/observability architecture.

## Key Decisions
- Go + Templ + SQLite stack (matches observability reference app)
- Dual data sources: loop files (status.json, history.jsonl) + hook events (POST /events)
- Build from scratch via beads (not pre-built) to exercise the full cook cycle
- 9 tasks across 4 features, sequenced so each iteration produces working increments

## Artifacts
- Brainstorm: docs/planning/brainstorm-demo-web.md
- Menu plan: docs/planning/menu-plan.yaml
- Architecture: docs/planning/context-demo-web/architecture.md
- Decisions: docs/planning/context-demo-web/decisions.log

## Scope
Phases: 1, Features: 4, Tasks: 9 (+1 parking lot)

Features:
- Real-time loop status display (3 tasks)
- Iteration history timeline (2 tasks)
- Hook event receiver (2 tasks)
- Live updates via WebSocket (2 tasks)
