Feature: Interactive follow-up via @mention
  As an issue participant
  I want to @mention Claude in issue comments
  So that I can ask follow-up questions or provide additional context

  Background:
    Given the issue-agent workflow is deployed with issue_comment triggers
    And a valid CLAUDE_CODE_OAUTH_TOKEN secret is configured

  Scenario: @mention triggers response
    Given an existing issue
    When I add a comment containing "@claude can you explain this further?"
    And I wait for the issue-agent workflow to complete
    Then the agent should post a response comment
    And the response should address my question

  Scenario: Non-mention comments ignored
    Given an existing issue
    When I add a comment that does not contain "@claude"
    Then the issue-agent workflow should not trigger
    And no new agent comment should appear

  Scenario: Response uses full thread context
    Given an issue with an initial agent analysis comment
    When I add a comment "@claude what about the config.yaml file?"
    And I wait for the issue-agent workflow to complete
    Then the response should reference both the original issue and prior comments
    And the response should include analysis of config.yaml
