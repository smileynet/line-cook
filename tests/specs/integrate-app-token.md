# Test Specification: Integrate create-github-app-token into workflow

## Bead
lc-769.1.2

## Tracer
Auth layer — proves App token works for git push and triggers downstream CI

## Context
- Add actions/create-github-app-token to workflow
- Use App token for git operations, GITHUB_TOKEN for API
- Deliverable: Workflow uses App token for git

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| Workflow with App token step | Token generated successfully | Auth works |
| Git push with App token | Branch push succeeds | Write access |
| Git push with App token | Validate workflow triggers on branch | CI triggering |
| Commit author | Shows App bot identity | Named identity |
| gh issue comment | Still uses GITHUB_TOKEN | Separate auth |

## Validation Checklist
- [ ] `actions/create-github-app-token@v2` step added
- [ ] App token passed to `actions/checkout` via `token:` input
- [ ] Git operations use App token (not GITHUB_TOKEN)
- [ ] Issue comments still use GITHUB_TOKEN (simpler, sufficient)
- [ ] Fix branch push triggers Validate workflow
- [ ] Commit author is App bot, not github-actions[bot]

## Implementation Notes
The key test is whether downstream CI triggers. GITHUB_TOKEN commits don't trigger workflows, but App token commits do.
