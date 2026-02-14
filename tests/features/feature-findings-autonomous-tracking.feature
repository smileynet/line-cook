Feature: Autonomous findings tracking
  As a loop operator
  I want to see what findings were filed during each iteration
  So that I can monitor code quality trends in watch mode

  Background:
    Given a completed iteration with tidy phase output

  Scenario: IterationResult findings count set from delta
    Given a before snapshot with 5 open beads
    And an after snapshot with 5 open beads plus 2 newly filed beads
    When the iteration result is computed
    Then findings_count should be 2

  Scenario: Findings shown in human readable output
    Given an IterationResult with findings_count=3
    When I call print_human_iteration()
    Then the output should contain "Findings: 3 filed"

  Scenario: Findings serialized in status and history
    Given an IterationResult with findings_count=2
    When I call serialize_iteration_for_status()
    Then the JSON should include "findings_count": 2
    When I call serialize_full_iteration()
    Then the JSON should include "findings_count": 2

  Scenario: Zero findings handled gracefully
    Given an IterationResult with findings_count=0
    When I call print_human_iteration()
    Then the output should not contain "Findings"
    When I call serialize_iteration_for_status()
    Then the JSON should include "findings_count": 0
