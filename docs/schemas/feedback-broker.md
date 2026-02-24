# Feedback Broker Schema

## Purpose

The feedback broker synthesizes feedback from multiple agents (inspect, loop, issue-agent) into a unified view for cross-component context.

## Feedback Sources

### 1. Inspect Feedback
**Location:** `.beads/inspect-feedback/issue-<number>.json`

**Schema:**
```json
{
  "issue_number": 42,
  "pr_number": 7,
  "verdict": "MERGE|POLISH|FEEDBACK|REWORK|REJECT",
  "polish_attempts": 0,
  "dimensions": {
    "what_changed": "...",
    "project_value": "...",
    "issue_validity": "...",
    "intent_alignment": "...",
    "scope": "...",
    "security": "...",
    "code_quality": "...",
    "root_cause_depth": "..."
  },
  "rationale": "...",
  "reviewed_at": "2026-02-23T21:00:00Z"
}
```

### 2. Loop Feedback
**Location:** `.beads/loop-feedback/<task-id>.json`

**Schema:**
```json
{
  "task_id": "lc-abc",
  "phase": "serve",
  "verdict": "APPROVED|NEEDS_CHANGES|BLOCKED",
  "feedback": "...",
  "iteration": 1,
  "reviewed_at": "2026-02-23T21:00:00Z"
}
```

### 3. Issue-Agent Feedback
**Location:** `.beads/issue-agent-feedback/issue-<number>.json`

**Schema:**
```json
{
  "issue_number": 42,
  "classification": "bug|enhancement|question",
  "confidence": 0.85,
  "labels": ["bug", "needs-triage"],
  "analysis": "...",
  "proposed_fix": "...",
  "reviewed_at": "2026-02-23T21:00:00Z"
}
```

## Unified View

The broker synthesizes these into a single view:

```json
{
  "context_type": "issue|task|pr",
  "context_id": "42|lc-abc",
  "feedback_sources": {
    "inspect": { ... },
    "loop": { ... },
    "issue_agent": { ... }
  },
  "summary": {
    "total_feedback_count": 3,
    "latest_verdict": "POLISH",
    "escalation_needed": false,
    "key_concerns": ["code_quality", "scope"]
  },
  "synthesized_at": "2026-02-23T21:00:00Z"
}
```

## Query Interface

### By Issue Number
```bash
feedback-broker --issue 42
```

### By Task ID
```bash
feedback-broker --task lc-abc
```

### By PR Number
```bash
feedback-broker --pr 7
```

