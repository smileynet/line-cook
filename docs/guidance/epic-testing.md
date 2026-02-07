# Epic-Level Testing

> End-to-end validation for complete capabilities.

Epic-level tests validate that multiple features work together to deliver a complete user experience. While tasks have unit tests (TDD) and features have acceptance tests (BDD), epics need E2E and smoke tests.

## Quick Reference

```
Epic (Full Service)
├── Feature 1 (BDD tests) ─ validated by maître
├── Feature 2 (BDD tests) ─ validated by maître
└── Feature 3 (BDD tests) ─ validated by maître
    └── Epic E2E tests ─ validated by critic
```

| Tier | Testing Style | Agent | Focus |
|------|---------------|-------|-------|
| **Task** | TDD (Red-Green-Refactor) | Taster | Test isolation, structure |
| **Feature** | BDD (Given-When-Then) | Maître | Acceptance criteria |
| **Epic** | E2E (User Journeys) | Critic | Cross-feature integration |

## The Kitchen Analogy

**Task = Individual Prep** — Each ingredient prepped to specification
**Feature = Course Tasting** — Complete dish works as intended
**Epic = Full Service** — The entire meal delivers a satisfying experience

Epic testing asks: "Did the guest leave satisfied with the complete dining experience?"

- **Smoke test** = Quick taste before serving (does the critical path work?)
- **E2E test** = Simulated dining experience (realistic user journey)
- **User journey** = The path a guest takes through the meal

## When to Write Epic-Level Tests

Write epic-level tests when:
- Multiple features must work together
- Critical user paths span feature boundaries
- The epic represents a complete, shippable capability
- User journeys require cross-feature data flow

**Keep coverage focused:**
- Test critical paths, not every path
- Prefer few reliable tests over many flaky ones
- E2E tests are expensive — use sparingly

## Choosing Your Approach

Epic-level testing approach varies by project type:

| Project Type | Simulation Approach | Key Tools | Pattern |
|--------------|-------------------|-----------|---------|
| **Web App** | Browser automation | Playwright, Cypress | Page Object + User Journeys |
| **CLI** | Process automation | Pexpect, BATS, CliRunner | Snapshot + Workflow |
| **Mobile** | Device automation | Appium, Detox | Cross-device matrix |
| **Desktop** | UI automation | WinAppDriver, Appium | Platform-specific |
| **Game** | Input replay + bots | Custom engines | Deterministic replay |
| **API/Backend** | Contract + load | Pact, Gatling | Consumer-driven |
| **Library/SDK** | Integration tests | Native test frameworks | Public API coverage |

### Web App

**Browser automation** simulates real users:

```typescript
// Playwright example: User registration journey
test('complete user registration flow', async ({ page }) => {
  // Journey: Landing → Signup → Verification → Dashboard
  await page.goto('/');
  await page.click('[data-testid="signup-button"]');
  await page.fill('#email', 'test@example.com');
  await page.fill('#password', 'SecurePass123');
  await page.click('[type="submit"]');

  // Crosses signup feature → verification feature
  await expect(page).toHaveURL('/verify-email');
  await page.fill('#verification-code', '123456');
  await page.click('[type="submit"]');

  // Crosses verification → dashboard feature
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('.welcome-message')).toContainText('test@example.com');
});
```

### CLI

**Process automation** runs commands and validates output:

```bash
# BATS example: Full workflow journey
@test "complete task workflow" {
  # Journey: create → work → complete
  run bd create --title="Test task" --type=task
  [ "$status" -eq 0 ]

  TASK_ID=$(echo "$output" | grep -oP 'Created: \K[^\s]+')

  run bd update "$TASK_ID" --status=in_progress
  [ "$status" -eq 0 ]

  run bd close "$TASK_ID"
  [ "$status" -eq 0 ]

  run bd show "$TASK_ID"
  [[ "$output" =~ "status: closed" ]]
}
```

```python
# Pexpect example: Interactive CLI journey
def test_interactive_setup_wizard():
    child = pexpect.spawn('myapp init')

    child.expect('Project name:')
    child.sendline('my-project')

    child.expect('Choose template:')
    child.sendline('1')  # Select first template

    child.expect('Setup complete!')
    child.wait()

    assert os.path.exists('my-project/config.yaml')
```

### Mobile

**Device automation** tests on real or emulated devices:

```javascript
// Detox example: Onboarding journey
describe('Onboarding Flow', () => {
  it('completes full onboarding journey', async () => {
    // Journey: Welcome → Permissions → Tutorial → Home
    await element(by.id('welcome-continue')).tap();

    await element(by.id('allow-notifications')).tap();
    await element(by.id('skip-location')).tap();

    await element(by.id('tutorial-next')).tap();
    await element(by.id('tutorial-next')).tap();
    await element(by.id('tutorial-done')).tap();

    await expect(element(by.id('home-screen'))).toBeVisible();
  });
});
```

### API/Backend

**Contract and integration tests** validate service boundaries:

```python
# Integration test: User flow across services
def test_complete_order_flow(api_client, db):
    # Journey: Auth → Cart → Checkout → Order History

    # Login (auth service)
    token = api_client.post('/auth/login', {
        'email': 'test@example.com',
        'password': 'password'
    }).json()['token']

    # Add to cart (cart service)
    api_client.post('/cart/add',
        json={'product_id': 'SKU-123', 'quantity': 2},
        headers={'Authorization': f'Bearer {token}'}
    )

    # Checkout (order service)
    order = api_client.post('/checkout',
        headers={'Authorization': f'Bearer {token}'}
    ).json()

    assert order['status'] == 'confirmed'
    assert order['items'][0]['product_id'] == 'SKU-123'

    # Verify in history (order service)
    history = api_client.get('/orders',
        headers={'Authorization': f'Bearer {token}'}
    ).json()

    assert any(o['id'] == order['id'] for o in history)
```

