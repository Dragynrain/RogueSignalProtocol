# Testing Automation - Local & CI

## The Core Problem

**You asked:** "How do we automate testing without wasting tokens?"

**Answer:** Pre-commit hooks + smart test selection

---

## Local Automation (Pre-Commit Hooks)

### Why Pre-Commit Hooks?

**Problem:** Manual testing is forgotten
```bash
# What happens now:
git add .
git commit -m "fix"
# ... later: "Oh no, I broke 5 tests!"
```

**Solution:** Tests run AUTOMATICALLY before commit
```bash
git add .
git commit -m "fix"
# → Tests run automatically
# → If fail, commit is BLOCKED
# → Fix tests, then commit succeeds
```

### Pre-Commit Hook (ALREADY CONFIGURED)

The pre-commit hook is already set up at `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Running full test suite before commit..."
.venv/Scripts/python.exe -m pytest tests/
if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "Tests failed! Commit aborted."
    echo "Fix the failing tests or use --no-verify to skip"
    echo "=========================================="
    exit 1
fi
```

**What this does:**
- Runs automatically before every commit
- Blocks commit if tests fail
- Runs FULL test suite (all unit + integration tests)
- Shows all test output for immediate debugging
- Can be bypassed in emergencies: `git commit --no-verify`

**No manual testing needed** - The hook handles it automatically!

---

## Smart Test Selection Strategy

### The Problem: Token Budget

**Full test suite:**
```bash
pytest tests/  # Takes 30k tokens to show all output
```

**Smart selection:**
```bash
# Changed game_combat.py?
pytest tests/ -k "combat" -q  # Only 2k tokens!
```

### Token-Efficient Testing Patterns

**Pattern 1: Targeted Testing**
```bash
# You changed: game_enemies.py
# Run only: enemy-related tests
pytest tests/ -k "enemy" -q --tb=line
```

**Pattern 2: Last-Failed Only**
```bash
# First run finds failures
pytest tests/

# Fix issues, then iterate on JUST the failures
pytest --lf -v  # Only re-runs what failed
```

**Pattern 3: Progressive Validation**
```bash
# 1. Quick sanity check (1k tokens)
pytest tests/ -q --tb=no | tail -10

# 2. If failures, investigate specific ones (2-3k tokens)
pytest --lf -v --tb=short

# 3. Full validation before final commit (10-20k tokens)
pytest tests/ -v
```

---

## The "Claude-Friendly" Test Workflow

### During Development

```bash
# You're coding... changed game_combat.py

# Quick check (200 tokens):
pytest tests/unit/test_core.py -q --tb=no

# If failure, detailed view (1k tokens):
pytest tests/unit/test_core.py -v --tb=short

# Fixed? Run related tests (2k tokens):
pytest tests/ -k "combat" -q
```

**Token spent: ~3k** vs. **30k for full suite**

### Before Commit

```bash
# Let pre-commit hook do its job:
git commit -m "fix combat system"

# → Hook runs automatically:
# → pytest tests/unit/ tests/integration/ -q --tb=line --maxfail=5
# → Takes 5 seconds, minimal output
# → If fails: commit blocked
# → If passes: commit succeeds
```

**Token spent by you: 0!** (runs locally, no Claude involvement)

---

## What About Claude?

### When Claude Runs Tests

**Good (efficient):**
```bash
# You tell Claude: "Run the combat tests"
pytest tests/ -k "combat" -v
# → 2-3k tokens, targeted feedback
```

**Bad (wasteful):**
```bash
# You tell Claude: "Run all tests"
pytest tests/ -v
# → 20-30k tokens, most output irrelevant
```

### Claude's Auto-Testing Policy

**SHOULD do:**
- Run targeted tests after making changes
- Use `-q --tb=line` for quick checks
- Use `--lf` when iterating on fixes
- Run minimal subset to validate change

**SHOULD NOT do:**
- Run full suite unless explicitly requested
- Run tests with `-v` by default
- Re-run passing tests repeatedly
- Show full tracebacks for all tests

**Token budget guideline:**
- Single file change: < 3k tokens on testing
- Small refactor: < 5k tokens on testing
- Major change: < 10k tokens on testing
- Full validation: 20-30k tokens (rare, pre-release only)

---

## The Automated Workflow

### Your Local Machine

```
1. You code
2. Pre-commit hook runs automatically
   ├─ Runs fast tests (< 5 sec)
   ├─ If fail → Blocks commit
   └─ If pass → Allows commit
3. You push to GitHub (optional)
```

