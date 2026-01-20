/**
 * Integration tests for Beads workflow scenarios
 *
 * Tests the LineCookPlugin's beads-related functionality:
 * - Beads project detection
 * - Session lifecycle events
 * - Compaction context injection
 * - File edit tracking
 * - Hierarchy navigation
 * - Backlog exclusion
 * - Task lifecycle
 */
import { describe, test, expect, beforeEach, afterEach } from "bun:test"
import { mkdtempSync } from "fs"
import { tmpdir } from "os"
import { join } from "path"

import { LineCookPlugin } from "../../src/line-cook-plugin"
import {
  createMockClient,
  setupBeadsProject,
  setupNonBeadsProject,
  cleanupTestDir,
  hasLogMessage,
  getLogsByLevel,
  getToastsByVariant,
  createMockShell,
  type MockClient,
} from "../mocks/plugin-input.mock"
import {
  loadMockIssues,
  EXPECTED_HIERARCHY,
  ISSUE_COUNTS,
  getIssueById,
  getChildren,
  getBlockers,
  isReady,
  type BeadsIssue,
} from "../fixtures/beads"

describe("Beads Workflow Integration", () => {
  let tempDir: string
  let mockClient: MockClient

  beforeEach(() => {
    tempDir = mkdtempSync(join(tmpdir(), "beads-test-"))
    mockClient = createMockClient()
  })

  afterEach(() => {
    cleanupTestDir(tempDir)
  })

  describe("Beads Detection", () => {
    test("detects beads-enabled project when .beads/issues.jsonl exists", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      // Trigger session.created event
      await hooks.event!({ event: { type: "session.created", properties: {} } as any })

      expect(hasLogMessage(mockClient, "Beads-enabled project detected")).toBe(true)
    })

    test("detects non-beads project when .beads/ missing", async () => {
      setupNonBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      // Trigger session.created event
      await hooks.event!({ event: { type: "session.created", properties: {} } as any })

      expect(hasLogMessage(mockClient, "No .beads/ directory")).toBe(true)
      expect(hasLogMessage(mockClient, "Beads-enabled project detected")).toBe(false)
    })
  })

  describe("Session Lifecycle Events", () => {
    test("session.created logs beads detection for beads project", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({ event: { type: "session.created", properties: {} } as any })

      const infoLogs = getLogsByLevel(mockClient, "info")
      expect(infoLogs.some((log) => log.body.message.includes("Beads-enabled"))).toBe(true)
    })

    test("session.created suggests /line-work workflow", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({ event: { type: "session.created", properties: {} } as any })

      expect(hasLogMessage(mockClient, "/line-work")).toBe(true)
    })

    test("session.idle reminds about /line-tidy for beads project", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({ event: { type: "session.idle", properties: {} } as any })

      expect(hasLogMessage(mockClient, "/line-tidy")).toBe(true)
    })

    test("session.idle does not log for non-beads project", async () => {
      setupNonBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({ event: { type: "session.idle", properties: {} } as any })

      // Should not log tidy reminder for non-beads projects
      expect(hasLogMessage(mockClient, "/line-tidy")).toBe(false)
    })
  })

  describe("Compaction Context Injection", () => {
    test("injects BEADS_COMPACTION_CONTEXT for beads projects", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      const output = { context: [] as string[], prompt: undefined }
      await hooks["experimental.session.compacting"]!(
        { sessionID: "test-session" },
        output
      )

      expect(output.context.length).toBe(1)
      expect(output.context[0]).toContain("Beads Workflow Context")
    })

    test("context includes SESSION CLOSE PROTOCOL", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      const output = { context: [] as string[], prompt: undefined }
      await hooks["experimental.session.compacting"]!(
        { sessionID: "test-session" },
        output
      )

      expect(output.context[0]).toContain("SESSION CLOSE PROTOCOL")
    })

    test("context includes bd ready, bd sync commands", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      const output = { context: [] as string[], prompt: undefined }
      await hooks["experimental.session.compacting"]!(
        { sessionID: "test-session" },
        output
      )

      expect(output.context[0]).toContain("bd ready")
      expect(output.context[0]).toContain("bd sync")
    })

    test("skips injection for non-beads projects", async () => {
      setupNonBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      const output = { context: [] as string[], prompt: undefined }
      await hooks["experimental.session.compacting"]!(
        { sessionID: "test-session" },
        output
      )

      expect(output.context.length).toBe(0)
    })
  })

  describe("File Edit Tracking", () => {
    test("logs .beads/ file edits as fileType: beads", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({
        event: {
          type: "file.edited",
          properties: { file: join(tempDir, ".beads/issues.jsonl") },
        } as any,
      })

      const debugLogs = getLogsByLevel(mockClient, "debug")
      const beadsLog = debugLogs.find(
        (log) =>
          log.body.message.includes("Workflow file edited") &&
          log.body.extra?.fileType === "beads"
      )
      expect(beadsLog).toBeDefined()
    })

    test("logs AGENTS.md edits as fileType: agents", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({
        event: {
          type: "file.edited",
          properties: { file: join(tempDir, "AGENTS.md") },
        } as any,
      })

      const debugLogs = getLogsByLevel(mockClient, "debug")
      const agentsLog = debugLogs.find(
        (log) =>
          log.body.message.includes("Workflow file edited") &&
          log.body.extra?.fileType === "agents"
      )
      expect(agentsLog).toBeDefined()
    })

    test("logs CLAUDE.md edits as fileType: claude", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({
        event: {
          type: "file.edited",
          properties: { file: join(tempDir, "CLAUDE.md") },
        } as any,
      })

      const debugLogs = getLogsByLevel(mockClient, "debug")
      const claudeLog = debugLogs.find(
        (log) =>
          log.body.message.includes("Workflow file edited") &&
          log.body.extra?.fileType === "claude"
      )
      expect(claudeLog).toBeDefined()
    })
  })

  describe("Session Error Handling", () => {
    test("shows toast notification for session errors", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({
        event: {
          type: "session.error",
          properties: {
            sessionID: "test-session",
            error: {
              name: "APIError",
              data: {
                message: "Rate limit exceeded",
                statusCode: 429,
                isRetryable: true,
              },
            },
          },
        } as any,
      })

      const errorToasts = getToastsByVariant(mockClient, "error")
      expect(errorToasts.length).toBeGreaterThan(0)
      expect(errorToasts[0].body.title).toContain("Rate Limit")
    })

    test("shows compaction toast for beads projects", async () => {
      setupBeadsProject(tempDir)

      const hooks = await LineCookPlugin({
        client: mockClient as any,
        directory: tempDir,
        $: createMockShell() as any,
      })

      await hooks.event!({
        event: {
          type: "session.compacted",
          properties: { sessionID: "test-session" },
        } as any,
      })

      const infoToasts = getToastsByVariant(mockClient, "info")
      expect(infoToasts.length).toBeGreaterThan(0)
      expect(infoToasts[0].body.message).toContain("Beads workflow context preserved")
    })
  })

  describe("Hierarchy Navigation", () => {
    let issues: BeadsIssue[]

    beforeEach(() => {
      issues = loadMockIssues()
    })

    test("loads correct number of issues", () => {
      expect(issues.length).toBe(ISSUE_COUNTS.total)
    })

    test("active epic has features as children", () => {
      const children = getChildren(issues, EXPECTED_HIERARCHY.activeEpic.id)
      expect(children.length).toBe(1)
      expect(children[0].id).toBe(EXPECTED_HIERARCHY.activeFeature.id)
    })

    test("features have tasks as children", () => {
      const children = getChildren(issues, EXPECTED_HIERARCHY.activeFeature.id)
      expect(children.length).toBe(3)
      expect(children.map((c) => c.id).sort()).toEqual(
        EXPECTED_HIERARCHY.activeFeature.childrenIds.sort()
      )
    })

    test("blocked task has blocks dependency", () => {
      const blockers = getBlockers(issues, EXPECTED_HIERARCHY.blockedTask.id)
      expect(blockers.length).toBe(1)
      expect(blockers[0].id).toBe(EXPECTED_HIERARCHY.readyTask.id)
    })

    test("backlog epic has correct priority", () => {
      const backlogEpic = getIssueById(issues, EXPECTED_HIERARCHY.backlogEpic.id)
      expect(backlogEpic?.priority).toBe(4)
    })
  })

  describe("Backlog Exclusion", () => {
    let issues: BeadsIssue[]

    beforeEach(() => {
      issues = loadMockIssues()
    })

    test("backlog epic (priority 4) excluded from active work", () => {
      const backlogEpic = getIssueById(issues, EXPECTED_HIERARCHY.backlogEpic.id)
      expect(backlogEpic?.priority).toBe(4)
      expect(isReady(issues, backlogEpic!.id)).toBe(false)
    })

    test("tasks under backlog epic inherit exclusion", () => {
      const backlogTask = getIssueById(issues, EXPECTED_HIERARCHY.backlogTask.id)
      expect(backlogTask?.priority).toBe(4)
      expect(isReady(issues, backlogTask!.id)).toBe(false)
    })

    test("active tasks are not excluded", () => {
      const readyTask = getIssueById(issues, EXPECTED_HIERARCHY.readyTask.id)
      expect(readyTask?.priority).toBe(2)
      expect(isReady(issues, readyTask!.id)).toBe(true)
    })
  })

  describe("Task Lifecycle", () => {
    let issues: BeadsIssue[]

    beforeEach(() => {
      issues = loadMockIssues()
    })

    test("ready task has no blockers", () => {
      const readyTask = getIssueById(issues, EXPECTED_HIERARCHY.readyTask.id)
      expect(readyTask?.status).toBe("open")

      const blockers = getBlockers(issues, readyTask!.id)
      expect(blockers.length).toBe(0)
      expect(isReady(issues, readyTask!.id)).toBe(true)
    })

    test("blocked task depends on open task", () => {
      const blockedTask = getIssueById(issues, EXPECTED_HIERARCHY.blockedTask.id)
      expect(blockedTask?.status).toBe("open")

      const blockers = getBlockers(issues, blockedTask!.id)
      expect(blockers.length).toBe(1)
      expect(blockers[0].status).toBe("open")
      expect(isReady(issues, blockedTask!.id)).toBe(false)
    })

    test("in_progress task represents active work", () => {
      const inProgressTask = getIssueById(issues, EXPECTED_HIERARCHY.inProgressTask.id)
      expect(inProgressTask?.status).toBe("in_progress")
      expect(isReady(issues, inProgressTask!.id)).toBe(false)
    })

    test("closed task has close_reason", () => {
      const closedTask = getIssueById(issues, EXPECTED_HIERARCHY.closedTask.id)
      expect(closedTask?.status).toBe("closed")
      expect(closedTask?.close_reason).toBeDefined()
      expect(closedTask?.close_reason).toBe(EXPECTED_HIERARCHY.closedTask.closeReason)
    })

    test("counts match expectations", () => {
      const openCount = issues.filter((i) => i.status === "open").length
      const inProgressCount = issues.filter((i) => i.status === "in_progress").length
      const closedCount = issues.filter((i) => i.status === "closed").length

      expect(openCount).toBe(ISSUE_COUNTS.open)
      expect(inProgressCount).toBe(ISSUE_COUNTS.inProgress)
      expect(closedCount).toBe(ISSUE_COUNTS.closed)
    })
  })
})
