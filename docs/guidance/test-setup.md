# Test Setup

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

<details><summary>Go</summary>

```go
func TestFeature_Something(t *testing.T) {
    // Setup: Create test fixtures
    db := setupTestDatabase(t)
    service := NewService(db)

    // ... test continues
}
```

</details>

<details><summary>Python</summary>

```python
def test_feature_something(db_session):
    # Setup: Create test fixtures (or use pytest fixtures)
    service = Service(db_session)

    # ... test continues
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
describe('Feature', () => {
  let service: Service;

  beforeEach(() => {
    // Setup: Create test fixtures
    const db = setupTestDatabase();
    service = new Service(db);
  });

  // ... tests continue
});
```

</details>

<details><summary>Rust</summary>

```rust
#[test]
fn feature_something() {
    // Setup: Create test fixtures
    let db = setup_test_database();
    let service = Service::new(db);

    // ... test continues
}
```

</details>

Rules:
- Use helper functions for common setup
- Create minimal fixtures (only what's needed)
- Isolate from other tests (no shared state)

### Execute (Cook)

Run the code under test:

```
result = service.do_something(input)
```

Rules:
- Single action per test (usually)
- Capture all outputs
- Don't assert during execution

### Validate (Taste)

Check the results:

<details><summary>Go</summary>

```go
    if err != nil {
        t.Fatalf("expected no error, got %v", err)
    }
    if result != expected {
        t.Errorf("expected %v, got %v", expected, result)
    }
```

</details>

<details><summary>Python</summary>

```python
    assert result == expected
    # or for errors:
    with pytest.raises(ExpectedError):
        service.do_something(bad_input)
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
    expect(result).toBe(expected);
    // or for errors:
    expect(() => service.doSomething(badInput)).toThrow(ExpectedError);
```

</details>

<details><summary>Rust</summary>

```rust
    assert_eq!(result, expected);
    // or for errors:
    assert!(matches!(result, Err(ExpectedError::Variant)));
```

</details>

Rules:
- Assert specific conditions
- Provide clear failure messages
- Check both success and failure paths

### Cleanup (Clean)

Reset for next test:

<details><summary>Go</summary>

```go
    t.Cleanup(func() {
        db.Close()
    })
```

</details>

<details><summary>Python</summary>

```python
# Use pytest fixtures with yield for cleanup
@pytest.fixture
def db_session():
    session = create_session()
    yield session
    session.close()
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
afterEach(() => {
  db.close();
});
```

</details>

<details><summary>Rust</summary>

```rust
// Use Drop trait for automatic cleanup, or explicit cleanup:
impl Drop for TestDb {
    fn drop(&mut self) {
        self.cleanup();
    }
}
```

</details>

Rules:
- Always cleanup, even on failure
- Use language-specific cleanup mechanisms (defer, fixtures, afterEach, Drop)
- Reset global state if modified

## Test Naming

Names should describe what's being tested and what's expected. Each language has its own conventions:

<details><summary>Go</summary>

```
Test<Component>_<Scenario>_<ExpectedBehavior>
```

```go
func TestAuthService_InvalidToken_ReturnsUnauthorized(t *testing.T)
func TestUserRepo_DuplicateEmail_ReturnsConflictError(t *testing.T)
```

</details>

<details><summary>Python</summary>

```
test_<component>_<scenario>_<expected_behavior>
```

```python
def test_auth_service_invalid_token_returns_unauthorized():
def test_user_repo_duplicate_email_returns_conflict_error():

# Or with classes:
class TestAuthService:
    def test_invalid_token_returns_unauthorized(self):
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```
describe('<Component>') + it('<scenario> <expected behavior>')
```

```typescript
describe('AuthService', () => {
  it('returns unauthorized for invalid token', () => { ... });
});
describe('UserRepo', () => {
  it('returns conflict error for duplicate email', () => { ... });
});
```

</details>

<details><summary>Rust</summary>

```
<component>_<scenario>_<expected_behavior>
```

```rust
#[test]
fn auth_service_invalid_token_returns_unauthorized() { ... }
#[test]
fn user_repo_duplicate_email_returns_conflict_error() { ... }
```

</details>

## Test Isolation

Tests must not depend on each other:

```
// Bad: Shared mutable state between tests
// Good: Each test creates its own state from scratch
```

### Isolation Techniques

1. **Fresh fixtures per test** - Create new test data for each test
2. **Parallel-safe design** - Tests can run concurrently without conflicts
3. **No shared files** - Use temp directories that are cleaned up automatically

## Test Data

### Factories

Create test data with sensible defaults:

<details><summary>Go</summary>

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

</details>

<details><summary>Python</summary>

```python
def make_user(**overrides) -> User:
    defaults = {
        "id": uuid4(),
        "name": "Test User",
        "email": "test@example.com",
    }
    defaults.update(overrides)
    return User(**defaults)

# Usage
user = make_user(name="Alice", email="alice@example.com")
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
function createTestUser(overrides: Partial<User> = {}): User {
  return {
    id: crypto.randomUUID(),
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  };
}

// Usage
const user = createTestUser({ name: 'Alice', email: 'alice@example.com' });
```

</details>

<details><summary>Rust</summary>

```rust
fn create_test_user() -> User {
    User {
        id: Uuid::new_v4(),
        name: "Test User".to_string(),
        email: "test@example.com".to_string(),
    }
}

// Or implement Default:
impl Default for User {
    fn default() -> Self {
        Self {
            id: Uuid::new_v4(),
            name: "Test User".to_string(),
            email: "test@example.com".to_string(),
        }
    }
}

// Usage
let user = User { name: "Alice".to_string(), ..Default::default() };
```

</details>

### Fixtures

For complex scenarios, use fixture files:

```
testdata/
  fixtures/
    valid_config.yaml
    invalid_config.yaml
    large_input.json
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
- Avoid sleep-based waiting (use polling/conditions)

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
- Parameterized/table-driven tests with error cases
- Property-based testing
- Mutation testing

## Parameterized / Table-Driven Tests

Test multiple scenarios efficiently:

<details><summary>Go</summary>

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

</details>

<details><summary>Python</summary>

```python
@pytest.mark.parametrize("email,should_raise", [
    ("user@example.com", False),
    ("userexample.com", True),
    ("", True),
    ("user@", True),
])
def test_validate_email(email, should_raise):
    if should_raise:
        with pytest.raises(InvalidEmailError):
            validate_email(email)
    else:
        validate_email(email)  # Should not raise
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
describe('validateEmail', () => {
  it.each([
    ['user@example.com', false],
    ['userexample.com', true],
    ['', true],
    ['user@', true],
  ])('validates %s (should error: %s)', (email, shouldThrow) => {
    if (shouldThrow) {
      expect(() => validateEmail(email)).toThrow();
    } else {
      expect(() => validateEmail(email)).not.toThrow();
    }
  });
});
```

</details>

<details><summary>Rust</summary>

```rust
#[test]
fn validate_email_cases() {
    let cases = vec![
        ("user@example.com", false),
        ("userexample.com", true),
        ("", true),
        ("user@", true),
    ];

    for (email, should_err) in cases {
        let result = validate_email(email);
        assert_eq!(result.is_err(), should_err,
            "validate_email({:?}) error = {:?}, want_err = {}",
            email, result, should_err);
    }
}
```

</details>

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
- [Vertical Slicing](./vertical-slicing.md) - Integration tests for tracers
- [Workflow](./workflow.md) - Where testing fits in the cycle
