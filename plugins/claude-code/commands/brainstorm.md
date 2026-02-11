---
description: Explore problem space before planning (divergent thinking)
allowed-tools: Bash, Read, Write, Glob, Grep, Task, AskUserQuestion, Skill, WebFetch, WebSearch
---


## Summary

**Divergent thinking phase: explore, question, research.** First phase of mise en place.

This phase focuses on understanding the problem before structuring a solution. Output is a brainstorm document that captures exploration, not a structured plan.

**Output:** `docs/planning/brainstorm-<name>.md`

**Arguments:** `$ARGUMENTS` (optional) - Topic or problem description to brainstorm

---

## Process

### Step 1: Understand the Problem

**If the user provided a topic or problem description:**
- Use it as the initial problem statement
- Proceed with exploration — skip asking "what should we brainstorm?"

**Otherwise:**
- Ask the user what they'd like to brainstorm

Ask clarifying questions to understand what we're solving:

**What problem are we solving?**
- What's the pain point?
- Who experiences this pain?
- What happens if we don't solve it?

**Who is the user?**
- Developer? End user? System?
- What's their context?
- What do they know/not know?

**What does success look like?**
- How will we know it works?
- What would the user be able to do?

**Use AskUserQuestion** if requirements are unclear. Do not assume.

### Step 2: Explore Technical Approaches

Research and explore different ways to solve the problem:

**Search the codebase:**
- Are there similar patterns we can follow?
- What existing code can we reuse or extend?
- What constraints does the existing architecture impose?

**Research external patterns:**
- How do other tools solve this?
- Are there standard approaches?
- What are the trade-offs?

**Use Task tool with Explore agent** for codebase research.

### Step 3: Identify Risks and Unknowns

Document what we don't know:

- Technical risks (performance, compatibility, complexity)
- Dependency risks (external services, libraries)
- Scope risks (feature creep, unclear boundaries)
- Open questions that need answers before planning

### Step 4: Recommend Direction

Based on exploration, provide a recommendation:

- **Recommended approach** with rationale
- **Alternatives considered** and why not chosen
- **Open questions** (if any remain)
- **Suggested scope** (MVP vs full feature vs epic)

### Step 5: Create Brainstorm Document

Write the brainstorm document to `docs/planning/brainstorm-<name>.md`.

**Use the template at `docs/templates/brainstorm.md`** as the starting point.

The document should include:
- Problem statement
- User perspective
- Technical approaches explored
- Risks and unknowns identified
- Recommended direction
- Open questions (if any)

### Step 5b: Create Planning Context Folder

Create `docs/planning/context-<name>/` with initial context files:

1. **Copy templates:**
   ```bash
   mkdir -p docs/planning/context-<name>
   cp docs/templates/planning-context/README.md docs/planning/context-<name>/README.md
   cp docs/templates/planning-context/architecture.md docs/planning/context-<name>/architecture.md
   cp docs/templates/planning-context/decisions.log docs/planning/context-<name>/decisions.log
   ```

2. **Populate README.md** — Fill in from brainstorm results:
   - Problem (2-3 sentences from problem statement)
   - Approach (chosen approach + rationale)
   - Key Decisions (major decisions made during brainstorm)
   - Set status to `brainstormed`
   - Set created date
   - Remove the "Usage Instructions" section from the copied template

3. **Populate architecture.md** — Fill in any technical patterns/constraints discovered during exploration

4. **Seed decisions.log** — Add brainstorm decisions:
   ```
   YYYY-MM-DD | brainstorm | <decision> | <rationale>
   ```

**Graceful fallback:** If `docs/templates/planning-context/` doesn't exist, create the files directly with minimal content.

### Step 6: Handoff

Output the brainstorm summary:

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/brainstorm-<name>.md
Context: docs/planning/context-<name>/

Problem: <1-sentence summary>
User: <who benefits>
Recommended approach: <1-sentence summary>

Key decisions:
  - <decision 1>
  - <decision 2>

Open questions: <N> (if any)
  - <question 1>
  - <question 2>
```

Then **use AskUserQuestion** to ask:

**Question:** "Brainstorm complete. How would you like to proceed?"
**Options:**
  - "Continue to /line:scope" — Create structured work breakdown now
  - "Review brainstorm first" — Stop here, review docs/planning/brainstorm-<name>.md
  - "Done for now" — End the planning session

If user chooses "Continue to /line:scope", invoke `Skill(skill="line:scope")`.
Otherwise, stop and output the artifact file paths.

---

## When to Skip Brainstorm

Skip this phase if:
- User has already done the exploration
- Requirements are crystal clear and well-documented
- It's a small, well-defined task (not an epic/feature)
- User explicitly asks to skip to planning

In these cases, proceed directly to `/line:scope`.

---

## Example Usage

```
/line:brainstorm
```

This command will:
1. Ask clarifying questions about the problem
2. Explore technical approaches
3. Identify risks and unknowns
4. Create brainstorm document
5. Output summary for review

---

## Example Output File

See `docs/templates/brainstorm.md` for the template structure.
