Feature: GitHub App identity for CI-triggering fix branches
  As a maintainer
  I want fix branches to trigger CI automatically
  So that I can see whether the proposed fix passes validation before reviewing it

  Background:
    Given a GitHub App is created with minimum required permissions
    And APP_ID and APP_PRIVATE_KEY are stored as repository secrets
    And the issue-agent workflow uses create-github-app-token

  Scenario: Fix branch triggers Validate workflow
    Given the agent creates a fix branch with a code change
    When the branch is pushed using the App token
    Then the Validate workflow should run on the fix branch
    And the workflow run should appear in the branch's status checks

  Scenario: Commits show bot identity
    Given the agent creates a fix branch using the App token
    When I inspect the commit on the fix branch
    Then the commit author should be the GitHub App bot identity
    And the author should not be "github-actions[bot]"

  Scenario: App token has minimum required permissions
    Given the GitHub App configuration
    Then the App should have "contents: write" permission
    And the App should have "issues: write" permission
    And the App should not have admin or organization-level permissions
