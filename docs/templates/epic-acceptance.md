# Full Service Report

> Template for documenting epic (full service) completion during epic plate phase.

**Epic:** <!-- Epic title -->
**Bead ID:** <!-- lc-xxx -->
**Service Date:** <!-- YYYY-MM-DD (completion date) -->
**Theme:** <!-- Brief capability description -->

---

## Service Overview

This epic delivers **<!-- capability description -->**.

### Courses Served (Features)

| Bead | Feature | Status |
|------|---------|--------|
| <!-- lc-xxx.1 --> | <!-- feature title --> | Plated |
| <!-- lc-xxx.2 --> | <!-- feature title --> | Plated |
| <!-- lc-xxx.3 --> | <!-- feature title --> | Plated |

---

## Guest Journey Validation

Critical user journeys tested end-to-end:

### Journey 1: <!-- Journey Name -->

**Path:** <!-- Feature A → Feature B → Feature C -->

**Scenario:** <!-- What the user is trying to accomplish -->

**Validation:**
- **Status:** Validated
- **Method:** <!-- E2E test, manual demo, smoke test -->
- **Evidence:** <!-- Test name, screenshot, or command output -->

### Journey 2: <!-- Journey Name -->

**Path:** <!-- Feature A → Feature D -->

**Scenario:** <!-- What the user is trying to accomplish -->

**Validation:**
- **Status:** Validated
- **Method:** <!-- E2E test, manual demo, smoke test -->
- **Evidence:** <!-- Test name, screenshot, or command output -->

### Journey 3: <!-- Journey Name -->

**Path:** <!-- Feature B → Feature C -->

**Scenario:** <!-- What the user is trying to accomplish -->

**Validation:**
- **Status:** Validated
- **Method:** <!-- E2E test, manual demo, smoke test -->
- **Evidence:** <!-- Test name, screenshot, or command output -->

<!-- Add more journeys as needed -->

---

## Smoke Test Results

End-to-end validation of critical paths:

| Critical Path | Status | Evidence |
|--------------|--------|----------|
| <!-- path name --> | Pass | <!-- test name or output --> |
| <!-- path name --> | Pass | <!-- test name or output --> |
| <!-- path name --> | Pass | <!-- test name or output --> |

**Smoke Test Command:**
```bash
<!-- command to run smoke tests -->
```

**Results:** All smoke tests passing

---

## Cross-Feature Integration

Features that must work together:

### <!-- Feature A --> + <!-- Feature B -->

**Integration Point:** <!-- How they connect -->

**Validation:** <!-- How verified (test, demo, etc.) -->

**Status:** Validated

### <!-- Feature B --> + <!-- Feature C -->

**Integration Point:** <!-- How they connect -->

**Validation:** <!-- How verified -->

**Status:** Validated

---

## Kitchen Staff Sign-Off

Quality assurance by Line Cook agents:

| Agent | Role | Status |
|-------|------|--------|
| **Taster** | Unit test quality | Approved |
| **Sous-Chef** | Code review | Approved |
| **Maître** | Feature BDD quality | Approved |
| **Critic** | Epic E2E coverage | Approved |

---

## Guest Experience

How users can experience this capability:

```bash
# Example commands demonstrating the epic's capability
<!-- command 1: Start of journey -->
<!-- command 2: Key operation -->
<!-- command 3: Completion/verification -->
```

**Expected Outcome:** <!-- What the user should see/experience -->

---

## Kitchen Notes

### Known Limitations

<!-- List any limitations or edge cases not handled -->
- None identified

### Future Enhancements

<!-- Ideas for future improvement (may become new beads) -->
- None identified

### Deployment Notes

<!-- Any special deployment or migration considerations -->
- None required

---

## Related Work

### Features Completed

| Bead | Title | Acceptance Report |
|------|-------|-------------------|
| <!-- lc-xxx.1 --> | <!-- feature title --> | [docs/features/xxx.1-acceptance.md](../features/xxx.1-acceptance.md) |
| <!-- lc-xxx.2 --> | <!-- feature title --> | [docs/features/xxx.2-acceptance.md](../features/xxx.2-acceptance.md) |

### Related Epics

| Bead | Title | Relationship |
|------|-------|--------------|
| <!-- lc-yyy --> | <!-- epic title --> | <!-- blocks/blocked-by/related --> |

---

**Status:** Epic Complete and Validated

---

## Usage Instructions

> Remove this section when using the template.

1. Create directory if needed: `mkdir -p docs/features`
2. Copy this template to `docs/features/<epic-id>-acceptance.md`
3. Fill in all `<!-- placeholder -->` fields
4. Delete sections that don't apply
5. Run `/line:plate <feature-id>` on the last feature to trigger epic validation

### Section Guide

| Section | Purpose |
|---------|---------|
| **Service Overview** | High-level summary of epic capability |
| **Guest Journey Validation** | Document each E2E user journey tested |
| **Smoke Test Results** | Critical path smoke test outcomes |
| **Cross-Feature Integration** | How features work together |
| **Kitchen Staff Sign-Off** | Track all agent approvals |
| **Guest Experience** | Show users how to use the capability |
| **Kitchen Notes** | Capture limitations, ideas, deployment info |
| **Related Work** | Link to feature acceptance reports |

### When to Use This Template

Use this template when:
- All features of an epic are complete (plated)
- The critic agent has approved E2E coverage
- The epic is ready for final closure

This template is generated automatically during epic plate phase when the last feature of an epic completes.
