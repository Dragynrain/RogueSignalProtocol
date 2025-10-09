# Test Suite Improvement Plan

**Date:** 2025-10-09
**Status:** Comprehensive Audit Complete
**Test Lines of Code:** ~14,782 lines across 47 test files

---

## Executive Summary

The RogueSignalProtocol test suite has made significant progress toward real object testing and configuration validation. However, there are critical opportunities to:

1. **Reduce over-testing** - Eliminate redundant mocked unit tests that provide no real value
2. **Increase integration test coverage** - Add more end-to-end gameplay scenarios
3. **Improve test maintainability** - Consolidate fixtures and remove builder pattern overhead
4. **Focus on behavior over implementation** - Test what players experience, not internal details

### Current State

**Strengths:**
- ✅ Excellent smoke tests in `test_config_validation_smoke.py` (528 lines)
- ✅ Strong real config behavior tests in `test_real_config_behavior.py` (375 lines)
- ✅ Good simple fixtures in `fixtures/simple_fixtures.py`
- ✅ Mock audit completed and documented
- ✅ Clear test guidelines established

**Weaknesses:**
- ⚠️ Over 10,000 lines of unit tests (25 files) with varying quality
- ⚠️ Builder pattern in `test_builders.py` is overly complex and rarely used
- ⚠️ Excessive mocking still present in some files (365 mock occurrences in unit tests)
- ⚠️ Many tests verify implementation details rather than behavior
- ⚠️ Limited end-to-end gameplay scenario coverage
- ⚠️ Some large test files (800+ lines) could be consolidated

---

## Testing Guidlines

Recommended Tests for a Roguelike
🔹 1. Unit Tests – High Priority

These will cover your core gameplay systems, which are often complex but self-contained.
What to test:

Combat mechanics (e.g., damage calculation, attack rolls)
Inventory logic (e.g., picking up, dropping, using items)
Movement and pathfinding
Line of sight / field of view
Procedural generation (e.g., dungeon layout validation, item/enemy spawning rules)
Turn order system
Stat changes (e.g., buffs, debuffs, leveling up)
Saving/loading game state

Focus on systems with complex rules or edge cases.
Aim for 80–90% coverage on logic-heavy modules.

🔹 2. Mocking – For Isolated Unit Tests

Use mocking to:

Simulate parts of the game loop.
Replace random number generators (e.g., seed or override random.randint).
Bypass file I/O or user input during tests.

🔹 3. Integration Tests – Moderate Priority

Useful for testing whole systems together (e.g., a turn in the game loop or a level generation pass).

What to test:

A full turn cycle (input → action → results).
Dungeon generation produces a connected, valid level.
Game start-to-end sequences, like loading a level, starting a new game, etc.

Tip:

Keep these limited in number (5–10 key scenarios).
Use them to catch regressions in game logic or shared state systems.

🔹 4. Smoke Tests – Optional / Low Priority

Coding for Windows, a smoke test might:

Launch the game.
Ensure it doesn’t crash immediately.
Load main menu or first level.
Could be automated with a CI tool, but for a solo dev or hobby project, a simple script or manual checklist might suffice.

⛔ What Not to Overdo

UI Testing: UI automation is overkill for a terminal-based or simple 2D roguelike.
End-to-end testing of every possible playthrough path — not worth the time.
Performance testing — unless you're doing something extremely complex, it's usually unnecessary early on.

🧠 Rule of Thumb: Where to Spend Your Time
System	Test Type	Priority	Notes
Combat, Inventory, Movement	Unit Tests	🔥 High	Lots of game logic, easy to isolate
Procedural Generation	Unit + Light Integration	🔥 High	Validate structure and rules
Game Loop / Turn System	Integration	✅ Medium	Keep a few smoke-like scenarios
UI, Rendering	Manual / Visual Testing	❌ Low	Often not worth automating
Input Handling	Unit (if decoupled)	✅ Medium	Useful if you map key presses to actions