### Game

**Deterministic replay and bot testing** for reproducible scenarios:

```python
# Input replay test
def test_level_completion():
    game = GameInstance()
    game.load_level('tutorial')

    # Replay recorded inputs
    game.replay_inputs('recordings/tutorial_completion.json')

    assert game.current_screen == 'level_complete'
    assert game.score >= 1000

# Bot-driven test
def test_ai_can_complete_tutorial():
    game = GameInstance()
    bot = TutorialBot()

    game.load_level('tutorial')

    while not game.is_level_complete():
        action = bot.decide(game.state)
        game.apply_action(action)

    assert game.is_level_complete()
```

## Cross-Cutting Patterns

These principles apply regardless of project type:

### Determinism

Make tests reproducible:
- Control random seeds
- Mock external time/date
- Use consistent test data
- Avoid environment-dependent paths

### Minimal Coverage

Test critical paths only:
- Identify the 3-5 most important user journeys
- Cover the "happy path" for each
- Add one error scenario per journey
- Don't test every permutation

### Observability

Make failures debuggable:
- Capture screenshots/recordings on failure (UI tests)
- Include request/response logs (API tests)
- Use trace IDs across services
- Store test artifacts for investigation

### Record/Replay

Capture minimal state for reproduction:
- Record failing scenarios for regression tests
- Store sanitized production traces
- Use snapshot testing for complex outputs

## Smoke Test Design

Smoke tests are the minimum E2E checks that validate critical functionality:

**Characteristics:**
- Fast (seconds, not minutes)
- Reliable (no flakiness)
- Critical path only
- Run on every deploy

**Example smoke test structure:**

```bash
#!/bin/bash
# smoke-test.sh

set -e

echo "=== Smoke Test: Core Functionality ==="

# Critical Path 1: Application starts
echo "Testing: Application startup..."
timeout 10 ./myapp --version || { echo "FAIL: App won't start"; exit 1; }

# Critical Path 2: Basic operation works
echo "Testing: Basic operation..."
./myapp create-item "test" > /dev/null || { echo "FAIL: Create failed"; exit 1; }

# Critical Path 3: Data persists
echo "Testing: Data persistence..."
./myapp list | grep -q "test" || { echo "FAIL: Data not persisted"; exit 1; }

# Cleanup
./myapp delete-item "test" 2>/dev/null || true

echo "=== All smoke tests passed ==="
```

## Antipatterns to Avoid

### Ice Cream Cone

**Problem:** More E2E tests than unit tests (inverted pyramid).

**Fix:** Keep E2E tests minimal. Most coverage should be unit tests.

### Flaky Tests

**Problem:** Tests pass/fail inconsistently due to timing, network, or state.

**Fix:**
- Add proper waits (not sleeps)
- Isolate test state
- Mock unreliable external services
- Retry with exponential backoff for network tests

### Slow Suites

**Problem:** E2E tests take so long they don't run regularly.

**Fix:**
- Parallelize independent tests
- Use test sharding
- Run full suite nightly, smoke tests on every commit

### Over-Testing

**Problem:** Testing every path end-to-end.

**Fix:** Critical paths only. Trust unit tests for edge cases.

### Environment Coupling

**Problem:** Tests only work in specific environments.

**Fix:**
- Use containers for consistent environments
- Mock external dependencies
- Configure via environment variables

### Simulated Testing

**Problem:** Tests use mocks or stubs that simulate behavior instead of exercising actual system interfaces. They prove mocks work, not the feature.

**Fix:** Feature and epic tests must exercise real interfaces. If the system creates files, create real files. If it calls a CLI, run the real CLI. Reserve mocks for unit tests and external third-party services only.

## Quality Checklist

Before closing an epic, verify:

### User Journeys
- [ ] Critical user journeys identified (3-5 max)
- [ ] Each journey has E2E test coverage
- [ ] Journeys test cross-feature integration
- [ ] Error paths have at least one journey

### Smoke Tests
- [ ] Smoke tests exist for critical paths
- [ ] Smoke tests run in < 5 minutes
- [ ] Smoke tests are reliable (no flakiness)
- [ ] Smoke tests run on every deploy

### Integration
- [ ] Data flows correctly between features
- [ ] State transitions are validated
- [ ] Error handling works across boundaries
- [ ] No features break each other

### Approach
- [ ] Testing approach fits project type
- [ ] No antipatterns (ice cream cone, flaky, slow)
- [ ] Tests are observable (logs, traces, artifacts)
- [ ] Tests are deterministic

## Epic Validation Workflow

When the last feature of an epic completes:

```bash
# 1. Run all tests
<test command>

# 2. Run smoke tests
./scripts/smoke-test.sh

# 3. Invoke critic for E2E review
# (Automatic during epic plate phase)

# 4. Generate epic acceptance report
# docs/features/<epic-id>-acceptance.md

# 5. Close epic
bd close <epic-id>
```

## Related

- [TDD/BDD Workflow](./tdd-bdd.md) - Task and feature-level testing
- [Workflow](./workflow.md) - Where epic testing fits in the cycle
- [ADR 0010](../decisions/0010-epic-level-testing-strategy.md) - Decision record for this approach
