---
name: fix-shipped
description: Notify reporter that a fix has shipped
close: true
close_reason: completed
variables:
  VERSION:
    required: true
    description: Release version (e.g., v0.20.0)
# NOTE: The "Notify fixed issues" step in .github/workflows/release.yml
# hardcodes this message. Update both if wording changes.
---
<!-- line:respond fix-shipped -->
> Automated follow-up from the maintainer.

Good news — the fix for this is live in **{{VERSION}}**! Update with `/plugin update line` in Claude Code and give it a spin.

We'd love to hear how it works for your workflow. If something's still off, let us know and we'll dig in further.

_— line-sous-chef_
