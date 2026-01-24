# Test Prep

> Prepare your testing mise en place before cooking begins.

Good test preparation ensures tests are isolated, fast, and meaningful. Like mise en place in a kitchen, everything should be in its place before execution begins.

## Quick Reference

| Test Type | Scope | Speed | When |
|-----------|-------|-------|------|
| **Unit** | Single function/class | Milliseconds | Every code change |
| **Integration** | Multiple components | Seconds | Feature completion |
| **BDD/Acceptance** | User scenario | Seconds-minutes | Feature validation |
| **Smoke** | Critical paths | Seconds | Before release |

## The Kitchen Analogy

Before service:

1. **Prep stations** - Each station has its ingredients ready (test fixtures)
2. **Clean equipment** - Tools are sanitized between uses (test isolation)
3. **Labeled containers** - Everything is clearly marked (test naming)
4. **Backup ingredients** - Spares ready if something goes wrong (test data factories)

## Test Structure

Every test follows the same pattern:

```
Setup → Execute → Validate → Cleanup
```

In kitchen terms:

```
Prep → Cook → Taste → Clean
```

### Setup (Prep)

Create the test environment:

```go
func TestFeature_Something(t *testing.T) {
    // Setup: Create test fixtures
    db := setupTestDatabase(t)
    service := NewService(db)

    // ... test continues
}
```

Rules:
- Use helper functions for common setup
- Create minimal fixtures (only what's needed)
- Isolate from other tests (no shared state)

### Execute (Cook)

Run the code under test:

```go
    // Execute: Call the function
    result, err := service.DoSomething(input)
```

Rules:
- Single action per test (usually)
- Capture all outputs
- Don't assert during execution

### Validate (Taste)

Check the results:

```go
    // Validate: Check expectations
    if err != nil {
        t.Fatalf("expected no error, got %v", err)
    }
    if result != expected {
        t.Errorf("expected %v, got %v", expected, result)
    }
```

Rules:
- Assert specific conditions
- Provide clear failure messages
- Check both success and failure paths

### Cleanup (Clean)

Reset for next test:

```go
    // Cleanup: Use t.Cleanup or defer
    t.Cleanup(func() {
        db.Close()
    })
```

Rules:
- Always cleanup, even on failure
- Use `t.Cleanup()` or `defer`
- Reset global state if modified

## Test Naming

Names should describe what's being tested and what's expected:

```
Test<Component>_<Scenario>_<ExpectedBehavior>
```

Examples:

```go
// Good: Clear what's tested and expected
func TestAuthService_InvalidToken_ReturnsUnauthorized(t *testing.T)
func TestUserRepo_DuplicateEmail_ReturnsConflictError(t *testing.T)

// Bad: Vague or missing context
func TestAuth(t *testing.T)
func Test1(t *testing.T)
```

## Test Isolation

Tests must not depend on each other:

```go
// Bad: Shared state between tests
var globalCounter int

func TestIncrement(t *testing.T) {
    globalCounter++
    // This depends on previous tests
}

// Good: Isolated state
func TestIncrement(t *testing.T) {
    counter := 0
    counter++
    // Each test starts fresh
}
```

### Isolation Techniques

1. **Fresh fixtures per test**
   ```go
   func TestSomething(t *testing.T) {
       db := createTestDB(t)  // New database per test
   }
   ```

2. **Parallel-safe design**
   ```go
   func TestSomething(t *testing.T) {
       t.Parallel()  // Safe to run concurrently
   }
   ```

3. **No shared files**
   ```go
   // Use t.TempDir() for temp files
   tmpDir := t.TempDir()
   ```

## Test Data

### Factories

Create test data with sensible defaults:

```go
func NewTestUser(t *testing.T, opts ...UserOption) *User {
    u := &User{
        ID:    uuid.New(),
        Name:  "Test User",
        Email: "test@example.com",
    }
    for _, opt := range opts {
        opt(u)
    }
    return u
}

// Usage
user := NewTestUser(t, WithName("Alice"), WithEmail("alice@example.com"))
```

### Fixtures

For complex scenarios, use fixture files:

```
testdata/
  fixtures/
    valid_config.yaml
    invalid_config.yaml
    large_input.json
```

Load with:

```go
data, err := os.ReadFile("testdata/fixtures/valid_config.yaml")
```

## Test Anti-patterns

### Flaky Tests

> Tests that sometimes pass, sometimes fail.

Causes:
- Timing dependencies
- Shared state
- External service calls

Fixes:
- Use mocks for external services
- Isolate test state
- Avoid `time.Sleep()` (use channels/conditions)

### Slow Tests

> Tests that take seconds or minutes.

Causes:
- Real database calls
- Network requests
- Excessive setup

Fixes:
- Use in-memory databases
- Mock external services
- Setup once, run multiple scenarios

### Fragile Tests

> Tests that break on unrelated changes.

Causes:
- Testing implementation details
- Over-mocking
- Asserting too much

Fixes:
- Test behavior, not implementation
- Assert minimum necessary
- Use integration tests for end-to-end

### Missing Error Cases

> Only testing the happy path.

Causes:
- Time pressure
- Optimism bias

Fixes:
- Table-driven tests with error cases
- Property-based testing
- Mutation testing

## Table-Driven Tests

Test multiple scenarios efficiently:

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid email", "user@example.com", false},
        {"missing @", "userexample.com", true},
        {"empty string", "", true},
        {"missing domain", "user@", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.email)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateEmail(%q) error = %v, wantErr %v",
                    tt.email, err, tt.wantErr)
            }
        })
    }
}
```

## Test Quality Checklist

Before marking tests complete:

- [ ] All tests pass consistently
- [ ] Tests are isolated (can run in any order)
- [ ] Tests are fast (< 1 second each for unit tests)
- [ ] Tests have clear names
- [ ] Both success and error paths covered
- [ ] No flaky behavior

## Related

- [TDD/BDD Workflow](./tdd-bdd.md) - When and how to write tests
- [Tracer Dishes](./tracer-dishes.md) - Integration tests for tracers
- [Workflow](./workflow.md) - Where testing fits in the cycle
