# TDD/BDD Workflow

> Red-Green-Refactor with quality gates at each phase.

Test-Driven Development (TDD) ensures code works by writing tests first. Behavior-Driven Development (BDD) ensures features work by testing user scenarios.

## Core Principles

**TDD (Test-Driven Development)** = Task-level implementation = **Individual prep**
**BDD (Behavior-Driven Development)** = Feature-level validation = **Course tasting**

```
Epic: Kitchen Service (Multi-course meal)
├── Feature: Appetizers ready on demand (Course tasting - BDD)
│   ├── Task: Prep mise en place (Individual prep - TDD)
│   ├── Task: Implement plating station (Individual prep - TDD)
│   └── Task: Configure timing system (Individual prep - TDD)
└── Feature: Main course coordination (Course tasting - BDD)
    └── ...
```

## Quick Reference

| Phase | What | Signal |
|-------|------|--------|
| **RED** | Write failing test | Test fails as expected |
| **GREEN** | Make test pass | Minimal code to pass |
| **REFACTOR** | Improve code | Tests still pass |

## The Kitchen Analogy

**Task = TDD = Individual Prep**
- Each ingredient prepped to specification
- Red: Define what "properly diced" means
- Green: Dice until it matches spec
- Refactor: Improve technique, same result

**Feature = BDD = Course Tasting**
- All prepped items combine into a dish
- Validate the complete dish works together
- Guest perspective: does the course deliver?

**Epic = Multi-course Meal**
- Multiple courses (features) compose the meal
- Each course validated independently
- Full meal validated at service

## TDD Cycle

### RED: Write Failing Test

**Goal:** Define what success looks like before writing code.

Write a test that describes the desired behavior, then run it to confirm it fails.

<details><summary>Go</summary>

```go
func TestAuthService_ValidToken_ReturnsUser(t *testing.T) {
    service := NewAuthService()

    user, err := service.ValidateToken("valid-token")

    if err != nil {
        t.Fatalf("expected no error, got %v", err)
    }
    if user.ID == "" {
        t.Error("expected user ID to be set")
    }
}
```

```bash
go test ./...
# FAIL: TestAuthService_ValidToken_ReturnsUser
```

</details>

<details><summary>Python</summary>

```python
def test_auth_service_valid_token_returns_user():
    service = AuthService()

    user = service.validate_token("valid-token")

    assert user.id != ""
```

```bash
pytest
# FAILED: test_auth_service_valid_token_returns_user
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
describe('AuthService', () => {
  it('returns user for valid token', () => {
    const service = new AuthService();

    const user = service.validateToken('valid-token');

    expect(user.id).toBeDefined();
  });
});
```

```bash
npm test
# FAIL: AuthService > returns user for valid token
```

</details>

<details><summary>Rust</summary>

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn auth_service_valid_token_returns_user() {
        let service = AuthService::new();

        let user = service.validate_token("valid-token").unwrap();

        assert!(!user.id.is_empty());
    }
}
```

```bash
cargo test
# FAILED: auth_service_valid_token_returns_user
```

</details>

**Rules:**
- Test must fail before proceeding
- Failure must be for the right reason
- Test describes desired behavior

**Quality Gate:** The taster agent reviews test quality after RED phase.

### GREEN: Make Test Pass

**Goal:** Write the minimum code to pass the test.

<details><summary>Go</summary>

```go
type AuthService struct{}

func NewAuthService() *AuthService {
    return &AuthService{}
}

func (s *AuthService) ValidateToken(token string) (*User, error) {
    if token == "valid-token" {
        return &User{ID: "user-1"}, nil
    }
    return nil, errors.New("invalid token")
}
```

```bash
go test ./...
# PASS
```

</details>

<details><summary>Python</summary>

```python
class AuthService:
    def validate_token(self, token: str) -> User:
        if token == "valid-token":
            return User(id="user-1")
        raise InvalidTokenError("invalid token")
