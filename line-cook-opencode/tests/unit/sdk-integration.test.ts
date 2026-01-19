/**
 * Unit tests for SDK integration
 *
 * Tests all 11 exported functions with mocked SDK responses.
 */
import { describe, test, expect, beforeEach, mock, spyOn } from "bun:test"
import {
  createMockSession,
  createMockMessageWithParts,
  createMockToolPart,
  createMockTextPart,
  successResponse,
  errorResponse,
} from "../mocks/sdk-client.mock"

// Create mock client factory
const createMockClientFactory = () => {
  const mockSession = {
    list: mock(() => Promise.resolve(successResponse([]))),
    create: mock(() => Promise.resolve(successResponse(createMockSession()))),
    get: mock(() => Promise.resolve(successResponse(createMockSession()))),
    delete: mock(() => Promise.resolve(successResponse(undefined))),
    abort: mock(() => Promise.resolve(successResponse(undefined))),
    prompt: mock(() => Promise.resolve(successResponse(undefined))),
    promptAsync: mock(() => Promise.resolve(successResponse(undefined))),
    summarize: mock(() => Promise.resolve(successResponse(undefined))),
    messages: mock(() => Promise.resolve(successResponse([]))),
  }

  return {
    session: mockSession,
    _reset() {
      Object.values(mockSession).forEach((m) => {
        if (typeof m === "function" && "mockReset" in m) {
          ;(m as ReturnType<typeof mock>).mockReset()
        }
      })
    },
  }
}

let mockClient: ReturnType<typeof createMockClientFactory>

// Mock the SDK module
mock.module("@opencode-ai/sdk", () => ({
  createOpencodeClient: (opts: { baseUrl?: string; logLevel?: string }) => {
    // Store options for verification
    ;(mockClient as unknown as Record<string, unknown>)._lastOpts = opts
    return mockClient
  },
}))

// Import functions after mocking
import {
  createClient,
  createSession,
  triggerCompaction,
  getSessionState,
  listSessions,
  getSession,
  abortSession,
  sendPrompt,
  sendPromptAsync,
  deleteSession,
  getSessionMessages,
} from "../../src/sdk-integration"

