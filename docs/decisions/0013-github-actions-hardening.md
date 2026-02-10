---
status: accepted
date: 2026-02-10
tags: [ci, security, github-actions]
relates-to: []
superseded-by: null
---

# 0013: GitHub Actions hardening

## Context

The Validate workflow failed on 4 consecutive pushes due to a broken relative link in a template. While investigating, an audit of all 3 workflows found brittleness: missing timeouts, no concurrency control, unpinned runtime versions, hardcoded repository URLs, and indentation-dependent `sed` processing.

Line Cook is a single-maintainer plugin project with no server infrastructure, no sensitive secrets beyond GITHUB_TOKEN, and CI jobs that complete in under 15 seconds. Hardening was scoped to what protects plugin quality and prevents wasted Actions minutes — not enterprise-grade supply-chain security.

**Options considered:**

1. Full supply-chain hardening (SHA-pinned actions, OIDC, matrix strategies, caching) — over-engineered for a plugin project with seconds-long jobs
2. Fix only the broken link — misses the systemic brittleness patterns
3. Targeted hardening of all 3 workflows with documented patterns — proportionate to risk

## Decision

All workflows must include:

- **Explicit permissions** — least-privilege (`contents: read` by default, `write` only for releases)
- **`timeout-minutes`** — prevents runaway jobs from burning Actions minutes
- **Concurrency groups** — cancels stale runs on rapid pushes (except releases, which must complete)
- **Path filters on PR triggers** — matches push `paths:` filters so unrelated PRs don't trigger validation
- **Pinned runtime versions** — pin to minor version (e.g., `bun-version: '1.2'`), not `latest`
- **`${{ github.repository }}`** — instead of hardcoded repo URLs, so fork releases work correctly

Not required (out of scope for this project):

- SHA-pinning official GitHub actions (`actions/checkout@v4`) — trusted, widely used, adds Dependabot maintenance burden
- SHA-pinning `oven-sh/setup-bun@v2` — no secrets exposure, maintenance cost exceeds risk
- Matrix strategies — single platform, single runtime
- Caching — jobs finish in seconds
- OIDC/secrets rotation — no cloud infrastructure

Patterns are documented in [CI/Actions guidance](../guidance/ci-actions.md).

## Consequences

**Positive:**
- Runaway jobs can't burn Actions minutes indefinitely (timeout)
- Rapid pushes cancel stale validation runs instead of queuing (concurrency)
- Bun version updates are intentional, not surprise breakage (pinned version)
- Fork releases point to correct repository (dynamic URL)
- Token permissions follow least-privilege principle (explicit permissions)
- PR path filters prevent unnecessary CI runs

**Negative:**
- Slightly more verbose workflow YAML
- Bun version requires manual update when upgrading (intentional friction)
