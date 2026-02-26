# State Machine Design: Best Practices and Antipatterns (BPAP)

Research document for designing configurable workflow state machines in agent-driven systems.

> Applied in the [Crumbs v2 Specification](../specs/crumbs-v2-spec.md). See [crumbs-v2-design.md](../specs/crumbs-v2-design.md) Section 10 for the alignment mapping.

---

## Key Principles

**1. Make illegal states unrepresentable.**
The state machine's type system should prevent invalid configurations at definition time, not just at runtime. If a state cannot be reached, it should not exist in the config. If two states are mutually exclusive, the schema should enforce that — not a runtime check. This is the single most impactful principle: bugs you cannot express are bugs you cannot ship.

**2. Separate the decision function from the execution function.**
The state machine decides what transition is valid (pure function: current state + event + guards → next state). The executor performs the work associated with that state (impure: I/O, side effects, agent invocations). Mixing these creates untestable systems where you cannot verify transition logic without running the full execution stack.

**3. State should be derived, not stored.**
Current state is a projection of the event history, not a mutable field. This eliminates the entire class of bugs where stored state diverges from actual history. If you can rebuild the current state by replaying events, you have a single source of truth. If you store state separately, you have two sources that will eventually disagree.

**4. Configuration is better than code for workflow definitions.**
State machines defined in declarative config (YAML, JSON) can be validated, visualized, diffed, and understood by non-programmers. State machines embedded in code (if/else chains, switch statements) are invisible to tooling and require reading implementation to understand behavior. Config-driven machines also enable per-project customization without code changes.

**5. Guards must be pure; effects must be ordered.**
Guard evaluation must be free of side effects — a guard that writes to a database or sends a message during evaluation creates action-at-a-distance bugs that are nearly impossible to debug. Side effects must execute in a defined order after the transition is committed, so that partial failures have predictable recovery paths.

---

## Best Practices

### BP-1: Explicit State Enumeration

**Practice:** Define all valid states as an explicit list in the workflow config. Reject any state name not in the list. No implicit states, no dynamic state generation.

**Rationale:** Explicit enumeration makes the state space visible and finite. Tools can validate that every state is reachable, that terminal states exist, and that no transition references an undefined state. Dynamic states (e.g., auto-generated `cook_attempt_2`) create unbounded state spaces that resist analysis.

