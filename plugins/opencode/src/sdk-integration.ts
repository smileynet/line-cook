/**
 * SDK Integration for Line Cook
 *
 * Provides utilities for programmatic session control using @opencode-ai/sdk.
 * These utilities enable automated workflows, compaction triggers, and
 * session state queries for progress tracking.
 *
 * @module sdk-integration
 */

import { createOpencodeClient } from "@opencode-ai/sdk"
import type {
  Session,
  Message,
  Part,
  ToolPart,
  ToolState,
} from "@opencode-ai/sdk"

/**
 * Re-export types for consumers
 */
export type { Session, Message, Part }

/**
 * Default OpenCode server URL
 */
const DEFAULT_SERVER_URL = "http://localhost:4096"

/**
 * Options for creating an SDK client
 */
export interface ClientOptions {
  /** Base URL of the OpenCode server */
  baseUrl?: string
  /** Enable debug logging */
  debug?: boolean
}

/**
 * Session creation options
 */
export interface CreateSessionOptions {
  /** Initial prompt to send after creation */
  initialPrompt?: string
}

/**
 * Session state summary for progress tracking
 */
export interface SessionState {
  /** Session ID */
  id: string
  /** Total number of messages in the session */
  messageCount: number
  /** Number of tool calls made */
  toolCallCount: number
  /** Number of completed tool calls */
  completedToolCalls: number
  /** Number of pending/running tool calls */
  pendingToolCalls: number
  /** Whether the session has any errors */
  hasErrors: boolean
  /** Last activity timestamp (epoch ms) */
  lastActivity?: number
}

/**
 * Compaction result
 */
export interface CompactionResult {
  /** Whether compaction was successful */
  success: boolean
  /** Session ID that was compacted */
  sessionId: string
  /** Error message if compaction failed */
  error?: string
}

/**
 * Message with parts (as returned by session.messages)
 */
export interface MessageWithParts {
  info: Message
  parts: Part[]
}

/**
 * Create an OpenCode SDK client
 *
 * @param options - Client configuration options
 * @returns Configured SDK client
 *
 * @example
 * ```typescript
 * const client = createClient()
 * const response = await client.session.list()
 * const sessions = response.data
 * ```
 */
export function createClient(options: ClientOptions = {}) {
  const baseUrl = options.baseUrl ?? DEFAULT_SERVER_URL

  return createOpencodeClient({
    baseUrl,
    ...(options.debug && { logLevel: "debug" }),
  })
}

/**
 * Create a new OpenCode session programmatically
 *
 * @param options - Session creation options
 * @param clientOptions - Client configuration
 * @returns The created session
 *
 * @example
 * ```typescript
 * const session = await createSession({
 *   title: "Automated workflow",
 *   initialPrompt: "Run the test suite"
 * })
 * console.log(`Created session: ${session.id}`)
 * ```
 */
export async function createSession(
  options: CreateSessionOptions = {},
  clientOptions: ClientOptions = {}
): Promise<Session> {
  const client = createClient(clientOptions)

  // Create the session
  const response = await client.session.create()

  if (response.error || !response.data) {
    throw new Error(`Failed to create session: ${response.error}`)
  }

  const session = response.data

  // Send initial prompt if provided
  if (options.initialPrompt) {
    await client.session.prompt({
      path: { id: session.id },
      body: {
        parts: [{ type: "text", text: options.initialPrompt }],
      },
    })
  }

  return session
}

/**
 * Trigger session compaction/summarization
 *
 * Compaction reduces context size by summarizing the conversation history.
 * This is useful when approaching context limits or for periodic cleanup
 * in long-running sessions.
 *
 * @param sessionId - ID of the session to compact
 * @param clientOptions - Client configuration
 * @returns Compaction result
 *
 * @example
 * ```typescript
 * const result = await triggerCompaction("session-123")
 * if (result.success) {
 *   console.log("Session compacted successfully")
 * }
 * ```
 */
