---
status: accepted
date: 2026-02-04
tags: [architecture]
relates-to: []
superseded-by: null
---

# 0009: Autonomous loop as external Python package

## Context

Users wanted multi-task autonomous execution — pick a task, cook it, review it, commit it, repeat. The loop needs to manage Claude CLI processes from outside: it must start and stop subprocesses, parse their structured output, handle timeouts, and decide whether to retry or move on. This orchestration can't run as a command inside Claude's own context because the loop must outlive individual Claude sessions.

Options considered:
- **Shell script** — simple to start but brittle for subprocess management, retry logic, and structured output parsing
- **Claude command (internal)** — would run inside the session it's managing, creating a circular dependency; can't restart Claude after crashes
- **External Python package** — full subprocess control, structured parsing, testable independently from Claude

## Decision

We will implement the autonomous loop as an external Python package (`scripts/line_loop/`) in the same repository. It manages Claude CLI as a subprocess — starting sessions, streaming output, parsing structured signals (SERVE_RESULT verdicts, COOK_INTENT blocks), and controlling lifecycle. The package implements exponential backoff with jitter for retries, a circuit breaker (5 consecutive failures in a 10-iteration window trips the breaker), and a skip list (3 failures per task before skipping) to prevent retry spirals.

The `/loop` command provides a TUI interface for starting, watching, and stopping the loop from within Claude Code.

## Consequences

- Positive: Clean separation of concerns — the loop orchestrates process lifecycle, commands define workflow behavior
- Positive: Testable independently — loop logic can be unit tested without running Claude
- Positive: Circuit breaker and skip list prevent runaway failure loops from burning tokens
- Negative: Adds a Python dependency to a project that is otherwise shell and markdown
- Negative: Two technologies to understand — contributors need to know both the command system and the Python orchestration layer
- Neutral: The loop parses structured text signals rather than using an API, coupling it to the output format of commands
