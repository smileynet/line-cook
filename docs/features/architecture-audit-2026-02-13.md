{
  "scope": "quick",
  "target_path": "/home/sam/code/line-cook",
  "validation_scripts": [
    {
      "name": "check-plugin-health.py",
      "status": "passed",
      "output": "# Plugin Health Report\n\n## Versions\n\n### Info\n  - Versions found: {'plugin.json': '0.14.0', 'package.json (version)': '0.14.0', 'package.json (opencode.version)': '0.14.0', 'install.py (Kiro)': '0.14.0', 'CHANGELOG.md': '0.14.0'}\n  - All versions match: 0.14.0\n\n## Metadata\n\n### Info\n  - Plugin metadata: name=line, author=smileynet\n  - OpenCode metadata: name=line, author=smileynet\n\n## Commands\n\n### Info\n  - Command counts: {'claude_code': 17, 'opencode': 17, 'kiro': 17}\n\n## Agents\n\n### Info\n  - Agent counts: {'claude_code': 5, 'opencode': 5, 'kiro': 6}\n\n## Summary\n\n  Errors: 0\n  Warnings: 0\n\n  All checks passed!"
    },
    {
      "name": "check-platform-parity.py",
      "status": "passed",
      "output": "# Platform Parity Report\n\n## Commands\n\n### Warnings\n  - Claude Code missing platform-specific: service\n  - OpenCode missing platform-specific: work\n\n### Info\n  - Kiro uses agent-based architecture (intentionally different from command-based)\n  - Claude Code has additional command: architecture-audit\n  - Claude Code has additional command: close-service\n  - Claude Code has additional command: help\n  - Claude Code has additional command: brainstorm\n  - Claude Code has additional command: loop\n  - Claude Code has additional command: scope\n  - Claude Code has additional command: plan-audit\n  - Claude Code has additional command: decision\n  - Claude Code has additional command: run\n  - Claude Code has additional command: finalize\n  - OpenCode has additional command: architecture-audit\n  - OpenCode has additional command: close-service\n  - OpenCode has additional command: help\n  - OpenCode has additional command: loop\n  - OpenCode has additional command: brainstorm\n  - OpenCode has additional command: scope\n  - OpenCode has additional command: plan-audit\n  - OpenCode has additional command: decision\n  - OpenCode has additional command: run\n  - OpenCode has additional command: finalize\n  - Claude Code commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'finalize', 'getting-started', 'help', 'loop', 'mise', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy']\n  - OpenCode commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'finalize', 'getting-started', 'help', 'loop', 'mise', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy']\n  - Kiro steering: ['critic', 'polisher']\n\n## Agents\n\n### Info\n  - Claude Code agents: ['critic', 'maitre', 'polisher', 'sous-chef', 'taster']\n  - OpenCode agents: ['critic', 'maitre', 'polisher', 'sous-chef', 'taster']\n  - Kiro agents: ['critic', 'line-cook', 'maitre', 'polisher', 'sous-chef', 'taster']\n\n## Summary\n\n  Errors: 0\n  Warnings: 2"
    },
    {
      "name": "doctor-docs.py",
      "status": "passed",
      "output": "# Documentation Health Report\n\n## Internal Links\n\n### Info\n  - Checked 163 markdown files for internal links\n\n## Command Frontmatter\n\n### Info\n  - Command plate.md has valid frontmatter\n  - Command run.md has valid frontmatter\n  - Command brainstorm.md has valid frontmatter\n  - Command plan-audit.md has valid frontmatter\n  - Command prep.md has valid frontmatter\n  - Command cook.md has valid frontmatter\n  - Command close-service.md has valid frontmatter\n  - Command architecture-audit.md has valid frontmatter\n  - Command finalize.md has valid frontmatter\n  - Command scope.md has valid frontmatter\n  - Command mise.md has valid frontmatter\n  - Command loop.md has valid frontmatter\n  - Command decision.md has valid frontmatter\n  - Command serve.md has valid frontmatter\n  - Command getting-started.md has valid frontmatter\n  - Command tidy.md has valid frontmatter\n  - Command help.md has valid frontmatter\n\n## Agent Frontmatter\n\n### Info\n  - Agent maitre.md has valid frontmatter\n  - Agent critic.md has valid frontmatter\n  - Agent polisher.md has valid frontmatter\n  - Agent sous-chef.md has valid frontmatter\n  - Agent taster.md has valid frontmatter\n\n## Changelog Format\n\n### Info\n  - CHANGELOG.md has 21 version entries: ['0.14.0', '0.13.2', '0.13.1', '0.13.0', '0.12.0']\n  - CHANGELOG uses sections: {'Deprecated', 'Fixed', 'Changed', 'Added'}\n\n## Required Sections\n\n### Info\n  - README.md has expected sections\n  - AGENTS.md has expected sections\n\n## Entity Existence\n\n### Info\n  - Actual commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'finalize', 'getting-started', 'help', 'loop', 'mise', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy']\n  - Actual agents: ['critic', 'maitre', 'polisher', 'sous-chef', 'taster']\n\n## Summary\n\n  Errors: 0\n  Warnings: 0\n\n  All checks passed!"
    }
  ],
  "metrics": {},
  "findings": {
    "critical": [],
    "high": [],
    "medium": [],
    "low": []
  },
  "external_tools": {
    "tools_available": {},
    "external": {}
  }
}