**Token cost: 0** (all local)

### When You Ask Claude for Help

```
You: "I changed game_combat.py, can you check if it works?"

Claude:
1. Runs targeted tests: pytest tests/ -k "combat" -q
2. Reports results concisely
3. If failures, investigates with --lf -v
4. Fixes issues
5. Validates fix with same targeted tests

Token cost: 3-5k (efficient!)
```

**Instead of:**
```
Claude: [runs full suite, 30k tokens]
You: "Uh, I just wanted to know if combat works..."
```

---

## Pre-Commit Hook Options

### Option 1: Fast & Strict (Recommended)
```bash
#!/bin/bash
# Blocks commit if ANY test fails
.venv/Scripts/python.exe -m pytest tests/unit/ tests/integration/ \
    -q --tb=line --maxfail=5 -x || exit 1
```

### Option 2: Agent Tests Only
```bash
#!/bin/bash
# Only run smoke tests (super fast)
.venv/Scripts/python.exe -m pytest \
    tests/integration/test_game_smoke.py \
    tests/integration/test_level_generation.py::TestLevelGeneration::test_level_1_spawn_quantities_match_config \
    -q --tb=line || exit 1
```

### Option 3: Warning Only (Soft Fail)
```bash
#!/bin/bash
# Runs tests but allows commit even if they fail
.venv/Scripts/python.exe -m pytest tests/unit/ tests/integration/ -q --tb=line
if [ $? -ne 0 ]; then
    echo "WARNING: Tests failed, but allowing commit (fix soon!)"
fi
exit 0
```

---

## Testing in Claude Code Sessions

### The Problem
Every time Claude runs `pytest`, it uses tokens to show output.

### The Solution
**Let the pre-commit hook catch issues BEFORE Claude sees them.**

**Workflow:**
1. You code locally
2. Git commit triggers pre-commit hook
3. Hook fails → You know there's a problem
4. You ask Claude: "Tests are failing, can you fix?"
5. Claude runs ONLY the failing tests (`pytest --lf`)
6. Token usage: minimal

**vs. Old Workflow:**
1. You code locally
2. Git commit (no validation)
3. Claude: "Let me check... *runs full test suite*"
4. Claude: "Found 5 failures, let me fix..."
5. Claude: "Fixed, let me validate... *runs full suite again*"
6. Token usage: 60k+

---

## For Claude: Test Running Guidelines

### Default Behavior

**After making changes:**
```bash
# If changed 1 specific file:
pytest tests/ -k "<related_keyword>" -q --tb=line

# If changed multiple files:
pytest tests/unit/ tests/integration/ -q --tb=line --maxfail=3

# If asked to validate everything:
pytest tests/ --tb=short  # Only if user explicitly requests
```

### When Iterating on Fixes

```bash
# FIRST run (find failures):
pytest tests/ -k "<area>" -v

# SUBSEQUENT runs (fix failures):
pytest --lf -v --tb=short  # Only re-run what failed!
```

### Token Budget Rules

- Quick check: Use `-q --tb=no` (500 tokens)
- Detailed failure: Use `-v --tb=short` (2-3k tokens)
- Full suite: Only if explicitly requested (20-30k tokens)
- Default: Run smallest relevant subset

---

## GitHub CI (Optional Future)

### If You Want GitHub Actions

Create `.github/workflows/test.yml`:
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --tb=short
```

**But you don't need this!** Pre-commit hooks work fine for solo dev.

---

## Summary

### For You (User)
1. **Set up pre-commit hook** (one-time, 2 minutes)
2. **Code normally**
3. **Git commit** → Tests run automatically
4. **If tests fail** → Fix them or ask Claude
5. **If tests pass** → Commit succeeds

**Benefit:** Never commit broken code

### For Claude
1. **Run targeted tests only** (3-5k tokens)
2. **Use --lf when iterating** (saves 50%+ tokens)
3. **Full suite only when requested** (20-30k tokens)

**Benefit:** 10x token efficiency

### Setup Steps

```bash
# 1. Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running pre-commit tests..."
.venv/Scripts/python.exe -m pytest tests/unit/ tests/integration/ \
    -q --tb=line --maxfail=5 -x || exit 1
echo "All tests passed!"
EOF

# 2. Make executable
chmod +x .git/hooks/pre-commit

# 3. Test it
git commit -m "test hook"
# → Should run tests automatically!
```

**That's it!** Now you have automated testing with zero token waste.
