**You are now executing this workflow.** Begin immediately with Step 1. Do not summarize, describe, or explain what you will do — just do it. If the user included any text in their message, that text is the input argument — use it directly, do not ask for it again.

## Summary

**Experiential thinking phase: walk through, question, sketch.** Second phase of mise en place.

This phase validates the recommended approach by walking through concrete user experience scenarios before structuring the work. Think of it as a lo-fi simulation — you experience the product through 5 beats, creating interaction sketches and catching UX problems early.

**Input:** Brainstorm document (optional) or direct requirements
**Output:** `docs/planning/walkthrough-<name>.md`

**Arguments:** `$ARGUMENTS` (optional) - Topic, brainstorm path, or software type override

---

## Process

### Step 1: Load Context & Detect Software Type

Look for brainstorm documents or context folders. If found, read and use as the basis for the walkthrough. If neither exists, ask the user for requirements.

**Detect software type** from the brainstorm or codebase:


| Type | Sketch Format | Example |
|------|--------------|---------|
| CLI | Shell command/output blocks | `$ mytool deploy --env=prod` |
| Web | ASCII wireframe boxes | `+--Header--+ | Content | +----------+` |
| API | Request/response pairs | `POST /api/v1/items -> 201 Created` |
| Library | Code usage examples | `client = Client(); result = client.process(data)` |
| TUI | Terminal panel mockups | `+--Status--+ +--Log--+` |
| Mobile | Screen flow descriptions | `[Home] -> tap "Add" -> [Form Screen]` |

Set the sketch format for all beats based on the detected type.

### Step 2: Establish Persona Lens

Before walking through beats, establish who the user is. Present this to the user and ask them to confirm or adjust:

- **Who is this person?** (role, experience level, context)
- **What do they already know?** (technical background, domain expertise)
- **What are they trying to accomplish?** (concrete goal, not abstract need)
- **What's their environment?** (device, time pressure, interruptions)

This anchors every beat in a specific scenario. If the brainstorm identified multiple user types, pick the primary one for the walkthrough.


### Step 3: Walk Through 5 Experience Beats

Walk through each beat interactively, one at a time. Each beat follows the same cycle.

**The 5 Beats:**

| Beat | Name | Focus |
|------|------|-------|
| 1 | **First Encounter** | First 60 seconds: install/launch/sign-up, first screen, first action |
| 2 | **Discovery** | How they learn the core capability, first success, feedback |
| 3 | **Core Workflow** | Complete happy-path cycle of the main use case |
| 4 | **Edge Cases & Recovery** | Most likely error, what it looks like, how to recover |
| 5 | **Return & Mastery** | Why come back, power-user workflow, advanced features |

**Each beat follows this cycle:**

1. **Present the moment** — Describe the scenario and ask 2-4 concrete questions. Act as a sidekick, not a director.

2. **User responds** with their vision.

3. **Create an interaction sketch** in the detected software type's format.

4. **Apply the 4 cognitive walkthrough questions:**
   - Q1: Would the user try to do this?
   - Q2: Would the user find the action?
   - Q3: Would the user understand the label?
   - Q4: Would the user know it worked?

   Flag failures and suggest fixes.

5. **Record decisions with provenance:** `user`, `suggested`, or `inferred`.

**Rubber-stamp guard:** If 3+ consecutive decisions have provenance `suggested`, pause and prompt the user to drive.

### Step 4: Anti-Pattern Review

After all 5 beats, review the full walkthrough against this anti-pattern taxonomy:

| Anti-Pattern | What to catch | Fix |
|---|---|---|
| Too abstract | "User finds it intuitive" | Describe specific actions and responses |
| Too technical | Implementation details exposed | Describe what user sees, not how it works |
| Missing errors | Only happy path covered | Must include at least one failure scenario |
| Feature listing | Feature salad without narrative | Narrate one discovery at a time |
| Emotion prescribing | "User feels satisfied" | Describe what happens, not how they feel |
| Missing interactions | Outcomes without HOW | Fill in the interaction sketch |
| Invisible actions | User can't find the control | Verify discoverability in sketch (CW Q2) |
| No feedback | Action succeeds silently | Add confirmation/progress indicator (CW Q4) |
| Wrong mental model | User wouldn't attempt this | Reframe the workflow (CW Q1) |
| Unclear labels | User wouldn't click that | Verify label matches user's vocabulary (CW Q3) |