Don’t aim for 100% coverage — test the parts most likely to break or regress.

---

## ✅ Phase 1 Progress Update (2025-10-09)

**Summary of Work Completed:**
- Audited and reduced 3 large test files (1,788 lines → 869 lines, 51% reduction)
- Deleted 2 unused fixture files (359 lines removed)
- **Total reduction: 1,278 lines of low-value test code removed**

**Test File Reductions:**
1. `test_map_generation.py`: 604 → 397 lines (34% reduction)
2. `test_configuration_settings.py`: 596 → 319 lines (46% reduction)
3. `test_menu_system.py`: 588 → 153 lines (74% reduction!)

**Fixture Files Deleted:**
1. `test_builders.py`: 225 lines (unused builder pattern)
2. `mock_helpers.py`: 134 lines (unused mock helpers)

**Impact:**
- Tests now focus on real behavior, not implementation details
- Removed duplicate coverage (config loading already in smoke tests)
- Removed UI rendering tests (not valuable for terminal roguelike)
- Kept only tests that would catch player-facing bugs

---

## Priority 1: CRITICAL - Reduce Over-Testing & Focus on Value

### Problem
The test suite has **too many tests testing the wrong things**. Many unit tests mock so heavily that they test mock behavior, not game behavior. This creates maintenance burden without catching real bugs.

### Impact
- Tests pass but game has bugs
- Refactoring breaks tests that shouldn't break
- Developers spend more time fixing tests than writing features
- Test suite is slow to run

### Action Items

#### 1.1 Audit and Consolidate Oversized Unit Test Files

**Files to Review:**
- ✅ `test_game_state_persistence.py` (802→206 lines) - Deleted 18 over-mocked tests (74% reduction)
- ✅ `test_save.py` (451→178 lines) - Deleted 17 over-mocked file I/O tests (60% reduction)
- ✅ `test_input_validation.py` (792→657 lines) - Deleted 2 low-value test classes (17% reduction)
- ✅ `test_audio_system.py` (680→309 lines) - Deleted pygame delegation tests, kept behavior tests (55% reduction)
- ✅ `test_vision_line_of_sight.py` (613→389 lines) - Deleted TCOD/Bresenham algorithm tests, kept gameplay behavior (37% reduction)
- ✅ `test_map_generation.py` (604→397 lines) - Removed over-mocked tests, kept real behavior tests (34% reduction)
- ✅ `test_configuration_settings.py` (596→319 lines) - Removed duplicate smoke test coverage (46% reduction)
- ✅ `test_menu_system.py` (588→153 lines) - Removed UI rendering tests, kept state management (74% reduction!)

**Strategy for Each File:**
1. Read through the test file
2. Identify tests that:
   - Mock more objects than they use real objects
   - Test private methods (implementation details)
   - Test framework behavior (TCOD, pygame)
   - Duplicate coverage from integration tests
3. Mark for deletion or simplification
4. Keep only tests that:
   - Would catch real player-facing bugs
   - Test actual game behavior
   - Use mostly real objects

**Estimated Impact:** Reduce unit test code by 30-40% (~3,000-4,000 lines)

#### 1.2 Delete or Simplify Builder Pattern

**File:** `tests/fixtures/test_builders.py` (225 lines)

**Status:** ✅ **COMPLETED** - File deleted (not being used anywhere)

**Problem:**
- Overly complex fluent builder pattern
- Creates mocked objects (defeats purpose of real object testing)
- Rarely actually used in tests
- Violates TEST_GUIDELINES.md principles

**Current Usage:**
```python
# Complex builder pattern - ANTI-PATTERN
player = PlayerBuilder()
    .at_position(10, 10)
    .with_cpu(100)
    .with_inventory_items([])
    .build()  # Returns MOCK, not real Player
```

**Preferred Pattern (Already Exists):**
```python
# Simple fixture function - GOOD
from tests.fixtures.simple_fixtures import player
p = player(x=10, y=10, cpu=100)  # Returns REAL Player
```

