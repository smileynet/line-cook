// @bun
// src/permission-utils.ts
var SAFE_BASH_PATTERNS = [
  /^cat\s+/i,
  /^head\s+/i,
  /^tail\s+/i,
  /^less\s+/i,
  /^more\s+/i,
  /^file\s+/i,
  /^wc\s+/i,
  /^stat\s+/i,
  /^ls(\s|$)/i,
  /^dir(\s|$)/i,
  /^tree(\s|$)/i,
  /^pwd(\s|$)/i,
  /^grep\s+/i,
  /^rg\s+/i,
  /^find\s+.*-type\s+[fd]/i,
  /^find\s+.*-name\s+/i,
  /^which\s+/i,
  /^whereis\s+/i,
  /^locate\s+/i,
  /^fd\s+/i,
  /^git\s+status(\s|$)/i,
  /^git\s+log(\s|$)/i,
  /^git\s+diff(\s|$)/i,
  /^git\s+show(\s|$)/i,
  /^git\s+branch(\s|$)/i,
  /^git\s+remote\s+-v(\s|$)/i,
  /^git\s+tag(\s|$)/i,
  /^git\s+describe(\s|$)/i,
  /^git\s+rev-parse(\s|$)/i,
  /^git\s+ls-files(\s|$)/i,
  /^git\s+blame(\s|$)/i,
  /^bd\s+list(\s|$)/i,
  /^bd\s+show(\s|$)/i,
  /^bd\s+ready(\s|$)/i,
  /^bd\s+blocked(\s|$)/i,
  /^bd\s+stats(\s|$)/i,
  /^bd\s+search(\s|$)/i,
  /^bd\s+sync\s+--status(\s|$)/i,
  /^bd\s+doctor(\s|$)/i,
  /^date(\s|$)/i,
  /^whoami(\s|$)/i,
  /^hostname(\s|$)/i,
  /^uname(\s|$)/i,
  /^env(\s|$)/i,
  /^printenv(\s|$)/i,
  /^echo\s+\$/i,
  /^npm\s+list(\s|$)/i,
  /^npm\s+ls(\s|$)/i,
  /^npm\s+view(\s|$)/i,
  /^npm\s+info(\s|$)/i,
  /^npm\s+outdated(\s|$)/i,
  /^bun\s+pm\s+ls(\s|$)/i,
  /^pip\s+list(\s|$)/i,
  /^pip\s+show(\s|$)/i,
  /^cargo\s+tree(\s|$)/i,
  /^go\s+list(\s|$)/i
];
var SAFE_BASH_EXCLUSIONS = [
  /^find\s+.*-exec/i,
  /^find\s+.*-delete/i,
  /^find\s+.*-ok/i,
  /\|\s*rm\s/i,
  /\|\s*xargs\s+rm/i,
  /\|\s*tee\s/i,
  /\s>\s/,
  /\s>>\s/
];
var SAFE_TOOL_TYPES = new Set([
  "read",
  "glob",
  "grep",
  "list",
  "search"
]);
var DANGEROUS_PATTERNS = [
  /git\s+push.*--force/i,
  /git\s+reset.*--hard/i,
  /rm\s+-rf\s+\/\s*$/i,
  /rm\s+-rf\s+\/\*/i,
  /rm\s+-rf\s+\/[a-z]/i,
  /rm\s+-rf\s+~/i,
  /rm\s+-rf\s+\$HOME/i,
  /rm\s+-rf\s+%USERPROFILE%/i,
  /rmdir\s+\/s\s+\/q\s+C:\\/i,
  /del\s+\/f\s+\/s\s+\/q\s+C:\\/i,
  /format\s+[A-Z]:/i,
  /:\(\)\{\s*:\|:&\s*\};:/,
  />\s*\/dev\/sda/,
  /dd\s+if=.*of=\/dev\/sd/i,
  /mkfs\./i
];
function isDangerousCommand(command) {
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return { dangerous: true, pattern: pattern.source };
    }
  }
  return { dangerous: false };
}
function isSafeBashCommand(command) {
  const trimmed = command.trim();
  for (const exclusion of SAFE_BASH_EXCLUSIONS) {
    if (exclusion.test(trimmed)) {
      return false;
    }
  }
  for (const pattern of SAFE_BASH_PATTERNS) {
    if (pattern.test(trimmed)) {
      return true;
    }
  }
  return false;
}
function shouldAutoApprove(permission) {
  const { type, pattern, metadata } = permission;
  const toolType = type.toLowerCase();
  if (SAFE_TOOL_TYPES.has(toolType)) {
    return "allow";
  }
  if (toolType === "bash" || toolType === "shell") {
    const command = (typeof pattern === "string" ? pattern : pattern?.[0]) || metadata?.command || metadata?.cmd || "";
    if (!command) {
      return "ask";
    }
    const { dangerous } = isDangerousCommand(command);
    if (dangerous) {
      return "deny";
    }
    if (isSafeBashCommand(command)) {
      return "allow";
    }
  }
  return "ask";
}

