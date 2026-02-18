# Planning Context: GitHub Issue Agent

**Status:** brainstormed
**Epic:** <!-- epic-bead-id (after finalize) -->
**Created:** 2026-02-18

## Problem
GitHub issues on line-cook sit until a human triages them. An AI agent using `claude-code-action` can auto-analyze issues, propose fixes on test branches for clear bugs, and ask clarifying questions for unclear reports — reducing response time from hours to minutes.

## Approach
Use `anthropics/claude-code-action@v1` in a dual-mode GitHub Actions workflow: auto-triage on `issues: [opened]` and interactive follow-up on `issue_comment: [created]` with @mention. Start line-cook-specific, generalize later. The action auto-reads CLAUDE.md/AGENTS.md for project context.

## Key Decisions
- `claude-code-action` over raw API or custom scripts — lowest effort, highest capability
- Dual-mode triggers (auto + @mention) for both triage and follow-up
- Start with analysis + comments MVP, graduate to branch creation in full feature
- No GitHub App initially — use GITHUB_TOKEN, add App token later if CI triggering is needed
- Never auto-merge — all fixes are proposals on test branches for human verification

## Artifacts
- Brainstorm: docs/planning/brainstorm-github-issue-agent.md
- Menu plan: docs/planning/menu-plan.yaml
- Architecture: docs/planning/context-github-issue-agent/architecture.md
- Decisions: docs/planning/context-github-issue-agent/decisions.log

## Scope
<!-- Added during /scope phase -->
