Feature: Auto-analyze and respond to new issues
  As an issue reporter
  I want my issue automatically analyzed
  So that I get a fast, informed response with either a diagnosis or targeted clarifying questions

  Background:
    Given the issue-agent workflow is deployed to the repository
    And a valid CLAUDE_CODE_OAUTH_TOKEN secret is configured

  Scenario: New issue gets analysis comment
    Given no open issue exists with title "Test: broken import in loop.py"
    When I create an issue with title "Test: broken import in loop.py" and body describing a missing import
    And I wait for the issue-agent workflow to complete
    Then the issue should have a comment from the agent
    And the comment should contain a structured analysis section

  Scenario: Issue classified and labeled
    When I create an issue describing a bug
    And I wait for the issue-agent workflow to complete
    Then the issue should have the "bug" label applied
    When I create an issue describing a feature request
    And I wait for the issue-agent workflow to complete
    Then the issue should have the "enhancement" label applied

  Scenario: Unclear issue gets clarifying questions
    When I create an issue with a vague description like "something is broken"
    And I wait for the issue-agent workflow to complete
    Then the agent's comment should contain specific clarifying questions
    And the comment should not contain a proposed fix

  Scenario: Bot-created issues are skipped
    Given an issue created by a bot user
    When the issue-agent workflow evaluates the trigger
    Then the workflow should skip execution
    And no comment should be posted