```

```bash
pytest
# PASSED
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
class AuthService {
  validateToken(token: string): User {
    if (token === 'valid-token') {
      return { id: 'user-1' };
    }
    throw new Error('invalid token');
  }
}
```

```bash
npm test
# PASS
```

</details>

<details><summary>Rust</summary>

```rust
impl AuthService {
    pub fn new() -> Self { Self {} }

    pub fn validate_token(&self, token: &str) -> Result<User, AuthError> {
        if token == "valid-token" {
            Ok(User { id: "user-1".to_string() })
        } else {
            Err(AuthError::InvalidToken)
        }
    }
}
```

```bash
cargo test
# ok
```

</details>

**Rules:**
- Only write code to pass the current test
- Don't anticipate future requirements
- Don't refactor yet

### REFACTOR: Improve Code

**Goal:** Clean up while keeping tests green.

<details><summary>Go</summary>

```go
func (s *AuthService) ValidateToken(token string) (*User, error) {
    if err := s.validateTokenFormat(token); err != nil {
        return nil, fmt.Errorf("invalid token format: %w", err)
    }

    user, err := s.lookupToken(token)
    if err != nil {
        return nil, fmt.Errorf("token lookup failed: %w", err)
    }

    return user, nil
}
```

</details>

<details><summary>Python</summary>

```python
class AuthService:
    def validate_token(self, token: str) -> User:
        self._validate_token_format(token)
        return self._lookup_token(token)
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
class AuthService {
  validateToken(token: string): User {
    this.validateTokenFormat(token);
    return this.lookupToken(token);
  }
}
```

</details>

<details><summary>Rust</summary>

```rust
impl AuthService {
    pub fn validate_token(&self, token: &str) -> Result<User, AuthError> {
        self.validate_token_format(token)?;
        self.lookup_token(token)
    }
}
```

</details>

Run tests after each change:

```bash
<test command>  # e.g., go test ./..., pytest, npm test, cargo test
# Should still PASS
```

**Rules:**
- Keep tests passing at all times
- Improve structure, naming, clarity
- Extract common patterns
- Remove duplication

## BDD for Features

While TDD is for unit/integration tests, BDD is for feature acceptance:

### User Story → Scenarios → Tests

```gherkin
Feature: User Authentication
  As a user
  I want to log in with my credentials
  So that I can access my account

  Scenario: Successful login
    Given I have valid credentials
    When I submit the login form
    Then I should be redirected to my dashboard
    And I should see my username in the header

  Scenario: Invalid password
    Given I have an incorrect password
    When I submit the login form
    Then I should see an error message
    And I should remain on the login page
```

### BDD Test Structure

Translate Gherkin scenarios into tests using your project's language and framework:

<details><summary>Go</summary>

```go
func TestFeature_UserAuthentication(t *testing.T) {
    t.Run("Acceptance_Criterion_1_Successful_login", func(t *testing.T) {
        // Given: Valid credentials exist
        user := NewTestUser(t, WithCredentials("user", "pass"))

        // When: Submit login form
        response := client.Login("user", "pass")

        // Then: Redirected to dashboard
        if response.StatusCode != http.StatusFound {
            t.Errorf("expected redirect, got %d", response.StatusCode)
        }
        if response.Header.Get("Location") != "/dashboard" {
            t.Error("expected redirect to dashboard")
        }
    })

    t.Run("Acceptance_Criterion_2_Invalid_password", func(t *testing.T) {
        // Given: User exists with different password
        user := NewTestUser(t, WithCredentials("user", "correct"))

        // When: Submit with wrong password
        response := client.Login("user", "wrong")

        // Then: Error shown, stay on page
        if response.StatusCode != http.StatusUnauthorized {
            t.Errorf("expected 401, got %d", response.StatusCode)
        }
    })
}
```

</details>

<details><summary>Python</summary>

```python
class TestFeature_UserAuthentication:
    def test_acceptance_criterion_1_successful_login(self, client, test_user):
        # Given: Valid credentials exist
        user = test_user(username="user", password="pass")

        # When: Submit login form
        response = client.post("/login", data={"username": "user", "password": "pass"})

        # Then: Redirected to dashboard
        assert response.status_code == 302
        assert response.headers["Location"] == "/dashboard"

    def test_acceptance_criterion_2_invalid_password(self, client, test_user):
        # Given: User exists with different password
        user = test_user(username="user", password="correct")

        # When: Submit with wrong password
        response = client.post("/login", data={"username": "user", "password": "wrong"})

        # Then: Error shown, stay on page
        assert response.status_code == 401
