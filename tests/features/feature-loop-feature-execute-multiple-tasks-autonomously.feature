# lc-cnl - Feature: Execute multiple tasks autonomously
Feature: Execute multiple tasks autonomously
  As a developer using Line Cook
  I want to execute multiple ready tasks in sequence
  So that I can batch work without manual restarts

  Background:
    Given the system is in a known state

  Scenario: Start loop that processes all ready tasks
    Given the preconditions are met
    When the action is performed
    Then can start loop that processes all ready tasks

  Scenario: Loop stops when no tasks remain (bd ready empty)
    Given the preconditions are met
    When the action is performed
    Then loop stops when no tasks remain (bd ready empty)

  Scenario: Loop stops on first task failure (stop-on-failure behavior)
    Given the preconditions are met
    When the action is performed
    Then loop stops on first task failure (stop-on-failure behavior)

  Scenario: Shows task-by-task progress as each task completes
    Given the preconditions are met
    When the action is performed
    Then shows task-by-task progress as each task completes

  Scenario: Outputs final summary with completed/failed counts
    Given the preconditions are met
    When the action is performed
    Then outputs final summary with completed/failed counts

  Scenario: Respects --max-iterations limit
    Given 10 ready tasks exist
    And the loop is invoked with "--max-iterations 3"
    When the loop executes
    Then exactly 3 tasks are processed
    And the final summary shows "Iterations: 3 / 3"
    And the status shows "Iteration Limit Reached"
    And remaining ready tasks count is shown

  Scenario: Uses default iteration limit of 25
    Given no iteration limit is specified
    When the loop is invoked
    Then the maximum iterations defaults to 25

  Scenario: Supports short form -n flag
    Given the loop is invoked with "-n 5"
    When the loop executes
    Then the maximum iterations is set to 5

