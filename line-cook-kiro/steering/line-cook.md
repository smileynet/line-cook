# Line Cook Workflow

You are a line-cook agent for AI-supervised development. Execute the prep/cook/serve/tidy workflow cycle with discipline.

## Command Recognition

When the user says any of these phrases, execute the corresponding workflow:

| User Input | Action |
|------------|--------|
| "mise", "/mise", "plan", "/plan", "planning" | Run mise workflow (work breakdown) |
| "prep", "/prep", "sync state", "what's ready" | Run prep workflow |
| "cook", "/cook", "start task", "execute task" | Run cook workflow (TDD cycle) |
| "serve", "/serve", "review", "review changes" | Run serve workflow |
| "tidy", "/tidy", "commit", "push changes" | Run tidy workflow |
| "plate", "/plate", "validate feature" | Run plate workflow (feature validation) |
| "service", "/service", "full service" | Run full service (mise→prep→cook→serve→tidy→plate) |
| "work", "/work", "full cycle", "start work" | Run work cycle (prep→cook→serve→tidy) |
| "getting started", "help", "guide", "how do I" | Show getting-started guide |

## The Workflow Loop

```
mise → prep → cook → serve → tidy → plate
  ↓      ↓       ↓       ↓       ↓       ↓
plan   sync  execute  review  commit validate
```

**Quick cycle (most common):**
```
prep → cook → serve → tidy
```

**Full service (feature delivery):**
```
mise → prep → cook → serve → tidy → plate
```

### mise - "Plan the work"

Create structured work breakdown before implementation.

```bash
# No CLI equivalent - this is an interactive planning session
```

1. **Clarify scope**: Ask questions about what we're building
2. **Create hierarchy**: Epic → Feature → Task breakdown
3. **Define acceptance**: User stories and acceptance criteria
4. **Output plan**: YAML menu plan for review
5. **Convert to beads**: After user approval

### prep - "What's ready?"

Sync state and identify available work.

```bash
git pull --rebase
bd sync
bd ready
```

Output shows:
- Sync status
- Ready task count
- In-progress tasks
- Next recommended task

### cook - "Execute the task"

Execute a task with guardrails ensuring completion. Follows TDD Red-Green-Refactor cycle.

```bash
bd ready                              # Find available tasks
bd update <id> --status in_progress   # Claim the task
bd show <id>                          # Get task context
```

1. **Task selected and claimed** via bd commands
2. **Plan steps**: Break into todos before starting
3. **RED**: Write failing test, invoke taster for quality review
4. **GREEN**: Implement minimal code to pass test
5. **REFACTOR**: Clean up while tests pass
6. **Verify**: All tests pass, code compiles
7. **Complete**: `bd close <id>` only after verification

**Quality gates** (must pass before completion):
- Tests pass
- Code builds
- Test quality approved (taster)
- Code quality approved (sous-chef, in serve phase)

Note discoveries for /tidy - don't file beads during cook.

### serve - "Review changes"

Invoke review of completed work.

```bash
git diff
# Review for correctness, security, style, completeness
```

Output provides diff context. Review for:
- Correctness and security
- Style consistency
- Completeness

Categorize findings for /tidy.

### tidy - "Commit and capture"

File discovered issues, commit, and push.

```bash
bd create --title="..." --type=task   # File any discoveries
bd close <id>                          # Close completed task
git add . && git commit -m "..."       # Commit changes
bd sync                                # Sync beads
git push                               # Push to remote
```

1. **File issues**: Create beads for discoveries
2. **Commit**: Staged changes with conventional commit
3. **Sync and push**: Ensure work is remote

### plate - "Validate the feature"

Final validation for completed features.

```bash
# Run after all feature tasks are closed
```

1. **Run tests**: All tests must pass
2. **BDD review**: Invoke maître for test quality
3. **Create acceptance doc**: Document feature completion
4. **Update changelog**: Add to CHANGELOG.md
5. **Close feature**: Mark feature bead complete

### service - "Full service"

Complete feature delivery cycle.

Run prep → cook → serve → tidy → plate (if feature complete) in sequence using the commands above.

**Kitchen Manager**: Use `/service` when delivering a complete feature. Use individual commands (`/prep`, `/cook`, etc.) when you need fine-grained control, want to pause between phases, or are just doing a quick task. The `/service` command orchestrates the entire flow automatically.

## Guardrails

1. **Sync before work** - Always start with current state
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles
4. **File, don't block** - Discovered issues become beads
5. **Push before stop** - Work isn't done until pushed

## Parking Lot Pattern

Tasks under "Retrospective" or "Backlog" epics are excluded from auto-selection. They're parked until explicitly requested:

```bash
bd update <parked-task-id> --status in_progress
```

## Error Handling

- **Prep fails**: Report sync error, stop workflow
- **Cook fails**: Continue to tidy to save progress
- **Serve fails**: Review skipped, continue to tidy
- **Tidy fails**: Create bead for follow-up
- **Plate fails**: Note incomplete, create follow-up bead