```

</details>

<details><summary>JavaScript/TypeScript</summary>

```typescript
describe('Feature: User Authentication', () => {
  it('Acceptance Criterion 1: Successful login', async () => {
    // Given: Valid credentials exist
    const user = await createTestUser({ username: 'user', password: 'pass' });

    // When: Submit login form
    const response = await client.post('/login', { username: 'user', password: 'pass' });

    // Then: Redirected to dashboard
    expect(response.status).toBe(302);
    expect(response.headers.location).toBe('/dashboard');
  });

  it('Acceptance Criterion 2: Invalid password', async () => {
    // Given: User exists with different password
    const user = await createTestUser({ username: 'user', password: 'correct' });

    // When: Submit with wrong password
    const response = await client.post('/login', { username: 'user', password: 'wrong' });

    // Then: Error shown, stay on page
    expect(response.status).toBe(401);
  });
});
```

</details>

<details><summary>Rust</summary>

```rust
#[cfg(test)]
mod feature_user_authentication {
    use super::*;

    #[test]
    fn acceptance_criterion_1_successful_login() {
        // Given: Valid credentials exist
        let user = create_test_user("user", "pass");

        // When: Submit login form
        let response = client.login("user", "pass");

        // Then: Redirected to dashboard
        assert_eq!(response.status(), StatusCode::FOUND);
        assert_eq!(response.header("Location"), Some("/dashboard"));
    }

