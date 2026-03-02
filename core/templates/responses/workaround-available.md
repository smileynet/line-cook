---
name: workaround-available
description: Share a workaround while a proper fix is in progress
close: false
variables:
  WORKAROUND:
    required: true
    description: The workaround steps or command
  FIX_TIMELINE:
    required: false
    description: When the proper fix is expected (e.g., next release, v0.21.0)
---
<!-- line:respond workaround-available -->
> Quick update from the project.

While we work on a proper fix, there's a workaround you can use right now:

{{WORKAROUND}}

{{FIX_TIMELINE}}

Not ideal, but it should unblock you in the meantime. Holler if you hit any snags with it.

_— line-sous-chef_
