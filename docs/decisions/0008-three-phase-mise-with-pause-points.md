---
status: accepted
date: 2026-02-04
tags: [commands, workflow]
relates-to: ["0002"]
superseded-by: null
---

# 0008: Three-phase mise with cognitive mode separation

## Context

The original `/mise` command was monolithic — brainstorm ideas, structure them into a work breakdown, and create beads all in one pass. This led to premature commitment: once ideas were flowing, the natural tendency was to lock them into structure before fully exploring the problem space. Mixing divergent thinking (generating options) with convergent thinking (choosing and structuring) in a single pass meant neither mode got full attention.

Options considered:
- **Monolithic mise** — one command does brainstorm, structure, and bead creation in sequence; simple but conflates cognitive modes
- **Two phases (plan + create)** — separates thinking from execution but still mixes divergent and convergent planning
- **Three phases with pause points** — brainstorm (divergent), scope (convergent), finalize (execution prep); each produces a reviewable artifact

## Decision

We will split mise into three commands with explicit pause points: `/brainstorm` (divergent thinking → `brainstorm.md`), `/scope` (convergent thinking → `menu-plan.yaml`), and `/finalize` (execution prep → beads + test specs). Each phase produces a reviewable artifact before the next phase begins. `/mise` orchestrates all three but pauses between them.

A `skip-brainstorm` option is available when requirements are already clear (e.g., a well-defined bug fix), allowing direct entry at the scope phase.

## Consequences

- Positive: Prevents premature commitment — brainstorm can explore freely without structural pressure
- Positive: Each phase produces a reviewable artifact (markdown, YAML, beads) that can be inspected before proceeding
- Positive: Cognitive mode separation — divergent thinking isn't interrupted by convergent structuring
- Negative: Three commands instead of one; the full mise flow takes longer than a single-pass approach
- Negative: Pause points can feel ceremonial for small, well-understood tasks
- Neutral: `skip-brainstorm` provides an escape valve for cases where the three-phase flow is overkill