describe("SDK Integration", () => {
  beforeEach(() => {
    mockClient = createMockClientFactory()
  })

  describe("createClient", () => {
    test("uses default URL when no options provided", () => {
      createClient()
      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        baseUrl: string
      }
      expect(opts.baseUrl).toBe("http://localhost:4096")
    })

    test("uses custom URL when provided", () => {
      createClient({ baseUrl: "http://custom:8080" })
      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        baseUrl: string
      }
      expect(opts.baseUrl).toBe("http://custom:8080")
    })

    test("enables debug logging when debug option is true", () => {
      createClient({ debug: true })
      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        logLevel?: string
      }
      expect(opts.logLevel).toBe("debug")
    })

    test("does not set logLevel when debug is false", () => {
      createClient({ debug: false })
      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        logLevel?: string
      }
      expect(opts.logLevel).toBeUndefined()
    })
  })

  describe("createSession", () => {
    test("creates session successfully", async () => {
      const session = createMockSession({ id: "new-session" })
      mockClient.session.create.mockResolvedValueOnce(successResponse(session))

      const result = await createSession()

      expect(result.id).toBe("new-session")
      expect(mockClient.session.create).toHaveBeenCalled()
    })

    test("sends initial prompt when provided", async () => {
      const session = createMockSession({ id: "session-with-prompt" })
      mockClient.session.create.mockResolvedValueOnce(successResponse(session))
      mockClient.session.prompt.mockResolvedValueOnce(successResponse(undefined))

      await createSession({ initialPrompt: "Hello, world!" })

      expect(mockClient.session.prompt).toHaveBeenCalledWith({
        path: { id: "session-with-prompt" },
        body: {
          parts: [{ type: "text", text: "Hello, world!" }],
        },
      })
    })

    test("throws error when creation fails", async () => {
      mockClient.session.create.mockResolvedValueOnce(
        errorResponse("Creation failed")
      )

      await expect(createSession()).rejects.toThrow("Failed to create session")
    })

    test("throws error when data is undefined", async () => {
      mockClient.session.create.mockResolvedValueOnce({ data: undefined })

      await expect(createSession()).rejects.toThrow("Failed to create session")
    })
  })

  describe("triggerCompaction", () => {
    test("returns success on successful compaction", async () => {
      mockClient.session.summarize.mockResolvedValueOnce(
        successResponse(undefined)
      )

      const result = await triggerCompaction("session-123")

      expect(result).toEqual({
        success: true,
        sessionId: "session-123",
      })
    })

    test("returns failure with error message on API error", async () => {
      mockClient.session.summarize.mockResolvedValueOnce(
        errorResponse("Summarization failed")
      )

      const result = await triggerCompaction("session-123")

      expect(result).toEqual({
        success: false,
        sessionId: "session-123",
        error: "Summarization failed",
      })
    })

    test("catches exceptions and returns failure", async () => {
      mockClient.session.summarize.mockRejectedValueOnce(
        new Error("Network error")
      )

      const result = await triggerCompaction("session-123")

      expect(result).toEqual({
        success: false,
        sessionId: "session-123",
        error: "Network error",
      })
    })

    test("handles non-Error exceptions", async () => {
      mockClient.session.summarize.mockRejectedValueOnce("String error")

      const result = await triggerCompaction("session-123")

      expect(result).toEqual({
        success: false,
        sessionId: "session-123",
        error: "String error",
      })
    })
  })

  describe("getSessionState", () => {
    test("returns empty state for session with no messages", async () => {
      mockClient.session.messages.mockResolvedValueOnce(successResponse([]))

      const state = await getSessionState("session-123")

      expect(state).toEqual({
        id: "session-123",
        messageCount: 0,
        toolCallCount: 0,
        completedToolCalls: 0,
        pendingToolCalls: 0,
        hasErrors: false,
        lastActivity: undefined,
      })
    })

    test("counts tool calls correctly", async () => {
      const messages = [
        createMockMessageWithParts({ time: { created: 1000 } }, [
          createMockToolPart({ status: "completed" }),
          createMockToolPart({ status: "completed" }),
        ]),
        createMockMessageWithParts({ time: { created: 2000 } }, [
          createMockToolPart({ status: "running" }),
        ]),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const state = await getSessionState("session-123")

      expect(state.messageCount).toBe(2)
      expect(state.toolCallCount).toBe(3)
      expect(state.completedToolCalls).toBe(2)
      expect(state.pendingToolCalls).toBe(1)
      expect(state.hasErrors).toBe(false)
    })

    test("detects error states in tool calls", async () => {
      const messages = [
        createMockMessageWithParts({}, [
          createMockToolPart({ status: "error" }),
        ]),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const state = await getSessionState("session-123")

      expect(state.hasErrors).toBe(true)
      expect(state.completedToolCalls).toBe(1) // Errors count as "done"
    })

    test("tracks pending tool calls", async () => {
      const messages = [
        createMockMessageWithParts({}, [
          createMockToolPart({ status: "pending" }),
          createMockToolPart({ status: "running" }),
        ]),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const state = await getSessionState("session-123")

      expect(state.pendingToolCalls).toBe(2)
    })

    test("calculates lastActivity from message timestamps", async () => {
      const messages = [
        createMockMessageWithParts({ time: { created: 1000 } }, [
          createMockTextPart(),
        ]),
        createMockMessageWithParts({ time: { created: 3000 } }, [
          createMockTextPart(),
        ]),
        createMockMessageWithParts({ time: { created: 2000 } }, [
          createMockTextPart(),
        ]),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const state = await getSessionState("session-123")

      expect(state.lastActivity).toBe(3000)
    })

    test("throws error when API call fails", async () => {
      mockClient.session.messages.mockResolvedValueOnce(
        errorResponse("API error")
      )

      await expect(getSessionState("session-123")).rejects.toThrow(
        "Failed to get session messages"
      )
    })

    test("handles mixed part types (ignores non-tool parts)", async () => {
      const messages = [
        createMockMessageWithParts({}, [
          createMockTextPart("hello"),
          createMockToolPart({ status: "completed" }),
          { type: "image", url: "http://example.com" } as unknown as import("@opencode-ai/sdk").Part,
        ]),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const state = await getSessionState("session-123")

      expect(state.toolCallCount).toBe(1)
    })
  })

  describe("listSessions", () => {
    test("returns empty array when no sessions", async () => {
      mockClient.session.list.mockResolvedValueOnce(successResponse([]))

      const sessions = await listSessions()

      expect(sessions).toEqual([])
    })

    test("returns array of sessions", async () => {
      const mockSessions = [
        createMockSession({ id: "session-1" }),
        createMockSession({ id: "session-2" }),
      ]
      mockClient.session.list.mockResolvedValueOnce(
        successResponse(mockSessions)
      )

      const sessions = await listSessions()

      expect(sessions).toHaveLength(2)
      expect(sessions[0].id).toBe("session-1")
      expect(sessions[1].id).toBe("session-2")
    })

    test("returns empty array when data is undefined", async () => {
      mockClient.session.list.mockResolvedValueOnce({ data: undefined })

      const sessions = await listSessions()

      expect(sessions).toEqual([])
    })
  })

  describe("getSession", () => {
    test("returns session when found", async () => {
      const session = createMockSession({ id: "found-session" })
      mockClient.session.get.mockResolvedValueOnce(successResponse(session))

      const result = await getSession("found-session")

      expect(result.id).toBe("found-session")
      expect(mockClient.session.get).toHaveBeenCalledWith({
        path: { id: "found-session" },
      })
    })

    test("throws error when session not found", async () => {
      mockClient.session.get.mockResolvedValueOnce(
        errorResponse("Session not found")
      )

      await expect(getSession("nonexistent")).rejects.toThrow(
        "Failed to get session"
      )
    })

    test("throws error when data is undefined", async () => {
      mockClient.session.get.mockResolvedValueOnce({ data: undefined })

      await expect(getSession("nonexistent")).rejects.toThrow(
        "Failed to get session"
      )
    })
  })

  describe("abortSession", () => {
    test("calls abort with correct session ID", async () => {
      mockClient.session.abort.mockResolvedValueOnce(successResponse(undefined))

      await abortSession("session-to-abort")

      expect(mockClient.session.abort).toHaveBeenCalledWith({
        path: { id: "session-to-abort" },
      })
    })

    test("passes through custom client options", async () => {
      mockClient.session.abort.mockResolvedValueOnce(successResponse(undefined))

      await abortSession("session-123", { baseUrl: "http://custom:9000" })

      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        baseUrl: string
      }
      expect(opts.baseUrl).toBe("http://custom:9000")
    })
  })

  describe("sendPrompt", () => {
    test("sends prompt with correct parts format", async () => {
      mockClient.session.prompt.mockResolvedValueOnce(successResponse(undefined))

      await sendPrompt("session-123", "Run the build")

      expect(mockClient.session.prompt).toHaveBeenCalledWith({
        path: { id: "session-123" },
        body: {
          parts: [{ type: "text", text: "Run the build" }],
        },
      })
    })

    test("handles empty prompt", async () => {
      mockClient.session.prompt.mockResolvedValueOnce(successResponse(undefined))

      await sendPrompt("session-123", "")

      expect(mockClient.session.prompt).toHaveBeenCalledWith({
        path: { id: "session-123" },
        body: {
          parts: [{ type: "text", text: "" }],
        },
      })
    })
  })

  describe("sendPromptAsync", () => {
    test("sends async prompt with correct parts format", async () => {
      mockClient.session.promptAsync.mockResolvedValueOnce(
        successResponse(undefined)
      )

      await sendPromptAsync("session-123", "Run tests in background")

      expect(mockClient.session.promptAsync).toHaveBeenCalledWith({
        path: { id: "session-123" },
        body: {
          parts: [{ type: "text", text: "Run tests in background" }],
        },
      })
    })

    test("passes through custom client options", async () => {
      mockClient.session.promptAsync.mockResolvedValueOnce(
        successResponse(undefined)
      )

      await sendPromptAsync("session-123", "test", {
        baseUrl: "http://other:5000",
      })

      const opts = (mockClient as unknown as Record<string, unknown>)._lastOpts as {
        baseUrl: string
      }
      expect(opts.baseUrl).toBe("http://other:5000")
    })
  })

  describe("deleteSession", () => {
    test("calls delete with correct session ID", async () => {
      mockClient.session.delete.mockResolvedValueOnce(successResponse(undefined))

      await deleteSession("session-to-delete")

      expect(mockClient.session.delete).toHaveBeenCalledWith({
        path: { id: "session-to-delete" },
      })
    })
  })

  describe("getSessionMessages", () => {
    test("returns messages on success", async () => {
      const messages = [
        createMockMessageWithParts({ id: "msg-1" }),
        createMockMessageWithParts({ id: "msg-2" }),
      ]
      mockClient.session.messages.mockResolvedValueOnce(successResponse(messages))

      const result = await getSessionMessages("session-123")

      expect(result).toHaveLength(2)
      expect(result[0].info.id).toBe("msg-1")
    })

    test("throws error on API failure", async () => {
      mockClient.session.messages.mockResolvedValueOnce(
        errorResponse("Messages fetch failed")
      )

      await expect(getSessionMessages("session-123")).rejects.toThrow(
        "Failed to get session messages"
      )
    })

    test("throws error when data is undefined", async () => {
      mockClient.session.messages.mockResolvedValueOnce({ data: undefined })

      await expect(getSessionMessages("session-123")).rejects.toThrow(
        "Failed to get session messages"
      )
    })
  })
})
