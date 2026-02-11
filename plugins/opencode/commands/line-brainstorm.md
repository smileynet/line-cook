---
description: Explore problem space before planning (divergent thinking)
---


## Summary

**Divergent thinking phase: explore, question, research.** First phase of mise en place.

This phase focuses on understanding the problem before structuring a solution. Output is a brainstorm document that captures exploration, not a structured plan.

**Output:** `docs/planning/brainstorm-<name>.md`

---

## Process

### Step 1: Understand the Problem

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

**Ask questions** if requirements are unclear. Do not assume.

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

Structure the document with these sections: Problem Statement, User Perspective, Technical Exploration, Approaches Considered, Risks and Unknowns, Recommended Direction, Next Steps.

### Step 5b: Create Planning Context Folder

Create `docs/planning/context-<name>/` with initial context files:

1. Create `docs/planning/context-<name>/` directory
2. Create README.md with Problem, Approach, Key Decisions from brainstorm
3. Create architecture.md with technical patterns/constraints discovered
4. Create decisions.log with brainstorm decisions (`YYYY-MM-DD | brainstorm | <decision> | <rationale>`)

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
```

Then ask the user how they'd like to proceed:

- **Continue to /line-scope** — Create structured work breakdown now
- **Review brainstorm first** — Stop here, review docs/planning/brainstorm-<name>.md
- **Done for now** — End the planning session

Wait for the user's response before continuing. If user chooses to continue, run `/line-scope`.

---

## When to Skip Brainstorm

Skip this phase if:
- User has already done the exploration
- Requirements are crystal clear and well-documented
- It's a small, well-defined task (not an epic/feature)

In these cases, proceed directly to `/line-scope`.

---

## Example Usage

```
/line-brainstorm
```

