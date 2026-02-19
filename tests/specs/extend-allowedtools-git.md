# Test Specification: Extend allowedTools for git write operations

## Bead
lc-p62.1.1

## Tracer
Capability layer — proves Claude can create branches and push code from CI

## Context
- Add git write operations to --allowedTools
- Configure git identity for commits
- Deliverable: Workflow with git write capability

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Workflow with `contents: write` | Can push branches | Permission check |
| `fetch-depth: 0` in checkout | Full history available for analysis | Deep clone |
| Git user.name configured | Commits have "github-actions[bot]" author | Identity |
| `git checkout -b fix/issue-99` | Branch created successfully | Branch creation |
| `git push origin fix/issue-99` | Branch pushed to remote | Push capability |
| Edit + Write tools allowed | Claude can modify files | File editing |

## Validation Checklist
- [ ] `contents: write` permission added
- [ ] `fetch-depth: 0` in checkout step
- [ ] Git user.name and user.email configured before any commits
- [ ] --allowedTools includes: Edit, Write, Bash(git:*)
- [ ] Branch creation and push works from runner
- [ ] No force-push capability (standard push only)

## Implementation Notes
Test by triggering the workflow on a test issue and verifying the branch appears.
