# Architecture: GitHub Issue Agent

> Technical patterns, constraints, and conventions discovered during planning.
> Loaded by `/cook` for design context (~800 tokens target).

## Layers
- **GitHub Actions workflow** (`.github/workflows/issue-agent.yml`) — event triggers, permissions, job definition
- **Claude Code Action** (`anthropics/claude-code-action@v1`) — AI analysis engine, tool access, context loading
- **Agent prompt** — instructions for issue analysis, fix proposal, clarifying questions
- **Git/GitHub CLI** — branch creation, issue commenting, labeling

## Patterns
- Follow ADR-0013 hardening: explicit permissions, timeout, concurrency, path filters (N/A for issue triggers)
- Agent prompt should follow the existing review agent pattern (ADR-0006): structured analysis with clear verdicts
- Use `--allowedTools` to scope Claude's capabilities: read-only file access + `gh issue comment` + `git` for branches
- Use `--max-turns` to cap API cost per invocation
- Guard auto-triage with `if:` conditions to skip bot-created issues and prevent loops

## Constraints
- `GITHUB_TOKEN` commits don't trigger downstream workflows — fix branches won't run CI unless we add a GitHub App token
- Must store `ANTHROPIC_API_KEY` as a repository secret
- Issue body may contain adversarial content — rely on Claude Code's built-in injection resistance + CLAUDE.md override
- GitHub-hosted runners have 7GB RAM, 2-core CPU — sufficient for Claude CLI but set timeout to prevent runaway

## Conventions
- Workflow file naming: `issue-agent.yml` (matches existing `validate.yml`, `ci.yml`, `release.yml` pattern)
- Branch naming for fixes: `fix/issue-{number}` (standard convention)
- Comment format: structured markdown with analysis summary, proposed fix (if any), and next steps
