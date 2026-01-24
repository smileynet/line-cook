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

Run the test:

```bash
go test ./...
# FAIL: TestAuthService_ValidToken_ReturnsUser
```

**Rules:**
- Test must fail before proceeding
- Failure must be for the right reason
- Test describes desired behavior

**Quality Gate:** The taster agent reviews test quality after RED phase.

### GREEN: Make Test Pass

**Goal:** Write the minimum code to pass the test.

```go
type AuthService struct{}

func NewAuthService() *AuthService {
    return &AuthService{}
}

func (s *AuthService) ValidateToken(token string) (*User, error) {
    // Minimal implementation to pass test
    if token == "valid-token" {
        return &User{ID: "user-1"}, nil
    }
    return nil, errors.New("invalid token")
}
```

Run the test:

```bash
go test ./...
# PASS
```

**Rules:**
- Only write code to pass the current test
- Don't anticipate future requirements
- Don't refactor yet

### REFACTOR: Improve Code

**Goal:** Clean up while keeping tests green.

```go
func (s *AuthService) ValidateToken(token string) (*User, error) {
    // Refactored: Extract validation, improve error handling
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

Run tests after each change:

```bash
go test ./...
# PASS (still)
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
- No compiler errors
- No linter errors

### After REFACTOR Phase

The **sous-chef** agent reviews (during serve):

- Correctness (logic, edge cases)
- Security (input validation, injection)
- Style (naming, consistency)
- Completeness (task fully addressed)

## When to Use TDD vs BDD

| Situation | Use | Why |
|-----------|-----|-----|
| Implementing function | TDD | Low-level behavior |
| Adding feature | Both | BDD for acceptance, TDD for units |
| Fixing bug | TDD | Reproduce with test first |
| Refactoring | TDD | Safety net for changes |
| Feature validation | BDD | User perspective |

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

> "All auth tests go in auth_test.go (5000 lines)."

Problem: Hard to navigate, slow to run.

Fix: Split by feature/scenario, use subtests.

## Example: Complete TDD Flow

**Task:** Add email validation to user registration.

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
go test ./...
go build ./...

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
go test ./... -run TestFeature

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
