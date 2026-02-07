import type { Plugin, Hooks, PluginInput } from "@opencode-ai/plugin"
import type { Event, Permission } from "@opencode-ai/sdk"
import { isDangerousCommand, shouldAutoApprove } from "./permission-utils"

/**
 * Formatter configurations: extension -> list of [formatter, args]
 * Each formatter is tried in order; first available one is used
 */
const FORMATTERS: Record<string, [string, string[]][]> = {
  ".py": [
    ["ruff", ["format", "{file}"]],
    ["ruff", ["check", "--fix", "{file}"]],
    ["black", ["{file}"]],
  ],
  ".ts": [["prettier", ["--write", "{file}"]], ["biome", ["format", "--write", "{file}"]]],
  ".tsx": [["prettier", ["--write", "{file}"]], ["biome", ["format", "--write", "{file}"]]],
  ".js": [["prettier", ["--write", "{file}"]], ["biome", ["format", "--write", "{file}"]]],
  ".jsx": [["prettier", ["--write", "{file}"]], ["biome", ["format", "--write", "{file}"]]],
  ".mjs": [["prettier", ["--write", "{file}"]]],
  ".cjs": [["prettier", ["--write", "{file}"]]],
  ".json": [["prettier", ["--write", "{file}"]]],
  ".yaml": [["prettier", ["--write", "{file}"]]],
  ".yml": [["prettier", ["--write", "{file}"]]],
  ".md": [["prettier", ["--write", "{file}"]]],
  ".go": [["goimports", ["-w", "{file}"]], ["gofmt", ["-w", "{file}"]]],
  ".rs": [["rustfmt", ["{file}"]]],
  ".sh": [["shfmt", ["-w", "{file}"]]],
  ".bash": [["shfmt", ["-w", "{file}"]]],
  ".rb": [["rubocop", ["-a", "{file}"]]],
  ".gd": [["gdformat", ["{file}"]]],
}

/**
 * Sensitive paths to skip formatting
 */
const SENSITIVE_PATTERNS = [
  ".env",
  ".git/",
  ".ssh/",
  "id_rsa",
  "id_ed25519",
  ".pem",
  "credentials",
  "secrets",
  ".key",
]

/**
 * Check if a path is safe to format (not sensitive)
 */
function isPathSafe(filePath: string): boolean {
  const pathLower = filePath.toLowerCase()
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pathLower.includes(pattern)) {
      return false
    }
  }
  return true
}

/**
 * Shell metacharacters that could enable command injection
 */
