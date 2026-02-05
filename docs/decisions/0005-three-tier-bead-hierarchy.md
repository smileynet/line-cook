---
status: accepted
date: 2026-02-04
tags: [workflow, architecture]
relates-to: [0001]
superseded-by: null
---

# 0005: Three-tier bead hierarchy

## Context

Work tracking needs structure. A flat list of issues doesn't convey relationships between capability areas, deliverables, and implementation steps. The project needed a hierarchy scheme for beads that would scale without becoming unwieldy.

Options considered:
- **Flat list** — simple but loses all structural information; no way to group related work
- **Two-tier (feature → task)** — covers most cases but can't represent capability areas that span multiple features
- **Unlimited nesting** — maximum flexibility but no consistent semantics per level; hard to reason about completion
- **Strict three-tier (epic → feature → task)** — clear semantics at each level with a hard depth limit

## Decision

We will use a strict three-level hierarchy — Epic → Feature → Task — because each level maps to a distinct concern: epics represent capability areas spanning multiple sessions, features represent user-verifiable outcomes, and tasks represent implementation steps completable in one session. The "Who Test" distinguishes features from tasks: if the beneficiary is "the system" or "developers," it's a task, not a feature.

Research and parking-lot epics are an explicit exception — they may contain tasks as direct children without a feature layer, since research tasks don't have user-observable outcomes.

## Consequences

- Positive: Each tier has clear creation criteria (epic: 3+ sessions or multiple features; feature: user can test it; task: one session)
- Positive: Features map naturally to BDD acceptance tests; tasks map to TDD unit tests
- Positive: Max depth of 3 prevents over-nesting and keeps the hierarchy browsable
- Negative: Requires discipline to apply the Who Test consistently — the feature/task boundary is a judgment call
- Negative: Small cross-feature changes (a one-line fix touching three features) feel heavy when they need their own task per feature
- Neutral: Research epics bypass the feature layer, which is pragmatic but creates a structural inconsistency to learn