export async function triggerCompaction(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<CompactionResult> {
  const client = createClient(clientOptions)

  try {
    const response = await client.session.summarize({ path: { id: sessionId } })
    if (response.error) {
      return {
        success: false,
        sessionId,
        error: String(response.error),
      }
    }
    return {
      success: true,
      sessionId,
    }
  } catch (error) {
    return {
      success: false,
      sessionId,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Query session state for progress tracking
 *
 * Returns a summary of the session's current state including message count,
 * tool call statistics, and error status.
 *
 * @param sessionId - ID of the session to query
 * @param clientOptions - Client configuration
 * @returns Session state summary
 *
 * @example
 * ```typescript
 * const state = await getSessionState("session-123")
 * console.log(`Messages: ${state.messageCount}`)
 * console.log(`Tool calls: ${state.completedToolCalls}/${state.toolCallCount}`)
 * ```
 */
export async function getSessionState(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<SessionState> {
  const client = createClient(clientOptions)

  const response = await client.session.messages({ path: { id: sessionId } })

  if (response.error || !response.data) {
    throw new Error(`Failed to get session messages: ${response.error}`)
  }

  const messagesWithParts: MessageWithParts[] = response.data

  // Count tool calls from message parts
  let toolCallCount = 0
  let completedToolCalls = 0
  let pendingToolCalls = 0
  let hasErrors = false
  let lastActivity: number | undefined

  for (const { info, parts } of messagesWithParts) {
    // Track last activity from message timestamps
    const messageTime = info.time.created
    if (!lastActivity || messageTime > lastActivity) {
      lastActivity = messageTime
    }

    // Count tool calls from parts
    for (const part of parts) {
      if (part.type === "tool") {
        toolCallCount++
        const toolPart = part as ToolPart
        const state: ToolState = toolPart.state

        if (state.status === "completed") {
          completedToolCalls++
        } else if (state.status === "error") {
          hasErrors = true
          completedToolCalls++ // Count errors as "done"
        } else if (state.status === "running" || state.status === "pending") {
          pendingToolCalls++
        }
      }
    }
  }

  return {
    id: sessionId,
    messageCount: messagesWithParts.length,
    toolCallCount,
    completedToolCalls,
    pendingToolCalls,
    hasErrors,
    lastActivity,
  }
}

/**
 * List all sessions
 *
 * @param clientOptions - Client configuration
 * @returns Array of sessions
 *
 * @example
 * ```typescript
 * const sessions = await listSessions()
 * for (const session of sessions) {
 *   console.log(`${session.id}: ${session.title ?? "Untitled"}`)
 * }
 * ```
 */
export async function listSessions(
  clientOptions: ClientOptions = {}
): Promise<Session[]> {
  const client = createClient(clientOptions)
  const response = await client.session.list()
  return response.data ?? []
}

/**
 * Get a session by ID
 *
 * @param sessionId - ID of the session to get
 * @param clientOptions - Client configuration
 * @returns The session
 *
 * @example
 * ```typescript
 * const session = await getSession("session-123")
 * console.log(`Title: ${session.title}`)
 * ```
 */
export async function getSession(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<Session> {
  const client = createClient(clientOptions)
  const response = await client.session.get({ path: { id: sessionId } })

  if (response.error || !response.data) {
    throw new Error(`Failed to get session: ${response.error}`)
  }

  return response.data
}

/**
 * Abort a running session
 *
 * Stops any in-progress operations in the session.
 *
 * @param sessionId - ID of the session to abort
 * @param clientOptions - Client configuration
 *
 * @example
 * ```typescript
 * await abortSession("session-123")
 * console.log("Session aborted")
 * ```
 */
export async function abortSession(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<void> {
  const client = createClient(clientOptions)
  await client.session.abort({ path: { id: sessionId } })
}

/**
 * Send a prompt to an existing session
 *
 * @param sessionId - ID of the session
 * @param prompt - The prompt to send
 * @param clientOptions - Client configuration
 *
 * @example
 * ```typescript
 * await sendPrompt("session-123", "Run the build")
 * ```
 */
export async function sendPrompt(
  sessionId: string,
  prompt: string,
  clientOptions: ClientOptions = {}
): Promise<void> {
  const client = createClient(clientOptions)
  await client.session.prompt({
    path: { id: sessionId },
    body: {
      parts: [{ type: "text", text: prompt }],
    },
  })
}

/**
 * Send a prompt asynchronously (returns immediately)
 *
 * @param sessionId - ID of the session
 * @param prompt - The prompt to send
 * @param clientOptions - Client configuration
 *
 * @example
 * ```typescript
 * await sendPromptAsync("session-123", "Run the tests")
 * // Returns immediately, session processes in background
 * ```
 */
export async function sendPromptAsync(
  sessionId: string,
  prompt: string,
  clientOptions: ClientOptions = {}
): Promise<void> {
  const client = createClient(clientOptions)
  await client.session.promptAsync({
    path: { id: sessionId },
    body: {
      parts: [{ type: "text", text: prompt }],
    },
  })
}

/**
 * Delete a session
 *
 * @param sessionId - ID of the session to delete
 * @param clientOptions - Client configuration
 *
 * @example
 * ```typescript
 * await deleteSession("session-123")
 * ```
 */
export async function deleteSession(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<void> {
  const client = createClient(clientOptions)
  await client.session.delete({ path: { id: sessionId } })
}

/**
 * Get messages for a session
 *
 * @param sessionId - ID of the session
 * @param clientOptions - Client configuration
 * @returns Array of messages with their parts
 *
 * @example
 * ```typescript
 * const messages = await getSessionMessages("session-123")
 * for (const { info, parts } of messages) {
 *   console.log(`${info.role}: ${parts.length} parts`)
 * }
 * ```
 */
export async function getSessionMessages(
  sessionId: string,
  clientOptions: ClientOptions = {}
): Promise<MessageWithParts[]> {
  const client = createClient(clientOptions)
  const response = await client.session.messages({ path: { id: sessionId } })

  if (response.error || !response.data) {
    throw new Error(`Failed to get session messages: ${response.error}`)
  }

  return response.data
}
