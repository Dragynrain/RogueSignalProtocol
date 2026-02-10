# Testing Strategy - Comprehensive Guide

## Quick Answer

**"Which test should I write?"**

```
Single function/calc → Unit Test (tests/unit/)
2-3 systems together → Integration Test (tests/integration/)
Full game simulation → Agent Test (tests/integration/test_*_agent.py)
```

---

## The Test Pyramid

```
     /\       Unit Tests (FAST, MANY)
    /  \      - 100s of these
   /____\     - Run in milliseconds
  /      \    - Mock dependencies
 / Integration Tests (MEDIUM, SOME)
/__________\  - 10s of these
            \ - Run in seconds
             \ - Real dependencies

            Agent Tests (SLOW, FEW)
            - 5-10 scenarios
            - Full game engine
            - Find integration bugs
```

**The 80/20 Rule:**
- 80% Unit Tests → **Correctness** (does this calculation work?)
- 15% Integration Tests → **Compatibility** (do these systems work together?)
- 5% Agent Tests → **Confidence** (does the whole game work?)

---

## Test Type Comparison

| Aspect | Unit | Integration | Agent |
|--------|------|-------------|-------|
| **Speed** | < 10ms | < 100ms | 0.1-2s |
| **Scope** | Single function | 2-3 systems | Full game |
| **Dependencies** | Mocked | Real | Real |
| **Assertions** | Exact values | Specific behavior | Loose validation |
| **When to use** | Always | System interactions | Complex scenarios |
| **Example** | `test_damage_calc()` | `test_pathfinding()` | `test_chaos_agent()` |

---

## When to Use What

### Unit Tests (`tests/unit/`)

**Write for:**
- Pure calculations
- State machines
- Single-method logic
- Algorithm implementations

**Example scenarios:**
- ✓ "Test heat calculation formula"
- ✓ "Test enemy state transition UNAWARE → ALERT"
- ✓ "Test pathfinding algorithm finds shortest path"
- ✗ "Test player can reach gateway" (too complex)

**Template:**
```python
def test_specific_calculation():
    """Unit: Test exact calculation logic."""
    # Arrange
    player = Player(5, 5)

    # Act
    result = player.calculate_heat(consecutive_attacks=3)

    # Assert exact value
    assert result == 11  # 8 base + 3 penalty
```

### Integration Tests (`tests/integration/`)

**Write for:**
- System interactions
- Data flow between modules
- Config loading + usage
- Multi-step processes

**Example scenarios:**
- ✓ "Test exploit system damages enemies"
- ✓ "Test level config loads and applies correctly"
- ✓ "Test enemy pathfinding avoids walls"
- ✗ "Test damage formula" (too simple, use unit test)

**Template:**
```python
def test_system_interaction():
    """Integration: Systems work together."""
    # Arrange
    engine = GameEngine(headless=True)
    enemy = enemy = Enemy(Position(10, 10), 'bot')

    # Act
    engine.exploit_system.use_exploit('buffer_overflow', Position(10, 10))

    # Assert behavior
    assert enemy.cpu < enemy.max_cpu
    assert 'damaged' in [msg.text for msg in engine.message_log.messages]
```

### Agent Tests (`tests/integration/test_*_agent.py`)

**Write for:**
- Full gameplay scenarios
- Map generation validation
- Crash detection (fuzzing)
- End-to-end workflows

**Example scenarios:**
- ✓ "Test 100 random turns don't crash"
- ✓ "Test level spawns correct quantities"
- ✓ "Test pathfinding works in real gameplay"
- ✗ "Test specific damage value" (use unit test)

**Template:**
```python
def test_gameplay_scenario():
    """Agent: Full gameplay validation."""
    # Arrange
    agent = GameTestAgent(seed=42)

    # Act
    stats = chaos_agent.run_chaos(max_turns=100)

    # Assert loosely (just verify it worked)
    assert not stats['crashed']
    assert stats['turns_survived'] >= 50
```

---

## Decision Tree

```
START: "I need to test [feature]"
│
├─ Q: Can I test it with a single function call?
│  YES → Unit Test
│  NO → Continue
│
├─ Q: Does it need 2-3 specific systems?
│  YES → Integration Test
│  NO → Continue
│
├─ Q: Does it need the full game running?
│  YES → Agent Test
│  NO → You probably want Integration Test
```

---

## Examples by Feature

### Feature: "Player Overheat Damage"

**Unit Test:**
```python
def test_calculate_overheat_damage():
    """Unit: Overheat damage formula."""
    player = Player(5, 5)
    player.heat = 105  # 5 over max

    damage = player.calculate_overheat_damage()
    assert damage == 10  # 5 base + 5 overheat
```

**Integration Test:**
```python
def test_overheat_applies_damage():
    """Integration: Heat system damages player."""
    engine = GameEngine(headless=True)
    engine.player.heat = 105

    initial_hp = engine.player.cpu
    engine.process_turn()

    assert engine.player.cpu < initial_hp
```

**Agent Test:**
```python
def test_overheat_in_combat():
    """Agent: Overheat happens in real combat."""
    agent = GameTestAgent(seed=42)
    # ... simulate combat until overheating
    # Just verify game doesn't crash
```

### Feature: "Enemy Pathfinding"

**Unit Test:**
```python
def test_astar_finds_path():
    """Unit: A* algorithm correctness."""
    walls = {(5, 5), (5, 6)}
    path = calculate_astar((0, 0), (10, 10), walls)

    assert (5, 5) not in path  # Avoids walls
    assert len(path) > 0
```

