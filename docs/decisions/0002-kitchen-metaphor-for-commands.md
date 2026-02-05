---
status: accepted
date: 2026-01-18
tags: [commands, naming]
relates-to: []
superseded-by: null
---

# 0002: Kitchen metaphor for workflow commands

## Context

Line Cook needs command names that are memorable and won't collide with other tools. Generic names like `/plan`, `/build`, `/test` conflict with common CLI tools and other plugins. The commands represent a structured workflow (planning, execution, review, commit) that needs a coherent naming scheme.

Options considered:
- **Generic names** (`/plan`, `/build`, `/review`) — collision-prone, hard to distinguish from other tools
- **Numbered phases** (`/phase1`, `/phase2`) — meaningless, hard to remember
- **Kitchen metaphor** (`/mise`, `/cook`, `/serve`, `/tidy`) — distinct, memorable, coherent theme

## Decision

We will use restaurant/kitchen terminology for workflow commands because it provides a coherent metaphor that maps naturally to the development workflow (prep ingredients, cook the dish, serve for review, tidy the station). The themed names are distinctive enough to avoid collision with other tools while remaining intuitive once learned. Direct terms are always included alongside themed terms in documentation.

## Consequences

- Positive: Commands are instantly recognizable as Line Cook commands
- Positive: No collision with generic tool names across the ecosystem
- Positive: The metaphor maps naturally (mise en place = preparation, cook = execute, serve = review)
- Negative: Initial learning curve for new users unfamiliar with kitchen terms
- Negative: "Mise en place" is less obvious than "prep" to non-culinary audiences
- Neutral: Documentation includes both themed and direct terms to bridge the gap
