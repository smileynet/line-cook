# Full Service Report

**Epic:** Loop Self-Healing
**Bead ID:** lc-3nl
**Service Date:** 2026-02-25
**Theme:** Self-healing improvements to the autonomous loop

---

## Service Overview

This epic delivers **self-healing improvements to the autonomous loop**, enabling it to detect failure patterns, accumulate feedback history, warn before tripping circuit breakers, classify failures for retry strategy, and track per-task retry budgets.

### Courses Served (Features)

| Bead | Feature | Status |
|------|---------|--------|
| lc-6vw | T1: Accumulate feedback history across iterations | Closed |
| lc-8y3 | T4: Circuit breaker warning threshold | Closed |
| lc-tb5 | T5: Classify failures before retry | Closed |
| lc-nu2 | T9: Per-task cross-iteration retry budget | Closed |

---

## Guest Journey Validation

Critical user journeys tested end-to-end:

### Journey 1: Repeated Failure Pipeline

**Path:** Task fails → CB warns → SkipList triggers → Feedback accumulates

**Scenario:** A task fails serve review repeatedly. The circuit breaker warns the operator before tripping. The skip list removes the task after its budget is exhausted. Feedback history accumulates throughout for pattern detection.

**Validation:**
- **Status:** Validated
- **Method:** Integration test
- **Evidence:** `TestSelfHealingIntegration.test_warning_then_skip_then_feedback` (19 assertions)

### Journey 2: Recovery After Success

**Path:** Failures accumulate → Success resets skip list → Feedback history persists

**Scenario:** A task fails twice, then succeeds. The skip list resets but the feedback history remains for cross-attempt pattern detection.

**Validation:**
- **Status:** Validated
- **Method:** Integration test
- **Evidence:** `TestSelfHealingIntegration.test_success_resets_skip_but_not_feedback_history`

### Journey 3: Environmental Error Detection

**Path:** Crash with environmental indicators → Loop halts

**Scenario:** A task crashes with system-level errors (disk full, permission denied, OOM). The loop detects the environmental error and halts instead of retrying futilely.

**Validation:**
- **Status:** Validated
- **Method:** Unit tests
- **Evidence:** `TestIsEnvironmentalError` (8 tests covering detection and exclusion patterns)

---

## Smoke Test Results

End-to-end validation of critical paths:

| Critical Path | Status | Evidence |
|--------------|--------|----------|
| Feedback accumulation + rolling window | Pass | `test_feedback_history.py` (3 tests) |
| Circuit breaker warning before trip | Pass | `test_circuit_breaker.py` (5 tests) |
| Failure classification categories | Pass | `test_failure_classification.py` (17 tests) |
| Per-task retry budgets | Pass | `test_per_task_retry_budget.py` (7 tests) |
| Cross-feature integration | Pass | `test_self_healing_integration.py` (19 tests) |

**Smoke Test Command:**
```bash
python3 -m unittest tests.test_line_loop tests.test_feedback_history tests.test_self_healing_integration tests.test_circuit_breaker tests.test_per_task_retry_budget -v
```

**Results:** 442 tests passing

---

## Cross-Feature Integration

Features that must work together:

### Feedback History (T1) + Retry Budget (T9)

**Integration Point:** Feedback accumulates across retries governed by the per-task budget. When a task exhausts its budget, the accumulated history is available for escalation reporting.

**Validation:** `test_warning_then_skip_then_feedback` exercises both features in sequence

**Status:** Validated

### Circuit Breaker Warning (T4) + Skip List (T9)

**Integration Point:** Circuit breaker tracks loop-wide failure rate while skip list tracks per-task failures. Warning fires before the loop-level trip, and skip list removes individual problematic tasks.

**Validation:** `test_warning_then_skip_then_feedback` verifies CB warns at threshold=3 while skip list triggers at max_failures=3

**Status:** Validated

### Failure Classification (T5) + Environmental Detection

**Integration Point:** `LoopError.classify_failure()` provides exception-level classification. `_is_environmental_error()` provides iteration-result-level detection. Both paths identify environmental failures for halt decisions.

**Validation:** `TestIsEnvironmentalError` (8 tests) + `TestCalculateRetryDelayWithCategory` (4 tests)

**Status:** Validated (with follow-up lc-cqi to wire classify_failure into retry path)

---

## Kitchen Staff Sign-Off

Quality assurance by Line Cook agents:

| Agent | Role | Status |
|-------|------|--------|
| **Taster** | Unit test quality | Approved |
| **Sous-Chef** | Code review | Approved |
| **Critic** | Epic E2E coverage | Approved (PASS on re-review) |

---

## Guest Experience

How users can experience this capability:

```bash
# Start the autonomous loop — self-healing features are automatic
/line:loop start --max-iterations 25

# Watch the loop handle failures gracefully
/line:loop watch

# See circuit breaker warnings and skip list activity in logs
/line:loop tail
```

**Expected Outcome:** The loop warns when failures accumulate (before tripping), skips tasks that repeatedly fail, halts on environmental errors, and accumulates feedback history so retry attempts can detect persistent issues and change strategy.

---

## Kitchen Notes

### Known Limitations

- `classify_failure()` is not yet wired into `run_loop`'s retry delay path (filed as lc-cqi, P3)
- Environmental detection uses heuristic string matching on action output summaries

### Future Enhancements

- lc-cqi: Wire classify_failure() into run_loop retry path for category-aware delay

### Deployment Notes

- None required — all changes are in the line_loop package and bundled line-loop.py

---

## Related Work

### Features Completed

| Bead | Title |
|------|-------|
| lc-6vw | T1: Accumulate feedback history across iterations |
| lc-8y3 | T4: Circuit breaker warning threshold |
| lc-tb5 | T5: Classify failures before retry |
| lc-nu2 | T9: Per-task cross-iteration retry budget |

### Follow-Up Issues

| Bead | Title | Priority |
|------|-------|----------|
| lc-cqi | Wire classify_failure() into run_loop retry path | P3 |

---

**Status:** Epic Complete and Validated
