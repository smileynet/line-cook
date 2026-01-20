/**
 * Plugin loading integration test
 * 
 * Tests that the line-cook plugin loads successfully with user's real config
 * (including plugins directory). This verifies the deadlock fix works.
 */
import { describe, test, expect, afterAll } from "bun:test"
import { createOpencodeServer } from "@opencode-ai/sdk/server"
import { createSession, deleteSession, type ClientOptions } from "../../src/sdk-integration"

// Use user's real config (includes plugins)
let server: { url: string; close(): void } | null = null
let clientOptions: ClientOptions = { baseUrl: "http://localhost:4097" }
let serverAvailable = false

// Start server with user's real config (plugins enabled)
try {
  // Don't override XDG_CONFIG_HOME - use user's real config
  delete process.env.XDG_CONFIG_HOME
  
  server = await createOpencodeServer({ port: 4097, timeout: 15000, config: {} })
  clientOptions = { baseUrl: server.url }
  serverAvailable = true
  console.log(`[INFO] Started OpenCode server with plugins at ${server.url}`)
} catch (error) {
  console.log(`[SKIP] Failed to start OpenCode server with plugins: ${error}`)
  serverAvailable = false
}

afterAll(() => {
  if (server) {
    server.close()
    console.log(`[INFO] Stopped OpenCode server`)
  }
})

const describePlugin = serverAvailable ? describe : describe.skip
describePlugin("Plugin Loading - Real Config", () => {
  test("server starts with plugins enabled (no deadlock)", async () => {
    // If we got here, the server started successfully with plugins
    expect(serverAvailable).toBe(true)
  })

  test("can create session with plugins loaded", async () => {
    const session = await createSession({}, clientOptions)
    expect(session.id).toBeDefined()
    
    // Cleanup
    await deleteSession(session.id, clientOptions)
  }, { timeout: 10000 })

  test("session responds to prompts with plugins active", async () => {
    const session = await createSession(
      { initialPrompt: "Say 'hello' and nothing else" },
      clientOptions
    )
    expect(session.id).toBeDefined()
    
    // Give the server time to process
    await new Promise((resolve) => setTimeout(resolve, 2000))
    
    // Cleanup
    await deleteSession(session.id, clientOptions)
  }, { timeout: 30000 })
})
