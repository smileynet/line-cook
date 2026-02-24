{
  "scope": "quick",
  "target_path": "/home/sam/code/line-cook",
  "validation_scripts": [
    {
      "name": "check-plugin-health.py",
      "status": "passed",
      "output": "# Plugin Health Report\n\n## Versions\n\n### Info\n  - Versions found: {'plugin.json': '0.17.1', 'package.json (version)': '0.17.1', 'package.json (opencode.version)': '0.17.1', 'install.py (Kiro)': '0.17.1', 'CHANGELOG.md': '0.17.1'}\n  - All versions match: 0.17.1\n\n## Metadata\n\n### Info\n  - Plugin metadata: name=line, author=smileynet\n  - OpenCode metadata: name=line, author=smileynet\n\n## Commands\n\n### Info\n  - Command counts: {'claude_code': 21, 'opencode': 21, 'kiro': 21}\n\n## Agents\n\n### Info\n  - Agent counts: {'claude_code': 6, 'opencode': 6, 'kiro': 6}\n\n## Summary\n\n  Errors: 0\n  Warnings: 0\n\n  All checks passed!"
    },
    {
      "name": "check-platform-parity.py",
      "status": "passed",
      "output": "# Platform Parity Report\n\n## Commands\n\n### Info\n  - Kiro uses agent-based architecture (intentionally different from command-based)\n  - Claude Code has additional command: init\n  - Claude Code has additional command: loop\n  - Claude Code has additional command: whats-new\n  - Claude Code has additional command: onboarding\n  - Claude Code has additional command: brainstorm\n  - Claude Code has additional command: finalize\n  - Claude Code has additional command: run\n  - Claude Code has additional command: plan-audit\n  - Claude Code has additional command: help\n  - Claude Code has additional command: decision\n  - Claude Code has additional command: scope\n  - Claude Code has additional command: doctor\n  - Claude Code has additional command: architecture-audit\n  - Claude Code has additional command: close-service\n  - OpenCode has additional command: init\n  - OpenCode has additional command: whats-new\n  - OpenCode has additional command: loop\n  - OpenCode has additional command: architecture-audit\n  - OpenCode has additional command: onboarding\n  - OpenCode has additional command: brainstorm\n  - OpenCode has additional command: finalize\n  - OpenCode has additional command: run\n  - OpenCode has additional command: help\n  - OpenCode has additional command: decision\n  - OpenCode has additional command: scope\n  - OpenCode has additional command: doctor\n  - OpenCode has additional command: plan-audit\n  - OpenCode has additional command: close-service\n  - Claude Code commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'doctor', 'finalize', 'getting-started', 'help', 'init', 'loop', 'mise', 'onboarding', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy', 'whats-new']\n  - OpenCode commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'doctor', 'finalize', 'getting-started', 'help', 'init', 'loop', 'mise', 'onboarding', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy', 'whats-new']\n  - Kiro stee",
      "truncated": true
    },
    {
      "name": "doctor-docs.py",
      "status": "passed",
      "output": "# Documentation Health Report\n\n## Internal Links\n\n### Info\n  - Checked 225 markdown files for internal links\n\n## Command Frontmatter\n\n### Info\n  - Command plate.md has valid frontmatter\n  - Command run.md has valid frontmatter\n  - Command brainstorm.md has valid frontmatter\n  - Command plan-audit.md has valid frontmatter\n  - Command prep.md has valid frontmatter\n  - Command cook.md has valid frontmatter\n  - Command close-service.md has valid frontmatter\n  - Command init.md has valid frontmatter\n  - Command architecture-audit.md has valid frontmatter\n  - Command finalize.md has valid frontmatter\n  - Command scope.md has valid frontmatter\n  - Command mise.md has valid frontmatter\n  - Command loop.md has valid frontmatter\n  - Command decision.md has valid frontmatter\n  - Command doctor.md has valid frontmatter\n  - Command serve.md has valid frontmatter\n  - Command onboarding.md has valid frontmatter\n  - Command getting-started.md has valid frontmatter\n  - Command tidy.md has valid frontmatter\n  - Command help.md has valid frontmatter\n  - Command whats-new.md has valid frontmatter\n\n## Agent Frontmatter\n\n### Info\n  - Agent maitre.md has valid frontmatter\n  - Agent critic.md has valid frontmatter\n  - Agent issue-agent.md has valid frontmatter\n  - Agent polisher.md has valid frontmatter\n  - Agent sous-chef.md has valid frontmatter\n  - Agent taster.md has valid frontmatter\n\n## Changelog Format\n\n### Info\n  - CHANGELOG.md has 26 version entries: ['0.17.1', '0.17.0', '0.16.1', '0.16.0', '0.15.0']\n  - CHANGELOG uses sections: {'Fixed', 'Added', 'Deprecated', 'Changed'}\n\n## Required Sections\n\n### Info\n  - README.md has expected sections\n  - AGENTS.md has expected sections\n\n## Entity Existence\n\n### Info\n  - Actual commands: ['architecture-audit', 'brainstorm', 'close-service', 'cook', 'decision', 'doctor', 'finalize', 'getting-started', 'help', 'init', 'loop', 'mise', 'onboarding', 'plan-audit', 'plate', 'prep', 'run', 'scope', 'serve', 'tidy', 'whats-new']\n  - Actual agents: ['c",
      "truncated": true
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