---
status: accepted
date: 2026-02-07
tags: [architecture, agents]
relates-to: [0003, 0006]
superseded-by: null
---

# 0011: Template-synced review agents

## Context

Line Cook's five review agents (sous-chef, taster, maitre, polisher, critic) exist on both Claude Code and Kiro with significant content divergence. The CC versions are concise (110-160 lines); the Kiro versions are detailed supersets (350-440 lines) with additional checklists, red flags, code examples, and anti-patterns. The drift is additive, not contradictory — same core concepts and review dimensions, but Kiro adds more detail because persistent agents need self-contained instructions while CC subagents receive context via Task() prompts.

ADR 0003 established a template system for commands that prevents drift across platforms. The same drift problem applies to agents.

Options considered:
- **Keep separate** — maintain CC and Kiro agents independently; current state, guaranteed continued drift
- **Converge-then-template** — merge content into templates using the existing conditional block system; extends proven infrastructure
- **Kiro as source of truth** — derive CC versions by stripping detail from Kiro files; simpler but loses CC-specific content like YAML frontmatter and decision frameworks

## Decision

We will converge agent content and templatize using the same infrastructure as commands (ADR 0003). Agent templates live in `agents/templates/` and the sync script generates CC agents (with YAML frontmatter) and Kiro steering files (without frontmatter). Only CC and Kiro are targeted — OpenCode uses CC's agents directly.

Key differences from command templates:
- No `@NAMESPACE@` substitution (agents don't reference command namespaces)
- No OpenCode output (OC shares CC's `agents/` directory)
- Higher conditional content ratio (~60% shared vs ~90% for commands) due to Kiro's detailed checklists and examples
- Kiro JSON configs are not templatized (12 lines each, fully platform-specific metadata)

## Consequences

- Positive: Single source of truth for all five review agents across CC and Kiro
- Positive: Reuses existing sync script and pre-commit guard infrastructure
- Positive: CC agents gain minor improvements from convergence (clarified scope, normalized naming)
- Positive: Kiro gains polisher and critic agents that were previously CC-only
- Negative: More conditional blocks than command templates due to platform-specific detail levels
- Negative: Template files are longer and harder to read than either platform's output
