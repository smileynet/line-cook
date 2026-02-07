---
status: accepted
date: 2026-02-07
tags: [architecture, kiro, agents]
relates-to: [0003, 0011]
superseded-by: null
---

# 0012: Steering files delegate to prompts, never duplicate them

## Context

The template sync system (ADRs 0003, 0011) keeps 11 commands and 5 review agents consistent across Claude Code, OpenCode, and Kiro. Kiro had several files outside this system that duplicated template-synced content:

- **kitchen-manager** (359 lines) — second orchestrator that inlined all phase logic already maintained in template-synced prompts
- **getting-started steering** (83 lines) — subset of the template-synced getting-started prompt (149 lines)
- **line-cook steering** (172 lines) — included 130+ lines of inline phase summaries duplicating template-synced prompt files

The kitchen-manager was the biggest risk: it competed with the template-synced `line-run.md` prompt for the same workflow, and its inline logic would silently diverge from the canonical templates over time.

**Options considered:**
1. Template the orchestrators too — adds complexity for files that are fundamentally platform-specific (persistent agents vs. stateless commands)
2. Keep both orchestrators — guaranteed drift between kitchen-manager and line-run prompt
3. Delete duplicates, establish delegation principle — removes drift vectors, clarifies the role boundary between steering and prompt files

## Decision

Steering files define agent personality and routing. Prompt files (template-synced) define phase logic. Steering files must never duplicate prompt content — they delegate by reading prompt files.

**Specifically:**
1. Delete kitchen-manager (agent + steering) — its role is fully covered by the template-synced line-run.md prompt
2. Delete getting-started steering — superset exists as template-synced prompt
3. Slim line-cook steering to routing table + guardrails + delegation instruction (~47 lines, down from 172)
4. Add alignment comments to genuinely Kiro-only files (beads.md, session.md) cross-referencing their CC equivalents
5. Grant line-cook agent access to prompt files via resources

## Consequences

**Positive:**
- Eliminates the largest drift vector (kitchen-manager's 359 lines of duplicated phase logic)
- line-cook steering drops from 172 to 48 lines — easier to maintain, impossible to drift
- Single orchestrator per platform (line-cook for Kiro, line:run command for CC)
- Clear principle for future Kiro-only files: personality and routing only, never phase logic

**Negative:**
- line-cook agent must read prompt files at runtime (added to resources)
- Kiro loses the kitchen-manager's "service report" output format (cosmetic, not functional)
