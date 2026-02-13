---
status: accepted
date: 2026-02-13
tags: [architecture, plugins]
relates-to: [0009]
superseded-by: null
---

# 0015: Shared modules vs bundled scripts for plugin scripts

## Context

Commit `0e09bfb` extracted shared `run_cmd`/`run_bd_json` helpers into a sibling module (`helpers.py`) — the first shared module in the plugin scripts directory. The project already has a self-contained bundled script (`line-loop.py`, see ADR-0009). This created two patterns for code sharing among plugin scripts without a clear guideline on when to use which.

**Options considered:**

1. **Always bundle** — every script is self-contained, no sibling imports. Simple deployment model but duplicates shared utilities across scripts.
2. **Always use modules** — all shared code lives in importable modules. Works for simple utilities but breaks down for complex multi-module packages with internal dependencies.
3. **Modules for simple utilities, bundles for complex packages** — use the right tool for the scale of the dependency.

## Decision

Plugin scripts use **sibling module imports** (`from helpers import run_cmd`) for simple shared utilities. Self-contained bundling is reserved for complex multi-module packages.

**Why sibling imports work:** Scripts are invoked as `python3 <absolute-path>`. Python adds the script's directory to `sys.path[0]` automatically, so `from helpers import ...` resolves regardless of the caller's working directory. The Claude Code marketplace plugin cache preserves directory structure, so sibling relationships survive installation.

**When to bundle instead:** When a script has complex internal dependencies (5+ modules, package structure with `__init__.py`, circular references) or needs to work outside the plugin directory context. The line-loop package (`core/line_loop/`) is the canonical example — it has its own config, models, parsing, iteration, and loop modules that are bundled into a single `line-loop.py` for distribution.

**Guideline:**

| Sharing pattern | When to use | Example |
|---|---|---|
| Sibling module import | Simple shared utilities, few functions | `helpers.py` → `from helpers import run_cmd` |
| Self-contained bundle | Complex multi-module package, 5+ internal modules | `line-loop.py` bundled from `core/line_loop/` |

## Consequences

**Positive:**
- Shared utilities like `run_cmd` and `run_bd_json` are defined once, reducing duplication across scripts
- Sibling imports require zero configuration — Python's default `sys.path` behavior handles resolution
- Clear escalation path: start with modules, bundle when complexity demands it

**Negative:**
- Scripts are no longer individually self-contained — moving a script without its dependencies breaks imports
- Contributors must understand two code-sharing patterns and when each applies
- Sibling imports create an implicit contract between files in the same directory