    #[test]
    fn acceptance_criterion_2_invalid_password() {
        // Given: User exists with different password
        let user = create_test_user("user", "correct");

        // When: Submit with wrong password
        let response = client.login("user", "wrong");

        // Then: Error shown, stay on page
        assert_eq!(response.status(), StatusCode::UNAUTHORIZED);
    }
}
```

</details>

## Quality Gates

Line Cook enforces quality gates at each phase:

### After RED Phase

The **taster** agent reviews:

- Test isolation (no shared state)
- Clear naming (describes behavior)
- Proper structure (Setup-Execute-Validate-Cleanup)
- No anti-patterns (flaky, slow, fragile)

If critical issues found, address before GREEN.

### After GREEN Phase

Automatic checks:

- All tests pass
- No compiler/interpreter errors
- No linter errors

### After REFACTOR Phase

The **sous-chef** agent reviews (during serve):

- Correctness (logic, edge cases)
- Security (input validation, injection)
- Style (naming, consistency)
- Completeness (task fully addressed)

### After Feature/Epic Completion

See [Workflow Quality Gates](./workflow.md#quality-gates) for plate-phase gates:
- **Maître** reviews feature BDD tests
- **Critic** reviews epic E2E coverage

## When to Use TDD vs BDD

| Situation | Use | Why |
|-----------|-----|-----|
| Implementing function | TDD | Low-level behavior |
| Adding feature | Both | BDD for acceptance, TDD for units |
| Fixing bug | TDD | Reproduce with test first |
| Refactoring | TDD | Safety net for changes |
| Feature validation | BDD | User perspective |

## Project Type Considerations

Different project types have different testing approaches:

| Project Type | Unit Test Approach | BDD/Acceptance Approach | Smoke Test Approach |
|---|---|---|---|
| CLI tool | Test individual commands/functions | Test command workflows end-to-end | Run key commands, check exit codes and output |
| Web app | Test handlers/controllers | Browser automation (Playwright/Cypress) | Load pages, submit forms, check responses |
| Mobile app | Test business logic/viewmodels | Device/emulator tests (Detox/Appium) | Launch app, navigate key flows |
| Game | Test game logic/systems | Simulate player interactions | Launch, verify rendering, test basic inputs |
| Library/SDK | Test public API surface | Test documented use cases | Import and call key functions |
| Docs-only | N/A | Content completeness checks | Validate links, cross-reference accuracy |

## TDD Anti-patterns

### Testing After Implementation

> "I'll write the tests after the code works."

Problem: Tests don't drive design, edge cases missed.

Fix: Always write failing test first.

### Over-Mocking

> "I'll mock everything except the function under test."

Problem: Tests pass but integration fails.

Fix: Mock only external dependencies; use integration tests.

### Testing Implementation

> "Check that internal method was called 3 times."

Problem: Tests break on refactoring.

Fix: Test behavior/output, not internal calls.

### Long Test Files

> "All auth tests go in one file (5000 lines)."

Problem: Hard to navigate, slow to run.

Fix: Split by feature/scenario, use subtests.

## Example: Complete TDD Flow

**Task:** Add email validation to user registration.

<details><summary>Go</summary>

**RED:**

```go
func TestUserService_Register_InvalidEmail_ReturnsError(t *testing.T) {
    service := NewUserService()

    _, err := service.Register("invalid-email", "password123")

    if err == nil {
        t.Error("expected error for invalid email")
    }
    if !errors.Is(err, ErrInvalidEmail) {
        t.Errorf("expected ErrInvalidEmail, got %v", err)
    }
}
```

Run: `FAIL`

**GREEN:**

```go
var ErrInvalidEmail = errors.New("invalid email format")

func (s *UserService) Register(email, password string) (*User, error) {
    if !strings.Contains(email, "@") {
        return nil, ErrInvalidEmail
    }
    // ... existing registration logic
}
```

Run: `PASS`

**REFACTOR:**

```go
func (s *UserService) Register(email, password string) (*User, error) {
    if err := s.validateEmail(email); err != nil {
        return nil, err
    }
    // ... existing registration logic
}

func (s *UserService) validateEmail(email string) error {
    if !emailRegex.MatchString(email) {
        return ErrInvalidEmail
    }
    return nil
}

var emailRegex = regexp.MustCompile(`^[^@]+@[^@]+\.[^@]+$`)
```

Run: `PASS`

</details>

<details><summary>Python</summary>

**RED:**

```python
def test_user_service_register_invalid_email_returns_error():
    service = UserService()

    with pytest.raises(InvalidEmailError):
        service.register("invalid-email", "password123")
```

Run: `FAIL`

**GREEN:**

```python
class UserService:
    def register(self, email: str, password: str) -> User:
        if "@" not in email:
            raise InvalidEmailError("invalid email format")
        # ... existing registration logic
```

Run: `PASS`

**REFACTOR:**

```python
import re

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

class UserService:
    def register(self, email: str, password: str) -> User:
        self._validate_email(email)
        # ... existing registration logic

    def _validate_email(self, email: str) -> None:
        if not EMAIL_REGEX.match(email):
            raise InvalidEmailError("invalid email format")
```

Run: `PASS`

</details>

<details><summary>JavaScript/TypeScript</summary>

**RED:**

```typescript
describe('UserService', () => {
  it('rejects invalid email on registration', () => {
    const service = new UserService();

    expect(() => service.register('invalid-email', 'password123'))
      .toThrow(InvalidEmailError);
  });
});
```

Run: `FAIL`

**GREEN:**

```typescript
class UserService {
  register(email: string, password: string): User {
    if (!email.includes('@')) {
      throw new InvalidEmailError('invalid email format');
    }
    // ... existing registration logic
  }
}
```

Run: `PASS`

**REFACTOR:**

```typescript
const EMAIL_REGEX = /^[^@]+@[^@]+\.[^@]+$/;

