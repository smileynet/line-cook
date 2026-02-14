Feature: Correct loop failure handling
  As a loop operator
  I want the circuit breaker and task detection to work correctly
  So that the loop stops when it should and attributes work to the right task

  Background:
    Given a CircuitBreaker with window_size=10 and failure_threshold=5
    And a set of beads in the snapshot

  Scenario: Circuit breaker trips on threshold failures in full window
    Given the circuit breaker window contains [F,F,F,F,F,S,F,F,F,F]
    When I check if the circuit breaker is open
    Then the breaker should be open
    Because 9 out of 10 entries are failures (exceeds threshold of 5)

  Scenario: Detect worked task prefers target over heuristic
    Given a before snapshot with tasks "lc-a" and "lc-b.1.2" both open
    And an after snapshot where both tasks have changed status
    And the target_task_id is "lc-a"
    When I call detect_worked_task with target_task_id="lc-a"
    Then the result should be "lc-a"
    Because target_task_id takes priority over dot-count heuristic

  Scenario: Mixed failure patterns evaluated correctly
    Given the following failure patterns and expected results:
      | pattern                        | expected |
      | [F,F,F,F,F,S,S,S,S,S]         | open     |
      | [S,S,S,S,S,F,F,F,F,F]         | open     |
      | [F,S,F,S,F,S,F,S,F,S]         | open     |
      | [F,F,F,F,S,S,S,S,S,S]         | closed   |
      | [S,S,S,S,S,S,S,S,S,S]         | closed   |
    When I evaluate each pattern
    Then the circuit breaker state should match the expected result

  Scenario: Existing behavior preserved for normal cases
    Given the existing TestCircuitBreaker test suite
    And the existing TestDetectWorkedTask test suite
    When I run all existing tests
    Then all tests should pass without modification