Flag any issues found and suggest specific fixes. For cognitive walkthrough failures (Q1-Q4), propose concrete UX changes.

### Step 5: Validate Scenario Checklist

Verify the walkthrough covers all essential elements:

- [ ] Persona established with concrete context
- [ ] First 60 seconds described with specific actions
- [ ] First error/failure described with recovery path
- [ ] Complete core workflow cycle narrated step-by-step
- [ ] Every primary interface element mentioned in a sketch
- [ ] A reason to return/continue present
- [ ] No beat prescribes emotions — actions only
- [ ] All 4 cognitive walkthrough questions pass for core workflow

If any item fails, go back and address it before writing the document.

### Step 6: Write Walkthrough Document

Write the walkthrough to `docs/planning/walkthrough-<name>.md` with this structure:

```markdown
# Walkthrough: <name>

## Persona Lens

- **Who:** <role, experience level, context>
- **Knows:** <technical background, domain expertise>
- **Goal:** <concrete goal>
- **Environment:** <device, time pressure, interruptions>

## Software Type: <type>

---

## Beat 1: First Encounter
### Narrative
<what happens in the first 60 seconds>

### Interaction Sketch
<sketch in the appropriate format>

### Cognitive Walkthrough
- Q1 (Right goal): PASS/FAIL — <notes>
- Q2 (Visibility): PASS/FAIL — <notes>
- Q3 (Label clarity): PASS/FAIL — <notes>
- Q4 (Feedback): PASS/FAIL — <notes>

### Decisions
| # | Decision | Provenance |
|---|----------|------------|
| 1 | ... | user/suggested/inferred |

---

## Beat 2: Discovery
<same structure>

## Beat 3: Core Workflow
<same structure>

## Beat 4: Edge Cases & Recovery
<same structure>

## Beat 5: Return & Mastery
<same structure>

---

## Decision Summary

| # | Decision | Beat | Provenance |
|---|----------|------|------------|
| 1 | ... | 1 | user |
| 2 | ... | 1 | suggested |
| ... | ... | ... | ... |

## Scenario Checklist
- [x] Persona established with concrete context
- [x] First 60 seconds described with specific actions
- ...

## Anti-Pattern Review
<any issues found and fixes applied>
```

### Step 6b: Update Planning Context

If a planning context folder exists (`docs/planning/context-<name>/`):

1. **Update README.md** — Set status to `sampled`
2. **Append to decisions.log:**
   ```
   YYYY-MM-DD | sample | <decision> | <rationale>
   ```

### Step 7: Handoff

Output the walkthrough summary:

```
WALKTHROUGH COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

File: docs/planning/walkthrough-<name>.md

Persona: <who> — <goal>
Software type: <type>
Beats: 5/5
Decisions: <N> (user: <X>, suggested: <Y>, inferred: <Z>)

CW Validation:
  Beat 1: PASS / <N issues>
  Beat 2: PASS / <N issues>
  Beat 3: PASS / <N issues>
  Beat 4: PASS / <N issues>
  Beat 5: PASS / <N issues>

Anti-patterns found: <N>
Checklist: <N>/8 passing
```

Then ask the user how they'd like to proceed:

- **Continue to @line-scope** — Create structured work breakdown now
- **Review walkthrough first** — Stop here, review docs/planning/walkthrough-<name>.md
- **Done for now** — End the planning session

Wait for the user's response before continuing. If user chooses to continue, run `@line-scope`.

---

## When to Skip Sample

Skip this phase if:
- UX is already documented or designed
- Backend-only work with no user-facing interface
- Small, well-defined task (not exploring new UX)

In these cases, proceed directly to `@line-scope`.

---

## Example Usage

```
@line-sample
```

