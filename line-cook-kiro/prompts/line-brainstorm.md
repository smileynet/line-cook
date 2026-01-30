Explore problem space before planning (divergent thinking). First phase of mise en place.

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

**What does success look like?**
- How will we know it works?
- What would the user be able to do?

**Ask questions** if requirements are unclear. Don't assume.

### Step 2: Explore Technical Approaches

Research and explore different ways to solve the problem:

- Are there similar patterns in the codebase?
- What existing code can we reuse or extend?
- How do other tools solve this?
- What are the trade-offs?

### Step 3: Identify Risks and Unknowns

- Technical risks (performance, compatibility, complexity)
- Dependency risks (external services, libraries)
- Scope risks (feature creep, unclear boundaries)
- Open questions that need answers before planning

### Step 4: Recommend Direction

- **Recommended approach** with rationale
- **Alternatives considered** and why not chosen
- **Open questions** (if any remain)
- **Suggested scope** (MVP vs full feature vs epic)

### Step 5: Create Brainstorm Document

Write to `docs/planning/brainstorm-<name>.md` using template at `docs/templates/brainstorm.md`.

### Step 6: Output Summary

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/brainstorm-<name>.md

Problem: <1-sentence summary>
User: <who benefits>
Recommended approach: <1-sentence summary>

NEXT STEP: Run @line-plan to create structured work breakdown
```

## When to Skip

Skip if requirements are crystal clear. Proceed to @line-plan.
