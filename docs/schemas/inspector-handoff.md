# Inspector Structured Handoff Format

## Overview

The inspect-issues command delegates to two review agents, each outputting structured JSON for reliable parsing by downstream agents (issue-agent, feedback broker):

- **Inspector** — reviews issue/PR pairs (8 dimensions, PR-specific verdicts)
- **Issue-reviewer** — triages standalone issues with no associated PR (5 dimensions, triage verdicts)

Both output JSON with a `type` discriminator field (`"pr_review"` or `"issue_review"`).

## Formats

### Inspector (PR Review)

The inspector returns valid JSON with this structure:

```json
{
  "issue_number": 42,
  "pr_number": 7,
  "verdict": "MERGE|POLISH|FEEDBACK|REWORK|REJECT",
  "dimensions": {
    "what_changed": "2-3 sentences describing the code change",
    "project_value": "2-3 sentences on why this matters",
    "issue_validity": "1-2 sentences",
    "intent_alignment": "1-2 sentences",
    "scope": "1-2 sentences",
    "security": "1-2 sentences",
    "code_quality": "1-2 sentences",
    "root_cause_depth": "1-2 sentences"
  },
  "rationale": "1 paragraph verdict explanation"
}
```

> **Note:** The inspector does not output `type` directly. The inspect-issues command augments
> the output with `"type": "pr_review"`, `"polish_attempts"`, and `"reviewed_at"` before
> writing to disk. See `docs/schemas/feedback-broker.md` for the stored schema.

### Issue Reviewer (Issue Review)

The issue-reviewer returns valid JSON with this structure:

```json
{
  "type": "issue_review",
  "issue_number": 42,
  "pr_number": null,
  "verdict": "VALID|NEEDS_INFO|DUPLICATE|REJECT",
  "dimensions": {
    "issue_validity": "1-2 sentences",
    "actionability": "1-2 sentences",
    "project_relevance": "1-2 sentences",
    "priority_signal": "1-2 sentences",
    "duplicate_check": "1-2 sentences"
  },
  "rationale": "1 paragraph verdict explanation",
  "duplicate_of": null
}
```

## Benefits

1. **No parsing errors** - JSON is machine-readable, eliminating markdown parsing brittleness
2. **Schema validation** - Downstream agents can validate structure before processing
3. **Reliable handoffs** - Solves AP-10 (handoff gaps at agent boundaries)
4. **Feedback persistence** - Enables BP-1 (structured feedback persistence across retries)

## Workflow

### PR Path
1. **Inspector** outputs JSON (8 dimensions)
2. **Inspect-issues command** augments with `type: "pr_review"`, `polish_attempts`, and `reviewed_at`
3. **Feedback file** written to `.beads/inspect-feedback/issue-<number>.json`
4. **Downstream agents** (issue-agent, feedback broker) read structured feedback

### Issue Path
1. **Issue-reviewer** outputs JSON (5 dimensions, includes `type: "issue_review"`)
2. **Inspect-issues command** augments with `reviewed_at`
3. **Feedback file** written to `.beads/inspect-feedback/issue-<number>.json`
4. **Downstream agents** (feedback broker) read structured feedback

## Migration

**Before:** Inspector output markdown → inspect-issues command parsed sections → wrote JSON

**After:** Inspector outputs JSON → inspect-issues command augments → writes JSON

No markdown parsing needed.
