# Multi-Course Meal Acceptance Report

> Template for documenting feature (multi-course meal) completion during plate service.

**Feature:** <!-- Feature title -->
**Bead ID:** <!-- lc-xxx.y -->
**Plated:** <!-- YYYY-MM-DD (completion date) -->
**Parent Menu:** <!-- epic-id - epic-title -->

---

## Chef's Selection (User Story)

As a **<!-- user role -->**, I want **<!-- capability -->** so that **<!-- benefit -->**.

---

## Tasting Notes (Acceptance Criteria)

Each course (task) in this feature has been verified against acceptance criteria:

### Course 1: <!-- criterion name -->

- **Status:** Served
- **Verification:** <!-- how verified (test, demo, manual inspection) -->
- **Evidence:** <!-- test name, screenshot, or command output -->

### Course 2: <!-- criterion name -->

- **Status:** Served
- **Verification:** <!-- how verified -->
- **Evidence:** <!-- test name, screenshot, or command output -->

### Course 3: <!-- criterion name -->

- **Status:** Served
- **Verification:** <!-- how verified -->
- **Evidence:** <!-- test name, screenshot, or command output -->

<!-- Add more courses as needed -->

---

## Quality Checks (BDD Tests)

### Feature Test: `<!-- Test suite/describe block name for this feature -->`

<!-- Use your project's naming convention:
  Go: TestFeature_FeatureName  |  Python: TestFeatureName / test_feature_name
  JS/TS: describe('Feature: Name')  |  Rust: mod tests { fn test_feature_name } -->

**Purpose:** Validate <!-- aspect being validated -->

**Scenarios:**
| Scenario | Status | Description |
|----------|--------|-------------|
| `<!-- scenario_1 -->` | Passed | <!-- description --> |
| `<!-- scenario_2 -->` | Passed | <!-- description --> |
| `<!-- scenario_3 -->` | Passed | <!-- description --> |

**Results:** All scenarios passing

### Smoke Tests

End-to-end validation from user perspective:

| Test | Status | Notes |
|------|--------|-------|
| <!-- smoke test 1 --> | Passed | <!-- notes --> |
| <!-- smoke test 2 --> | Passed | <!-- notes --> |

**Results:** All smoke tests passing

---

## Kitchen Staff Sign-Off

Quality assurance by Line Cook agents:

| Agent | Role | Status |
|-------|------|--------|
| **Sous-Chef** | Code review | Approved |
| **Quality-Control** | Test quality | Approved |
| **Maître** | BDD test quality | Approved |

---

## Guest Experience

How users can verify this feature works:

```bash
# Example commands demonstrating the feature
<!-- command 1 -->
<!-- command 2 -->
```

**Expected Outcome:** <!-- what user should see/experience -->

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

## Related Orders

### Tasks Completed

| Bead | Title | Status |
|------|-------|--------|
| <!-- lc-xxx.y.1 --> | <!-- task title --> | Closed |
| <!-- lc-xxx.y.2 --> | <!-- task title --> | Closed |

### Related Features

| Bead | Title | Relationship |
|------|-------|--------------|
| <!-- lc-xxx.z --> | <!-- feature title --> | <!-- blocks/blocked-by/related --> |

---

**Status:** Feature Complete and Validated

---

## Usage Instructions

> Remove this section when using the template.

1. Create directory if needed: `mkdir -p docs/features`
2. Copy this template to `docs/features/<feature-id>-acceptance.md`
3. Fill in all `<!-- placeholder -->` fields
4. Delete sections that don't apply (e.g., deployment notes if none)
5. Run `/line:plate <feature-id>` to complete validation

### Section Guide

| Section | Purpose |
|---------|---------|
| **Chef's Selection** | User story from feature definition |
| **Tasting Notes** | Map acceptance criteria to verification |
| **Quality Checks** | Document BDD and smoke test results |
| **Kitchen Staff Sign-Off** | Track agent approvals |
| **Guest Experience** | Show users how to use the feature |
| **Kitchen Notes** | Capture limitations, ideas, deployment info |
| **Related Orders** | Link to tasks and related features |
