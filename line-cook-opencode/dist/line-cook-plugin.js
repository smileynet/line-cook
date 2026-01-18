// @bun
// src/line-cook-plugin.ts
var LineCookPlugin = async ({ client, directory }) => {
  await client.app.log({
    body: {
      service: "line-cook",
      level: "info",
      message: "Plugin initialized",
      extra: {
        pluginVersion: "0.3.1",
        directory
      }
    }
  });
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
      }
    }
  };
};
async function handleSessionCreated(client, directory) {
  try {
    const beadsDir = Bun.file(`${directory}/.beads`);
    const hasBeads = await beadsDir.exists();
    if (hasBeads) {
      await client.app.log({
        body: {
          service: "line-cook",
          level: "info",
          message: "Beads-enabled project detected. Use /line-work to start workflow cycle.",
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
    const beadsDir = Bun.file(`${directory}/.beads`);
    const hasBeads = await beadsDir.exists();
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
export {
  LineCookPlugin
};
