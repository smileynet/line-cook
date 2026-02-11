# Project Structure

Three clear zones: **plugins/** (shipped per-platform artifacts), **core/** (shared source material that generates plugins), **dev/** (tooling that operates on core → plugins).

```
line-cook/
├── plugins/                   # Shipped per-platform artifacts
│   ├── claude-code/           # Claude Code plugin
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json    # Plugin manifest (version source of truth)
│   │   ├── commands/          # Generated (from core/templates) + native
│   │   ├── agents/            # Generated (from core/templates)
│   │   └── scripts/
│   │       ├── diff-collector.py     # Collects diffs for serve review
│   │       ├── kitchen-equipment.py  # Tool/dependency checks
│   │       ├── line-loop.py          # Bundled from core/line_loop
│   │       ├── menu-plan-to-beads.sh # Converts menu plan YAML to beads
│   │       ├── metrics-collector.py  # Project metrics gathering
│   │       ├── plan-validator.py     # Validates menu plan structure
│   │       ├── preflight.py          # Pre-execution checks
│   │       └── state-snapshot.py     # Captures bead state snapshot
│   ├── opencode/              # OpenCode plugin
│   │   ├── package.json       # Plugin manifest
│   │   ├── src/               # TypeScript source
│   │   ├── dist/              # Built output
│   │   ├── commands/          # Generated (from core/templates)
│   │   ├── skills/
│   │   ├── install.sh         # User-facing installer
│   │   └── AGENTS.md
│   └── kiro/                  # Kiro plugin
│       ├── agents/            # JSON configs (platform-specific)
│       ├── prompts/           # Generated (from core/templates)
│       ├── steering/          # Generated (from core/templates/agents) + native
│       ├── skills/
│       ├── install.py         # User-facing installer
│       └── README.md
│
├── core/                      # Shared source material
│   ├── templates/
│   │   ├── commands/          # *.md.template → plugins/*/commands/
│   │   └── agents/            # *.md.template → plugins/*/agents|steering/
│   ├── line_loop/             # Python package (bundled → plugins/claude-code/scripts/)
│   └── line-loop-cli.py       # CLI wrapper source for bundling
│
├── dev/                       # Development tooling
│   ├── release.py             # Release automation
│   ├── sync-commands.sh       # Template → plugin sync
│   ├── install-claude-code.sh # Local plugin installer
│   ├── check-plugin-health.py # Version and metadata checks
│   ├── check-platform-parity.py # Cross-platform command parity
│   ├── doctor-docs.py         # Documentation validation
│   └── validate-smoke-test.py # Smoke test verification
│
├── tests/                     # Test suite
├── docs/                      # Documentation
│   ├── demos/                 # Demo project templates
│   ├── decisions/             # Architecture decision records (ADRs)
│   ├── dev/                   # Developer docs
│   └── guidance/              # Workflow guidance docs
│
├── .claude/                   # Dev-only local Claude Code config
│   └── agents/
│       └── release-editor.md  # Release coordinator (not shipped)
├── .claude-plugin/
│   └── marketplace.json       # Points to plugins/claude-code/
├── .github/
│   └── workflows/             # CI/CD automation
│       ├── ci.yml             # Continuous integration (OpenCode)
│       ├── release.yml        # Automated releases
│       └── validate.yml       # Validation checks
├── AGENTS.md                  # Dev reference (not shipped)
├── CHANGELOG.md
├── CLAUDE.md
└── README.md
```

## Data Flow

```
core/templates/commands/  ──sync──>  plugins/claude-code/commands/
                          ──sync──>  plugins/opencode/commands/
                          ──sync──>  plugins/kiro/prompts/

core/templates/agents/    ──sync──>  plugins/claude-code/agents/
                          ──sync──>  plugins/kiro/steering/

core/line_loop/           ──bundle──> plugins/claude-code/scripts/line-loop.py
```
