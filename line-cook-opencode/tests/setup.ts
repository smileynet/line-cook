/**
 * Test setup for SDK integration tests
 */
import { mock, type Mock } from "bun:test"
import type { OpencodeClient } from "@opencode-ai/sdk"

// Type for mocked SDK client
export type MockedClient = {
  session: {
    list: Mock<() => Promise<{ data?: unknown; error?: unknown }>>
    create: Mock<() => Promise<{ data?: unknown; error?: unknown }>>
    get: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    delete: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    abort: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    prompt: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    promptAsync: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    summarize: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
    messages: Mock<(opts: unknown) => Promise<{ data?: unknown; error?: unknown }>>
  }
}

// Global mock client that tests can configure
export let mockClient: MockedClient

/**
 * Create a fresh mock client with all methods stubbed
 */
export function createMockClient(): MockedClient {
  return {
    session: {
      list: mock(() => Promise.resolve({ data: [] })),
      create: mock(() => Promise.resolve({ data: { id: "test-session" } })),
      get: mock(() => Promise.resolve({ data: { id: "test-session" } })),
      delete: mock(() => Promise.resolve({ data: undefined })),
      abort: mock(() => Promise.resolve({ data: undefined })),
      prompt: mock(() => Promise.resolve({ data: undefined })),
      promptAsync: mock(() => Promise.resolve({ data: undefined })),
      summarize: mock(() => Promise.resolve({ data: undefined })),
      messages: mock(() => Promise.resolve({ data: [] })),
    },
  }
}

/**
 * Reset the mock client to fresh state
 */
export function resetMockClient(): MockedClient {
  mockClient = createMockClient()
  return mockClient
}

// Initialize mock client
mockClient = createMockClient()
