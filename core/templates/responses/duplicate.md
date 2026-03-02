---
name: duplicate
description: Close as duplicate of an existing issue
close: true
close_reason: not_planned
variables:
  ORIGINAL_ISSUE:
    required: true
    description: "Original issue number (e.g., 12)"
---
<!-- line:respond duplicate -->
> Heads up from the project.

This overlaps with #{{ORIGINAL_ISSUE}}, which has a bunch more context already. Closing this one in its favor — all the good discussion carries over there.

If your situation is different from what's described in #{{ORIGINAL_ISSUE}}, feel free to reopen this with the extra details and we'll take another look.

_— line-sous-chef_
