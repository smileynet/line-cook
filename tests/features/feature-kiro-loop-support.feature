Feature: Run autonomous loop with Kiro CLI
  As a Line Cook user running Kiro CLI
  I want to use @line-loop start
  So that I get the same autonomous batch execution that Claude Code users have

  Background:
    Given the line_loop package is available
    And CLI profiles are configured for both "claude" and "kiro"

  Scenario: Loop starts with kiro-cli
    Given a loop configured with --cli kiro
    When the loop builds a phase command for "cook"
    Then the command should start with "kiro-cli" "chat"
    And the command should include "--no-interactive"
    And the command should include "--trust-all-tools"
    And the command should include "--agent" "line-cook"
    And the prompt should be "@line-cook" format

  Scenario: All phases execute via Kiro
    Given a loop configured with --cli kiro
    When the loop runs an iteration
    Then run_phase is called for "cook" with the kiro CLI profile
    And run_phase is called for "serve" with the kiro CLI profile
    And run_phase is called for "tidy" with the kiro CLI profile
    And run_phase is called for "plate" with the kiro CLI profile if feature complete
    And run_phase is called for "close-service" with the kiro CLI profile if epic complete

  Scenario: Signal detection works from Kiro output
    Given a Kiro CLI subprocess producing output
    When the output contains "KITCHEN_COMPLETE"
    Then the signal should be detected
    When the output contains "SERVE_RESULT"
    Then the signal should be detected
    When the output contains "KITCHEN_IDLE"
    Then the signal should be detected
    And ANSI escape codes in output should not interfere with signal detection

  Scenario: Tool action tracking from Kiro plain text
    Given a Kiro CLI subprocess producing output
    When a line contains "(using tool: read)"
    Then a pending action should be created for tool "read"
    When a subsequent line contains a checkmark result
    Then the action should be marked as completed successfully
    When a line contains "(using tool: shell)"
    And a subsequent line contains a cross result
    Then the action should be marked as failed

  Scenario: Claude loop backward compatible
    Given a loop configured with default CLI (no --cli flag)
    When the loop builds a phase command for "cook"
    Then the command should start with "claude"
    And the command should include "--dangerously-skip-permissions"
    And the command should include "--output-format" "stream-json"
    And the prompt should be "/line:cook" format
    And existing streaming JSON parsing should work unchanged
