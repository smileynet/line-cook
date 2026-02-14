Feature: Reduced iteration overhead
  As a loop operator
  I want iterations to complete faster
  So that more work gets done per hour of autonomous execution

  Background:
    Given a BeadSnapshot with multiple beads in a hierarchy

  Scenario: BeadSnapshot get_by_id uses dict index
    Given a snapshot with 100 beads
    When I call get_by_id() for a known bead ID
    Then the lookup should use O(1) dict access
    And the result should match the linear scan result
    And the _index should be built lazily on first access

  Scenario: Ancestor cache built once per snapshot
    Given a snapshot with beads in epic/feature/task hierarchy
    When I call build_epic_ancestor_map(snapshot)
    Then every ready_work item should have a cached ancestor
    And subsequent ancestor lookups should use the cache (no subprocess calls)
    And the cache should map task IDs to their epic ancestor IDs

  Scenario: Snapshot taken once before cook once after tidy
    Given a mock run_iteration that tracks snapshot captures
    When I run a complete iteration
    Then get_bead_snapshot should be called exactly twice
    And the first call should be before the cook phase
    And the second call should be after the tidy phase

  Scenario: Subprocess calls reduced
    Given a mock iteration environment tracking subprocess calls
    When I run a complete iteration
    Then the total subprocess calls should be approximately 15
    And no redundant snapshot captures should occur
