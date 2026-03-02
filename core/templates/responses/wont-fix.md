---
name: wont-fix
description: Close as intentional behavior or out of scope
close: true
close_reason: not_planned
variables:
  REASON:
    required: true
    description: Why this won't be fixed
  ALTERNATIVE:
    required: false
    description: Suggested alternative or workaround
---
<!-- line:respond wont-fix -->
> Heads up from the project.

Appreciate you raising this! {{REASON}}

{{ALTERNATIVE}}

Closing this out for now — but if there's context we're missing, feel free to reopen and we'll happily take another look.

_— line-sous-chef_