**Integration Test:**
```python
def test_enemy_pathfinds_to_player():
    """Integration: Enemy + pathfinding + map."""
    engine = GameEngine(headless=True)
    enemy = Enemy(Position(10, 10), 'bot')

    enemy.calculate_path_to_player(engine.player, engine.game_map)

    assert len(enemy.move_queue) > 0
```

**Agent Test:**
```python
def test_exploration_agent():
    """Agent: Pathfinding works in gameplay."""
    agent = GameTestAgent(seed=42)
    explorer = ExplorationAgent(agent)

    stats = explorer.explore_map(max_turns=300)

    assert not stats['got_stuck']
    assert stats['tiles_explored'] >= 50
```

---

## For New Features: TDD Workflow

### Step 1: Write Unit Tests First
```python
# Feature: Add "EMP Burst" exploit

# FIRST: Test the core logic
def test_emp_finds_enemies_in_radius():
    enemies = [Enemy(Position(5, 5), 'bot'), Enemy(Position(20, 20), 'bot')]
    affected = calculate_enemies_in_radius(Position(5, 5), radius=5, enemies)
    assert len(affected) == 1  # Only first enemy in radius
```

### Step 2: Write Integration Tests
```python
# SECOND: Test system interactions
def test_emp_disables_enemies():
    engine = GameEngine(headless=True)
    enemy = Enemy(Position(10, 10), 'bot')

    engine.exploit_system.use_exploit('emp_burst', Position(10, 10))

    assert enemy.disabled_turns > 0
```

### Step 3: (Optional) Add Agent Test
```python
# THIRD: Only if complex - validate in real gameplay
def test_emp_tactical_use():
    agent = GameTestAgent(seed=42)
    # ... full scenario
```

---

## What We Have Now

### Existing Tests (Keep!)
```
tests/unit/
├── test_audio_system.py       # Audio logic
├── test_enemies.py            # Enemy behavior
├── test_game_config.py        # Config loading
└── test_game_combat.py        # Combat calculations

tests/integration/
├── test_balance_relationships.py      # Config relationships
├── test_complete_level_playthrough.py # Multi-system
├── test_config_*.py                   # Config validation
└── test_level_progression_critical.py # Level transitions
```

### New Agent Tests (Just Added!)
```
tests/integration/
├── test_game_smoke.py         # Basic gameplay smoke tests
├── test_chaos_agent.py        # Random fuzzing for crashes
├── test_exploration_agent.py  # Smart exploration validation
├── test_level_generation.py   # Full level validation (quantities!)
└── test_scenario_agent.py     # Specific gameplay scenarios
```

---

## Current Performance

**Measured speeds (excellent!):**
```
Smoke tests:        16 tests in 0.35s
Level generation:   12 tests in 1.30s
Chaos agent:        1 test in 0.16s
Exploration:        1 test in 0.44s

Total agent suite: ~2 seconds ← Perfect for pre-commit!
```

---

## Speed Targets

### Unit Tests
- Each: < 10ms
- Suite: < 1 second
- Run: **Constantly during development**

### Integration Tests
- Each: < 100ms
- Suite: < 5 seconds
- Run: **Before committing**

### Agent Tests
- Each: 0.1-2 seconds
- Suite: < 10 seconds
- Run: **Before committing + CI**

---

## Common Mistakes

### Don't Do This

**Wrong: Integration test for simple logic**
```python
def test_damage_calculation():
    engine = GameEngine(headless=True)  # Overkill!
    damage = engine.player.calculate_damage()
    assert damage == 30
```

**Wrong: Agent test for specific value**
```python
def test_player_moves():
    agent = GameTestAgent()
    agent.move_player(1, 0)
    assert agent.player.x == 6  # Too heavyweight
```

**Wrong: Unit test for complex interaction**
```python
def test_level_generation():
    # Can't test this with just function calls!
    map = generate_map()
    # ... this needs full engine
```

### Do This Instead

**Right: Unit test for simple logic**
```python
def test_damage_calculation():
    player = Player(5, 5)
    damage = player.calculate_damage()
    assert damage == 30
```

**Right: Integration for movement**
```python
def test_player_moves():
    engine = GameEngine(headless=True)
    old_x = engine.player.x
    engine.move_player(1, 0)
    assert engine.player.x == old_x + 1
```

**Right: Agent for level generation**
```python
def test_level_generation():
    agent = GameTestAgent(seed=42)
    # Validate full level
    assert len(agent.enemies) == 24  # From config
```

---

## Summary

**The Rules:**
1. **Default to unit tests** - fastest and most specific
2. **Use integration for system interactions** - when 2-3 systems must work together
3. **Use agents sparingly** - for validation, fuzzing, complex scenarios

**For new code:**
- Write unit tests first (TDD)
- Add integration tests for interactions
- Add agent tests only if complex

**Remember:**
- Unit = **Correctness** (is the math right?)
- Integration = **Compatibility** (do systems connect?)
- Agent = **Confidence** (does it work in practice?)

**Speed matters:**
- Fast tests = run often = catch bugs early
- Slow tests = run rarely = bugs slip through
- Balance all three types

---

## See Also
- `.claude/TESTING_GUIDE.md` - Quick reference for running tests
- `.claude/TESTING_AUTOMATION.md` - Pre-commit hooks and automation
