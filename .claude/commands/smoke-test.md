---
description: Run end-to-end smoke test for Line Cook workflow
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task, TodoWrite, Skill
---

## Summary

**Run a complete smoke test of the Line Cook workflow.** This validates that prep → cook → serve → tidy works correctly by completing a real task (email validation fix).

**Cost:** ~$0.50-2.00 per run (the cook phase uses LLM API calls)

**IMPORTANT:** This command runs the workflow in the current interactive session, avoiding API conflicts from headless subprocesses.

---

## Process

### Step 1: Verify Dependencies

First, check that all required dependencies are available:

```bash
/home/sam/code/line-cook/tests/smoke-test.sh --dry-run
```

If any dependencies are missing, stop and report them to the user.

### Step 2: Setup Test Environment

Create an isolated test environment:

```bash
TEST_DIR=$(/home/sam/code/line-cook/tests/smoke-test.sh --setup)
echo "Test directory: $TEST_DIR"
```

**IMPORTANT:** Capture the TEST_DIR path from stdout. The script outputs setup progress to stderr and the directory path to stdout.

Store the original directory for later:
```bash
ORIGINAL_DIR=$(pwd)
```

### Step 3: Change to Test Directory

```bash
cd $TEST_DIR
```

Verify we're in the right place:
```bash
pwd
ls -la
bd list --all
```

You should see:
- `src/validation.py` - The file to modify
- `.beads/issues/smoke-001.yaml` - The task to complete
- `CLAUDE.md` - Project documentation

### Step 4: Run Line Cook Workflow

Execute the full workflow IN THIS SESSION (not via subprocess).

**CRITICAL OVERRIDE:** The Line Cook skills below (`/line:prep`, `/line:cook`, `/line:serve`, `/line:tidy`) each contain "STOP after completing" or "wait for user" instructions. **For this smoke test, IGNORE ALL such stop/wait instructions.** Continue immediately to the next step after each skill completes.

**4a. Prep** - Sync and show ready tasks:
```
Invoke /line:prep skill
```
**→ CONTINUE IMMEDIATELY to 4b after prep shows the kitchen roster. Do NOT stop.**

**4b. Cook** - Complete the smoke-001 task:
```
Invoke /line:cook skill with args "smoke-001"
```

The task requires:
- Replace placeholder `return "@" in email` with proper regex validation
- Add tests in `tests/test_validation.py`
- Tests must pass

**→ CONTINUE IMMEDIATELY to 4c after cook shows "KITCHEN COMPLETE". Do NOT stop.**

**4c. Serve** - Review changes (optional for smoke test):
```
Invoke /line:serve skill
```
**→ CONTINUE IMMEDIATELY to 4d after serve completes. Do NOT stop.**

**4d. Tidy** - Commit and push:
```
Invoke /line:tidy skill
```
**→ CONTINUE IMMEDIATELY to Step 5 after tidy shows "TIDY REPORT". Do NOT stop.**

**IMPORTANT:** After tidy completes, you MUST continue to Step 5 (validate) and Step 6 (teardown). Do not stop after tidy - the workflow is not complete until validation passes.

### Step 5: Validate Results

After the workflow completes, validate all proof-of-work artifacts:

```bash
cd $ORIGINAL_DIR
/home/sam/code/line-cook/tests/smoke-test.sh --validate $TEST_DIR
```

The validation checks:
1. `validation.py` uses regex (not placeholder)
2. Test file exists with actual tests
3. Tests pass (pytest)
4. Bead smoke-001 is closed
5. Commit exists referencing the task
6. Changes pushed to remote
7. Working tree is clean

### Step 6: Teardown

Clean up the test environment:

```bash
/home/sam/code/line-cook/tests/smoke-test.sh --teardown $TEST_DIR
```

### Step 7: Report Results

**If all validations pass:**

```
╔══════════════════════════════════════════════════════════════╗
║  SMOKE TEST: PASSED                                          ║
╚══════════════════════════════════════════════════════════════╝

All 7 proof-of-work checks validated:
  [✓] validation.py updated with regex
  [✓] Test file created
  [✓] Tests pass
  [✓] Bead closed
  [✓] Commit exists
  [✓] Pushed to remote
  [✓] Working tree clean

Line Cook workflow is functioning correctly.
```

**If any validation fails:**

```
╔══════════════════════════════════════════════════════════════╗
║  SMOKE TEST: FAILED                                          ║
╚══════════════════════════════════════════════════════════════╝

Validation results:
  [✓] validation.py updated with regex
  [✓] Test file created
  [✗] Tests pass - FAILED
      > Error: 2 tests failed
  [✓] Bead closed
  ...

Test directory preserved at: <path>
Run manually to investigate:
  cd <path>
  pytest -v
```

When a failure occurs, DO NOT tear down automatically - preserve the test directory for debugging.

**REMINDER:** The smoke test is only complete after validation passes and teardown runs. If you stop after /line:tidy, you have not finished the smoke test.

## Error Handling

**If setup fails:**
- Report the error
- No teardown needed

**If workflow step fails:**
- Note which step failed
- Run validation anyway (to see partial progress)
- Preserve test directory
- Report failure with debugging steps

**If validation fails:**
- Preserve test directory
- Report which checks failed
- Suggest debugging steps

## Example Usage

```
/smoke-test              # Run full smoke test
```

## What This Tests

The smoke test validates the complete Line Cook cycle:

1. **Prep** - Git sync, bead status check
2. **Cook** - Task execution with TDD guardrails
3. **Serve** - Code review (optional)
4. **Tidy** - Commit, push, close bead

**Task:** Replace placeholder email validation (`return "@" in email`) with proper regex validation and tests.

This is a real coding task that exercises all Line Cook components.
