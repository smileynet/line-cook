Feature: Propose fixes on test branches
  As an issue reporter
  I want the agent to propose a concrete fix on a test branch
  So that I can verify it works before it gets merged

  Background:
    Given the issue-agent workflow is deployed with git write permissions
    And a valid CLAUDE_CODE_OAUTH_TOKEN secret is configured

  Scenario: Clear bug gets fix branch
    When I create an issue describing a clear, reproducible bug
    And I wait for the issue-agent workflow to complete
    Then a branch named "fix/issue-{number}" should exist
    And the branch should contain commits referencing the issue number

  Scenario: Fix comment includes checkout instructions
    Given an issue where the agent created a fix branch
    Then the agent's comment should contain the branch name
    And the comment should contain a git checkout command
    And the comment should contain instructions for testing the fix
    And the comment should request user verification

  Scenario: Ambiguous issue gets questions not fix
    When I create an issue with an ambiguous description
    And I wait for the issue-agent workflow to complete
    Then no fix branch should be created
    And the agent should ask clarifying questions

  Scenario: Fix branch follows naming convention
    When the agent creates a fix branch for issue number 42
    Then the branch should be named "fix/issue-42"
    And the commit message should reference "issue #42"