**Sources:** [Statecharts: A Visual Formalism for Complex Systems (Harel, 1987)](https://www.sciencedirect.com/science/article/pii/0167642387900359), [XState Documentation: Finite States](https://xstate.js.org/docs/guides/states.html)

### BP-2: Event-Sourced State Derivation

**Practice:** Store transitions as immutable, append-only events. Derive current state by replaying the event log. Never persist current state as a mutable field.

**Rationale:** Event sourcing provides a complete audit trail, supports temporal queries ("what state was this issue in on Tuesday?"), and eliminates state-storage divergence. The replay function serves as both the state derivation algorithm and the correctness proof — if replay produces the expected state, the event log is consistent.

**Sources:** [Event Sourcing (Martin Fowler)](https://martinfowler.com/eaaDev/EventSourcing.html), [Event Sourcing Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)

### BP-3: Pure Guard Functions

**Practice:** Guards evaluate conditions using only the data available in the state machine context (current state, event payload, issue data, attempt count). They perform no I/O, no network calls, no database writes. They return a boolean.

**Rationale:** Pure guards are testable in isolation, deterministic under replay, and safe to evaluate speculatively (e.g., for "what transitions are available?" queries). A guard with side effects means that merely *asking* what transitions are valid can change system state — a severe violation of the principle of least surprise.

**Sources:** [UML State Machine (Wikipedia)](https://en.wikipedia.org/wiki/UML_state_machine#Guard_conditions), [XState Guards](https://xstate.js.org/docs/guides/guards.html)

### BP-4: Ordered, Idempotent Side Effects

**Practice:** Side effects (status updates, parent cascade checks, hook invocations) execute in a declared order after the transition is committed. Each effect should be idempotent — safe to re-execute on recovery without producing duplicate results.

**Rationale:** Ordered execution provides predictable recovery: if the process crashes between effects 3 and 4, recovery re-runs from effect 4 (or re-runs all effects if they're idempotent). Unordered effects require complex coordination to determine which have completed. Non-idempotent effects require exactly-once delivery guarantees that are expensive and fragile.

**Sources:** [Idempotency Patterns (Stripe)](https://stripe.com/docs/api/idempotent_requests), [Saga Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga)

### BP-5: Hierarchical State Composition

**Practice:** Support nested workflows where a child workflow operates within a parent lifecycle. A task workflow runs inside a feature lifecycle, which runs inside an epic lifecycle. Cross-cutting concerns (cascading close, progress aggregation) operate at the hierarchy boundary.

**Rationale:** Flat state machines that try to represent multi-level work items either explode in state count or lose fidelity. Hierarchical composition keeps each level's state machine small and comprehensible while supporting the natural structure of project work (epics contain features contain tasks).

**Sources:** [Statecharts (Harel)](https://www.sciencedirect.com/science/article/pii/0167642387900359), [XState Hierarchical States](https://xstate.js.org/docs/guides/hierarchical.html)

### BP-6: Context Variables Over State Explosion

**Practice:** Use context variables (attempt count, feedback history, retry metadata) instead of encoding dynamic data into state names. The state is "cook," the context is "attempt 2 with feedback from prior rejection."

**Rationale:** Encoding dynamic data into states (e.g., `cook_attempt_1`, `cook_attempt_2`, `cook_attempt_3`) creates a state for every possible value of the variable, producing exponential blowup. Context variables keep the state machine finite and comprehensible while preserving all the dynamic information.

**Sources:** [XState Context](https://xstate.js.org/docs/guides/context.html), [Statecharts: Extended State](https://statecharts.dev/glossary/extended-state.html)

### BP-7: Declarative Config Over Imperative Code

**Practice:** Define workflows in a declarative configuration format (YAML, JSON) that can be validated, diffed, and visualized independently of the engine implementation. The engine reads the config; it does not contain the workflow logic.

**Rationale:** Declarative configs are diffable in code review, validatable by tooling (`cr workflow validate`), and comprehensible without reading engine source code. Imperative workflow definitions (if/else chains, switch statements) are invisible to external tools and require understanding the engine to understand the workflow.

**Sources:** [Temporal Workflow Definitions](https://docs.temporal.io/workflows), [AWS Step Functions (Declarative State Machines)](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)

### BP-8: Machine-Driven Prompting

**Practice:** The state machine tells the consumer what to do next (`cr next` returns the next action). The consumer does not decide the workflow sequence — it asks the machine, executes, and reports the result.

**Rationale:** When consumers decide their own sequence, workflow logic is duplicated across every consumer. Changes to the workflow require updating every consumer independently. Machine-driven prompting centralizes workflow knowledge in the config, making consumers simple executors that follow instructions.

**Sources:** [Anthropic: Chain Prompts](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-prompts), [Building Effective Agents (Anthropic)](https://www.anthropic.com/engineering/building-effective-agents)

### BP-9: Terminal State Enforcement

**Practice:** Declare terminal states explicitly in the config. Validate that at least one terminal state exists and that every non-terminal state has a path to a terminal state. Reject configs with unreachable states or states with no outbound transitions that aren't terminal.

**Rationale:** A state machine without terminal states runs forever. A state with no outbound transitions that isn't declared terminal is a bug — the work item is stuck with no way to complete. Static validation catches these at config time, not at runtime when an issue is already trapped.

**Sources:** [Formal Methods for State Machines](https://en.wikipedia.org/wiki/Finite-state_machine#Classification), [TLA+ Model Checking](https://lamport.azurewebsites.net/tla/tla.html)

### BP-10: Cascading with Bounded Depth

**Practice:** When a child completes, evaluate the parent for state change. Cascade upward, bounded by a maximum depth (e.g., 3 levels: task → feature → epic). Report cascade results in the transition response.

**Rationale:** Unbounded cascading can loop infinitely in malformed hierarchies. Bounded cascading provides automatic progress propagation (all tasks done → feature closes → epic closes) with guaranteed termination. The cascade result in the response makes the behavior observable and debuggable.

**Sources:** [Hierarchical State Machine Patterns](https://statecharts.dev/), [Composite Pattern (GoF)](https://refactoring.guru/design-patterns/composite)

### BP-11: Deterministic Guard Ordering

**Practice:** When multiple transitions share the same `(from, event)` pair, evaluate guards in declaration order. The first matching guard wins. Require that guards on shared transitions are mutually exclusive.

**Rationale:** Non-deterministic guard evaluation produces different results on different runs, making debugging impossible. Declaration-order evaluation is simple, predictable, and matches how humans read config files. Mutually exclusive guards ensure that adding a new transition doesn't change the behavior of existing transitions.

**Sources:** [Priority-Based Transition Resolution (UML)](https://www.omg.org/spec/UML/), [XState: Guarded Transitions](https://xstate.js.org/docs/guides/guards.html)

### BP-12: Stale State Detection

**Practice:** Detect phases that were started but never completed or failed (the session crashed mid-phase). Report stale phases in audit output. On resume, re-enter the phase without incrementing the attempt counter.

**Rationale:** Without stale detection, crashed sessions leave issues in limbo — they appear active but no agent is working on them. Stale detection is the liveness check that prevents orphaned work items. Not incrementing the attempt counter on resume prevents penalizing the work item for infrastructure failures.

**Sources:** [Heartbeat Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring), [Effective Harnesses for Long-Running Agents (Anthropic)](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

---

## Antipatterns

### AP-1: Boolean Flags for State

**What it looks like:** Instead of explicit states, the system uses boolean flags: `is_reviewing`, `is_retrying`, `is_blocked`, `needs_changes`. Current state is inferred from the combination of flags.

**Why it is harmful:** With N boolean flags, there are 2^N possible combinations, most of which are invalid (`is_reviewing && is_blocked && is_retrying`). The system must guard against each invalid combination individually, and any new flag doubles the state space. Explicit state enumeration makes the valid states obvious and the invalid states unrepresentable.

**Sources:** [Making Illegal States Unrepresentable (Yaron Minsky)](https://blog.janestreet.com/effective-ml-revisited/), [State Machine Thinking (Kent Beck)](https://medium.com/@kentbeck_7670/state-machine-thinking-7b8d67b2d5d0)

### AP-2: God State

**What it looks like:** A single "active" or "in_progress" state with internal branching logic. The system checks sub-conditions within the state to determine what to do: "if active and review pending, do X; if active and tests passing, do Y."

**Why it is harmful:** The state machine degenerates into a single-state system with imperative logic inside. All the benefits of state machines (visible transitions, guard validation, tooling support) are lost. The "state" provides no information — the real state is hidden in the branching logic.

**Sources:** [State Pattern vs. Boolean Soup (Refactoring Guru)](https://refactoring.guru/design-patterns/state), [Statecharts: Why (David Khourshid)](https://statecharts.dev/what-is-a-statechart.html)

### AP-3: Mutable State Without Event History

**What it looks like:** The system stores `current_state` as a mutable field, updated in-place on each transition. No record of prior states, transitions, or the events that caused them.

**Why it is harmful:** Debugging requires reproducing the sequence of events. Without history, the only information is "it's in state X" with no explanation of how it got there. Temporal queries ("was this ever in blocked state?") are impossible. Recovery from corruption requires manual investigation. Event sourcing solves all of these by making history the primary data and current state a derived view.

**Sources:** [Event Sourcing (Martin Fowler)](https://martinfowler.com/eaaDev/EventSourcing.html), [Why Event Sourcing (Greg Young)](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)

### AP-4: Implicit Transitions

**What it looks like:** State changes happen as side effects of other operations. Setting `status = "closed"` implicitly fires close effects. Assigning a user implicitly starts the first phase. There is no explicit transition concept — state changes are embedded in various update paths.

**Why it is harmful:** Implicit transitions cannot be guarded, audited, or validated. The workflow is scattered across multiple code paths instead of centralized in a definition. Adding a new constraint (e.g., "can only close if all children are closed") requires finding and modifying every code path that sets the status, rather than adding a guard to one transition definition.

**Sources:** [Explicit State Transitions (XState)](https://xstate.js.org/docs/guides/transitions.html), [Command Pattern (GoF)](https://refactoring.guru/design-patterns/command)

### AP-5: Impure Guards

**What it looks like:** Guard functions perform I/O: querying external services, reading files, sending notifications. A guard that "checks if tests pass" by actually running the test suite. A guard that "checks if the reviewer is available" by calling a scheduling API.

**Why it is harmful:** Evaluating "what transitions are available?" becomes an expensive, side-effect-producing operation. Guard evaluation during replay produces different results than the original evaluation. Speculative queries ("what would happen if event X fired?") cannot be answered without performing the I/O. Guards should evaluate precomputed data, not compute it on demand.

**Sources:** [Pure Functions (Wikipedia)](https://en.wikipedia.org/wiki/Pure_function), [Side Effects in State Machines (David Khourshid)](https://dev.to/davidkpiano/no-disabling-a-button-is-not-app-logic-598i)

### AP-6: State Explosion from Dynamic Encoding

**What it looks like:** Dynamic values encoded as state names: `cook_attempt_1`, `cook_attempt_2`, `cook_attempt_3`, `serve_with_feedback`, `serve_without_feedback`. Each combination of dynamic values produces a new state.

**Why it is harmful:** The state count grows combinatorially with the number of dynamic variables. A workflow with 5 states, 3 retry levels, and 2 feedback modes would need 5 × 3 × 2 = 30 explicit states instead of 5 states + 2 context variables. The config becomes unreadable, validation becomes impractical, and adding a new dynamic variable requires rewriting the entire state machine.

**Sources:** [Extended State Machines (Wikipedia)](https://en.wikipedia.org/wiki/Extended_finite-state_machine), [XState Context vs States](https://xstate.js.org/docs/guides/context.html)

### AP-7: Denormalization Drift

**What it looks like:** Derived values (`progress_pct`, `close_eligible`, `current_phase`) are stored alongside source data and updated "when convenient." The stored value gradually diverges from the actual computed value as edge cases accumulate.

**Why it is harmful:** The system now has two sources of truth that disagree. Queries against the stored value return stale results. Bugs manifest as "the UI shows 80% but the actual count is 3/5." The fix is always the same: derive on read, never store derived values. The performance cost of re-derivation is negligible compared to the debugging cost of divergence.

**Sources:** [Normalization (Database Theory)](https://en.wikipedia.org/wiki/Database_normalization), [CQRS Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)

### AP-8: Fat Nodes (All Logic in State)

**What it looks like:** Each state contains its own execution logic: what tools to run, what agents to invoke, what files to read. The state machine is both the workflow definition and the execution engine.

**Why it is harmful:** The state machine becomes untestable without the full execution environment. You cannot validate the workflow (are all states reachable? are guards correct?) without also running the tools. The two-layer architecture (core defines states/transitions; project hooks define execution) keeps the state machine pure and testable.

**Sources:** [Separation of Concerns (Wikipedia)](https://en.wikipedia.org/wiki/Separation_of_concerns), [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)

### AP-9: Stuck States Without Detection

**What it looks like:** A state has no outbound transitions (dead end) or all outbound transitions have guards that can never be satisfied. Issues enter this state and remain there permanently with no automated detection.

**Why it is harmful:** Stuck issues are invisible unless someone manually audits the issue list. In agent-driven systems, stuck issues consume mental overhead ("why isn't this progressing?") without producing any signal. Static validation (`cr workflow validate`) should catch dead-end states at config time. Runtime stale detection should catch dynamically stuck issues.

**Sources:** [Reachability Analysis (Model Checking)](https://en.wikipedia.org/wiki/Reachability), [Temporal Logic for State Machines](https://lamport.azurewebsites.net/tla/tla.html)

### AP-10: Undifferentiated Error Handling

**What it looks like:** All errors route to the same `error` or `failed` state with no distinction between transient failures (timeout, network), deterministic failures (wrong approach, missing capability), and infrastructure failures (process crash, disk full).

**Why it is harmful:** Recovery strategy depends on failure type. Transient failures benefit from retry. Deterministic failures need strategy change. Infrastructure failures need escalation. A single `failed` state forces the recovery logic to re-classify the failure after the fact, duplicating work the state machine could have done with distinct error states or typed error context.

**Sources:** [Circuit Breaker Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Agent Self-Healing BPAP: BP-2](agent-self-healing-bpap.md)

### AP-11: Cascading Without Bounds

**What it looks like:** When a child completes, the system cascades upward through the hierarchy without a depth limit. In a malformed hierarchy (circular parent references, extremely deep nesting), cascading runs indefinitely.

**Why it is harmful:** Unbounded recursion can crash the process, corrupt state (partial cascades), or produce stack overflows. Bounded cascading (e.g., max 3 levels) guarantees termination. The bound should match the maximum hierarchy depth defined in the constraints.

**Sources:** [Recursive Algorithm Termination](https://en.wikipedia.org/wiki/Recursion_(computer_science)#Termination), [Composite Pattern Depth Guards](https://refactoring.guru/design-patterns/composite)

### AP-12: Workflow in Code, Not Config

**What it looks like:** The state machine is implemented as if/else chains or switch statements in the engine code. Adding a new state or transition requires code changes, recompilation, and redeployment. Different projects cannot have different workflows without forking the engine.

**Why it is harmful:** Workflow changes require developer intervention and code review for what is fundamentally a configuration change. The workflow is invisible to non-developers. Tooling cannot visualize, validate, or analyze the workflow without parsing the code. Declarative config makes the workflow a first-class artifact that can be versioned, reviewed, and validated independently.

**Sources:** [AWS Step Functions (State Machine as Config)](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html), [Temporal Workflow Definitions](https://docs.temporal.io/workflows)

---

## Canonical References

| Source | Relevance |
|---|---|
| [Statecharts: A Visual Formalism for Complex Systems (Harel, 1987)](https://www.sciencedirect.com/science/article/pii/0167642387900359) | Foundational paper on hierarchical state machines, orthogonal regions, and history states |
| [XState Documentation](https://xstate.js.org/docs/) | Modern implementation of statecharts in JavaScript/TypeScript; practical patterns for guards, context, and hierarchical states |
| [Event Sourcing (Martin Fowler)](https://martinfowler.com/eaaDev/EventSourcing.html) | Canonical description of event-sourced state derivation |
| [Making Illegal States Unrepresentable (Yaron Minsky)](https://blog.janestreet.com/effective-ml-revisited/) | Type-driven design for eliminating invalid state combinations |
| [AWS Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html) | Production-grade declarative state machine definitions |
| [Temporal.io Workflows](https://docs.temporal.io/workflows) | Durable workflow execution with deterministic replay |
| [UML State Machine Specification](https://www.omg.org/spec/UML/) | Formal specification for state machine semantics including guards, effects, and composition |
| [Effective Harnesses for Long-Running Agents (Anthropic)](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Agent-specific patterns for checkpoint commits, stale detection, and session recovery |
| [Agent Self-Healing BPAP](agent-self-healing-bpap.md) | Companion BPAP for agent loop patterns (retry, escalation, feedback persistence) |