**Action:**
1. Search codebase for usage of builder pattern classes
2. Replace all usages with simple fixtures
3. Delete `test_builders.py` entirely
4. Update any tests that import from it

**Files Potentially Using Builders:**
```bash
grep -r "PlayerBuilder\|EnemyBuilder\|GameEngineBuilder\|ScenarioBuilder" tests/
```

**Estimated Impact:** Remove 225 lines, improve test clarity

#### 1.3 Eliminate Redundant Mock Helper Functions

**File:** `tests/fixtures/mock_helpers.py` (134 lines)

**Status:** ✅ **COMPLETED** - File deleted (not being used anywhere)

**Problem:**
- Creates "properly configured mocks" - contradicts real object philosophy
- Functions like `create_mock_game_map()`, `create_mock_game_state()` encourage mocking
- `setup_game_engine_mocks()` is a 60-line function to mock what should be real

**Current State:**
```python
# Encourages mocking core game logic - BAD
def create_mock_game_map(width=80, height=40):
    mock_game_map = Mock()
    mock_game_map.width = width
    # ... 30 more lines of mock setup
```

**Better Approach:**
```python
# Use real objects - GOOD
from tests.fixtures.simple_fixtures import test_map
game_map = test_map(width=80, height=40)  # Real GameMap object
```

**Action:**
1. Search for all usages of functions from `mock_helpers.py`
2. Replace with real object creation from `simple_fixtures.py` or direct instantiation
3. Keep ONLY `create_mock_sound_manager()` (external dependency)
4. Keep ONLY `create_mock_message_log()` (UI concern, not game logic)
5. Delete all game logic mocking functions

**Estimated Impact:** Remove ~100 lines of mock helpers, improve test reliability

---

## Priority 2: HIGH - Increase Integration Test Coverage

### Problem
Only **13 integration test files** (~3,974 lines) vs **25 unit test files** (~10,296 lines). This ratio is backwards for a game project.

### Target Ratio
For a game, the ideal is **60% integration tests, 40% unit tests** focused on pure functions.

### Action Items

#### 2.1 Add Critical Gameplay Workflow Tests

**Missing Integration Tests:**

1. **Complete Enemy AI Workflow**
   - File: `test_enemy_ai_complete_workflow.py` (NEW)
   - Test: Player enters vision → Enemy alerts nearby → Chase → Combat → Victory
   - Uses: Real Player, Real Enemies, Real GameMap, Real pathfinding
   - Mocks: Only sound_manager, message_log (UI concerns)

2. **Full Level Progression**
   - File: `test_complete_level_playthrough.py` (NEW)
   - Test: Start level → Collect items → Defeat enemies → Reach gateway → Next level
   - Verifies: Level generation, progression, state persistence
   - Uses: Real game objects throughout

3. **Exploit System End-to-End**
   - File: `test_exploit_combat_scenarios.py` (NEW)
   - Test: Equip exploit → Target enemy → Execute → Apply effects → Verify outcome
   - Covers: All exploit types with real game data
   - Uses: Real ExploitSystem, Real GameData.EXPLOITS

4. **Save/Load During Gameplay**
   - File: `test_save_load_mid_gameplay.py` (NEW)
   - Test: Play several turns → Save → Load → Continue → Verify state matches
   - Uses: Real SaveGameManager, full game state

5. **Heat/Trace/CPU Resource Management**
   - File: `test_resource_management_workflow.py` (NEW)
   - Test: Multiple turns of actions → Verify heat/trace/CPU updates correctly
   - Uses: Real game systems, real balance values

6. **Stealth and Detection Mechanics**
   - File: `test_stealth_detection_scenarios.py` (NEW)
   - Test: Player in shadows → Move near enemy → Verify detection logic
   - Test: Player in light → Enemy spots immediately
   - Uses: Real vision system, real game map