const SHELL_METACHARACTERS = /[;&|`$(){}[\]<>\\!#*?'"]/

/**
 * Check if a file path is safe for shell operations (no injection risk)
 */
function isPathSafeForShell(filePath: string): boolean {
  return !SHELL_METACHARACTERS.test(filePath)
}

/**
 * Get file extension from path
 */
function getExtension(filePath: string): string {
  const lastDot = filePath.lastIndexOf(".")
  if (lastDot === -1) return ""
  return filePath.slice(lastDot).toLowerCase()
}

/**
 * Run formatters on a file using the shell
 */
async function formatFile(
  $: PluginInput["$"],
  filePath: string,
  client: PluginInput["client"]
): Promise<string[]> {
  // Security: Reject paths with shell metacharacters to prevent injection
  if (!isPathSafeForShell(filePath)) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "warn",
        message: "Skipped formatting: path contains shell metacharacters",
        extra: { filePath },
      },
    })
    return []
  }

  const ext = getExtension(filePath)
  const formatters = FORMATTERS[ext]
  if (!formatters) return []

  const successful: string[] = []

  for (const [tool, args] of formatters) {
    try {
      // Check if tool exists (using command -v for better portability)
      const whichResult = await $`command -v ${tool}`.nothrow().quiet()
      if (whichResult.exitCode !== 0) continue

      // Run the formatter
      const cmdArgs = args.map((arg) => arg.replace("{file}", filePath))
      const result = await $`${tool} ${cmdArgs}`.nothrow().quiet()

      if (result.exitCode === 0) {
        successful.push(tool)
      }
    } catch (error) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: `Formatter ${tool} failed`,
          extra: { error: String(error), filePath },
        },
      })
    }
  }

  return successful
}

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
export const LineCookPlugin: Plugin = async ({ client, directory, $ }: PluginInput): Promise<Hooks> => {
  // NOTE: Do not await any API calls here - it causes a deadlock because:
  // 1. OpenCode loads plugins synchronously at server startup
  // 2. Plugin waits for API call to complete
  // 3. Server waits for plugin to finish before processing API requests
  // See: https://github.com/anthropics/claude-code/issues/XXX

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

        case "session.compacted":
          await handleSessionCompacted(client, directory, event.properties.sessionID)
          break

        case "session.error":
          await handleSessionError(
            client,
            directory,
            event.properties.sessionID,
            event.properties.error as SessionError | undefined
          )
          break
      }
    },

    /**
     * Tool execute before hook
     * Blocks dangerous bash commands before they execute
     */
    "tool.execute.before": async (
      input: { tool: string; sessionID: string; callID: string },
      output: { args: any }
    ): Promise<void> => {
      // Only check bash/shell commands
      if (input.tool.toLowerCase() !== "bash" && input.tool.toLowerCase() !== "shell") {
        return
      }

      const command = output.args?.command || output.args?.cmd || ""
      if (!command) return

      const { dangerous, pattern } = isDangerousCommand(command)
      if (dangerous) {
        await client.app.log({
          body: {
            service: "line-cook",
            level: "warn",
            message: "Blocked dangerous command",
            extra: {
              sessionID: input.sessionID,
              callID: input.callID,
              pattern,
              command: command.slice(0, 100),
            },
          },
        })

        // Throw to block the command execution
        throw new Error(
          `Command blocked by line-cook safety hook: matches dangerous pattern "${pattern}". ` +
            `Command: ${command.slice(0, 100)}${command.length > 100 ? "..." : ""}`
        )
      }
    },

    /**
     * Permission ask hook
     * Auto-approves read-only operations and beads commands,
     * while keeping manual approval for destructive operations
     */
    "permission.ask": async (
      input: Permission,
      output: { status: "ask" | "deny" | "allow" }
    ): Promise<void> => {
      const decision = shouldAutoApprove(input)

      if (decision === "allow") {
        output.status = "allow"
        await client.app.log({
          body: {
            service: "line-cook",
            level: "debug",
            message: "Auto-approved permission",
            extra: {
              permissionId: input.id,
              type: input.type,
              pattern: input.pattern,
              sessionID: input.sessionID,
            },
          },
        })
      } else if (decision === "deny") {
        output.status = "deny"
        await client.app.log({
          body: {
            service: "line-cook",
            level: "warn",
            message: "Auto-denied permission (dangerous operation)",
            extra: {
              permissionId: input.id,
              type: input.type,
              pattern: input.pattern,
              sessionID: input.sessionID,
            },
          },
        })
      }
      // If decision is "ask", leave output.status unchanged (defaults to "ask")
    },

    /**
     * Tool execute after hook
     * Auto-formats edited files after write/edit operations
     */
    "tool.execute.after": async (
      input: { tool: string; sessionID: string; callID: string },
      output: { title: string; output: string; metadata: any }
    ): Promise<void> => {
      // Only process file editing tools
      const toolLower = input.tool.toLowerCase()
      if (toolLower !== "edit" && toolLower !== "write" && toolLower !== "file_write") {
        return
      }

      // Get file path from metadata
      const filePath = output.metadata?.file_path || output.metadata?.filePath || output.metadata?.path
      if (!filePath) return

      // Skip sensitive paths
      if (!isPathSafe(filePath)) {
        await client.app.log({
          body: {
            service: "line-cook",
            level: "debug",
            message: "Skipped formatting sensitive file",
            extra: { filePath },
          },
        })
        return
      }

      // Check if file exists
      const file = Bun.file(filePath)
      if (!(await file.exists())) return

      // Run formatters
      const successful = await formatFile($, filePath, client)

      if (successful.length > 0) {
        // Append formatting info to output
        const formatInfo = `\n[Auto-formatted with: ${successful.join(", ")}]`
        output.output = (output.output || "") + formatInfo

        await client.app.log({
          body: {
            service: "line-cook",
            level: "info",
            message: "Auto-formatted file",
            extra: {
              filePath,
              formatters: successful,
              sessionID: input.sessionID,
            },
          },
        })
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
          message: "Beads-enabled project detected. Use /line-run to start workflow cycle.",
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

/**
 * Session error types from OpenCode SDK
 */
type SessionError =
  | { name: "ProviderAuthError"; data: { providerID: string; message: string } }
  | { name: "UnknownError"; data: { message: string } }
  | { name: "MessageOutputLengthError"; data: { [key: string]: unknown } }
  | { name: "MessageAbortedError"; data: { message: string } }
  | {
      name: "APIError"
      data: {
        message: string
        statusCode?: number
        isRetryable: boolean
        responseHeaders?: { [key: string]: string }
        responseBody?: string
      }
    }

/**
 * Error pattern definitions for common error types
 * Each pattern includes detection criteria and recovery suggestions
 */
const ERROR_PATTERNS: {
  name: string
  match: (error: SessionError) => boolean
  getSuggestion: (error: SessionError) => string
}[] = [
  {
    name: "Authentication Error",
    match: (error) => error.name === "ProviderAuthError",
    getSuggestion: (error) => {
      const providerID = error.name === "ProviderAuthError" ? error.data.providerID : "unknown"
      return `Check API key configuration for provider "${providerID}". Run: opencode config`
    },
  },
  {
    name: "Rate Limit",
    match: (error) =>
      error.name === "APIError" &&
      (error.data.statusCode === 429 ||
        error.data.message.toLowerCase().includes("rate limit") ||
        error.data.message.toLowerCase().includes("too many requests")),
    getSuggestion: () => "Wait before retrying. Consider switching to a different model or provider.",
  },
  {
    name: "Context Length Exceeded",
    match: (error) =>
      error.name === "MessageOutputLengthError" ||
      (error.name === "APIError" &&
        (error.data.message.toLowerCase().includes("context length") ||
          error.data.message.toLowerCase().includes("max tokens") ||
          error.data.message.toLowerCase().includes("too long"))),
    getSuggestion: () =>
      "Context limit reached. Run /compact to summarize conversation, or start a new session with /line-prep.",
  },
  {
    name: "Message Aborted",
    match: (error) => error.name === "MessageAbortedError",
    getSuggestion: () => "Message was interrupted. Re-run your last command or continue where you left off.",
  },
  {
    name: "Server Error",
    match: (error) =>
      error.name === "APIError" && error.data.statusCode !== undefined && error.data.statusCode >= 500,
    getSuggestion: (error) => {
      const isRetryable = error.name === "APIError" ? error.data.isRetryable : false
      return isRetryable
        ? "Server error occurred. The request can be retried automatically."
        : "Server error occurred. Try again later or switch to a different provider."
    },
  },
  {
    name: "Network/Connection Error",
    match: (error) =>
      error.name === "APIError" &&
      (error.data.message.toLowerCase().includes("network") ||
        error.data.message.toLowerCase().includes("connection") ||
        error.data.message.toLowerCase().includes("timeout") ||
        error.data.message.toLowerCase().includes("econnrefused")),
    getSuggestion: () => "Network error occurred. Check your internet connection and try again.",
  },
]

/**
 * Detect error pattern and return recovery suggestion
 */
function detectErrorPattern(error: SessionError): { patternName: string; suggestion: string } | null {
  for (const pattern of ERROR_PATTERNS) {
    if (pattern.match(error)) {
      return {
        patternName: pattern.name,
        suggestion: pattern.getSuggestion(error),
      }
    }
  }
  return null
}

/**
 * Handle session.error event
 * Detects common error patterns and provides recovery suggestions
 */
async function handleSessionError(
  client: PluginInput["client"],
  directory: string,
  sessionID: string | undefined,
  error: SessionError | undefined
): Promise<void> {
  try {
    const hasBeads = await hasBeadsEnabled(directory)

    // If no error object, just log the event
    if (!error) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "warn",
          message: "Session error event received without error details",
          extra: { sessionID, directory },
        },
      })
      return
    }

    // Detect error pattern
    const pattern = detectErrorPattern(error)
    const errorMessage = "message" in error.data ? (error.data as { message: string }).message : error.name

    // Show toast notification with recovery suggestion
    await client.tui.showToast({
      body: {
        title: pattern ? `Error: ${pattern.patternName}` : `Error: ${error.name}`,
        message: pattern ? pattern.suggestion : `An error occurred: ${errorMessage}`,
        variant: "error",
        duration: 10000,
      },
    })

    // Log detailed error information
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: pattern ? `Session error: ${pattern.patternName}` : `Session error: ${error.name}`,
        extra: {
          sessionID,
          directory,
          errorName: error.name,
          errorData: error.data,
          patternDetected: pattern?.patternName,
          suggestion: pattern?.suggestion,
          hasBeads,
        },
      },
    })

    // If beads is enabled and this is a significant error, suggest filing it
    if (hasBeads && (error.name === "APIError" || error.name === "UnknownError")) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Consider filing error as bead for tracking: bd create --title='Error: ...' --type=bug",
          extra: { sessionID },
        },
      })
    }
  } catch (err) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to handle session error",
        extra: { error: String(err), sessionID },
      },
    })
  }
}

/**
 * Handle session.compacted event
 * Notifies user about context preservation and suggests refreshing state
 *
 * Note: The beads workflow context is preserved during compaction via the
 * experimental.session.compacting hook. This event handler just notifies
 * the user that compaction completed and suggests next steps.
 */
async function handleSessionCompacted(
  client: PluginInput["client"],
  directory: string,
  sessionID: string
): Promise<void> {
  try {
    const hasBeads = await hasBeadsEnabled(directory)

    if (hasBeads) {
      // Show toast notification to user about context preservation
      await client.tui.showToast({
        body: {
          title: "Session Compacted",
          message: "Beads workflow context preserved. Run /line-prep to refresh task state.",
          variant: "info",
          duration: 8000,
        },
      })

      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Session compacted - beads workflow context preserved",
          extra: {
            sessionID,
            directory,
            preservedContext: [
              "SESSION CLOSE PROTOCOL",
              "Core beads rules",
              "Essential commands reference",
            ],
            suggestion: "Run /line-prep to refresh task state",
          },
        },
      })
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to handle session compaction",
        extra: { error: String(error), sessionID },
      },
    })
  }
}
