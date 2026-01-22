# Subagent Research: Claude Code vs OpenCode
## OpenCode (Kiro) - Documented
- Has explicit subagent system with mode: 'subagent'
- Built-in subagents: General, Explore
- Invocation methods:
  - Automatic by primary agents based on descriptions
  - Manual via @mention
  - Task tool with permission.task configuration
- Configuration: JSON or Markdown in ~/.config/opencode/agents/ or .opencode/agents/
- Model can be overridden per subagent
- Tools and permissions can be restricted
- Hidden agents (hidden: true) excluded from @autocomplete

## Claude Code - Unknown
- Plugin system exists but subagent support unclear from docs
- Public docs returning 404 for subagent information
- No Task tool or explicit subagent delegation found
- Current plugin.json shows minimal configuration (name, description, version, author, repository, license, homepage, keywords)

## Key Differences
- OpenCode: Built-in agent system with subagent mode, Task tool, permission.task
- Claude Code: Plugin system without documented subagent support

## Implementation Options for Claude Code

### Option 1: Manual @mention in Commands

**Approach:**
- Use @mention syntax within slash commands
- Example: `@quality-control review this test`
- Requires subagent prompts to be accessible in context

**Pros:**
- Works with current Claude Code infrastructure
- No plugin changes needed
- Clear, explicit invocation

**Cons:**
- Not automatic (requires manual @mention)
- Unclear if @mention works inside slash commands
- No guarantee of reliability

**Status**: ⚠️ **Unverified** - Unknown if @mention works in this context

### Option 2: Subagent Slash Commands

**Approach:**
- Create separate slash commands for each subagent
- Example: `/line:quality-control`, `/line:sous-chef`
- Each command contains subagent prompt in frontmatter or file
- Reference in commands: `Use @quality-control skill` or similar

**Pros:**
- Works with current Claude Code infrastructure
- Clear, explicit invocation
- Can be tested independently

**Cons:**
- Not automatic delegation
- Requires user to know about each subagent command
- More commands to maintain

**Status**: ✅ **Feasible** - Follows existing command pattern

### Option 3: SKILL.md Pattern

**Approach:**
- Create subagent prompts as SKILL.md files in `.claude/` directory
- Reference in commands: `Use @quality-control skill` or similar
- Leverage Claude Code skills system
- Use file:// protocol to load skill

**Pros:**
- Leverages Claude Code skills system
- Reusable prompts
- Can be project-specific

**Cons:**
- Unclear how to invoke automatically from commands
- May require user knowledge of skill system
- Not automatic delegation

**Status**: ⚠️ **Uncertain** - Skill invocation mechanism unclear

### Option 4: Extend plugin.json (Future)

**Approach:**
- Wait for Claude Code to add native subagent support
- Extend plugin.json when available
- Follow OpenCode pattern for subagent definitions
- Implement automatic delegation

**Pros:**
- Native integration
- Automatic delegation
- Proper tool/permission control

**Cons:**
- Not currently supported
- Waiting for platform update
- Unclear timeline

**Status**: ❌ **Blocked** - Feature doesn't exist yet

### Option 5: Kiro CLI as Middleware (Alternative)

**Approach:**
- Use Kiro CLI for subagent delegation from Claude Code
- Call Kiro from Claude Code commands
- Integrate with OpenCode's Kiro agents
- Cross-platform subagent support

**Pros:**
- Works immediately with existing Kiro agents
- Same agent behavior across platforms
- Automatic delegation supported

**Cons:**
- Requires Kiro CLI dependency
- Adds external dependency
- More complex integration

**Status**: ✅ **Alternative** - Different approach, same agents

---

## Recommendations

### Immediate (Current State)

1. **Document limitation**: Update AGENTS.md to note Claude Code subagent limitation
2. **Use OpenCode for full automation**: Document that quality gates work fully in OpenCode but require manual invocation in Claude Code
3. **Create Claude Code subagent commands**: Implement Option 2 as fallback for Claude Code users
4. **Track platform feature requests**: Monitor Claude Code releases for subagent support

### Future (When Claude Code Adds Subagent Support)

1. **Extend plugin.json**: Add subagent definitions following OpenCode pattern
2. **Update commands**: Remove manual subagent commands, use native system
3. **Deprecate fallback**: Mark manual commands as legacy when native support arrives
4. **Test cross-platform**: Ensure quality gates work equally on both platforms

---

## Reference Implementation Notes

### OpenCode Kiro Agents (Already Implemented)

**quality-control.json:**
```json
{
  "name": "quality-control",
  "description": "Test quality specialist - ensures tests meet quality standards",
  "prompt": "file://.kiro/steering/quality-control.md",
  "tools": ["read", "write", "shell"],
  "allowedTools": ["read", "write", "shell"]
}
```

**sous-chef.json:**
```json
{
  "name": "sous-chef",
  "description": "Code review specialist - ensures code quality before commit",
  "prompt": "file://.kiro/steering/sous-chef.md",
  "tools": ["read", "write", "shell"],
  "allowedTools": ["read", "write", "shell"]
}
```

### Claude Code Commands (Current State)

**commands/cook.md:**
- Uses `Task tool` syntax (OpenCode/Kiro only)
- Won't work in Claude Code without subagent support

**commands/serve.md:**
- References subagent for code review
- No clear invocation mechanism for Claude Code

---

## Conclusion

OpenCode has a mature, documented subagent system with automatic delegation. Claude Code's subagent capabilities are undocumented and possibly non-existent.

**Short-term solution:** Create manual subagent slash commands for Claude Code with clear documentation that quality gates require manual invocation.

**Long-term solution:** Wait for Claude Code to add native subagent support, then extend plugin.json to match OpenCode's capabilities.

**Cross-platform strategy:** Use Kiro CLI as middleware for immediate cross-platform subagent support while waiting for Claude Code native support.
