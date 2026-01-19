import type { Plugin, Hooks, PluginInput } from "@opencode-ai/plugin"
import type { Event } from "@opencode-ai/sdk"

/**
 * Beads workflow context to preserve during session compaction.
 * This is injected into the compaction prompt to ensure beads state
 * and workflow instructions survive summarization.
 */
const BEADS_COMPACTION_CONTEXT = `## Beads Workflow Context (Preserve During Compaction)

**Context Recovery**: Run \`bd prime\` after compaction, clear, or new session.

### SESSION CLOSE PROTOCOL

Before saying "done" or "complete", run this checklist:

1. \`git status\` - check what changed
2. \`git add <files>\` - stage code changes
3. \`bd sync\` - commit beads changes
4. \`git commit -m "..."\` - commit code
5. \`bd sync\` - commit any new beads changes
6. \`git push\` - push to remote

**Work is NOT done until pushed.**

### Core Rules
- Track strategic work in beads (multi-session, dependencies, discovered work)
- Use \`bd create\` for issues, TodoWrite for simple single-session execution
- Git workflow: hooks auto-sync, run \`bd sync\` at session end
- Session management: check \`bd ready\` for available work

### Essential Commands
- \`bd ready\` - Show issues ready to work (no blockers)
- \`bd list --status=open\` - All open issues
- \`bd list --status=in_progress\` - Your active work
- \`bd show <id>\` - Detailed issue view with dependencies
- \`bd create --title="..." --type=task|bug|feature --priority=2\` - New issue
- \`bd update <id> --status=in_progress\` - Claim work
- \`bd close <id>\` - Mark complete
- \`bd sync\` - Sync with git remote`

/**
 * Check if a project has beads enabled by looking for the issues.jsonl file.
 * Using the JSONL file instead of the directory because Bun.file() is designed
 * for files, not directories.
 */
async function hasBeadsEnabled(directory: string): Promise<boolean> {
  const issuesFile = Bun.file(`${directory}/.beads/issues.jsonl`)
  return issuesFile.exists()
}

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

    /**
     * Session compacting hook
     * Injects beads workflow context before session summarization to preserve
     * critical workflow state across compaction.
     */
    "experimental.session.compacting": async (
      input: { sessionID: string },
      output: { context: string[]; prompt?: string }
    ): Promise<void> => {
      try {
        const hasBeads = await hasBeadsEnabled(directory)

        if (hasBeads) {
          // Inject beads workflow context to be preserved during compaction
          output.context.push(BEADS_COMPACTION_CONTEXT)

          await client.app.log({
            body: {
              service: "line-cook",
              level: "info",
              message: "Injected beads context for session compaction",
              extra: {
                sessionID: input.sessionID,
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
            message: "Failed to inject compaction context",
            extra: { error: String(error), sessionID: input.sessionID },
          },
        })
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
    const hasBeads = await hasBeadsEnabled(directory)

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
    const hasBeads = await hasBeadsEnabled(directory)

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
