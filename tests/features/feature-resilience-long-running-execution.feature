Feature: Resilient long-running execution
  As a loop operator
  I want long-running loops to stay in sync with remote state and detect stuck phases
  So that multi-hour loops run reliably

  Background:
    Given a loop configuration with default settings

  Scenario: Periodic sync fires every N iterations
    Given PERIODIC_SYNC_INTERVAL is set to 5
    When the loop completes iteration 5
    Then bd sync should be called
    When the loop completes iteration 6
    Then bd sync should not be called
    When the loop completes iteration 10
    Then bd sync should be called

  Scenario: Phase specific idle timeouts applied
    Given the DEFAULT_PHASE_IDLE_TIMEOUTS configuration
    When I start the cook phase without an explicit idle timeout
    Then the idle timeout should be 180 seconds
    When I start the serve phase without an explicit idle timeout
    Then the idle timeout should be 300 seconds
    When I start the tidy phase without an explicit idle timeout
    Then the idle timeout should be 90 seconds

  Scenario: Tuned timeouts applied to serve plate close-service
    Given the DEFAULT_PHASE_TIMEOUTS configuration
    Then the serve timeout should be 450 seconds
    And the plate timeout should be 450 seconds
    And the close-service timeout should be 750 seconds

  Scenario: Explicit idle timeout overrides per-phase default
    Given a phase with default idle timeout of 180 seconds
    When I start the phase with an explicit idle timeout of 60 seconds
    Then the idle timeout should be 60 seconds
    And the default should not be used
