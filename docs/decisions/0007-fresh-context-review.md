---
status: accepted
date: 2026-02-04
tags: [architecture, workflow]
relates-to: [0006]
superseded-by: null
---

# 0007: Fresh-context review via subagent

## Context

When the same AI session that wrote code also reviews it, the reviewer has seen every compromise, dead end, and rationale. This creates confirmation bias — the reviewer is more likely to rationalize decisions than challenge them. Human code review works partly because the reviewer lacks the author's sunk cost.

Options considered:
- **Same-session review** — no overhead but the reviewer inherits the author's context and biases
- **Manual review by user** — high quality but doesn't scale and defeats the purpose of automation
- **Fresh-context subagent** — spawns a new agent with only the diff and task description, no implementation history

## Decision

We will use Claude Code's Task tool to spawn review subagents with fresh context. The reviewer receives only the git diff, the task description, and a project conventions summary (CLAUDE.md excerpt) — not the full implementation history. This mirrors what a human reviewer sees: the changes, the intent, and the project norms.

As a fallback when the Task tool is unavailable, headless Claude CLI can be invoked directly with `git diff` piped to stdin and `--max-turns 1` to enforce single-pass review with read-only tools (Read, Glob, Grep).

## Consequences

- Positive: Eliminates confirmation bias — the reviewer has no stake in defending implementation choices
- Positive: The reviewer sees what a human reviewer would see, making its feedback more representative
- Positive: Headless CLI fallback provides a manual escape hatch when subagent spawning isn't available
- Negative: Spawning a subagent adds overhead per review cycle
- Negative: The reviewer lacks implementation intent — it may flag intentional trade-offs as issues
- Neutral: The diff-only approach means reviewers can't assess "what was considered and rejected," only "what was produced"
