# Proposal: Integrating Line Cook with Daedalus

**Status**: Draft
**Date**: 2026-02-25
**Author**: Cross-project analysis
**Scope**: How Line Cook could adopt Daedalus's principles and breadth

---

## Motivation

Line Cook provides disciplined execution: the Mise Cycle turns ideas into tasks, the Run Cycle ships them with TDD and AI peer review, and the Loop Cycle automates the whole thing. Its weakness is that it has no pre-execution quality agreement, no behavioral patterns for AI communication, no security-first principle, no structured onboarding for unfamiliar codebases, and it only works for code.

Daedalus provides universal principles (quality standards, specification-first, verification mindset, security-first) and multi-domain patterns (development, writing, academic, research). Its Three-Tier quality agreement (ASK/OFFER/CONFIRM) prevents "working but not good" outcomes. Its mode system adapts the same core principles to different types of knowledge work.

This proposal describes five integration points where Line Cook could adopt Daedalus's principles without losing its identity as a workflow engine.

---

## 1. Add Pre-Execution Quality Agreement to Mise

### Problem

Line Cook's Mise Cycle moves from brainstorm to scope without a deliberate checkpoint for agreeing on quality expectations. The brainstorm document captures what to build and how, but not what "good" looks like. This means quality standards are implicit — they depend on whatever the AI infers from context.

Daedalus's Three-Tier approach (`ASK/OFFER/CONFIRM`) from `quality-standards.md` solves this by making the quality conversation explicit before work begins.

### Proposal

Insert an ASK/OFFER/CONFIRM step at the brainstorm-to-scope pause point. This is not a new phase — it fits inside the existing pause between brainstorm and scope (ADR-0008).

**During `/line:brainstorm` completion:**

After the "Recommended Direction" section is written, and before the user is prompted to continue to scope, the AI asks:

```
BRAINSTORM COMPLETE
━━━━━━━━━━━━━━━━━━━
File: docs/planning/brainstorm-auth-system.md
Open questions: 0

QUALITY AGREEMENT
━━━━━━━━━━━━━━━━━
Before we scope this work, let's agree on quality expectations:

  Reference: Is there an existing feature whose quality level we should match?
  Level: Prototype (functional, rough edges) or Production (polished, tested)?
  Standards: Any specific requirements? (performance targets, test coverage, etc.)

[User responds]

Agreement recorded in brainstorm doc.
Continue to /line:scope? [Y/n]
```

**Record in brainstorm document:**

Add a "Quality Agreement" section to `docs/templates/brainstorm.md`:

```markdown
## Quality Agreement

**Reference**: [existing feature or "none"]
**Level**: [Prototype | Production | Excellence]
**Standards**:
- [Standard 1]
- [Standard 2]

**Agreed**: [date]
```

**Flow into scope:** The scope phase reads the quality agreement and uses it to set acceptance criteria precision. A "Production" agreement generates stricter acceptance criteria than a "Prototype" agreement.

### What Not to Do

Do not create a separate quality-agreement phase or slash command. The agreement is a conversation that happens at an existing pause point. Adding a phase would violate the Mise Cycle's three-phase design (ADR-0008).

---

## 2. Create a `daedalus-spice`

### Problem

Daedalus's principles are valuable during Line Cook's planning and execution but are currently locked in a separate repository. An AI using Line Cook cannot access them unless someone manually references the framework.

### Proposal

Create a `daedalus-spice` following ADR-0014's spice architecture: a separate GitHub repository with five skills that inject Daedalus's principles into Line Cook's workflow.

**Repository:** `github.com/smileynet/daedalus-spice`

**Structure:**
```
daedalus-spice/
  .claude-plugin/
    plugin.json
  skills/
    quality-agreement/SKILL.md       — Three-Tier ASK/OFFER/CONFIRM protocol
    verification-mindset/SKILL.md    — "Always verify, never assume" checks
    security-first/SKILL.md          — Day-one security checklist
    spec-completeness/SKILL.md       — Specification component checklist
    session-continuity/SKILL.md      — Beads + session summary hybrid approach
```