class UserService {
  register(email: string, password: string): User {
    this.validateEmail(email);
    // ... existing registration logic
  }

  private validateEmail(email: string): void {
    if (!EMAIL_REGEX.test(email)) {
      throw new InvalidEmailError('invalid email format');
    }
  }
}
```

Run: `PASS`

</details>

<details><summary>Rust</summary>

**RED:**

```rust
#[test]
fn user_service_register_invalid_email_returns_error() {
    let service = UserService::new();

    let result = service.register("invalid-email", "password123");

    assert!(matches!(result, Err(RegistrationError::InvalidEmail)));
}
```

Run: `FAIL`

**GREEN:**

```rust
impl UserService {
    pub fn register(&self, email: &str, password: &str) -> Result<User, RegistrationError> {
        if !email.contains('@') {
            return Err(RegistrationError::InvalidEmail);
        }
        // ... existing registration logic
    }
}
```

Run: `PASS`

**REFACTOR:**

```rust
use regex::Regex;
use std::sync::LazyLock;

static EMAIL_REGEX: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^[^@]+@[^@]+\.[^@]+$").unwrap()
});

impl UserService {
    pub fn register(&self, email: &str, password: &str) -> Result<User, RegistrationError> {
        self.validate_email(email)?;
        // ... existing registration logic
    }

    fn validate_email(&self, email: &str) -> Result<(), RegistrationError> {
        if !EMAIL_REGEX.is_match(email) {
            return Err(RegistrationError::InvalidEmail);
        }
        Ok(())
    }
}
```

Run: `PASS`

</details>

## Task Workflow (TDD/Individual Prep)

```bash
# 1. Claim task
/line:cook <task-id>

# 2. RED: Write failing test
# Define what success looks like

# 3. GREEN: Implement minimal code
# Make the test pass

# 4. REFACTOR: Clean up
# Improve without breaking tests

# 5. Verify
<test command>   # e.g., go test ./..., pytest, npm test, cargo test
<build command>  # e.g., go build ./..., npm run build, cargo build

# 6. Close task
bd close <task-id>
```

**Task complete when:**
- All unit tests pass
- Code builds without errors
- Coverage meets threshold (>80%)

## Feature Workflow (BDD/Course Tasting)

After all tasks in a feature complete:

```bash
# 1. Write feature acceptance tests
# Map each acceptance criterion to a test

# 2. Run feature tests
<feature test command>  # e.g., go test -run TestFeature, pytest -k "test_feature", npm test -- --grep "Feature"

# 3. Verify all acceptance criteria pass
# Each criterion = one test case

# 4. Document results (optional)
# Add to docs/testing/ if complex

# 5. Close feature
bd close <feature-id>
```

**Feature complete when:**
- All acceptance criteria have passing tests
- Tests use Given-When-Then structure
- Tests map 1:1 to acceptance criteria
- Real-world scenarios validated

## Quality Checklist

### TDD Unit Tests (Task-level / Individual Prep)

- [ ] Tests written before implementation
- [ ] One test per function/method
- [ ] Fast (< 100ms each)
- [ ] Isolated (no shared state)
- [ ] Clear test names
- [ ] Minimal mocking

### BDD Feature Tests (Feature-level / Course Tasting)

- [ ] Maps to acceptance criteria
- [ ] Given-When-Then structure
- [ ] User-centric language
- [ ] Real-world scenarios
- [ ] Error cases included
- [ ] Self-documenting test names

## Related

- [Test Setup](./test-setup.md) - Setting up test infrastructure
- [Vertical Slicing](./vertical-slicing.md) - Integration testing vertical slices
- [Workflow](./workflow.md) - Where TDD fits in the cook phase
