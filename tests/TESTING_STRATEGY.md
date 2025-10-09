# Testing Strategy for RogueSignalProtocol

## Philosophy: Integration Over Mocking

This project follows a **pragmatic testing approach** focused on catching real bugs rather than achieving 100% coverage through heavily mocked tests.

### Core Principles

1. **Fewer, Better Tests** - Quality over quantity
2. **Real Config, Real Behavior** - Minimize mocking, maximize integration
3. **Smoke Tests First** - Catch catastrophic failures immediately
4. **Test What Matters** - Focus on gameplay behavior, not implementation details

---

## Test Categories

### 1. Smoke Tests (CRITICAL)
**Location:** `tests/integration/test_config_validation_smoke.py`

**Purpose:** Catch catastrophic failures before they reach production

**What they test:**
- ✅ All required JSON files exist and are valid
- ✅ All required JSON keys are present
- ✅ Real objects can be instantiated with real config
- ✅ No missing dependencies or import errors

**Why they matter:**
- These tests caught the `cpu_recovery_nodes` vs `cpu_nodes` bug
- They verify JSON structure matches what code expects
- They use ZERO mocking - pure integration

**Run before every commit:**
```bash
pytest tests/integration/test_config_validation_smoke.py -v
```

---

### 2. Integration Tests
**Location:** `tests/integration/test_real_config_behavior.py`

**Purpose:** Verify real game systems work together correctly

**What they test:**
- ✅ Config values load correctly from JSON
- ✅ Game objects use real config (not fallback values)
- ✅ All enemy types can be created
- ✅ All exploits have CPU costs defined
- ✅ Config values are internally consistent

**Why they matter:**
- Catch config loading bugs that unit tests miss
- Verify code doesn't use wrong attribute names
- Ensure fallback values match JSON

**Minimal mocking:**
- Only mock message logs (UI concerns, not game logic)
- Everything else uses real objects and real config

---

### 3. Unit Tests
**Location:** `tests/unit/`

**Purpose:** Test specific functions and classes

**IMPROVED APPROACH:**
- ❌ OLD: Mock GameBalance values with wrong numbers
- ✅ NEW: Load real config, test against real values

**Example - test_code_hacks.py:**

```python
# OLD WAY (WRONG):
@patch('game_inventory.GameBalance')
def test_restore_cpu(self, mock_balance):
    mock_balance.CPU_RESTORE_MIN = 30  # Could diverge from JSON!
    # Test uses mock values...

# NEW WAY (RIGHT):
@classmethod
def setUpClass(cls):
    GameConfig.load_from_json()
    GameBalance.load_from_json()

def test_restore_cpu(self):
    # Test uses REAL values from JSON
    assert player.cpu >= initial + GameBalance.CPU_RESTORE_MIN
```

**Benefits:**
- Tests fail if JSON values change (catches regressions)
- Tests fail if code uses wrong config attributes
- No divergence between test mocks and reality

---

## What We DON'T Test

For a game project (not safety-critical software), we **intentionally skip**:

- ❌ Testing every private method
- ❌ Testing implementation details that may change
- ❌ Achieving 100% code coverage through excessive mocking
- ❌ Testing framework internals (TCOD, pygame, etc.)

Instead, we focus on:
- ✅ Gameplay behavior
- ✅ Config correctness
- ✅ Critical game systems (pathfinding, combat, saves)

---

## Test Smells to Avoid

### ❌ BAD: Heavy Mocking
```python
def test_enemy_movement(self):
    mock_map = MagicMock()
    mock_player = MagicMock()
    mock_pathfinder = MagicMock()
    mock_config = MagicMock()
    # ... 20 more mocks
    # Test tells us nothing about real behavior!
```

### ✅ GOOD: Integration Testing
```python
def test_enemy_movement(self):
    game_map = GameMap(50, 50)  # Real map
    player = Player(10, 10)     # Real player
    enemy = Enemy(15, 15, "patrol")  # Real enemy
    # Test actual behavior with real objects
```

### Rule of Thumb
**If your test has more mocks than real objects, you're testing the wrong thing.**

---

## Running Tests

### Full suite (all tests)
```bash
pytest tests/ -v
```

### Smoke tests only (fast, run before commits)
```bash
pytest tests/integration/test_config_validation_smoke.py -v
```

### Integration tests (verify real behavior)
```bash
pytest tests/integration/ -v
```

### Unit tests (specific functionality)
```bash
pytest tests/unit/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=. --cov-report=html
```

---

## Adding New Tests

### When to add a smoke test:
- Adding new JSON config files
- Adding new required JSON keys
- Creating new core game objects

### When to add an integration test:
- Implementing new game mechanics
- Adding multi-system features (e.g., enemy AI + pathfinding)
- Testing save/load behavior

### When to add a unit test:
- Testing pure functions (calculations, utilities)
- Testing single-responsibility classes
- Testing edge cases in isolated code

### When NOT to test:
- Private implementation details
- Framework internals
- Trivial getters/setters
- Code that's purely cosmetic (UI positioning)

---

## Recent Improvements

### Problems We Fixed:

1. **Config Fallback Bug**
   - Code had fallback values that diverged from JSON
   - Tests didn't catch it because they mocked config
   - **Fix:** Load real config in tests

2. **Attribute Name Mismatch**
   - Tests used `cpu_recovery_nodes` but real code uses `cpu_nodes`
   - Heavy mocking hid the discrepancy
   - **Fix:** Smoke tests instantiate real objects

3. **Missing JSON Validation**
   - No tests verified JSON structure
   - Game could crash with unclear errors
   - **Fix:** Comprehensive structure validation tests

### Impact:

- **Before:** Tests passed but game had config bugs
- **After:** Tests catch real config issues immediately

---

## Philosophy Summary

> **"A test that catches no real bugs has negative value."**
>
> It takes time to maintain but provides no benefit. We prefer:
> - 50 useful integration tests over 500 heavily mocked unit tests
> - Real behavior verification over implementation testing
> - Fast smoke tests over slow exhaustive coverage

For a game project, **player experience matters more than code coverage metrics.**

Our tests ensure:
- ✅ Game doesn't crash on startup
- ✅ Config loads correctly
- ✅ Core mechanics work
- ✅ Saves persist correctly

Everything else is secondary.

---

## Questions?

If you're unsure whether to add a test, ask:
1. **Would this test catch a real bug?** (Not just implementation changes)
2. **Does it test behavior, not implementation?** (Would it survive refactoring?)
3. **Is it fast enough to run frequently?** (Slow tests don't get run)

If you answer "no" to any of these, reconsider the test.