**Marketplace registration** (added to `.claude-plugin/marketplace.json`):
```json
{
  "name": "daedalus-spice",
  "source": {
    "source": "url",
    "url": "https://github.com/smileynet/daedalus-spice.git"
  },
  "description": "Daedalus Framework principles — quality agreement, verification mindset, security-first, specification completeness, and session continuity",
  "category": "domain-knowledge",
  "tags": ["quality", "spice", "principles", "security", "planning"]
}
```

**Installation:**
```
/plugin install daedalus-spice@line-cook
```

### Skill Details

**`quality-agreement.md`**
- **Triggers during:** `/line:brainstorm`, `/line:scope`
- **Teaches:** The Three-Tier ASK/OFFER/CONFIRM protocol for establishing quality expectations before work begins
- **Source:** Daedalus `framework/core-universal/quality-standards.md`

**`verification-mindset.md`**
- **Triggers during:** `/line:cook`, `/line:serve`
- **Teaches:** Verify actual state before making decisions. Check real behavior, not documented behavior. Find root causes, not symptoms.
- **Source:** Daedalus `framework/core-universal/verification-mindset.md`

**`security-first.md`**
- **Triggers during:** `/line:serve`
- **Teaches:** Security is a day-one responsibility. Provides the checklist: data at rest, data in transit, access control, application security.
- **Source:** Daedalus `framework/core-universal/GOLDEN_RULES.md` (Rule #5)

**`spec-completeness.md`**
- **Triggers during:** `/line:scope`
- **Teaches:** Every specification needs five components: requirements, design, quality standards, success criteria, and constraints. Checks the menu plan against this list.
- **Source:** Daedalus `framework/core-universal/specification-first.md`

**`session-continuity.md`**
- **Triggers during:** `/line:prep`, `/line:tidy`
- **Teaches:** Use beads for structured state tracking and prose summaries for context and lessons learned. Neither alone is sufficient.
- **Source:** Daedalus `framework/core-universal/session-workflow.md`

### What Not to Do

Do not embed workflow logic, slash commands, or agent definitions in the spice. Per ADR-0014, spices are pure knowledge — skills that enhance existing workflow phases. The daedalus-spice must not depend on Daedalus being installed or cloned locally.

---

## 3. Extend to Non-Code Domains via Mode-Aware Spices

### Problem

Line Cook's Mise and Run cycles are designed for code: TDD in Cook, code review in Serve, conventional commits in Tidy. But the planning abstractions (brainstorm, scope, finalize) and the execution discipline (one task at a time, quality gates, file don't block) are domain-agnostic. Users doing writing, academic, or research work currently have no structured workflow.

Daedalus already has mode-specific patterns for writing (`framework/modes/writing/`), academic (`framework/modes/academic/`), and research (`framework/modes/research/`), each with quality gates, workflows, and templates.

### Proposal

Create mode-aware spices that adapt Line Cook's vocabulary and phases for non-code work:

**`writing-spice`** — Technical writing, blog posts, documentation

| Run Phase | Code (default) | Writing Adaptation |
|-----------|---------------|-------------------|
| Prep | Sync git, show tasks | Sync git, show sections to write |
| Cook | TDD (Red-Green-Refactor) | Draft (Outline-Draft-Revise) |
| Serve | Code review (sous-chef) | Editorial review (clarity, accuracy, audience) |
| Tidy | Conventional commit | Commit with section status |

Mise adaptations:
- Brainstorm: Audience analysis, topic exploration, angle selection
- Scope: Article outline as menu plan (sections = features, paragraphs = tasks)
- Finalize: Beads per section, acceptance criteria = editorial checklist

**`academic-spice`** — Research papers, dissertations, teaching materials