// src/line-cook-plugin.ts
var FORMATTERS = {
  ".py": [
    ["ruff", ["format", "{file}"]],
    ["ruff", ["check", "--fix", "{file}"]],
    ["black", ["{file}"]]
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
  ".gd": [["gdformat", ["{file}"]]]
};
var SENSITIVE_PATTERNS = [
  ".env",
  ".git/",
  ".ssh/",
  "id_rsa",
  "id_ed25519",
  ".pem",
  "credentials",
  "secrets",
  ".key"
];
function isPathSafe(filePath) {
  const pathLower = filePath.toLowerCase();
  for (const pattern of SENSITIVE_PATTERNS) {
    if (pathLower.includes(pattern)) {
      return false;
    }
  }
  return true;
}
var SHELL_METACHARACTERS = /[;&|`$(){}[\]<>\\!#*?'"]/;
function isPathSafeForShell(filePath) {
  return !SHELL_METACHARACTERS.test(filePath);
}
function getExtension(filePath) {
  const lastDot = filePath.lastIndexOf(".");
  if (lastDot === -1)
    return "";
  return filePath.slice(lastDot).toLowerCase();
}
async function formatFile($, filePath, client) {
  if (!isPathSafeForShell(filePath)) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "warn",
        message: "Skipped formatting: path contains shell metacharacters",
        extra: { filePath }
      }
    });
    return [];
  }
  const ext = getExtension(filePath);
  const formatters = FORMATTERS[ext];
  if (!formatters)
    return [];
  const successful = [];
  for (const [tool, args] of formatters) {
    try {
      const whichResult = await $`command -v ${tool}`.nothrow().quiet();
      if (whichResult.exitCode !== 0)
        continue;
      const cmdArgs = args.map((arg) => arg.replace("{file}", filePath));
      const result = await $`${tool} ${cmdArgs}`.nothrow().quiet();
      if (result.exitCode === 0) {
        successful.push(tool);
      }
    } catch (error) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: `Formatter ${tool} failed`,
          extra: { error: String(error), filePath }
        }
      });
    }
  }
  return successful;
}
var BEADS_COMPACTION_CONTEXT = `## Beads Workflow Context (Preserve During Compaction)

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
- \`bd sync\` - Sync with git remote`;
async function hasBeadsEnabled(directory) {
  const issuesFile = Bun.file(`${directory}/.beads/issues.jsonl`);
  return issuesFile.exists();
}
var LineCookPlugin = async ({ client, directory, $ }) => {
  return {
    event: async ({ event }) => {
      switch (event.type) {
        case "session.created":
          await handleSessionCreated(client, directory);
          break;
        case "session.idle":
          await handleSessionIdle(client, directory);
          break;
        case "command.executed":
          await handleCommandExecuted(client, event.properties.name);
          break;
        case "file.edited":
          await handleFileEdited(client, event.properties.file);
          break;
        case "session.compacted":
          await handleSessionCompacted(client, directory, event.properties.sessionID);
          break;
        case "session.error":
          await handleSessionError(client, directory, event.properties.sessionID, event.properties.error);
          break;
      }
    },
    "tool.execute.before": async (input, output) => {
      if (input.tool.toLowerCase() !== "bash" && input.tool.toLowerCase() !== "shell") {
        return;
      }
      const command = output.args?.command || output.args?.cmd || "";
      if (!command)
        return;
      const { dangerous, pattern } = isDangerousCommand(command);
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
              command: command.slice(0, 100)
            }
          }
        });
        throw new Error(`Command blocked by line-cook safety hook: matches dangerous pattern "${pattern}". ` + `Command: ${command.slice(0, 100)}${command.length > 100 ? "..." : ""}`);
      }
    },
    "permission.ask": async (input, output) => {
      const decision = shouldAutoApprove(input);
      if (decision === "allow") {
        output.status = "allow";
        await client.app.log({
          body: {
            service: "line-cook",
            level: "debug",
            message: "Auto-approved permission",
            extra: {
              permissionId: input.id,
              type: input.type,
              pattern: input.pattern,
              sessionID: input.sessionID
            }
          }
        });
      } else if (decision === "deny") {
        output.status = "deny";
        await client.app.log({
          body: {
            service: "line-cook",
            level: "warn",
            message: "Auto-denied permission (dangerous operation)",
            extra: {
              permissionId: input.id,
              type: input.type,
              pattern: input.pattern,
              sessionID: input.sessionID
            }
          }
        });
      }
    },
    "tool.execute.after": async (input, output) => {
      const toolLower = input.tool.toLowerCase();
      if (toolLower !== "edit" && toolLower !== "write" && toolLower !== "file_write") {
        return;
      }
      const filePath = output.metadata?.file_path || output.metadata?.filePath || output.metadata?.path;
      if (!filePath)
        return;
      if (!isPathSafe(filePath)) {
        await client.app.log({
          body: {
            service: "line-cook",
            level: "debug",
            message: "Skipped formatting sensitive file",
            extra: { filePath }
          }
        });
        return;
      }
      const file = Bun.file(filePath);
      if (!await file.exists())
        return;
      const successful = await formatFile($, filePath, client);
      if (successful.length > 0) {
        const formatInfo = `
[Auto-formatted with: ${successful.join(", ")}]`;
        output.output = (output.output || "") + formatInfo;
        await client.app.log({
          body: {
            service: "line-cook",
            level: "info",
            message: "Auto-formatted file",
            extra: {
              filePath,
              formatters: successful,
              sessionID: input.sessionID
            }
          }
        });
      }
    },
    "experimental.session.compacting": async (input, output) => {
      try {
        const hasBeads = await hasBeadsEnabled(directory);
        if (hasBeads) {
          output.context.push(BEADS_COMPACTION_CONTEXT);
          await client.app.log({
            body: {
              service: "line-cook",
              level: "info",
              message: "Injected beads context for session compaction",
              extra: {
                sessionID: input.sessionID,
                directory
              }
            }
          });
        }
      } catch (error) {
        await client.app.log({
          body: {
            service: "line-cook",
            level: "error",
            message: "Failed to inject compaction context",
            extra: { error: String(error), sessionID: input.sessionID }
          }
        });
      }
    }
  };
};
async function handleSessionCreated(client, directory) {
  try {
    const hasBeads = await hasBeadsEnabled(directory);
    if (hasBeads) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Beads-enabled project detected. Use /line-run to start workflow cycle.",
          extra: {
            hasBeads: true,
            directory,
            suggestion: "Run /line-prep to sync state and see available work"
          }
        }
      });
    } else {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: "No .beads/ directory - workflow available but beads not initialized",
          extra: { directory }
        }
      });
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to detect beads project",
        extra: { error: String(error) }
      }
    });
  }
}
async function handleSessionIdle(client, directory) {
  try {
    const hasBeads = await hasBeadsEnabled(directory);
    if (hasBeads) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Session idle - remember to complete work with /line-tidy before ending",
          extra: {
            suggestion: "Run: git status && bd sync && git push",
            directory
          }
        }
      });
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log session idle",
        extra: { error: String(error) }
      }
    });
  }
}
async function handleCommandExecuted(client, command) {
  try {
    const isLineCommand = command.startsWith("/line-");
    if (isLineCommand) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: `Command executed: ${command}`
        }
      });
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log command execution",
        extra: { error: String(error), command }
      }
    });
  }
}
async function handleFileEdited(client, filePath) {
  try {
    const isBeadsFile = filePath.includes(".beads/");
    const isAgentsFile = filePath.endsWith("AGENTS.md");
    const isClaudeFile = filePath.endsWith("CLAUDE.md");
    if (isBeadsFile || isAgentsFile || isClaudeFile) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "debug",
          message: "Workflow file edited",
          extra: {
            filePath,
            fileType: isBeadsFile ? "beads" : isAgentsFile ? "agents" : "claude"
          }
        }
      });
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to log file edit",
        extra: { error: String(error), filePath }
      }
    });
  }
}
var ERROR_PATTERNS = [
  {
    name: "Authentication Error",
    match: (error) => error.name === "ProviderAuthError",
    getSuggestion: (error) => {
      const providerID = error.name === "ProviderAuthError" ? error.data.providerID : "unknown";
      return `Check API key configuration for provider "${providerID}". Run: opencode config`;
    }
  },
  {
    name: "Rate Limit",
    match: (error) => error.name === "APIError" && (error.data.statusCode === 429 || error.data.message.toLowerCase().includes("rate limit") || error.data.message.toLowerCase().includes("too many requests")),
    getSuggestion: () => "Wait before retrying. Consider switching to a different model or provider."
  },
  {
    name: "Context Length Exceeded",
    match: (error) => error.name === "MessageOutputLengthError" || error.name === "APIError" && (error.data.message.toLowerCase().includes("context length") || error.data.message.toLowerCase().includes("max tokens") || error.data.message.toLowerCase().includes("too long")),
    getSuggestion: () => "Context limit reached. Run /compact to summarize conversation, or start a new session with /line-prep."
  },
  {
    name: "Message Aborted",
    match: (error) => error.name === "MessageAbortedError",
    getSuggestion: () => "Message was interrupted. Re-run your last command or continue where you left off."
  },
  {
    name: "Server Error",
    match: (error) => error.name === "APIError" && error.data.statusCode !== undefined && error.data.statusCode >= 500,
    getSuggestion: (error) => {
      const isRetryable = error.name === "APIError" ? error.data.isRetryable : false;
      return isRetryable ? "Server error occurred. The request can be retried automatically." : "Server error occurred. Try again later or switch to a different provider.";
    }
  },
  {
    name: "Network/Connection Error",
    match: (error) => error.name === "APIError" && (error.data.message.toLowerCase().includes("network") || error.data.message.toLowerCase().includes("connection") || error.data.message.toLowerCase().includes("timeout") || error.data.message.toLowerCase().includes("econnrefused")),
    getSuggestion: () => "Network error occurred. Check your internet connection and try again."
  }
];
function detectErrorPattern(error) {
  for (const pattern of ERROR_PATTERNS) {
    if (pattern.match(error)) {
      return {
        patternName: pattern.name,
        suggestion: pattern.getSuggestion(error)
      };
    }
  }
  return null;
}
async function handleSessionError(client, directory, sessionID, error) {
  try {
    const hasBeads = await hasBeadsEnabled(directory);
    if (!error) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "warn",
          message: "Session error event received without error details",
          extra: { sessionID, directory }
        }
      });
      return;
    }
    const pattern = detectErrorPattern(error);
    const errorMessage = "message" in error.data ? error.data.message : error.name;
    await client.tui.showToast({
      body: {
        title: pattern ? `Error: ${pattern.patternName}` : `Error: ${error.name}`,
        message: pattern ? pattern.suggestion : `An error occurred: ${errorMessage}`,
        variant: "error",
        duration: 1e4
      }
    });
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
          hasBeads
        }
      }
    });
    if (hasBeads && (error.name === "APIError" || error.name === "UnknownError")) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Consider filing error as bead for tracking: bd create --title='Error: ...' --type=bug",
          extra: { sessionID }
        }
      });
    }
  } catch (err) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to handle session error",
        extra: { error: String(err), sessionID }
      }
    });
  }
}
async function handleSessionCompacted(client, directory, sessionID) {
  try {
    const hasBeads = await hasBeadsEnabled(directory);
    if (hasBeads) {
      await client.tui.showToast({
        body: {
          title: "Session Compacted",
          message: "Beads workflow context preserved. Run /line-prep to refresh task state.",
          variant: "info",
          duration: 8000
        }
      });
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
              "Essential commands reference"
            ],
            suggestion: "Run /line-prep to refresh task state"
          }
        }
      });
    }
  } catch (error) {
    await client.app.log({
      body: {
        service: "line-cook",
        level: "error",
        message: "Failed to handle session compaction",
        extra: { error: String(error), sessionID }
      }
    });
  }
}
export {
  LineCookPlugin
};
