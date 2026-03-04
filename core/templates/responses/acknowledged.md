---
name: acknowledged
description: Acknowledge a valid issue and propose a solution
close: false
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
  PR_NUMBER:
    required: true
    description: Candidate fix PR number (e.g., 20)
---
<!-- line:respond acknowledged -->
> Quick note from the project.

{{SUMMARY}}

**What we're thinking:** {{PROPOSAL}}

{{QUESTIONS}}

There's a candidate fix in PR #{{PR_NUMBER}} — you can try it now before it ships:

```bash
# check out the fix branch
gh pr checkout {{PR_NUMBER}}

# reinstall from your local copy so the changes take effect
claude install /path/to/line-cook/plugins/claude-code
```

If you installed line-cook from the marketplace and don't have the repo cloned yet:

```bash
gh repo clone smileynet/line-cook
cd line-cook
gh pr checkout {{PR_NUMBER}}
claude install ./plugins/claude-code
```

Appreciate the report!

_— line-sous-chef_
