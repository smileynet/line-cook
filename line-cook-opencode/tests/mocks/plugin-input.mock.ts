/**
 * Mock factories for PluginInput and related types
 *
 * Provides utilities for testing LineCookPlugin event handlers.
 */
import { mock, type Mock } from "bun:test"
import { mkdirSync, writeFileSync, rmSync } from "fs"
import { join } from "path"
import { getMockIssuesContent } from "../fixtures/beads"

/**
 * Log call entry for verification
 */
export interface LogCall {
  body: {
    service: string
    level: string
    message: string
    extra?: Record<string, unknown> // Optional - may not be present in all log calls
  }
}

/**
 * Toast call entry for verification
 */
export interface ToastCall {
  body: {
    title: string
    message: string
    variant: "info" | "error" | "success" | "warning"
    duration?: number
  }
}

/**
 * Mock client type that matches PluginInput["client"] interface
 */
export interface MockClient {
  app: {
    log: Mock<(params: LogCall) => Promise<void>>
    _logCalls: LogCall[]
  }
  tui: {
    showToast: Mock<(params: ToastCall) => Promise<void>>
    _toastCalls: ToastCall[]
  }
}

/**
 * Create a mock client with spied methods
 *
 * The client records all log and toast calls for verification.
 */
export function createMockClient(): MockClient {
  const logCalls: LogCall[] = []
  const toastCalls: ToastCall[] = []

  return {
    app: {
      log: mock(async (params: LogCall) => {
        logCalls.push(params)
      }),
      _logCalls: logCalls,
    },
    tui: {
      showToast: mock(async (params: ToastCall) => {
        toastCalls.push(params)
      }),
      _toastCalls: toastCalls,
    },
  }
}

/**
 * Get log calls filtered by level
 */
export function getLogsByLevel(client: MockClient, level: string): LogCall[] {
  return client.app._logCalls.filter((call) => call.body.level === level)
}

/**
 * Get log calls containing a message substring
 */
export function getLogsContaining(client: MockClient, substring: string): LogCall[] {
  return client.app._logCalls.filter((call) =>
    call.body.message.toLowerCase().includes(substring.toLowerCase())
  )
}

/**
 * Check if any log call contains the given message
 */
export function hasLogMessage(client: MockClient, substring: string): boolean {
  return getLogsContaining(client, substring).length > 0
}

/**
 * Get toast calls filtered by variant
 */
export function getToastsByVariant(
  client: MockClient,
  variant: ToastCall["body"]["variant"]
): ToastCall[] {
  return client.tui._toastCalls.filter((call) => call.body.variant === variant)
}

/**
 * Set up a beads-enabled project in a temporary directory
 *
 * Creates .beads/issues.jsonl with the mock fixture content.
 *
 * @param tempDir - Temporary directory path
 * @param content - Optional custom JSONL content (defaults to fixture)
 */
export function setupBeadsProject(tempDir: string, content?: string): void {
  const beadsDir = join(tempDir, ".beads")
  mkdirSync(beadsDir, { recursive: true })
  writeFileSync(join(beadsDir, "issues.jsonl"), content ?? getMockIssuesContent())
}

/**
 * Set up a non-beads project (no .beads directory)
 *
 * Creates a basic project structure without beads.
 */
export function setupNonBeadsProject(tempDir: string): void {
  // Just ensure the directory exists, no .beads
  mkdirSync(tempDir, { recursive: true })
}

/**
 * Create a mock shell function ($)
 *
 * Returns a tagged template function that simulates shell execution.
 */
export function createMockShell() {
  const shellFn = mock((strings: TemplateStringsArray, ...values: unknown[]) => {
    // Combine template literal parts
    const command = strings.reduce((acc, str, i) => {
      return acc + str + (values[i] ?? "")
    }, "")

    return {
      nothrow: () => ({
        quiet: () =>
          Promise.resolve({
            exitCode: 0,
            stdout: "",
            stderr: "",
          }),
      }),
      quiet: () =>
        Promise.resolve({
          exitCode: 0,
          stdout: "",
          stderr: "",
        }),
      text: () => Promise.resolve(""),
    }
  })

  // Add tagged template literal support
  return Object.assign(shellFn, {
    nothrow: () => shellFn,
    quiet: () => shellFn,
  })
}

/**
 * Create full mock PluginInput for testing
 */
export function createMockPluginInput(
  directory: string,
  overrides?: {
    client?: Partial<MockClient>
  }
): {
  client: MockClient
  directory: string
  $: ReturnType<typeof createMockShell>
} {
  const client = createMockClient()

  return {
    client: {
      ...client,
      ...overrides?.client,
    } as MockClient,
    directory,
    $: createMockShell(),
  }
}

/**
 * Clean up a test directory
 */
export function cleanupTestDir(tempDir: string): void {
  try {
    rmSync(tempDir, { recursive: true, force: true })
  } catch {
    // Ignore cleanup errors - directory may already be cleaned up by OS or previous test
  }
}
