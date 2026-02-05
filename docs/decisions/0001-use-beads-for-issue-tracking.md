---
status: accepted
date: 2026-01-15
tags: [workflow]
relates-to: []
superseded-by: null
---

# 0001: Use beads for git-native issue tracking

## Context

AI coding assistants lose context across sessions. Work tracked only in conversation history disappears after compaction or new sessions. The project needs persistent issue tracking that survives context loss and supports multi-session work with dependencies.

Options considered:
- **GitHub Issues** — requires network, API calls, separate from repo
- **Jira / Linear** — heavyweight, external service dependency
- **Plain TODO comments** — no status tracking, no dependencies, scattered across files
- **beads (bd CLI)** — git-native JSONL, syncs with git, supports dependencies and hierarchy

## Decision

We will use beads (`bd` CLI) as the primary issue tracker because it stores issues as JSONL in the git repo itself. Issues travel with the code, sync via normal git operations, and survive AI session boundaries through git persistence. The `bd ready` command provides immediate context recovery — agents can find available work without prior session knowledge.

## Consequences

- Positive: Issues persist across sessions via git — no external service needed
- Positive: Dependencies model blocking relationships between tasks
- Positive: `bd ready` enables context recovery after compaction
- Positive: Issues live in the repo, visible to all collaborators
- Negative: Extra CLI tool to install and learn
- Negative: Requires `bd sync` discipline at session end
- Neutral: JSONL format is append-friendly but not human-browsable
