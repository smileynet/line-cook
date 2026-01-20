/**
 * Beads fixture helpers for integration tests
 *
 * Provides mock data loading and expected hierarchy constants
 * for testing beads workflow scenarios.
 */
import { readFileSync } from "fs"
import { join, dirname } from "path"
import { fileURLToPath } from "url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

/**
 * Beads issue structure (simplified for testing)
 */
export interface BeadsIssue {
  id: string
  title: string
  description?: string
  status: "open" | "in_progress" | "closed"
  priority: number
  issue_type: "epic" | "feature" | "task" | "bug"
  owner?: string
  created_at: string
  created_by?: string
  updated_at: string
  closed_at?: string
  close_reason?: string
  dependencies?: {
    issue_id: string
    depends_on_id: string
    type: "parent-child" | "blocks"
    created_at: string
    created_by?: string
  }[]
}

/**
 * Load mock beads issues from fixture file
 */
export function loadMockIssues(): BeadsIssue[] {
  const fixturePath = join(__dirname, "issues.jsonl")
  const content = readFileSync(fixturePath, "utf-8")
  return content
    .trim()
    .split("\n")
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as BeadsIssue)
}

/**
 * Get JSONL content for setting up test directories
 */
export function getMockIssuesContent(): string {
  const fixturePath = join(__dirname, "issues.jsonl")
  return readFileSync(fixturePath, "utf-8")
}

/**
 * Expected hierarchy for test validation
 *
 * Structure:
 * test-epic-1 (priority 2, active)
 * ├── test-feature-1 (User can authenticate)
 * │   ├── test-task-1 (open, ready - no blockers)
 * │   ├── test-task-2 (open, blocked by task-1)
 * │   └── test-task-3 (in_progress)
 *
 * test-epic-2 (priority 4, BACKLOG - should be excluded)
 * └── test-feature-2 (User can manage profile)
 *     └── test-task-4 (should NOT appear in ready work)
 *
 * test-closed (closed task for lifecycle testing)
 */
export const EXPECTED_HIERARCHY = {
  // Active epic with priority 2
  activeEpic: {
    id: "test-epic-1",
    title: "Authentication Epic",
    priority: 2,
    childrenIds: ["test-feature-1"],
  },

  // Feature under active epic
  activeFeature: {
    id: "test-feature-1",
    title: "User can authenticate",
    parentId: "test-epic-1",
    childrenIds: ["test-task-1", "test-task-2", "test-task-3"],
  },

  // Ready task - open with no blockers
  readyTask: {
    id: "test-task-1",
    title: "Implement login form",
    status: "open",
    parentId: "test-feature-1",
    blockedBy: [],
  },

  // Blocked task - depends on test-task-1
  blockedTask: {
    id: "test-task-2",
    title: "Add password validation",
    status: "open",
    parentId: "test-feature-1",
    blockedBy: ["test-task-1"],
  },

  // In-progress task
  inProgressTask: {
    id: "test-task-3",
    title: "Implement OAuth integration",
    status: "in_progress",
    parentId: "test-feature-1",
  },

  // Backlog epic with priority 4
  backlogEpic: {
    id: "test-epic-2",
    title: "Profile Management Epic",
    priority: 4,
    childrenIds: ["test-feature-2"],
  },

  // Feature under backlog epic
  backlogFeature: {
    id: "test-feature-2",
    title: "User can manage profile",
    parentId: "test-epic-2",
    childrenIds: ["test-task-4"],
  },

  // Task under backlog - should be excluded from ready work
  backlogTask: {
    id: "test-task-4",
    title: "Add profile picture upload",
    status: "open",
    parentId: "test-feature-2",
    priority: 4,
  },

  // Closed task for lifecycle testing
  closedTask: {
    id: "test-closed",
    title: "Setup project structure",
    status: "closed",
    closeReason: "Initial project setup completed successfully",
  },
} as const

/**
 * Issue counts for validation
 */
export const ISSUE_COUNTS = {
  total: 9,
  open: 7, // 2 epics + 2 features + 3 tasks with status "open"
  inProgress: 1,
  closed: 1,
  epics: 2,
  features: 2,
  tasks: 5,
  activeWork: 4, // Tasks under active epic (priority != 4)
  backlogWork: 1, // Tasks under backlog epic (priority 4)
  readyWork: 1, // Open tasks with no blockers, not backlog
  blockedTasks: 1, // Tasks with blocking dependencies
} as const

/**
 * Get issue by ID from loaded issues
 */
export function getIssueById(issues: BeadsIssue[], id: string): BeadsIssue | undefined {
  return issues.find((issue) => issue.id === id)
}

/**
 * Get children of an issue (issues with parent-child dependency)
 */
export function getChildren(issues: BeadsIssue[], parentId: string): BeadsIssue[] {
  return issues.filter((issue) =>
    issue.dependencies?.some(
      (dep) => dep.depends_on_id === parentId && dep.type === "parent-child"
    )
  )
}

/**
 * Get blocking dependencies for an issue
 */
export function getBlockers(issues: BeadsIssue[], issueId: string): BeadsIssue[] {
  const issue = getIssueById(issues, issueId)
  if (!issue?.dependencies) return []

  const blockerIds = issue.dependencies
    .filter((dep) => dep.type === "blocks" && dep.issue_id === issueId)
    .map((dep) => dep.depends_on_id)

  return issues.filter((i) => blockerIds.includes(i.id))
}

/**
 * Check if an issue is ready (open, no blockers, not backlog)
 */
export function isReady(issues: BeadsIssue[], issueId: string): boolean {
  const issue = getIssueById(issues, issueId)
  if (!issue) return false
  if (issue.status !== "open") return false
  if (issue.priority === 4) return false
  if (getBlockers(issues, issueId).length > 0) return false
  return true
}
