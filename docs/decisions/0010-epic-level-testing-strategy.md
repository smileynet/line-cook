---
status: accepted
date: 2026-02-05
tags: [testing, agents, architecture]
relates-to: ["0005", "0006"]
superseded-by: null
---

# 0010: Epic-level testing strategy

## Context

Line Cook's testing guidance covered task-level (TDD/unit tests) and feature-level (BDD/acceptance tests) but lacked guidance for epic-level validation. When multiple features compose a complete capability, users need to verify:

1. Cross-feature integration works
2. Critical user journeys function end-to-end
3. The testing approach fits their project type

Options considered:
- **No epic-level guidance** — leave E2E testing to user discretion
- **Generic E2E guidance** — one-size-fits-all documentation
- **Project-type-specific guidance** — different approaches for web apps, CLIs, mobile, etc.
- **Project-type-specific guidance + review agent** — guidance plus automated quality gate

## Decision

We will add epic-level testing guidance with:

1. **Critic agent** — A fourth review agent that evaluates E2E test coverage when an epic completes. It validates user journeys, cross-feature integration, and smoke test existence.

2. **Project-type-specific guidance** — Documentation covering different simulation approaches (browser automation for web apps, process automation for CLIs, device automation for mobile, etc.).

3. **Epic acceptance template** — A "Full Service Report" template mirroring the feature acceptance template but focused on user journeys and cross-feature validation.

The testing pyramid now has four agents, each at a different tier:

| Agent | Tier | Focus |
|-------|------|-------|
| Taster | Task (TDD) | Test structure, isolation |
| Sous-chef | Task | Code quality, security |
| Maître | Feature (BDD) | Acceptance criteria coverage |
| Critic | Epic (E2E) | User journey validation |

## Consequences

- Positive: Complete testing pyramid guidance from unit tests to E2E
- Positive: Project-type-specific recommendations prevent misapplied patterns
- Positive: Critic agent provides automated quality gate for epic completion
- Positive: Kitchen metaphor extends naturally (critic = food critic evaluating the full dining experience)
- Negative: Fourth agent to maintain; epic plate phase becomes more complex
- Negative: Risk of over-prescribing E2E tests (addressed with antipattern guidance)
- Neutral: Epic-level tests remain optional for small projects or research work
