---
description: Record, list, or supersede architecture decisions (ADRs)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---


## Summary

**Manage architecture decision records (ADRs) for this project.** ADRs capture the "why" behind significant design choices - persistent, project-level decisions that guide future context recovery.

Storage: `docs/decisions/NNNN-slug.md` with YAML frontmatter and Nygard's 4-section format.

---

## Arguments

Parse the user's input to determine the action:

| Input | Action |
|-------|--------|
| *(empty or unrecognized)* | **Create** a new decision interactively |
| `list` | **List** all decisions with status |
| `show NNN` | **Show** a specific decision |
| `supersede NNN` | **Supersede** decision NNN with a new one |

---

## Create Flow (default)

### Step 1: Gather context

Ask the user:
- "What area does this decision affect?" with options: workflow, commands, architecture, testing, other

Then ask the user conversationally:
1. What's the context/situation motivating this decision?
2. What did you decide (and why)?
3. What are the consequences (positive and negative)?
4. Any related beads? (optional)
5. Any additional tags? (suggest based on area)

### Step 2: Determine next number

```bash
ls docs/decisions/[0-9]*.md 2>/dev/null | wc -l
```

Next number = count + 1, zero-padded to 4 digits (e.g., `0004`).

### Step 3: Create slug

Generate a URL-friendly slug from the decision title:
- Lowercase
- Replace spaces with hyphens
- Remove special characters
- Truncate to ~50 chars

Filename: `docs/decisions/NNNN-slugified-title.md`

### Step 4: Write the ADR file

Use this template structure:

```markdown
---
status: accepted
date: YYYY-MM-DD
tags: [area, ...]
relates-to: []
superseded-by: null
---

# NNNN: Decision title

## Context

[Context from user input — facts and forces at play]

## Decision

[What was decided and why — active voice]

## Consequences

- Positive: ...
- Negative: ...
- Neutral: ...
```

### Step 5: Update the index

Read `docs/decisions/README.md` and append a new row to the table:

```
| NNNN | Decision title | accepted | YYYY-MM-DD | tags |
```

### Step 6: Output confirmation

```
DECISION RECORDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/decisions/NNNN-slug.md
Status: accepted
Tags: area, ...

Title: Decision title

Related: lc-xyz (if any)

Total decisions: N (N accepted, N superseded, N deprecated)
```

---

## List Flow

When the user specified `list`:

1. Read `docs/decisions/README.md`
2. Also scan `docs/decisions/[0-9]*.md` files to get current status from frontmatter
3. Output formatted table:

```
ARCHITECTURE DECISIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

+ 0001  Use beads for issue tracking          [workflow]       2026-01-15
+ 0002  TDD workflow for cook phase            [testing]        2026-01-20
x 0003  Single context file (-> 0004)          [architecture]   2026-02-01
+ 0004  Progressive disclosure context folder  [architecture]   2026-02-03

Total: 4 (3 accepted, 1 superseded)
```

Use `+` for accepted, `x` for superseded, `-` for deprecated.

---

## Show Flow

When the user specified `show NNN`:

1. Find the file matching the number: `docs/decisions/NNN*.md` (pad to 4 digits)
2. Read and display the full ADR content
3. If not found, report error

---

## Supersede Flow

When the user specified `supersede NNN`:

### Step 1: Read existing ADR

Find and read `docs/decisions/NNN*.md` (pad to 4 digits). Display it.

### Step 2: Gather replacement context

Ask the user conversationally:
1. Why is the old decision being superseded?
2. What's the new decision?
3. What are the new consequences?

### Step 3: Update old ADR

Edit the old ADR's YAML frontmatter:
- Set `status: superseded`
- Set `superseded-by: NNNN` (the new ADR number)

### Step 4: Create new ADR

Follow the Create flow (Steps 2-6), but:
- Add context referencing the old decision: "This supersedes ADR NNNN because..."
- Include the old decision number in `relates-to`

### Step 5: Update index

Update the old decision's row to show `superseded` status and add the new decision row.

---

## Error Handling

- If `docs/decisions/` doesn't exist, create it and `docs/decisions/README.md` with the initial template
- If a decision number doesn't match any file, report clearly which number was requested and list available decisions
- If the user's input doesn't match any known action, default to the Create flow

---

## Notes

- ADRs are **never deleted** — only superseded or deprecated
- Keep ADRs concise: ~200-400 tokens each
- Tags should use lowercase, single-word terms where possible
- Date format: ISO 8601 (YYYY-MM-DD)
