# Inspector Structured Handoff Format

## Overview

The inspector agent outputs structured JSON instead of markdown to enable reliable parsing by downstream agents (inspect command, issue-agent, feedback broker).

## Format

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

## Benefits

1. **No parsing errors** - JSON is machine-readable, eliminating markdown parsing brittleness
2. **Schema validation** - Downstream agents can validate structure before processing
3. **Reliable handoffs** - Solves AP-10 (handoff gaps at agent boundaries)
4. **Feedback persistence** - Enables BP-1 (structured feedback persistence across retries)

## Workflow

1. **Inspector** outputs JSON
2. **Inspect command** augments with `polish_attempts` and `reviewed_at`
3. **Feedback file** written to `.beads/inspect-feedback/issue-<number>.json`
4. **Downstream agents** (issue-agent, feedback broker) read structured feedback

## Migration

**Before:** Inspector output markdown → inspect command parsed sections → wrote JSON

**After:** Inspector outputs JSON → inspect command augments → writes JSON

No markdown parsing needed.