| Run Phase | Code (default) | Academic Adaptation |
|-----------|---------------|---------------------|
| Prep | Sync git, show tasks | Sync git, show sections/chapters to write |
| Cook | TDD | Research-Draft-Cite (gather sources, draft section, verify citations) |
| Serve | Code review | Academic review (rigor, methodology, citations, structure) |
| Tidy | Conventional commit | Commit with IMRaD section status |

**`research-spice`** — Literature reviews, analysis, synthesis

| Run Phase | Code (default) | Research Adaptation |
|-----------|---------------|---------------------|
| Prep | Sync git, show tasks | Sync git, show sources to analyze |
| Cook | TDD | Search-Collect-Analyze (find sources, extract data, synthesize) |
| Serve | Code review | Research quality review (comprehensiveness, source quality, bias) |
| Tidy | Conventional commit | Commit with analysis status |

### Implementation Approach

Each mode-spice is a separate repository following ADR-0014:

```
writing-spice/
  .claude-plugin/
    plugin.json
  skills/
    writing-workflow/SKILL.md        — Outline-Draft-Revise cycle
    writing-quality-gates/SKILL.md   — Editorial review checklist
    writing-decomposition/SKILL.md   — Article → Section → Paragraph hierarchy
```

The spices do not modify Line Cook's commands or agents. They provide domain knowledge that the existing agents use when reviewing non-code work. For example, the sous-chef agent already reviews for "correctness, security, style, completeness" — a writing-spice skill redefines those dimensions as "accuracy, sensitivity, clarity, coverage" when the project contains primarily markdown/text files.

### What Not to Do

Do not fork Line Cook for each domain. Do not create separate `/write:cook` or `/research:prep` commands. The same `/line:run` cycle works; the spice changes what the agents look for, not how the workflow operates.

---

## 4. Add Structured Onboarding Beyond Beads

### Problem

Line Cook's `/line:prep` syncs state and shows ready tasks, but it does not orient a new AI instance to the project's architecture, conventions, or history. Beads tell the AI what to do next but not why the project is structured the way it is. For unfamiliar codebases, the AI may make changes that are technically correct but architecturally wrong.

Daedalus addresses this with a mandatory onboarding protocol (`framework/core-universal/onboarding-protocol.md`) that takes 10-30 minutes. That is too heavy for Line Cook's "sync and go" philosophy, but a lightweight version would help.

### Proposal

Add an optional project context document that `/line:prep` displays when it exists:

**File:** `docs/project-context.md` (50-100 lines, maintained by the team)

**Template:**
```markdown
# Project Context

## What This Project Does
[2-3 sentences: what it is, who it's for, what problem it solves]

## Architecture Overview
[Key directories, main data flow, 3-5 bullet points]

## Conventions
[Naming patterns, test structure, commit style — things not in linters]

## Things That Will Bite You
[Non-obvious gotchas, known quirks, "don't touch X because Y"]

## Recent Direction
[What the last 2-3 sessions focused on, current priorities]
```

**Integration with Prep:**

When `/line:prep` runs, if `docs/project-context.md` exists, display a summary:

```
SESSION: reading-cli @ main
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Context: CLI tool for tracking reading lists. JSON file storage.
         Gotchas: File locking not implemented yet.

Sync: up to date
Ready: 3 tasks
```

**Integration with Tidy:**

During `/line:tidy`, if the "Recent Direction" section is stale (last updated >3 sessions ago), prompt the user to update it.

### What Not to Do

Do not implement Daedalus's full 10-30 minute onboarding protocol. Line Cook's value proposition is "sync and go" — the context document must be skimmable in 30 seconds. Do not make it mandatory; projects that don't need it should not be nagged.

---

## 5. Surface Security as First-Class in Serve

### Problem

Line Cook's sous-chef agent reviews for correctness, security, style, and completeness. But "security" is one bullet among four — it carries the same weight as style. Daedalus's Golden Rule #5 ("Security is a Day One Responsibility") treats security as non-negotiable: it cannot be deferred, compromised for convenience, or traded off against other concerns.

