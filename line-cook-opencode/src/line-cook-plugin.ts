import type { Plugin, Hooks, PluginInput } from "@opencode-ai/plugin"
import type { Event } from "@opencode-ai/sdk"

/**
 * Line Cook Plugin for OpenCode
 *
 * Provides workflow orchestration for AI-assisted development:
 * - Auto-detection of beads-enabled projects (.beads/)
 * - Session lifecycle hooks for workflow guidance
 * - Command execution tracking
 */
export const LineCookPlugin: Plugin = async ({ client, directory }: PluginInput): Promise<Hooks> => {
  // Log plugin initialization
  await client.app.log({
    body: {
      service: "line-cook",
      level: "info",
      message: "Plugin initialized",
      extra: {
        pluginVersion: "0.3.1",
        directory,
      },
    },
  })

  return {
    /**
     * Event handler for all OpenCode events
     */
    event: async ({ event }: { event: Event }): Promise<void> => {
      switch (event.type) {
        case "session.created":
          await handleSessionCreated(client, directory)
          break

        case "session.idle":
          await handleSessionIdle(client, directory)
          break

        case "command.executed":
          await handleCommandExecuted(client, event.properties.name)
          break

        case "file.edited":
          await handleFileEdited(client, event.properties.file)
          break
      }
    },
  }
}

/**
 * Handle session.created event
 * Detects beads-enabled projects and provides workflow context
 */
async function handleSessionCreated(
  client: PluginInput["client"],
  directory: string
): Promise<void> {
  try {
    const beadsDir = Bun.file(`${directory}/.beads`)
    const hasBeads = await beadsDir.exists()

    if (hasBeads) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Beads-enabled project detected. Use /line-work to start workflow cycle.",
          extra: {
            hasBeads: true,
            directory,
            suggestion: "Run /line-prep to sync state and see available work",
          },
        },
      })
    } else {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: "No .beads/ directory - workflow available but beads not initialized",
          extra: { directory },
        },
      })
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to detect beads project",
        extra: { error: String(error) },
      },
    })
  }
}

/**
 * Handle session.idle event
 * Reminds about session completion protocol
 */
async function handleSessionIdle(
  client: PluginInput["client"],
  directory: string
): Promise<void> {
  try {
    const beadsDir = Bun.file(`${directory}/.beads`)
    const hasBeads = await beadsDir.exists()

    if (hasBeads) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Session idle - remember to complete work with /line-tidy before ending",
          extra: {
            suggestion: "Run: git status && bd sync && git push",
            directory,
          },
        },
      })
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log session idle",
        extra: { error: String(error) },
      },
    })
  }
}

/**
 * Handle command.executed event
 * Tracks usage of line-cook commands
 */
async function handleCommandExecuted(
  client: PluginInput["client"],
  command: string
): Promise<void> {
  try {
    const isLineCommand = command.startsWith("/line-")

    if (isLineCommand) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: `Command executed: ${command}`,
        },
      })
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log command execution",
        extra: { error: String(error), command },
      },
    })
  }
}

/**
 * Handle file.edited event
 * Tracks edits to workflow-related files
 */
async function handleFileEdited(
  client: PluginInput["client"],
  filePath: string
): Promise<void> {
  try {
    const isBeadsFile = filePath.includes(".beads/")
    const isAgentsFile = filePath.endsWith("AGENTS.md")
    const isClaudeFile = filePath.endsWith("CLAUDE.md")

    if (isBeadsFile || isAgentsFile || isClaudeFile) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: "Workflow file edited",
          extra: {
            filePath,
            fileType: isBeadsFile ? "beads" : isAgentsFile ? "agents" : "claude",
          },
        },
      })
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log file edit",
        extra: { error: String(error), filePath },
      },
    })
  }
}