**Estimated Impact:** Add 1,500-2,000 lines of high-value integration tests

#### 2.2 Convert Heavy-Mock Unit Tests to Integration Tests

**Candidates for Conversion:**

**Example: test_combat.py (currently 371 lines with heavy mocking)**

**Current State:**
```python
def test_use_exploit_requires_targeting(self):
    mock_game = Mock()
    mock_player = Mock()
    mock_player.x = 10
    mock_player.y = 10
    mock_player.heat = 50
    # ... 30 more lines of mock setup
```

**Better Integration Test:**
```python
def test_targeting_exploit_workflow(self):
    """Test complete targeting workflow with real objects."""
    from tests.fixtures.simple_fixtures import player, enemy, test_map

    # Real objects
    p = player(10, 10, cpu=100)
    e = enemy("scanner", 15, 10)
    game_map = test_map(30, 30)

    # Minimal mock container
    game = Mock()
    game.player = p
    game.game_map = game_map
    game.message_log = Mock()
    game.sound_manager = Mock()

    exploit_system = ExploitSystem(game)
    result = exploit_system.use_exploit("buffer_overflow")

    # Test real behavior
    assert game.targeting_mode is True
    assert p.heat > 0  # Real heat calculation
```

**Files to Convert:**
- Parts of `test_combat.py` → new `test_combat_integration.py`
- Parts of `test_enemies.py` → new `test_enemy_behavior_integration.py`
- Parts of `test_inventory.py` → new `test_inventory_integration.py`

**Estimated Impact:** Convert 500-800 lines, improve bug detection

---

## Priority 3: MEDIUM - Improve Config and Data Testing

### Problem
Config validation is good, but we need more tests that verify game systems **actually use** the config correctly.

### Action Items

#### 3.1 Add Config Integration Tests

**New Tests Needed:**

1. **Balance Value Integration**
   - File: Expand `test_real_config_behavior.py`
   - Test: Verify every balance value from JSON is actually used in gameplay
   - Example: GameBalance.CPU_RESTORE_MIN is used in CodeHack restore_cpu effect

2. **Enemy Type Completeness**
   - File: `test_enemy_types_integration.py` (NEW)
   - Test: Create one of each enemy type → Verify all attributes load correctly
   - Test: Enemy movement matches its movement type from JSON
   - Test: Enemy damage matches its damage value from JSON

3. **Exploit Definition Completeness**
   - File: `test_exploit_definitions_integration.py` (NEW)
   - Test: Create one of each exploit → Verify all attributes
   - Test: Execute each exploit type → Verify behavior matches description

**Estimated Impact:** Add 300-500 lines of config validation

#### 3.2 Add Data Consistency Tests

**New Tests:**

1. **Cross-File Config Consistency**
   - File: `test_config_consistency.py` (NEW)
   - Test: Values that appear in JSON files match help in the code exactly
   - Example: cpu_restore_min/max in game_data.json matches descriptions written in py code

2. **Balance Value Relationships**
   - File: `test_balance_relationships.py` (NEW)
   - Test: Related balance values make sense together
   - Example: MIN < MAX, difficulty scales correctly, etc.
   
3. **No redundency**
   - There should not be the same data defined in multiple files like cpu_restore_min/max being in game_data.json and game_config.json

**Estimated Impact:** Add 200-300 lines of consistency checks

---

## Priority 4: MEDIUM - Consolidate and Simplify Fixtures

### Problem
Multiple fixture systems exist with different philosophies. Need consolidation.

### Current State

**Fixture Files:**
1. `fixtures/simple_fixtures.py` (76 lines) - ✅ GOOD - Real objects, simple API
2. `fixtures/test_builders.py` (225 lines) - ❌ BAD - Complex, uses mocks
3. `fixtures/mock_helpers.py` (134 lines) - ⚠️ MIXED - Some useful, some harmful
4. `fixtures/real_game_data.py` (30 lines) - ✅ GOOD - Real data access
5. `conftest.py` (minimal) - ✅ GOOD - Could expand for shared setup

