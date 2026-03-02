---
name: needs-info
description: Ask reporter for more details
close: false
variables:
  QUESTIONS:
    required: true
    description: Specific questions (newline-separated)
---
<!-- line:respond needs-info -->
> Quick note from the project.

Thanks for filing this — we'd love to help! Could you share a bit more detail?

{{QUESTIONS}}

Any of that would really help us narrow things down.

_— line-sous-chef_
