import type { Plugin, Hooks, PluginInput } from "@opencode-ai/plugin"
import type { Event } from "@opencode-ai/sdk"

/**
 * Dangerous command patterns to block in tool.execute.before
 * These patterns match destructive operations that should never be run automatically
 */
const DANGEROUS_PATTERNS: RegExp[] = [
  /git\s+push.*--force/i,
  /git\s+reset.*--hard/i,
  /rm\s+-rf\s+\/\s*$/i,         // rm -rf / (root, end of command)
  /rm\s+-rf\s+\/\*/i,           // rm -rf /* (root wildcard)
  /rm\s+-rf\s+\/[a-z]/i,        // rm -rf /home, /etc, etc. (root subdirs)
  /rm\s+-rf\s+~/i,              // rm -rf ~ (home)
  /rm\s+-rf\s+\$HOME/i,         // rm -rf $HOME
  /rm\s+-rf\s+%USERPROFILE%/i,  // Windows home
  /rmdir\s+\/s\s+\/q\s+C:\\/i,  // Windows root delete
  /del\s+\/f\s+\/s\s+\/q\s+C:\\/i, // Windows recursive delete
  /format\s+[A-Z]:/i,           // Windows format drive
  /:\(\)\{\s*:\|:&\s*\};:/,     // Fork bomb
  />\s*\/dev\/sda/,             // Write to disk device
  /dd\s+if=.*of=\/dev\/sd/i,    // dd to disk
  /mkfs\./i,                    // Format filesystem
]

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
 * Check if a command matches any dangerous pattern
 */
function isDangerousCommand(command: string): { dangerous: boolean; pattern?: string } {
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return { dangerous: true, pattern: pattern.source }
    }
  }
  return { dangerous: false }
}

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
  // Log plugin initialization
  await client.app.log({
    body: {
      service: "line-cook",
      level: "info",
      message: "Plugin initialized",
      extra: {
        pluginVersion: "0.4.3",
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