### Proposal

Give security a dedicated section in the sous-chef review output and make security BLOCK verdicts non-overridable.

**Changes to sous-chef agent template:**

Add a dedicated security section to the review output:

```
REVIEW: sous-chef
━━━━━━━━━━━━━━━━━

Correctness: PASS
  - Logic verified, edge cases handled

Security: PASS
  - No injection vectors
  - Input validation present
  - No hardcoded credentials
  - Encryption at rest/transit verified (if applicable)

Style: PASS
  - Naming consistent, code readable

Completeness: PASS
  - All acceptance criteria met

Verdict: APPROVED
```

**Security BLOCK verdicts:**

When the sous-chef identifies a security issue, the verdict is BLOCKED and cannot be overridden by the user during that Serve phase. The user must fix the issue and re-serve.

Security issues that trigger BLOCK:
- Hardcoded credentials or secrets
- SQL injection, XSS, or command injection vectors
- Missing input validation on user-facing endpoints
- Disabled encryption where data sensitivity requires it
- Overly permissive access controls (e.g., `chmod 777`, `*` IAM policies)

**Security tier configuration:**

For projects with different security needs, set the tier in project config (e.g., `CLAUDE.md` or `.line-cook.yaml`):

| Tier | Checks |
|------|--------|
| `basic` | Input validation, no hardcoded secrets |
| `standard` (default) | + encryption, access control |
| `strict` | + OWASP top 10, dependency audit |

The sous-chef reads the configured tier and adjusts its security review depth accordingly.

### What Not to Do

Do not make every security concern a BLOCK. False positives erode trust. Only block on clear, unambiguous vulnerabilities. Style-level security suggestions (like preferring `===` over `==`) should remain NEEDS_CHANGES, not BLOCKED.

---

## "Better Together" Combined Workflow

```
                    DAEDALUS PRINCIPLES
                    (knowledge base)
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
Quality Standards   Verification         Security-First
(ASK/OFFER/CONFIRM) (never assume)       (day one)
    │                    │                    │
    └────────┬───────────┘                    │
             │                                │
             ▼                                │
    LINE COOK MISE CYCLE                      │
    ┌─────────────────────┐                   │
    │ Brainstorm (diverge) │                  │
    │   + quality agreement │◄────────────────┘
    │ Scope (converge)      │
    │   + spec completeness │
    │ Finalize (commit)     │
    └──────────┬────────────┘
               │
               ▼
    LINE COOK RUN CYCLE
    ┌──────────────────────┐
    │ Prep (sync + orient)  │ ◄── session continuity + project context
    │ Cook (TDD execute)    │ ◄── verification mindset
    │ Serve (review)        │ ◄── security-first + quality gates
    │ Tidy (commit + push)  │ ◄── beads + context update
    └──────────────────────┘
```

**Flow:**
1. Daedalus principles are delivered via the daedalus-spice (installed once)
2. During brainstorm, the quality-agreement skill triggers the ASK/OFFER/CONFIRM conversation
3. The agreement is recorded in the brainstorm doc and flows into scope's acceptance criteria
4. During cook, the verification-mindset skill reminds the AI to check actual state
5. During serve, security-first elevates security to a dedicated review section with BLOCK authority
6. During tidy, session-continuity prompts for context document updates when stale

---

## What NOT to Do

1. **Don't add a planning phase before Mise.** Daedalus's 10-30 minute onboarding is a knowledge-loading ritual for AI instances. Line Cook's `/line:prep` is a state-sync operation. They solve different problems. If onboarding is needed, it happens before the user runs any Line Cook command — it is not part of the workflow.

2. **Don't make Daedalus a hard dependency.** The daedalus-spice is optional. Every Line Cook command must work identically whether the spice is installed or not. The spice adds depth; it does not change behavior.

