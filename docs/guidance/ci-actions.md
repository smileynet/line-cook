# CI / GitHub Actions Guide

> Developer reference for maintaining GitHub Actions workflows.

## Workflow Inventory

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Validate** (`validate.yml`) | Push to main, PRs | Plugin health, platform parity, documentation quality |
| **CI** (`ci.yml`) | Push to main, PRs (opencode paths only) | TypeScript build and typecheck for the OpenCode plugin |
| **Create Release** (`release.yml`) | Push to main (plugin.json change) | Creates GitHub release with changelog and install instructions |

## Validation Scripts

These scripts run in the Validate workflow and can be run locally during development.

| Script | What it checks | Exit codes |
|--------|---------------|------------|
| `dev/check-plugin-health.py` | Version consistency across plugins, changelog currency | 0 = pass, 1 = errors |
| `dev/check-platform-parity.py` | Commands and agents are consistent across Claude Code, OpenCode, and Kiro | 0 = pass, 1 = errors |
| `dev/doctor-docs.py` | Documentation quality: broken links, missing files, stale references | 0 = pass, 1 = errors |

Run all three locally before pushing:

```bash
python dev/check-plugin-health.py && python dev/check-platform-parity.py && python dev/doctor-docs.py
```

## Required Patterns

Every workflow must include these. See [ADR 0013](../decisions/0013-github-actions-hardening.md) for rationale.

### Explicit permissions

Declare the minimum permissions needed. Most workflows only read:

```yaml
permissions:
  contents: read
```

Release workflows need write:

```yaml
permissions:
  contents: write
```

### Timeout

Prevent runaway jobs from burning Actions minutes:

```yaml
jobs:
  my-job:
    timeout-minutes: 5
```

### Concurrency control

Prevent stale runs from queuing up on rapid pushes:

```yaml
concurrency:
  group: workflow-name-${{ github.ref }}
  cancel-in-progress: true
```

For release workflows, let in-progress runs complete:

```yaml
concurrency:
  group: release
  cancel-in-progress: false
```

### Path filters on PR triggers

If the push trigger has `paths:`, the PR trigger should match:

```yaml
on:
  push:
    paths: ['plugins/**', 'dev/*.py']
  pull_request:
    paths: ['plugins/**', 'dev/*.py']  # Same paths
```

### Pinned runtime versions

Pin runtime versions to a minor release to prevent random breakage:

```yaml
- uses: oven-sh/setup-bun@v2
  with:
    bun-version: '1.2'    # Not 'latest'
```

## Anti-Patterns

### Unpinned runtime versions

`bun-version: latest` allows Bun breaking changes to break CI with no code change. Pin to a minor version.

### Missing path filters on PR triggers

If push has `paths:` but PR doesn't, every PR (including README typos) triggers the full workflow.

### Hardcoded repository URLs

Use `${{ github.repository }}` instead of `smileynet/line-cook` so forks generate correct release notes.

### Indentation-dependent sed

```yaml
# Bad: breaks silently if YAML indent changes
run: |
    cat > /tmp/file << 'EOF'
    content here
    EOF
    sed -i 's/^    //' /tmp/file
```

YAML `|` blocks strip the block's indentation level automatically. Write heredoc content at script indentation level — no `sed` post-processing needed.

## Adding a New Workflow

Checklist:

1. Add `permissions:` block with minimum required access
2. Add `timeout-minutes: 5` to every job
3. Add `concurrency:` group (use `cancel-in-progress: false` for releases)
4. If using `paths:` on push, add matching `paths:` on pull_request
5. Pin all runtime versions to minor releases (not `latest`)
6. Use `${{ github.repository }}` instead of hardcoded repo names
7. Update this guide's workflow inventory table

## Related

- [ADR 0013: GitHub Actions Hardening](../decisions/0013-github-actions-hardening.md) — rationale for these patterns
- [Changelog Guide](./changelog.md) — changelog format used by release workflow
