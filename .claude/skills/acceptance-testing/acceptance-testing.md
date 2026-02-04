---
name: acceptance-testing
description: Acceptance testing patterns across languages and project types. Use during plate phase, when writing BDD tests, creating smoke tests, or validating features for completion.
---

# Acceptance Testing

Best practices for acceptance testing, BDD tests, and smoke tests across languages and project types.

## When to Use

- During plate phase (feature validation)
- Writing BDD/acceptance tests for features
- Creating smoke tests for critical paths
- Choosing a testing approach for a new project type

## Quick Reference: Test Types by Project Type

| Project Type | Unit Tests | BDD/Acceptance Tests | Smoke Tests |
|---|---|---|---|
| CLI tool | Individual commands/functions | Command workflows end-to-end | Run key commands, check exit codes and output |
| Web app | Handlers/controllers | Browser automation (Playwright/Cypress) | Load pages, submit forms, check responses |
| Mobile app | Business logic/viewmodels | Device/emulator tests (Detox/Appium) | Launch app, navigate key flows |
| Game | Game logic/systems | Simulate player interactions | Launch, verify rendering, test basic inputs |
| Library/SDK | Public API surface | Test documented use cases | Import and call key functions |
| Docs-only | N/A | Content completeness checks | Validate links, cross-reference accuracy |

## BDD Test Patterns

### Given-When-Then Structure

Every BDD test follows this structure regardless of language:

```
Given: Initial state / preconditions
When:  Action taken by user
Then:  Expected observable outcome
```

### Multi-Language BDD Patterns

<details><summary>Go</summary>

```go
func TestFeature_FeatureName(t *testing.T) {
    t.Run("Acceptance_Criterion_1_description", func(t *testing.T) {
        // Given: describe preconditions
        setup := createTestFixture(t)

        // When: perform user action
        result, err := setup.service.DoAction(input)

        // Then: verify outcome
        if err != nil {
            t.Fatalf("expected no error, got %v", err)
        }
        if result.Status != "expected" {
            t.Errorf("expected status 'expected', got %q", result.Status)
        }
    })
}
```

**Naming:** `TestFeature_<FeatureName>` with `t.Run("Acceptance_Criterion_N_description")`

</details>

<details><summary>Python</summary>

```python
class TestFeature_FeatureName:
    def test_acceptance_criterion_1_description(self, client):
        # Given: describe preconditions
        fixture = create_test_fixture()

        # When: perform user action
        result = client.do_action(fixture.input)

        # Then: verify outcome
        assert result.status == "expected"
```

**Naming:** `class TestFeature_FeatureName` with `def test_acceptance_criterion_N_description`

**Frameworks:** pytest (recommended), behave (for Gherkin), pytest-bdd

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
describe('Feature: FeatureName', () => {
  it('Acceptance Criterion 1: description', async () => {
    // Given: describe preconditions
    const fixture = await createTestFixture();

    // When: perform user action
    const result = await service.doAction(fixture.input);

    // Then: verify outcome
    expect(result.status).toBe('expected');
  });
});
```

**Naming:** `describe('Feature: X')` with `it('Acceptance Criterion N: description')`

**Frameworks:** Jest, Vitest, Playwright (E2E), Cypress (E2E)

</details>

<details><summary>Rust</summary>

```rust
#[cfg(test)]
mod feature_feature_name {
    use super::*;

    #[test]
    fn acceptance_criterion_1_description() {
        // Given: describe preconditions
        let fixture = create_test_fixture();

        // When: perform user action
        let result = service.do_action(&fixture.input).unwrap();

        // Then: verify outcome
        assert_eq!(result.status, "expected");
    }
}
```

**Naming:** `mod feature_<name>` with `fn acceptance_criterion_N_description`

</details>

## Smoke Test Best Practices

Smoke tests verify that critical paths work without exercising every detail. They should be:

- **Fast** - Complete in seconds, not minutes
- **Critical-path only** - Test the most important user flows
- **End-to-end** - Exercise the real system, not mocks
- **Independent** - Each smoke test can run alone

### Smoke Test Patterns by Project Type

**CLI tool:**
```bash
# Run key commands, check exit codes and output
command --version && echo "PASS: version" || echo "FAIL: version"
command create --name test && echo "PASS: create" || echo "FAIL: create"
command list | grep -q "test" && echo "PASS: list" || echo "FAIL: list"
```

**Web app:**
```bash
# Check critical endpoints respond
curl -sf http://localhost:3000/ > /dev/null && echo "PASS: home"
curl -sf http://localhost:3000/api/health > /dev/null && echo "PASS: health"
curl -sf -X POST http://localhost:3000/api/login -d '{}' | grep -q "error\|token" && echo "PASS: login"
```

**Library/SDK:**
```python
# Import and call key functions
import mylib
result = mylib.core_function("test")
assert result is not None, "core_function returned None"
```

### Smoke Test Anti-Patterns

- **Too comprehensive** - Smoke tests should not be a full test suite; they check that the system starts and key paths work
- **Fragile assertions** - Don't assert exact output strings that change often; check exit codes and key indicators
- **External dependencies** - Smoke tests should not require external services to be running (unless testing integration)
- **Slow** - If a smoke test takes more than 30 seconds, it's too thorough for a smoke test

## E2E Test Best Practices

- Test user journeys, not individual pages/screens
- Use realistic data, not minimal fixtures
- Set up and tear down state per test (no test ordering)
- Prefer waiting for conditions over fixed timeouts
- Run in CI with headless browsers/emulators

### E2E Anti-Patterns

- **Flaky selectors** - Use data-testid attributes, not CSS classes or text content
- **Sleep-based waits** - Use explicit waits for conditions (`waitFor`, `expect.poll`)
- **Shared state** - Each test should create its own users/data
- **Testing implementation** - E2E tests should verify user-visible outcomes, not internal API responses

## Common Acceptance Testing Anti-Patterns

### Testing Implementation Instead of Behavior

```
# BAD: Tests internal state
assert service._internal_cache.size == 5

# GOOD: Tests user-observable outcome
assert service.get_items() == expected_items
```

### BDD Tests Without Given-When-Then

```
# BAD: No structure, unclear intent
def test_login():
    response = client.post("/login", data={"user": "a", "pass": "b"})
    assert response.status == 200

# GOOD: Clear structure
def test_successful_login(self):
    # Given: Valid user exists
    user = create_user("alice", "secret")
    # When: Login with correct credentials
    response = client.post("/login", data={"user": "alice", "pass": "secret"})
    # Then: Login succeeds
    assert response.status == 200
```

### Over-Reliance on Mocks in Acceptance Tests

Acceptance tests should exercise the real system as much as possible. Only mock external services you don't control (third-party APIs, email providers). Internal components should be tested with real implementations.

### Missing Error/Edge Case Scenarios

Every feature should have acceptance tests for:
- Happy path (primary use case)
- Error cases (invalid input, missing data, permission denied)
- Edge cases (empty lists, maximum values, concurrent access)

## See Also

- [TDD/BDD Workflow](../../docs/guidance/tdd-bdd.md) - Full TDD/BDD guidance
- [Test Setup](../../docs/guidance/test-setup.md) - Test infrastructure patterns
- [Feature Acceptance Template](../../docs/templates/feature-acceptance.md) - Acceptance documentation template
