---
description: Synthesize feedback from multiple agents (inspect, loop, issue-agent) into a unified view for cross-component context
keywords: feedback, context, handoff, agent-coordination, inspect, loop, issue-agent
---

# Feedback Broker

## Purpose

The feedback broker synthesizes feedback from multiple agents into a unified view, solving the handoff gap problem (AP-10) where context is lost at agent boundaries.

## When to Use

Use the feedback broker when:
- You need to understand prior feedback from other agents
- You're working on an issue/task that has been reviewed before
- You need to check if escalation is needed (e.g., 3+ polish attempts)
- You want to see all feedback sources in one place

## Feedback Sources

The broker reads from three sources:

1. **Inspect feedback** (`.beads/inspect-feedback/issue-<number>.json`)
   - Two feedback types, discriminated by the `type` field:
     - **PR review** (`"type": "pr_review"`): 8 dimensions (what changed, value, validity, alignment, scope, security, quality, root cause), polish attempt tracking, PR-specific verdicts (MERGE/POLISH/FEEDBACK/REWORK/REJECT)
     - **Issue review** (`"type": "issue_review"`): 5 dimensions (validity, actionability, relevance, priority, duplicate check), no polish attempts, triage verdicts (VALID/NEEDS_INFO/DUPLICATE/REJECT)
   - Both stored in the same directory

2. **Loop feedback** (`.beads/loop-feedback/<task-id>.json`)
   - Autonomous loop serve-phase feedback
   - Retry context from sous-chef reviews
   - Iteration history

3. **Issue-agent feedback** (`.beads/issue-agent-feedback/issue-<number>.json`)
   - Automated issue classification
   - Confidence scores
   - Proposed fixes

## Usage

### Query by Issue Number

```bash
python3 plugins/claude-code/scripts/feedback_broker.py --issue 42
```

### Query by Task ID

```bash
python3 plugins/claude-code/scripts/feedback_broker.py --task lc-abc
```

### Query by PR Number

```bash
python3 plugins/claude-code/scripts/feedback_broker.py --pr 7
```

## Output Format

The broker returns a unified JSON view:

```json
{
  "context_type": "issue|task|pr",
  "context_id": "42",
  "feedback_sources": {
    "inspect": { ... },
    "loop": { ... },
    "issue_agent": { ... }
  },
  "summary": {
    "total_feedback_count": 2,
    "latest_verdict": "POLISH",
    "escalation_needed": false,
    "key_concerns": ["code_quality", "scope"]
  },
  "synthesized_at": "2026-02-23T21:00:00Z"
}
```

## Integration Points

### For Issue-Agent

When re-triggered on an issue, check for prior inspect feedback:

```bash
FEEDBACK=$(python3 plugins/claude-code/scripts/feedback_broker.py --issue $ISSUE_NUMBER)
VERDICT=$(echo "$FEEDBACK" | jq -r '.feedback_sources.inspect.verdict // "none"')

if [ "$VERDICT" = "POLISH" ]; then
  echo "Prior review requested polish. Focus on code quality improvements."
fi
```

### For Loop Retry

When retrying a task, include prior serve feedback:

```bash
FEEDBACK=$(python3 plugins/claude-code/scripts/feedback_broker.py --task $TASK_ID)
PRIOR_FEEDBACK=$(echo "$FEEDBACK" | jq -r '.feedback_sources.loop.feedback // "none"')

if [ "$PRIOR_FEEDBACK" != "none" ]; then
  echo "Prior feedback: $PRIOR_FEEDBACK"
fi
```

### For Inspector

When reviewing a fix, check if issue-agent already analyzed it:

```bash
FEEDBACK=$(python3 plugins/claude-code/scripts/feedback_broker.py --issue $ISSUE_NUMBER)
CLASSIFICATION=$(echo "$FEEDBACK" | jq -r '.feedback_sources.issue_agent.classification // "none"')

if [ "$CLASSIFICATION" != "none" ]; then
  echo "Issue-agent classified as: $CLASSIFICATION"
fi
```

## Escalation Detection

The broker automatically detects escalation conditions:

- **Polish attempts >= 3**: Indicates infinite refinement loop (AP-4)
- **Multiple NEEDS_CHANGES verdicts**: Indicates stuck task
- **Low confidence + proposed fix**: Indicates uncertain classification

When `escalation_needed: true`, consider:
- Human review
- Different approach
- Breaking into smaller tasks
- Clarifying requirements

## Schema Reference

See `docs/schemas/feedback-broker.md` for detailed schema documentation.
