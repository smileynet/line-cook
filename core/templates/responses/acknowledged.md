---
name: acknowledged
description: Acknowledge a valid issue and signal we're looking at it
close: false
variables:
  SUMMARY:
    required: true
    description: Plain-language summary of what's happening and why it matters
  QUESTIONS:
    required: false
    description: Optional clarifying questions (newline-separated)
---
<!-- line:respond acknowledged -->
> Quick note from the project.

{{SUMMARY}}

{{QUESTIONS}}

We'll follow up here as things take shape. Appreciate the report!

_— line-sous-chef_