### Action Items

#### 4.1 Consolidate Fixture Files

**Plan:**

1. **Keep and Expand:** `simple_fixtures.py`
   - Add more scenario builders using real objects
   - Add common game setup patterns
   - Keep simple function-based API

2. **Delete:** `test_builders.py`
   - Replace all usages with simple fixtures
   - Remove builder pattern entirely

3. **Reduce:** `mock_helpers.py`
   - Keep only external dependency mocks (audio)
   - Delete game logic mocking functions
   - Rename to `external_mocks.py` for clarity

4. **Keep:** `real_game_data.py`
   - Good pattern for accessing real data
   - Consider expanding with more helpers

5. **Expand:** `conftest.py`
   - Add pytest fixtures for common setups
   - Use for test configuration, not object creation

**Estimated Impact:** Reduce fixture code by 40%, improve clarity

#### 4.2 Create Standard Test Patterns

**New File:** `fixtures/standard_patterns.py`

**Contents:**
```python
"""Standard test patterns for common scenarios."""

def create_basic_game_environment():
    """Create minimal game environment for testing."""
    game_map = GameMap(30, 30)
    player = Player(15, 15)
    message_log = MessageLog()

    # Minimal mock for game container
    game = Mock()
    game.player = player
    game.game_map = game_map
    game.message_log = message_log
    game.sound_manager = Mock()  # External dependency

    return game

def create_combat_scenario(player_pos=(10,10), enemy_pos=(12,10)):
    """Create standard combat test scenario."""
    # Real objects for combat testing
    ...

def create_stealth_scenario():
    """Create stealth testing scenario with shadows."""
    ...

def create_multi_enemy_scenario(enemy_count=5):
    """Create scenario with multiple enemies."""
    ...
```

**Estimated Impact:** Add 150-200 lines of reusable patterns, reduce duplication

---

## Priority 5: LOW - Improve Test Organization and Documentation

### Action Items

#### 5.1 Reorganize Test Files by System

**Current Problem:** Some test files are massive (800+ lines) and test multiple systems.

**Proposed Structure:**

```
tests/
├── unit/
│   ├── core/                    # Core game logic
│   │   ├── test_player.py      # Player mechanics only
│   │   ├── test_enemy.py       # Enemy mechanics only
│   │   ├── test_combat.py      # Combat calculations only
│   │   └── test_movement.py    # Movement logic only
│   ├── systems/                 # Game systems
│   │   ├── test_exploit_system.py
│   │   ├── test_inventory_system.py
│   │   └── test_vision_system.py
│   ├── data/                    # Pure functions, data handling
│   │   ├── test_config_loading.py
│   │   ├── test_data_loading.py
│   │   └── test_validation.py
│   └── external/                # External dependencies (keep mocked)
│       ├── test_audio_interface.py
│       └── test_save_file_io.py
├── integration/
│   ├── workflows/               # Complete gameplay workflows
│   │   ├── test_level_playthrough.py
│   │   ├── test_combat_scenarios.py
│   │   ├── test_stealth_mechanics.py
│   │   └── test_resource_management.py
│   ├── systems/                 # Multi-system integration
│   │   ├── test_player_enemy_interaction.py
│   │   ├── test_save_load_cycle.py
│   │   └── test_level_progression.py
│   └── smoke/                   # Fast smoke tests
│       ├── test_config_validation.py  # Already exists
│       ├── test_real_config_behavior.py  # Already exists
│       └── test_critical_imports.py  # NEW: Verify imports work
└── fixtures/
    ├── simple_fixtures.py       # Keep and expand
    ├── real_game_data.py        # Keep
    ├── standard_patterns.py     # NEW
    └── external_mocks.py        # Rename from mock_helpers.py
```

