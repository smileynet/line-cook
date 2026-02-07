# Kitchen Terminology

Line Cook uses restaurant/kitchen terminology throughout its workflow:

| Term | Meaning | Context |
|------|---------|---------|
| **Mise** | Create work breakdown before starting | `/mise` phase |
| **Audit** | Validate bead structure and quality | `/audit` phase |
| **Prep** | Sync git, show ready tasks | `/prep` phase |
| **Cook** | Execute task with TDD cycle | `/cook` phase |
| **Serve** | Review code changes | `/serve` phase |
| **Tidy** | Commit and push changes | `/tidy` phase |
| **Plate** | Validate completed feature | `/plate` phase |
| **Run** | Run full workflow cycle | `/run` phase |
| **Chef** | Subagent that executes tasks with TDD cycle | `/cook` phase |
| **Sous-Chef** | Subagent that reviews code changes | `/serve` phase |
| **Taster** | Subagent that reviews test quality | After RED phase |
| **Maître** | Subagent that reviews feature acceptance | `/plate` phase |
| **Expeditor** | Subagent that orchestrates full workflow | `/run` phase |
| **ORDER_UP** | Signal emitted when task is ready for review | End of cook phase |
| **GOOD_TO_GO** | Assessment from sous-chef indicating code is ready to commit | After serve phase |
| **Tracer** | Task that proves one aspect of a feature through all layers | Planning methodology |
| **Feature Complete** | All tasks for a feature closed, ready for plate phase | `/plate` phase trigger |
| **Acceptance Report** | Document validating feature against acceptance criteria | Created in plate |
