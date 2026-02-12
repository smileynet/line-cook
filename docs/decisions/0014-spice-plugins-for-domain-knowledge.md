---
status: accepted
date: 2026-02-11
tags: [plugins, architecture, naming]
relates-to: [0002]
superseded-by: null
---

# 0014: Spice plugins for domain knowledge

## Context

Line Cook's mise workflow (brainstorm→scope→finalize) benefits from domain-specific knowledge — game design, API design, etc. This knowledge doesn't belong in the core plugin (bloats it for non-game users) but needs discoverable distribution.

Options considered:
- **Embed in line-cook repo** — bloats core, couples release cycles
- **Separate marketplace per addon** — fragmenting, users must add multiple marketplaces
- **Separate repos, referenced from line-cook marketplace** — independent repos, single discovery point

## Decision

Domain knowledge addons are called "spices" (adding flavor to the base workflow). Each spice lives in its own GitHub repo and is listed in line-cook's marketplace.json via external GitHub source reference. Users discover and install all plugins through the single line-cook marketplace.

Naming convention: `<domain>-spice` (e.g., game-spice, api-spice).

## Consequences

- Positive: Independent release cycles per spice — no version coupling with line-cook
- Positive: Single marketplace for users — one `/plugin marketplace add` for all plugins
- Positive: Kitchen metaphor extends naturally — spices add flavor
- Positive: No submodules, no file copying — GitHub source references are self-contained
- Negative: Spice repos must be public on GitHub (or users need tokens)
- Negative: marketplace.json must be updated manually when adding new spices
