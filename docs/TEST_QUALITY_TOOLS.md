# Test Quality & Enforcement Tools

This document explains the test quality tools and how to use them.

---

## Overview

We've implemented two key tools to prevent test suite degradation:

1. **Test Isolation Checker** - Detects test pollution
2. **Pre-Commit Hook Enforcement** - Warns about bypassed commits

---

## 1. Test Isolation Checker

### What It Does

Identifies tests that **pass in isolation but fail in the full suite** - a classic sign of test pollution.

### Why It Matters

Test pollution happens when:
- Tests modify shared state (class-level caches, global variables)
- Tests don't clean up after themselves
- Tests depend on execution order

**The Problem We Solved**: We had 168 tests failing in the suite but passing alone due to `GameConfig._config_data` cache pollution.

### How to Use

```bash
# Check all tests for isolation issues
python scripts/check_test_isolation.py

# Check specific test directory
python scripts/check_test_isolation.py tests/unit/

# Check specific test file
python scripts/check_test_isolation.py tests/unit/test_game_config.py
```

### Example Output

```
====================================================================================
TEST ISOLATION CHECKER
====================================================================================

Checking: tests/

[1/2] Running full test suite...
  Found 5 failures in full suite

[2/2] Re-running failed tests in isolation...
  [1/5] tests/unit/test_foo.py::test_bar... PASSES (isolation issue!)
  [2/5] tests/unit/test_foo.py::test_baz... still fails
  ...

====================================================================================
RESULTS
====================================================================================

⚠️  ISOLATION ISSUES DETECTED: 1 tests

These tests pass alone but fail in the suite (test pollution):
  - tests/unit/test_foo.py::test_bar

Recommendation: Check for shared state, mocking issues, or
class-level caches being polluted across tests.

❌ LEGITIMATE FAILURES: 4 tests

These tests fail both ways (not pollution):
  - tests/unit/test_foo.py::test_baz
  ...
```

### When to Run

- **After refactoring** - Ensure you didn't break test isolation
- **When tests mysteriously fail** - Diagnose if it's pollution
- **In CI** (optional) - Catch pollution early

### Integration with CI

Add to your GitHub Actions workflow:

```yaml
- name: Check test isolation
  run: python scripts/check_test_isolation.py
  # Only warn, don't fail CI (use ||  true)
  continue-on-error: true
```

---

## 2. Pre-Commit Hook Enforcement

### What It Does

Scans recent commits for signs of bypassing the pre-commit hook with `--no-verify`.

### Why It Matters

Our investigation found commits like:
```
commit 96243f4
Author: ...
Date: ...

    Refactor: Improve helper utilization

    (Committed with --no-verify)
```

**Result**: 176 failing tests got into main!

### How to Use

```bash
# Check last 5 commits (default)
python scripts/enforce_hooks.py

# Check last 20 commits
python scripts/enforce_hooks.py 20
```

### Example Output

```
================================================================================
PRE-COMMIT HOOK ENFORCEMENT CHECK
================================================================================

Checking last 5 commits for hook bypassing...

⚠️  96243f4 - Refactor: Improve helper utilization
     └─ Commit message mentions '--no-verify'

================================================================================
❌ VIOLATIONS DETECTED: 1 commit(s)

Action Required:
1. Review the flagged commits
2. Ensure tests were actually passing
3. Run full test suite: pytest tests/
4. If tests fail, fix them before pushing

Note: This is a warning, not a hard block.
      Use discretion for emergency hotfixes.
```

### When to Run

- **In CI (recommended)** - Warn about suspicious commits
- **Before releases** - Ensure quality hasn't degraded
- **During code review** - Flag risky commits

### Integration with CI

Add to your GitHub Actions workflow:

```yaml
- name: Enforce pre-commit hooks
  run: python scripts/enforce_hooks.py 10
  # Warn but don't fail the build
  continue-on-error: true
```

---

## Best Practices

### ✅ DO:

1. **Run tests before committing** - Let the hook do its job
2. **Fix failures immediately** - Don't bypass hooks to "save time"
3. **Use isolation checker** - After complex refactoring
4. **Keep test fixtures clean** - Avoid shared mutable state

### ❌ DON'T:

1. **Don't use `--no-verify`** - Unless absolute emergency
2. **Don't commit failing tests** - Ever
3. **Don't ignore warnings** - They exist for a reason
4. **Don't rush** - Broken tests waste everyone's time

### When `--no-verify` Is Acceptable:

- **Emergency hotfix** - Production is down, tests can wait
- **Documentation-only changes** - No code affected
- **Test fixes** - When fixing the test suite itself

**ALWAYS**: Run `pytest tests/` manually if you bypass hooks!

---

## Technical Details

### Test Isolation Implementation

The checker:
1. Runs full suite with `pytest tests/ -v --tb=no`
2. Parses output to find failures
3. Re-runs each failed test individually
4. Compares results to identify pollution

**Performance**: ~2x test suite time (suite + isolated re-runs)

### Hook Enforcement Implementation

The enforcer:
1. Gets last N commits with `git log`
2. Checks commit messages for keywords
3. Checks git stats for suspicious changes
4. Reports violations with context

**Performance**: Instant (just git log parsing)

---

## Troubleshooting

### False Positives

**Problem**: Isolation checker flags test that legitimately fails

**Solution**: That test has a real bug! Fix it.

### False Negatives

**Problem**: Pollution exists but not detected

**Solution**:
- Test may be flaky (random failures)
- Test may depend on specific order
- Run checker multiple times

### Hook Enforcement Misses Bypass

**Problem**: Someone used `--no-verify` but script didn't catch it

**Reason**: Script only checks recent commits and commit messages

**Solution**: Manual code review + mandatory CI test runs

---

## Future Improvements

Potential enhancements:

1. **Parallel isolation checking** - Speed up by running isolated tests in parallel
2. **Git hook to prevent `--no-verify`** - Block at commit time
3. **Test dependency graph** - Visualize which tests affect others
4. **Automatic pollution fix** - Suggest fixture changes

---

## Summary

**Test Isolation Checker**:
- Purpose: Detect test pollution
- When: After refactoring, when mysteries occur
- Output: Lists polluted vs legitimate failures

**Hook Enforcement**:
- Purpose: Warn about bypassed commits
- When: In CI, before releases
- Output: Lists suspicious commits

Both tools are **warnings, not blockers** - use judgment!

**The Goal**: Keep test suite reliable and maintainable 🎯
