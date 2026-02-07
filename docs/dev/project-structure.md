# Project Structure

> **Note:** This structure is auto-generated. To update, run `tree -I '.git|__pycache__|.beads' --dirsfirst -L 3` and edit.

```
line-cook/
├── .claude/
│   └── agents/            # Project-specific agents (not shipped)
│       └── release-editor.md  # Release coordinator
├── agents/                # Claude Code subagent definitions (shipped)
│   ├── taster.md          # Test quality review (cook RED phase)
│   ├── sous-chef.md       # Code review (serve phase)
│   ├── maitre.md          # BDD test review (plate phase)
│   └── critic.md          # E2E test review (epic plate phase)
├── commands/              # Claude Code command definitions
│   ├── getting-started.md # → /line:getting-started
│   ├── mise.md            # → /line:mise (planning orchestrator)
│   ├── brainstorm.md      # → /line:brainstorm
│   ├── scope.md           # → /line:scope
│   ├── finalize.md        # → /line:finalize
│   ├── plan-audit.md      # → /line:plan-audit
│   ├── architecture-audit.md  # → /line:architecture-audit
│   ├── prep.md            # → /line:prep
│   ├── cook.md            # → /line:cook
│   ├── serve.md           # → /line:serve
│   ├── tidy.md            # → /line:tidy
│   ├── plate.md           # → /line:plate
│   └── run.md             # → /line:run
├── scripts/               # Installation and utility scripts
│   ├── install-claude-code.sh    # Install Claude Code plugin locally
│   ├── sync-commands.sh          # Sync commands across platforms
│   ├── check-platform-parity.py  # Verify command parity across platforms
│   ├── check-plugin-health.py    # Health checks for plugin files
│   ├── doctor-docs.py            # Validate documentation consistency
│   ├── menu-plan-to-beads.sh     # Convert menu plans to beads issues
│   └── validate-smoke-test.py    # Validate smoke test results
├── line-cook-opencode/    # OpenCode plugin
│   ├── package.json       # Plugin manifest
│   ├── install.sh         # Installation script
│   ├── AGENTS.md          # Agent instructions (bundled)
│   └── commands/          # OpenCode command definitions
│       ├── line-getting-started.md # → /line-getting-started
│       ├── line-prep.md   # → /line-prep
│       ├── line-cook.md   # → /line-cook
│       ├── line-serve.md  # → /line-serve
│       ├── line-tidy.md   # → /line-tidy
│       ├── line-mise.md   # → /line-mise
│       ├── line-brainstorm.md  # → /line-brainstorm
│       ├── line-scope.md       # → /line-scope
│       ├── line-finalize.md    # → /line-finalize
│       ├── line-plate.md  # → /line-plate
│       └── line-run.md    # → /line-run
├── line-cook-kiro/        # Kiro CLI prompts
│   ├── prompts/           # Kiro prompt definitions
│   │   ├── line-getting-started.md
│   │   ├── line-prep.md
│   │   ├── line-cook.md
│   │   ├── line-serve.md
│   │   ├── line-tidy.md
│   │   ├── line-mise.md
│   │   ├── line-brainstorm.md
│   │   ├── line-scope.md
│   │   ├── line-finalize.md
│   │   ├── line-plate.md
│   │   └── line-run.md
│   └── steering/          # Workflow steering docs
│       ├── beads.md
│       ├── getting-started.md
│       ├── kitchen-manager.md
│       ├── line-cook.md
│       ├── maitre.md
│       ├── session.md
│       ├── sous-chef.md
│       └── taster.md
├── tests/                 # Test files
├── docs/                  # Documentation
│   ├── decisions/         # Architecture decision records (ADRs)
│   ├── guidance/          # Workflow guidance docs
│   ├── planning/          # Planning methodology
│   ├── templates/         # Document templates
│   └── dev/               # Developer docs
├── .github/
│   └── workflows/         # CI/CD automation
│       ├── ci.yml         # Continuous integration
│       └── release.yml    # Automated releases
├── .claude-plugin/
│   └── plugin.json        # Claude Code plugin manifest
├── AGENTS.md              # Agent workflow instructions
└── README.md              # User documentation
```
