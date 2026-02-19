# Planning Context: GitHub Issue Agent

**Status:** finalized
**Epic:** lc-wbo (Phase 1), lc-p62 (Phase 2), lc-769 (Phase 3)
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
- Menu plan: docs/planning/menu-plan-github-issue-agent.yaml
- Architecture: docs/planning/context-github-issue-agent/architecture.md
- Decisions: docs/planning/context-github-issue-agent/decisions.log

## Scope
Phases: 3, Features: 5, Tasks: 11

- **Phase 1: Auto-Triage** (1-2 sessions)
  - Feature 1.1: Auto-analyze and respond to new issues (3 tasks)
- **Phase 2: Fix Proposals & Follow-up** (2-3 sessions)
  - Feature 2.1: Propose fixes on test branches (2 tasks)
  - Feature 2.2: Interactive follow-up via @mention (2 tasks)
- **Phase 3: Hardening & Generalization** (2-3 sessions)
  - Feature 3.1: GitHub App identity for CI-triggering fix branches (2 tasks)
  - Feature 3.2: Reusable issue agent template (2 tasks)
