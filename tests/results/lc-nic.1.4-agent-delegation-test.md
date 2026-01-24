# Agent Delegation Test Results

**Task:** lc-nic.1.4 - Test agent delegation
**Date:** 2026-01-24
**Platform:** Claude Code

## Summary

**Result: PARTIAL PASS** - Line Cook subagents are defined but not registered as Claude Code Task tool subagent types.

## Test Results

### Test 1: Taster Agent (Cook RED Phase)

**Expected:** Invoke `subagent_type="taster"` during TDD RED phase
**Actual:** `Agent type 'taster' not found`

**Status:** FAIL

**Available agents:** Bash, general-purpose, statusline-setup, Explore, Plan, claude-code-guide, beads:task-agent, code-reviewer, test-runner, config-auditor, doc-validator, python-craftsman, code-troubleshooter, skill-author, code-change-architect, hook-debugger, mcp-helper, claude-md-optimizer

### Test 2: Sous-Chef Agent (Serve Phase)

**Expected:** Invoke `subagent_type="sous-chef"` during serve phase
**Actual:** `Agent type 'sous-chef' not found`

**Status:** FAIL

### Test 3: Maître Agent (Plate Phase)

**Expected:** Invoke `subagent_type="maître"` during plate phase
**Actual:** `Agent type 'maître' not found`

**Status:** FAIL

### Test 4: Alternative - code-reviewer Agent

**Test:** Invoke the built-in `code-reviewer` agent
**Result:** Successfully invoked and returned code review

**Output format verified:**
- Summary with files reviewed and issues found
- Detailed assessment by category
- Positive notes
- Checklist summary
- Overall verdict

**Status:** PASS

### Test 5: Blocking Behavior with code-reviewer

**Test:** Provide code with command injection vulnerability
**Expected:** Agent should return BLOCKED verdict
**Result:** Agent correctly identified critical security issue and returned BLOCKED verdict

**Status:** PASS

## Root Cause Analysis

The Line Cook subagents (`taster`, `sous-chef`, `maître`) are defined in the `agents/` directory as markdown files, but they are **not registered** with Claude Code's Task tool system.

**Files exist:**
- `agents/taster.md` - Test quality review
- `agents/sous-chef.md` - Code review
- `agents/maitre.md` - BDD test review

**Commands reference them:**
- `commands/cook.md:116-124` - References `subagent_type="taster"`
- `commands/serve.md:60-90` - References `subagent_type="sous-chef"`
- `commands/plate.md:54-72` - References `subagent_type="maître"`

**Problem:** Claude Code's Task tool has a fixed list of subagent types. Plugin-defined agents in `agents/*.md` are not automatically registered as Task tool subagent types.

## Recommendations

### Option 1: Use Built-in Agents (Quick Fix)

Update commands to use available agents:
- `taster` → `code-reviewer` (partial match - reviews code, not test quality specifically)
- `sous-chef` → `code-reviewer` (good match)
- `maître` → `code-reviewer` or `doc-validator` (partial match)

**Pros:** Works immediately
**Cons:** Loses specialized behavior, `code-reviewer` doesn't focus on test quality or BDD patterns

### Option 2: Inline Agent Instructions (Medium Effort)

Instead of invoking named subagents, the commands can include the agent instructions inline in the Task prompt.

Example for cook.md:
```markdown
Task(description="Review test code for quality", prompt="You are a test quality specialist...

Review tests against these criteria:
- Isolated: Each test runs independently
- Fast: Tests complete quickly
...

[Full taster.md content embedded]

Review test code for <package>...", subagent_type="general-purpose")
```

**Pros:** Uses full agent instructions, works with existing Task tool
**Cons:** Larger prompts, duplicate content maintenance

### Option 3: Register Custom Agents (Long-term)

Investigate how to register custom subagent types with Claude Code. This may require:
- Plugin system changes
- Claude Code configuration
- Feature request to Anthropic

**Pros:** Clean solution, preserves agent definitions
**Cons:** May not be possible with current Claude Code capabilities

## Conclusion

The agent delegation system is **architecturally sound** but the implementation relies on subagent types that don't exist in Claude Code's Task tool.

**Immediate workaround:** Commands can be updated to use `code-reviewer` or `general-purpose` with embedded instructions.

**Finding to file:** The subagent architecture needs to be adapted to Claude Code's actual capabilities.
