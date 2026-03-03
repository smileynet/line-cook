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

We'll file a candidate fix PR with this approach shortly. Once it's up you can try the fix before it ships — just grab the branch and reinstall the plugin:

```bash
# check out the fix branch
gh pr checkout <pr-number>

# reinstall from your local copy so the changes take effect
claude install /path/to/line-cook/plugins/claude-code
```

If you installed line-cook from the marketplace and don't have the repo cloned yet:

```bash
gh repo clone smileynet/line-cook
cd line-cook
gh pr checkout <pr-number>
claude install ./plugins/claude-code
```

Appreciate the report!

_— line-sous-chef_
