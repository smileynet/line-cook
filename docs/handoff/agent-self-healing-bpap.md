# Agent Self-Healing: Best Practices and Antipatterns (BPAP)

Research document for auditing Line Cook's autonomous loop, issue agent, and inspect command.

---

## Key Principles

**1. Persistence is memory; context windows are volatile.**
An agent's learning must live outside its context window -- in files, git history, status records, and structured logs. Fresh context per iteration is a feature, not a bug, as long as accumulated knowledge is re-injected from durable storage. The Ralph Loop pattern proves this: progress lives in files and git, not in conversation history.

**2. Fail forward: every failure must leave the system strictly better-informed than before.**
A failed iteration that records *why* it failed (structured feedback, reviewer comments, error messages, task-specific notes) gives the next iteration a head start. A failed iteration that only increments a retry counter is a wasted opportunity. The difference between a self-healing system and a retry loop is whether failure produces reusable signal.

**3. Escalation is a feature, not an admission of defeat.**
Autonomous agents should have clear thresholds for when to stop trying and produce an actionable handoff for humans. The best systems use predictive escalation -- anticipating the need for human intervention before critical failures occur -- rather than waiting until the circuit breaker trips.

**4. Classify before retrying; not all failures deserve the same response.**
Transient failures (timeouts, flaky tests, network blips) benefit from retry with backoff. Deterministic failures (wrong approach, misunderstood requirements, missing capabilities) need strategy change, not repetition. Retrying a deterministic failure is the single most common antipattern in agent loops.

**5. The agent's job after failure is to make the *next* attempt cheaper, not to brute-force the same attempt.**
Whether the next attempt is by the same agent, a different agent, or a human, the quality of the handoff note determines whether progress compounds or resets to zero.

---

## Best Practices

### BP-1: Structured Feedback Persistence Across Retries

**Practice:** When a review rejects work (e.g., sous-chef returns NEEDS_CHANGES), capture the *specific* feedback -- which files, which issues, what severity -- and inject it into the next iteration's prompt or context file.

**Rationale:** LLMs in fresh-context loops have no memory of prior feedback unless it is explicitly persisted. Research on self-correcting agents (Self-Refine, AWS Evaluator-Reflect-Refine) shows that the FEEDBACK -> REFINE -> FEEDBACK loop only works when the full feedback text, not just "it failed," reaches the refinement step. Studies show that agents with structured feedback injection correct errors 2-3x faster than agents that only know "retry."

