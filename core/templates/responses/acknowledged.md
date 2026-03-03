---
name: acknowledged
description: Acknowledge a valid issue and propose a solution
close: false
follow_up: trigger-issue-agent
variables:
  SUMMARY:
    required: true
    description: Plain-language summary of what's happening and why it matters
  PROPOSAL:
    required: true
    description: Proposed solution framed in terms of user value (what improves for them)
  QUESTIONS:
    required: false
    description: Optional clarifying questions (newline-separated)
---
<!-- line:respond acknowledged -->
> Quick note from the project.

{{SUMMARY}}

**What we're thinking:** {{PROPOSAL}}

{{QUESTIONS}}

We'll file a candidate fix PR with this approach shortly. Appreciate the report!

_— line-sous-chef_
