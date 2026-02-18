Feature: Reusable issue agent template
  As a developer using line-cook on another repo
  I want to install the issue agent from a template
  So that I get automated issue triage without building it from scratch

  Background:
    Given the issue agent prompt has been extracted to core/templates/

  Scenario: Template syncs to all plugin dirs
    When I run the sync script
    Then the issue agent prompt should appear in plugins/claude-code/
    And the issue agent prompt should appear in plugins/opencode/
    And the issue agent prompt should appear in plugins/kiro/

  Scenario: Fresh repo install works
    Given a fresh repository with a CLAUDE.md file
    When I copy the issue-agent workflow to .github/workflows/
    And I add a CLAUDE_CODE_OAUTH_TOKEN secret
    And I create an issue
    Then the agent should analyze the issue and respond

  Scenario: Agent adapts to target repo CLAUDE.md
    Given a repository with domain-specific CLAUDE.md instructions
    When the agent analyzes an issue in that repository
    Then the analysis should reflect the project-specific context from CLAUDE.md
