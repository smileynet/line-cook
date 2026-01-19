// @bun
// src/line-cook-plugin.ts
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
export {
  LineCookPlugin
};