3. **Don't import Daedalus's mode system into Line Cook core.** Modes belong in spices (writing-spice, academic-spice, research-spice). Line Cook core remains domain-agnostic.

4. **Don't duplicate Daedalus's documentation.** The spice skills should reference Daedalus concepts by name and provide just enough context for the AI to apply them. The full documentation lives in the Daedalus repository.

5. **Don't add behavioral patterns to Line Cook agents.** Daedalus's behavioral-patterns.md (communication style, decision-making framework) is guidance for AI personality, not workflow logic. It does not belong in agent prompts that need to be concise and action-oriented.

---

## Implementation Sketch

### Phase 1: Quality Agreement (1 session)

- [ ] Add quality agreement conversation to brainstorm template (`docs/templates/brainstorm.md`)
- [ ] Update `/line:brainstorm` command to include agreement prompt at completion
- [ ] Document the quality agreement flow in `docs/cycles/mise-cycle.md`

### Phase 2: Daedalus Spice (2-3 sessions)

- [ ] Create `daedalus-spice` repository with five skills
- [ ] Register in `.claude-plugin/marketplace.json`
- [ ] Write skill content derived from Daedalus source documents
- [ ] Test with a sample project end-to-end

### Phase 3: Security in Serve (1-2 sessions)

- [ ] Add dedicated security section to sous-chef agent template
- [ ] Implement security BLOCK verdict logic (non-overridable)
- [ ] Add `--security-tier` flag to `/line:serve`
- [ ] Create ADR documenting the security tier system

### Phase 4: Project Context (1 session)

- [ ] Create `docs/templates/project-context.md` template
- [ ] Update `/line:prep` to display context summary when file exists
- [ ] Update `/line:tidy` to prompt for context refresh when stale

### Phase 5: Mode Spices (2-3 sessions per spice)

- [ ] Create `writing-spice` repository
- [ ] Create `academic-spice` repository
- [ ] Create `research-spice` repository
- [ ] Register all in marketplace.json
- [ ] Test each with a representative project

---

## References

### Line Cook Files Referenced

| File | Path |
|------|------|
| Mise Cycle | `docs/cycles/mise-cycle.md` |
| Run Cycle | `docs/cycles/run-cycle.md` |
| Brainstorm Template | `docs/templates/brainstorm.md` |
| Marketplace | `.claude-plugin/marketplace.json` |
| ADR-0005: Three-Tier Hierarchy | `docs/decisions/0005-three-tier-bead-hierarchy.md` |
| ADR-0006: Review Agents | `docs/decisions/0006-phase-specialized-review-agents.md` |
| ADR-0007: Fresh-Context Review | `docs/decisions/0007-fresh-context-review.md` |
| ADR-0008: Three-Phase Mise | `docs/decisions/0008-three-phase-mise-with-pause-points.md` |
| ADR-0014: Spice Architecture | `docs/decisions/0014-spice-plugins-for-domain-knowledge.md` |
| ADR-0017: Deferred Findings | `docs/decisions/0017-deferred-findings-triage.md` |

### Daedalus Files Referenced

| File | Path (in daedalus-framework repo) |
|------|-----------------------------------|
| Quality Standards | `framework/core-universal/quality-standards.md` |
| Specification-First | `framework/core-universal/specification-first.md` |
| Verification Mindset | `framework/core-universal/verification-mindset.md` |
| Golden Rules | `framework/core-universal/GOLDEN_RULES.md` |
| Session Workflow | `framework/core-universal/session-workflow.md` |
| Onboarding Protocol | `framework/core-universal/onboarding-protocol.md` |
| Behavioral Patterns | `framework/core-universal/behavioral-patterns.md` |
| Development Quality Gates | `framework/modes/development/quality-gates.md` |
| Writing Patterns | `framework/modes/writing/patterns.md` |
| Academic Patterns | `framework/modes/academic/patterns.md` |
| Research Patterns | `framework/modes/research/patterns.md` |
