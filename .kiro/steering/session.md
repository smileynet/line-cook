# Session Protocols

Rules for managing work sessions with line-cook.

## Session Start

Before working:

1. Sync state: `git fetch origin && git pull --rebase && bd sync`
2. Check ready work: `bd ready`
3. Claim task: `bd update <id> --status=in_progress`

Or run the prep workflow.

## Session Close Protocol

CRITICAL: Before saying "done" or "complete", run this checklist:

```
[ ] 1. git status              (check what changed)
[ ] 2. git add <files>         (stage code changes)
[ ] 3. bd sync                 (commit beads changes)
[ ] 4. git commit -m "..."     (commit code)
[ ] 5. bd sync                 (commit any new beads changes)
[ ] 6. git push                (push to remote)
```

Work is NOT done until pushed.

## Task Lifecycle

```
open -> in_progress -> closed
```

1. **Select**: `bd ready` or explicit ID
2. **Claim**: `bd update <id> --status=in_progress`
3. **Execute with TDD**: RED → GREEN → REFACTOR
4. **Verify**: All quality gates pass
5. **Close**: `bd close <id>`
6. **Push**: `bd sync && git push`

## Quality Gates

Before closing a task, ALL must pass:
- [ ] Tests pass (project test command)
- [ ] Code builds (project build command)
- [ ] Test quality reviewed (taster agent, during RED phase)
- [ ] Code quality reviewed (sous-chef agent, in serve phase)

## Guardrails

### On Start
- Always sync first
- One task at a time

### During Work
- Track progress with todos
- Note discoveries for later filing
- Don't file beads mid-task

### On Completion
- Verify ALL checks pass
- Close task only after verification
- File discovered issues in tidy
- Commit and push

## Context Handoff

Between sessions or after context clear:

1. Run `bd prime` to reload workflow context and beads state
2. Check `bd list --status=in_progress` for active work
3. Review `bd ready` for available tasks

## Workflow Cycle

Each prep -> cook -> serve -> tidy cycle completes one task.

For multiple tasks:
- Complete the full cycle
- Clear context if needed
- Start fresh with prep
