---
status: accepted
date: 2026-02-04
tags: [architecture, agents]
relates-to: ["0002"]
superseded-by: null
---

# 0006: Phase-specialized review agents

## Context

Code review in an AI-assisted workflow can happen at several points and with varying scope. The project needed to decide how to structure automated review — one generalist reviewer, no reviewers (trust the author), or multiple specialists.

Options considered:
- **No automated review** — fastest but relies entirely on the implementing agent's judgment
- **Single general reviewer** — simpler to maintain but tries to evaluate test quality, code correctness, and acceptance coverage in one pass
- **External CI pipeline** — standard for human teams but adds infrastructure and doesn't integrate with the conversational workflow
- **Phase-specialized agents** — dedicated reviewers at specific workflow phases, each with focused expertise

## Decision

We will use three review agents, each tied to a specific workflow phase: taster (test quality during cook's RED phase), sous-chef (code correctness during serve), and maître (BDD acceptance coverage before plate). Each agent has read-only tool access and produces a structured verdict — `APPROVED`, `NEEDS_CHANGES`, or `BLOCKED` — that gates progression to the next phase.

Read-only tooling is deliberate: reviewers examine, they don't fix. This prevents reviewers from silently papering over issues and ensures the implementing agent addresses feedback explicitly.

## Consequences

- Positive: Each agent has a focused domain — test structure, code quality, or acceptance coverage — reducing the chance of superficial review
- Positive: Read-only tools prevent reviewers from "fixing" issues themselves, preserving clear author/reviewer separation
- Positive: Verdict-based blocking creates enforceable quality gates at phase boundaries
- Negative: Three agents to maintain instead of one; changes to review criteria require updating the right agent
- Negative: Adds latency — each review is a separate subagent invocation
- Neutral: Agent names follow the kitchen metaphor (ADR 0002), reinforcing the project's naming convention