**Sources:** [Self-Refine: Iterative Refinement with Self-Feedback](https://selfrefine.info/), [AWS Evaluator Reflect-Refine Loop](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/evaluator-reflect-refine-loop-patterns.html)

### BP-2: Failure Classification Before Retry Decision

**Practice:** Classify each failure into categories (transient, deterministic, environmental, scope) before deciding whether to retry, skip, escalate, or change strategy.

**Rationale:** 70-80% of transient failures resolve within seconds, making retries valuable for that class. But retrying a deterministic failure (e.g., the agent misunderstood the requirement, or the task needs capabilities the agent lacks) is pure waste. Explicit classification prevents the single most common failure mode in agent loops: retrying the exact same approach that just failed.

**Sources:** [Mastering Retry Logic Agents](https://sparkco.ai/blog/mastering-retry-logic-agents-a-deep-dive-into-2025-best-practices), [Retries, Fallbacks, and Circuit Breakers in LLM Apps](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/)

### BP-3: Health Check Before New Work

**Practice:** Before starting each iteration, validate system state: run tests, check for uncommitted changes, verify external services are reachable. Fix regressions before compounding them.

**Rationale:** Anthropic's long-running agent harness research recommends: "Start the session by reading the progress notes file and git commit logs, and run a basic test on the development server to catch any undocumented bugs." Agents that skip health checks build on broken foundations, producing cascading failures that are expensive to unwind.

**Sources:** [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### BP-4: Escalation Reports with Actionable Context

**Practice:** When a circuit breaker trips or all tasks are skipped, generate a structured escalation report that includes: which tasks failed, how many times, what the failure patterns were, and concrete suggested next actions for a human.

**Rationale:** An escalation that says "loop stopped after 5 failures" forces the human to re-investigate from scratch. An escalation that says "task X failed 3 times: sous-chef rejected because of missing error handling in `parser.py:142`; task Y timed out twice during the `serve` phase" gives the human a running start. The value of autonomous work is partially preserved even when the agent cannot complete it.

**Sources:** [PraisonAI Graceful Degradation](https://docs.praison.ai/docs/best-practices/graceful-degradation), [When AI Agents Fail](https://yuv.ai/blog/when-ai-agents-fail-a-real-pipeline-break-and-what-it-teaches-us)

### BP-5: Multi-Channel Memory Persistence

**Practice:** Use at least three complementary persistence channels: (1) git commit history for code state, (2) structured status/progress files for machine-readable state, (3) human-readable notes (progress logs, AGENTS.md-style knowledge) for accumulated wisdom.

**Rationale:** Each channel serves a different consumer. Git history lets the agent diff and revert. Status files let monitoring tools and watch commands display progress. Human-readable notes let both agents and humans understand *why* decisions were made, not just *what* changed. The Ralph Loop and Addy Osmani's self-improving agents research both converge on this pattern.

**Sources:** [Self-Improving Coding Agents (Addy Osmani)](https://addyosmani.com/blog/self-improving-agents/), [Ralph Loop](https://block.github.io/goose/docs/tutorials/ralph-loop/)

### BP-6: Circuit Breakers with Sliding Windows, Not Simple Counters

**Practice:** Track failures in a sliding window (e.g., last N iterations) rather than a simple consecutive-failure counter. Trip the breaker when the failure *rate* exceeds a threshold within the window, not just when N consecutive failures occur.

**Rationale:** A simple consecutive counter resets on any success, which means an agent alternating success-failure-success-failure can run indefinitely at 50% waste without ever tripping the breaker. A sliding window catches degraded-but-not-dead patterns. The three-state model (Closed -> Open -> Half-Open) from distributed systems applies directly: after tripping, the agent should cautiously test with one attempt before fully reopening.

**Sources:** [Circuit Breaker Pattern (Microsoft)](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Circuit Breaker Pattern (AWS)](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html)

### BP-7: Dual-Threshold Exit Gates

**Practice:** Use two thresholds: a *warning* threshold (agent gets nudged to wrap up or change strategy) and a *hard* threshold (execution is forcibly terminated). The warning threshold should fire well before the hard limit.

**Rationale:** Hard stops without warning produce incomplete work. Warning thresholds give the agent a chance to commit partial progress, file issues for remaining work, and write handoff notes. This is the "landing the plane" pattern -- the agent should always have time to leave the codebase in a known-good state.

**Sources:** [Agents: Loop Control (AI SDK)](https://ai-sdk.dev/docs/agents/loop-control), [The Agentic AI Handbook](https://www.nibzard.com/agentic-handbook/)

### BP-8: Idle Detection as a Liveness Signal

**Practice:** Monitor tool action timestamps during phase execution. If no tool action occurs for longer than a phase-specific threshold, the agent is likely stuck (infinite reasoning, waiting for input, hallucinating tool calls). Apply the idle_action policy: warn or terminate.

**Rationale:** Runaway phases are invisible without idle detection. A stuck agent consumes time and API tokens while producing no value. Idle detection is the canary in the coal mine -- it catches problems that neither test results nor output parsing can detect.

**Sources:** [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### BP-9: Per-Task Failure Budget, Not Just Global

**Practice:** Track failures per task, not just globally. After N failures on the same task, skip it and move to the next. This prevents one intractable task from consuming the entire iteration budget.

**Rationale:** Without per-task tracking, the loop can burn all its retries on one task while other achievable tasks sit idle. The skip list pattern (with a configurable max_task_failures) lets the loop make progress on tasks it *can* solve while accumulating evidence about the ones it cannot.

**Sources:** [7 AI Agent Failure Modes (Galileo)](https://galileo.ai/blog/agent-failure-modes-guide), [12 Failure Patterns of Agentic AI](https://www.concentrix.com/insights/blog/12-failure-patterns-of-agentic-ai-systems/)

### BP-10: Checkpoint Commits as Rollback Points

**Practice:** Commit passing state before attempting risky operations. If the next step breaks things, the agent can `git revert` to the last known-good state rather than trying to manually undo complex changes.

**Rationale:** Anthropic's research found that "the best way to elicit this behavior was to ask the model to commit its progress to git with descriptive commit messages... this allowed the model to use git to revert bad code changes and recover working states." Without checkpoint commits, failed refactors can leave the codebase in an unrecoverable state.

**Sources:** [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### BP-11: Exponential Backoff with Jitter for Transient Failures

**Practice:** When retrying transient failures, apply exponential backoff (2s, 4s, 8s...) with random jitter (0.8x-1.2x) and a cap on maximum delay. This prevents thundering-herd problems when multiple agents or processes retry simultaneously.

**Rationale:** Fixed-interval retries cause synchronized retry storms. Exponential backoff spreads load over time. Jitter prevents multiple agents from synchronizing their retries. The cap prevents absurdly long waits for failures that need escalation, not patience.

**Sources:** [Mastering Retry Logic Agents](https://sparkco.ai/blog/mastering-retry-logic-agents-a-deep-dive-into-2025-best-practices)

### BP-12: Context-Aware Strategy Adjustment on Retry

**Practice:** When retrying a task, modify the approach based on the failure mode. If sous-chef rejected for code quality, emphasize conventions. If tests failed, add test-focused context. Do not re-run the identical prompt.

**Rationale:** The Self-Refine pattern works because the refinement step receives the evaluator's critique, not just a "try again" signal. An agent that retries with the same prompt and same context will produce the same output (or a stochastic variation of it). The retry must carry new information.

**Sources:** [Self-Refine](https://selfrefine.info/), [OpenAI Self-Evolving Agents Cookbook](https://cookbook.openai.com/examples/partners/self_evolving_agents/autonomous_agent_retraining)

---

## Antipatterns

### AP-1: Blind Retry (Same Prompt, Same Context)

**What it looks like:** The agent fails, and the loop re-invokes it with the identical prompt and context. The agent produces the same or very similar output. This repeats until the retry limit is exhausted.

**Why it is harmful:** This is the most common and most wasteful failure mode in agent loops. It consumes tokens, time, and iteration budget while producing no new information. Without new context (feedback, error messages, a different strategy hint), the LLM has no reason to produce a different result. Studies show agents without real-time memory "may not recognize repeating patterns of failure, such as continuing to try accessing a broken link instead of attempting a different approach."

**Sources:** [Why Do Multi-Agent LLM Systems Fail (Galileo)](https://galileo.ai/blog/multi-agent-llm-systems-fail), [Retries, Fallbacks, and Circuit Breakers](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/)

### AP-2: Context Amnesia Across Iterations

**What it looks like:** Each fresh-context iteration starts from scratch with no memory of what previous iterations learned, which tasks were already attempted, what reviewer feedback was given, or what approaches were tried and failed.

**Why it is harmful:** The loop re-discovers the same dead ends, re-proposes the same rejected fixes, and re-triggers the same reviewer objections. "Standard agent loops suffer from context accumulation, where every failed attempt stays in the conversation history" -- but the opposite (zero accumulation in fresh-context loops) is equally problematic. The fix is not stuffing the full history into the context window, but selectively injecting the relevant lessons learned.

**Sources:** [Ralph Orchestrator: Solving the Context Window Crisis](https://medium.com/@sponge-theory.ai/ralph-orchestrator-solving-the-context-window-crisis-in-ai-powered-development-d91cee615656)

### AP-3: Silent Failure Escalation

**What it looks like:** The loop stops (circuit breaker, max iterations, all tasks skipped) and writes a generic "loop stopped" message with no detail about what went wrong, which tasks were problematic, or what a human should do next.

**Why it is harmful:** It forces the human to re-investigate from scratch, discarding all the diagnostic information the loop accumulated during its failed attempts. The human has to read logs, check git history, and reproduce failures -- work the loop already did. "Most 'agent failures' are not model failures -- they're loop design failures," and silent escalation is the loop design failure that destroys the most human time.

**Sources:** [When AI Agents Fail (YUV.AI)](https://yuv.ai/blog/when-ai-agents-fail-a-real-pipeline-break-and-what-it-teaches-us), [PraisonAI Graceful Degradation](https://docs.praison.ai/docs/best-practices/graceful-degradation)

### AP-4: Infinite Refinement Loop

**What it looks like:** The agent continuously "improves" its output without converging on a done state. Each iteration makes minor changes that trigger new review feedback, which triggers new changes, indefinitely.

**Why it is harmful:** Without a definition of "good enough" and a maximum refinement count, the agent burns resources on diminishing returns. This is especially insidious because each individual iteration looks productive -- it is making changes, passing some tests, getting partial approval. But the overall trajectory is asymptotic, never reaching completion.

**Sources:** [7 AI Agent Failure Modes (Galileo)](https://galileo.ai/blog/agent-failure-modes-guide), [Engineering Challenges and Failure Modes in Agentic AI](https://medium.com/@sahin.samia/engineering-challenges-and-failure-modes-in-agentic-ai-systems-a-practical-guide-f9c43aa0ae3f)

### AP-5: Over-Corrective Tone in Feedback

**What it looks like:** The agent's feedback to users or in issue comments adopts a lecturing, corrective tone: "Your report is wrong because..." or "You should have included..."

**Why it is harmful:** In the issue-agent context, the reporter is a user who took the time to file an issue. A corrective tone discourages future reports and creates a hostile experience. The agent should frame everything as "here's what I found" rather than "here's what's wrong with your report." This applies equally to inter-agent feedback: sous-chef reviewing cook's output should produce actionable critique, not condescension.

**Sources:** Direct project experience (issue-agent template rule: "Frame everything as 'here's what I found' not 'here's what's wrong with your report'")

### AP-6: Retry Without Error Classification

**What it looks like:** All failures are treated identically: increment counter, wait, retry. There is no distinction between a timeout (transient, worth retrying), a test failure (deterministic, needs approach change), and a blocked dependency (environmental, needs skip or escalation).

**Why it is harmful:** Retrying a blocked dependency wastes all available retries on something that cannot succeed regardless of how many times it is attempted. Meanwhile, tasks that could benefit from a simple retry are starved of attempts. This is the "thundering herd of one" -- the loop hammers one impossible task while ignoring achievable ones.

**Sources:** [Error Recovery and Fallback Strategies in AI Agent Development](https://www.gocodeo.com/post/error-recovery-and-fallback-strategies-in-ai-agent-development), [Handling Tool Errors and Agent Recovery](https://apxml.com/courses/langchain-production-llm/chapter-2-sophisticated-agents-tools/agent-error-handling)

### AP-7: Uncontrolled Context Accumulation

**What it looks like:** The loop stuffs all prior iteration history, all prior feedback, all prior error messages into the prompt for the next iteration. After several iterations, the context window is dominated by noise from old, irrelevant failures.

**Why it is harmful:** LLM performance degrades as context fills with irrelevant information. "Context failures are invisible -- agents continue to run with incomplete information, producing confident but wrong results." The fix is bounded context injection: only the most recent and most relevant feedback, not the full history. Summarize older iterations; preserve only actionable lessons.

**Sources:** [Self-Improving Coding Agents (Addy Osmani)](https://addyosmani.com/blog/self-improving-agents/), [Context Window: What It Is and Why It Matters](https://www.comet.com/site/blog/context-window/)

### AP-8: Symptom-Only Fixes Without Flagging

**What it looks like:** The agent adds a null check, try/catch, or guard clause at the crash site without investigating why the bad state occurred. The fix "works" (no more crash) but the root cause remains, and the same bug class will recur.

**Why it is harmful:** In the issue-agent context, a symptom fix merged without flagging creates a false sense of resolution. The issue closes, the reporter sees a fix, but the underlying problem persists and manifests later in a harder-to-diagnose form. Symptom fixes are sometimes appropriate (when the root cause is out of scope), but they must be explicitly flagged as such.

**Sources:** Inspector agent template ("Symptom-fix signals: guard/null-check at crash site without addressing why bad state occurs")

### AP-9: One-Shot Fix Attempts Without Verification

**What it looks like:** The agent proposes and commits a fix without running tests, checking for regressions, or validating that the fix actually resolves the reported issue.

**Why it is harmful:** Unverified fixes create new problems. In the issue-agent workflow, the bot creates a branch and PR -- if the fix introduces regressions, the human reviewer must catch them, which defeats the purpose of automation. The fix branch should at minimum pass existing tests before PR creation. "Agents must self-verify all features... using actual testing rather than code inspection alone."

**Sources:** [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### AP-10: Handoff Gaps at Agent Boundaries

**What it looks like:** When one agent (e.g., cook) hands off to another (e.g., serve/sous-chef), context is lost at the boundary. The reviewing agent does not know what the implementing agent was trying to do, what constraints it faced, or what trade-offs it made.

**Why it is harmful:** "Reliability lives and dies in the handoffs -- most 'agent failures' are actually orchestration and context-transfer issues." Free-text handoffs are the main source of context loss. The fix is structured handoff data: intent, approach taken, known limitations, and trade-offs made. This is equally important for agent-to-human handoffs (escalation reports).

**Sources:** [Best Practices for Multi-Agent Orchestration and Reliable Handoffs](https://skywork.ai/blog/ai-agent-orchestration-best-practices-handoffs/), [When AI Agents Fail](https://yuv.ai/blog/when-ai-agents-fail-a-real-pipeline-break-and-what-it-teaches-us)

---

## Audit Targets: Line Cook Components

This BPAP document is intended for auditing three components:

### 1. Autonomous Loop (`core/line_loop/`)

The loop already implements several best practices: circuit breaker with sliding window (BP-6), per-task skip list (BP-9), exponential backoff with jitter (BP-11), escalation reports with suggested actions (BP-4), multi-channel persistence via status.json and history.jsonl (BP-5), idle detection (BP-8), and health check via sync_at_start (BP-3, partial).

**Primary audit questions:**
- Does reviewer feedback (sous-chef NEEDS_CHANGES details) persist into the retry iteration's context? (BP-1, AP-1, AP-2)
- When a task retries, does the next iteration receive the *reason* for rejection, or just "needs_retry"? (BP-12, AP-1)
- Are failures classified by type before choosing retry vs. skip vs. escalate? (BP-2, AP-6)
- Does the escalation report include enough detail for a human to resume without re-investigation? (BP-4, AP-3)
- Is there a warning threshold before the hard circuit breaker trips? (BP-7)

### 2. Issue Agent (`core/templates/agents/issue-agent.md.template`)

The issue agent runs as a one-shot agent (no loop), but has self-healing concerns around fix quality, verification, and graceful degradation when it cannot fix something.

**Primary audit questions:**
- Does the agent verify its fix (run tests) before creating a PR? (AP-9)
- When taking Path B (no fix), does the comment provide enough context for the *next* attempt (human or agent) to succeed? (BP-4, principle 5)
- Does the agent's root-cause-vs-symptom assessment align with the inspector's criteria? (AP-8)
- If the agent fails mid-execution (tool denied, git error), does it leave useful notes or just stop? (AP-3, BP-4)

### 3. Inspect Command (`.claude/commands/inspect.md`, `.claude/agents/inspector.md`)

The inspect command is a human-in-the-loop review gate. Its self-healing role is to prevent bad fixes from merging and to provide actionable feedback when fixes need rework.

**Primary audit questions:**
- When the inspector returns REWORK or FEEDBACK, does the verdict include enough specific detail for the issue-agent (or human) to know *what* to fix? (BP-1, AP-3)
- Does the POLISH -> re-inspect cycle have a bounded retry count? (AP-4)
- If the inspector fails (tool error, context too large), does the system degrade gracefully? (BP-7, AP-3)
- Does the inspector's feedback format align with what the issue-agent would need to self-correct on a future run? (BP-12, AP-10)