**Migration Strategy:**
1. Create new directory structure
2. Move tests gradually (don't break everything at once)
3. Update imports as files move
4. Keep old structure until migration complete

**Estimated Impact:** Better organization, easier to find relevant tests

---

## Implementation Roadmap

### Phase 1: Immediate (1-2 weeks)
**Goal:** Reduce test maintenance burden

1. ✅ Audit builder pattern usage
2. ✅ Delete `test_builders.py` and replace usages
3. ✅ Simplify `mock_helpers.py` → `external_mocks.py`
4. ✅ Identify and mark redundant unit tests for deletion
5. ✅ Delete or consolidate 500-1000 lines of low-value tests

**Deliverables:**
- Cleaner fixture system
- 10-15% reduction in test code
- Faster test runs

### Phase 2: Short-term (2-4 weeks)
**Goal:** Add high-value integration tests

1. ✅ Create 5-6 new integration test files (Priority 2.1)
2. ✅ Convert heavy-mock unit tests to integration tests (Priority 2.2)
3. ✅ Add config integration tests (Priority 3.1)
4. ✅ Create standard test patterns (Priority 4.2)

**Deliverables:**
- 1,500+ lines of high-value integration tests
- Better bug detection
- Real gameplay coverage

### Phase 3: Medium-term (1-2 months)
**Goal:** Optimize test organization

1. ✅ Reorganize test directory structure (Priority 5.1)
2. ✅ Add data consistency tests (Priority 3.2)


**Deliverables:**
- Clear test organization
- Coverage visibility
- Better documentation

---

## Metrics to Track

### Before Improvements
- Total test LOC: ~14,782
- Unit test LOC: ~10,296 (70%)
- Integration test LOC: ~3,974 (27%)
- Mock occurrences: 365 in unit tests, 31 in integration tests
- Test files: 47 total (25 unit, 13 integration)
- Test run time: [Measure baseline]

### Target After Phase 2
- Total test LOC: ~12,000-13,000 (reduce 15-20%)
- Unit test LOC: ~5,000-6,000 (40-45%)
- Integration test LOC: ~6,000-7,000 (50-55%)
- Mock occurrences: < 150 in unit tests
- Test files: ~35-40 (delete redundant, add valuable)
- Test run time: Same or faster (less code, more efficient)

### Success Criteria
- ✅ Tests catch real bugs before they reach production
- ✅ Refactoring doesn't break tests unnecessarily
- ✅ New developers can understand test patterns
- ✅ Test suite runs fast enough to run frequently
- ✅ Integration tests provide confidence in game behavior

---

## Specific Files to Address

### DELETE ENTIRELY (after migrating any valuable tests)
- None identified yet - audit first

### REDUCE SIGNIFICANTLY (50%+ reduction)
1. `test_game_state_persistence.py` (802 lines → ~400 lines)
2. `test_input_validation.py` (792 lines → ~400 lines)
3. `test_audio_system.py` (680 lines → ~300 lines)
4. `test_vision_line_of_sight.py` (613 lines → ~350 lines)
5. `test_configuration_settings.py` (596 lines → ~250 lines)
6. `test_menu_system.py` (588 lines → ~300 lines)

**Strategy:** Keep only tests that verify behavior, not implementation.

### CONVERT TO INTEGRATION TESTS
1. Heavy-mock tests in `test_combat.py`
2. Heavy-mock tests in `test_enemies.py`
3. State transition tests in `test_game_state_persistence.py`

### EXPAND AND IMPROVE
1. `test_config_validation_smoke.py` - Already excellent, maybe add a few more
2. `test_real_config_behavior.py` - Add more behavior verification
3. `simple_fixtures.py` - Add more scenario builders

---

## Anti-Patterns to Eliminate

### 1. Testing Implementation Details
**Bad:**
```python
def test_private_method_implementation():
    obj._internal_helper(data)  # Testing private method
    assert obj._state == expected  # Testing internal state
```

**Good:**
```python
def test_public_api_behavior():
    result = obj.do_action(input)  # Test public API
    assert result.visible_outcome == expected  # Test observable behavior
```

### 2. Excessive Mocking
**Bad:**
```python
def test_with_20_mocks():
    mock_a = Mock()
    mock_b = Mock()
    mock_c = Mock()
    # ... 17 more mocks
    # Test tells us nothing about real system behavior
```

**Good:**
```python
def test_with_real_objects():
    player = Player(10, 10)  # Real object
    enemy = Enemy(15, 10, "scanner")  # Real object
    # Test actual game behavior
```

### 3. Testing Framework Internals
**Bad:**
```python
def test_tcod_pathfinding_algorithm():
    # Testing TCOD's A* implementation
    path = tcod.path.AStar(...)
    assert len(path) == expected
```

**Good:**
```python
def test_enemy_reaches_player():
    # Test that OUR usage of TCOD works
    enemy.move_toward_player(player, game_map)
    assert enemy.position_closer_to(player)
```

### 4. Builder Pattern Over-Engineering
**Bad:**
```python
player = (PlayerBuilder()
    .at_position(10, 10)
    .with_cpu(100)
    .with_max_cpu(100)
    .with_inventory([])
    .with_temp_effects({})
    .build())  # Returns Mock, not Player!
```

**Good:**
```python
from tests.fixtures.simple_fixtures import player
p = player(10, 10, cpu=100)  # Real Player, simple API
```

---

## Answers to Key Questions (2025-10-09)

**Q1: Builder Pattern Deletion (Priority 1.2)** - The builders aren't being used anywhere. Should I just delete `test_builders.py` entirely?
**A1:** Yes - delete entirely

**Q2: Mock Helpers (Priority 1.3)** - `mock_helpers.py` has 0 imports. Should I delete it entirely, or examine first?
**A2:** Examine first, keep only what's valuable (external dependency mocks)

**Q3: Large Test Files (Priority 1.1)** - Should I audit the 3 remaining large files and reduce them?
**A3:** Yes - audit and remove over-mocked/low-value tests

**Q4: Update TODO as I go** - Should I update TEST_TODO.md with checkmarks and notes as I complete items?
**A4:** Yes - track progress with checkmarks

**Q5: Priority Order** - Delete unused fixtures first, or audit large files first?
**A5:** Audit and reduce 3 large test files FIRST, then delete unused fixtures

---

## Questions to Ask Before Adding a Test

1. **Would this test catch a real bug that affects players?**
   - If no → Don't write it

2. **Does this test behavior or implementation?**
   - Implementation → Don't write it
   - Behavior → Write it

3. **Does this test have more mocks than real objects?**
   - Yes → Rewrite with real objects or don't write it

4. **Would this test break if I refactor without changing behavior?**
   - Yes → Don't write it (or rewrite to test behavior)

5. **Is there already an integration test covering this?**
   - Yes → Don't duplicate with unit test

6. **Is this testing my code or a framework/library?**
   - Framework/library → Don't write it (trust the library)
   - My code → Write it

---

## Conclusion

The RogueSignalProtocol test suite has a solid foundation but needs refocusing:

**Current State:** Too many unit tests testing mocks, not enough integration tests testing gameplay.

**Target State:** Fewer, better tests that focus on real game behavior and catch real bugs.

**Philosophy:** For a game project, integration tests > unit tests. Test what players experience.

**Next Steps:**
1. Start with Phase 1: Delete builders, simplify fixtures
2. Add 5-6 new integration test files (Phase 2)
3. Gradually convert or delete low-value unit tests
4. Track metrics and iterate

**Success Metric:** Can we refactor confidently, knowing tests will catch real problems but won't break unnecessarily?

---

**Remember:** The goal is not 100% coverage. The goal is **catching bugs players would encounter** while **making the codebase easy to change**.

Quality > Quantity. Behavior > Implementation. Integration > Unit.
