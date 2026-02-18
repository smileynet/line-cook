# Test Specification: Create GitHub App with minimum permissions

## Bead
lc-769.1.1

## Tracer
Identity layer — proves a named bot can authenticate and push

## Context
- Create GitHub App for line-cook
- Store credentials as repository secrets
- Deliverable: GitHub App with credentials stored

## Test Cases

| Input | Expected Output | Notes |
|-------|-----------------|-------|
| GitHub App creation | App exists with correct permissions | Setup verification |
| APP_ID secret | Stored in repository secrets | Secret management |
| APP_PRIVATE_KEY secret | Stored in repository secrets | Secret management |
| App permissions | contents: write, issues: write, pull-requests: write | Minimum privilege |
| App permissions | No admin or org-level access | Security |

## Validation Checklist
- [ ] GitHub App created in correct account/org
- [ ] Permissions are minimum required (contents, issues, pull-requests: write)
- [ ] No admin, organization, or member permissions
- [ ] Private key generated and stored as APP_PRIVATE_KEY
- [ ] App ID stored as APP_ID
- [ ] App installed on the line-cook repository
- [ ] Setup documented

## Implementation Notes
This task involves GitHub UI configuration, not code. Document the steps for reproducibility.
