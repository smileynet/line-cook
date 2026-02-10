# Architecture Decisions

Decisions are recorded as lightweight ADRs (Architecture Decision Records).
Run `/decision` to create, list, or supersede decisions.

**Why ADRs?** Decisions made during planning and development get lost across sessions. ADRs capture the "why" behind significant design choices — persistent, project-level decisions that guide future context recovery.

**When to record:** When choosing between technical approaches, establishing conventions, making tradeoffs, or reversing a previous decision. Not for routine implementation choices or one-time fixes.

| # | Decision | Status | Date | Tags |
|---|----------|--------|------|------|
| [0001](0001-use-beads-for-issue-tracking.md) | Use beads for git-native issue tracking | accepted | 2026-01-15 | workflow |
| [0002](0002-kitchen-metaphor-for-commands.md) | Kitchen metaphor for workflow commands | accepted | 2026-01-18 | commands, naming |
| [0003](0003-template-synced-multi-platform-commands.md) | Template-synced multi-platform commands | accepted | 2026-01-22 | architecture, commands |
| [0004](0004-commands-vs-skills-directory-convention.md) | Commands vs skills directory convention | accepted | 2026-02-04 | commands, architecture |
| [0005](0005-three-tier-bead-hierarchy.md) | Three-tier bead hierarchy | accepted | 2026-02-04 | workflow, architecture |
| [0006](0006-phase-specialized-review-agents.md) | Phase-specialized review agents | accepted | 2026-02-04 | architecture, agents |
| [0007](0007-fresh-context-review.md) | Fresh-context review via subagent | accepted | 2026-02-04 | architecture, workflow |
| [0008](0008-three-phase-mise-with-pause-points.md) | Three-phase mise with cognitive mode separation | accepted | 2026-02-04 | commands, workflow |
| [0009](0009-autonomous-loop-as-external-package.md) | Autonomous loop as external Python package | accepted | 2026-02-04 | architecture |
| [0010](0010-epic-level-testing-strategy.md) | Epic-level testing strategy | accepted | 2026-02-05 | testing, agents, architecture |
| [0011](0011-template-synced-review-agents.md) | Template-synced review agents | accepted | 2026-02-07 | architecture, agents |
| [0012](0012-steering-delegates-to-prompts.md) | Steering delegates to prompts | accepted | 2026-02-07 | architecture, kiro, agents |
| [0013](0013-github-actions-hardening.md) | GitHub Actions hardening | accepted | 2026-02-10 | ci, security, github-actions |
