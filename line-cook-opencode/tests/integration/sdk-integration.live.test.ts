/**
 * Live integration tests for SDK integration
 *
 * These tests run against a live OpenCode server at localhost:4096.
 * Tests auto-skip if the server is unavailable.
 *
 * Prerequisites:
 * - Start OpenCode server: opencode serve
 * - Set OPENCODE_SERVER_URL env var to override default
 */
import { describe, test, expect, beforeAll, afterEach } from "bun:test"
import {
  createSession,
  getSession,
  getSessionState,
  getSessionMessages,
  listSessions,
  deleteSession,
  sendPrompt,
  sendPromptAsync,
  abortSession,
  triggerCompaction,
  type ClientOptions,
} from "../../src/sdk-integration"

const SERVER_URL = process.env.OPENCODE_SERVER_URL ?? "http://localhost:4096"

/**
 * Check if OpenCode server is available
 */
async function isServerAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${SERVER_URL}/health`, {
      signal: AbortSignal.timeout(2000),
    })
    return response.ok
  } catch {
    return false
  }
}

// Track sessions created during tests for cleanup
const testSessions: string[] = []

// Client options for all tests
const clientOptions: ClientOptions = { baseUrl: SERVER_URL }

// Check server availability once before all tests
let serverAvailable = false

beforeAll(async () => {
  serverAvailable = await isServerAvailable()
  if (!serverAvailable) {
    console.log(
      `[SKIP] OpenCode server not available at ${SERVER_URL} - integration tests will be skipped`
    )
  }
})

afterEach(async () => {
  // Skip cleanup if server wasn't available
  if (!serverAvailable) return

  // Clean up all test sessions
  for (const sessionId of testSessions) {
    try {
      await deleteSession(sessionId, clientOptions)
    } catch {
      // Ignore cleanup errors
    }
  }
  testSessions.length = 0
})

describe.skipIf(() => !serverAvailable)("SDK Integration - Live Server", () => {
  describe("Session Lifecycle", () => {
    test("create session, verify exists, delete, verify gone", async () => {
      // Create
      const session = await createSession({}, clientOptions)
      expect(session.id).toBeDefined()
      testSessions.push(session.id)

      // Verify exists
      const fetched = await getSession(session.id, clientOptions)
      expect(fetched.id).toBe(session.id)

      // Delete
      await deleteSession(session.id, clientOptions)
      testSessions.pop() // Remove from cleanup list since we deleted it

      // Verify gone
      await expect(getSession(session.id, clientOptions)).rejects.toThrow()
    })

    test(
      "create with initial prompt, verify messages exist",
      async () => {
        const session = await createSession(
          { initialPrompt: "Hello, this is a test prompt" },
          clientOptions
        )
        testSessions.push(session.id)

        // Give the server a moment to process
        await new Promise((resolve) => setTimeout(resolve, 500))

        const messages = await getSessionMessages(session.id, clientOptions)
        expect(messages.length).toBeGreaterThan(0)
      },
      { timeout: 30000 }
    )

    test("list sessions returns array", async () => {
      const session = await createSession({}, clientOptions)
      testSessions.push(session.id)

      const sessions = await listSessions(clientOptions)
      expect(Array.isArray(sessions)).toBe(true)
      expect(sessions.some((s) => s.id === session.id)).toBe(true)
    })
  })

  describe("Operations", () => {
    test(
      "sendPrompt adds message to session",
      async () => {
        const session = await createSession({}, clientOptions)
        testSessions.push(session.id)

        await sendPrompt(session.id, "Test prompt message", clientOptions)

        // Give server time to process
        await new Promise((resolve) => setTimeout(resolve, 500))

        const messages = await getSessionMessages(session.id, clientOptions)
        expect(messages.length).toBeGreaterThan(0)
      },
      { timeout: 30000 }
    )

    test(
      "sendPromptAsync returns immediately",
      async () => {
        const session = await createSession({}, clientOptions)
        testSessions.push(session.id)

        const startTime = Date.now()
        await sendPromptAsync(
          session.id,
          "Test async prompt message",
          clientOptions
        )
        const elapsed = Date.now() - startTime

        // Should return quickly (not wait for processing)
        // Allow some network latency but shouldn't take more than a few seconds
        expect(elapsed).toBeLessThan(5000)
      },
      { timeout: 30000 }
    )

    test(
      "abortSession stops running session",
      async () => {
        const session = await createSession({}, clientOptions)
        testSessions.push(session.id)

        // Start a prompt asynchronously
        await sendPromptAsync(
          session.id,
          "Run a complex operation that takes time",
          clientOptions
        )

        // Abort should not throw
        await expect(
          abortSession(session.id, clientOptions)
        ).resolves.toBeUndefined()
      },
      { timeout: 30000 }
    )

    test("getSessionState returns correct structure", async () => {
      const session = await createSession({}, clientOptions)
      testSessions.push(session.id)

      const state = await getSessionState(session.id, clientOptions)

      expect(state).toMatchObject({
        id: session.id,
        messageCount: expect.any(Number),
        toolCallCount: expect.any(Number),
        completedToolCalls: expect.any(Number),
        pendingToolCalls: expect.any(Number),
        hasErrors: expect.any(Boolean),
      })
    })
  })

  describe("Compaction", () => {
    test("triggerCompaction returns result object", async () => {
      const session = await createSession({}, clientOptions)
      testSessions.push(session.id)

      const result = await triggerCompaction(session.id, clientOptions)

      // May succeed or fail depending on session state (empty sessions may fail)
      expect(result).toMatchObject({
        sessionId: session.id,
        success: expect.any(Boolean),
      })
      if (!result.success) {
        expect(result.error).toBeDefined()
      }
    })
  })

  describe("Error Handling", () => {
    test("getSession throws for non-existent ID", async () => {
      await expect(
        getSession("nonexistent-session-id-12345", clientOptions)
      ).rejects.toThrow()
    })

    test("getSessionState throws for non-existent ID", async () => {
      await expect(
        getSessionState("nonexistent-session-id-12345", clientOptions)
      ).rejects.toThrow()
    })

    test("getSessionMessages throws for non-existent ID", async () => {
      await expect(
        getSessionMessages("nonexistent-session-id-12345", clientOptions)
      ).rejects.toThrow()
    })
  })
})
