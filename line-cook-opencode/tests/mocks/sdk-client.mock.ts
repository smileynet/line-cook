/**
 * Mock factories for @opencode-ai/sdk client
 *
 * Provides utilities for creating mock SDK responses and clients.
 */
import { mock, type Mock } from "bun:test"
import type { Session, Message, Part, ToolPart } from "@opencode-ai/sdk"

/**
 * Create a mock Session object
 */
export function createMockSession(overrides: Partial<Session> = {}): Session {
  return {
    id: "mock-session-id",
    path: "/mock/path",
    time: {
      created: Date.now(),
      updated: Date.now(),
    },
    ...overrides,
  } as Session
}

/**
 * Create a mock Message object
 */
export function createMockMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: "mock-message-id",
    sessionID: "mock-session-id",
    role: "user",
    time: {
      created: Date.now(),
    },
    ...overrides,
  } as Message
}

/**
 * Create a mock text Part
 */
export function createMockTextPart(text: string = "mock text"): Part {
  return {
    type: "text",
    text,
  } as Part
}

/**
 * Create a mock tool Part with state
 */
export function createMockToolPart(
  overrides: Partial<ToolPart> & { status?: string } = {}
): ToolPart {
  const { status = "completed", ...rest } = overrides
  return {
    type: "tool",
    id: "mock-tool-id",
    tool: "mock-tool",
    state: {
      status,
      input: {},
    },
    ...rest,
  } as ToolPart
}

/**
 * Create a mock MessageWithParts structure
 */
export function createMockMessageWithParts(
  messageOverrides: Partial<Message> = {},
  parts: Part[] = []
) {
  return {
    info: createMockMessage(messageOverrides),
    parts: parts.length > 0 ? parts : [createMockTextPart()],
  }
}

/**
 * Create a success response wrapper
 */
export function successResponse<T>(data: T) {
  return { data, error: undefined }
}

/**
 * Create an error response wrapper
 */
export function errorResponse(error: string | object) {
  return { data: undefined, error }
}
