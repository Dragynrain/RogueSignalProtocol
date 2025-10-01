# Test Guidelines for RogueSignalProtocol

## Philosophy: Real Objects Over Mocks

**Goal**: Write tests that catch real bugs by testing actual game behavior, not mock behavior.

**Principle**: Use real game objects whenever possible. Only mock external dependencies like audio, file I/O, or complex UI components.

## When to Use Real Objects vs Mocks

### ✅ USE REAL OBJECTS FOR:
- **Core Game Logic**: Player, Enemy, ExploitSystem, InventoryManager
- **Game Data**: Use `GameData.EXPLOITS`, `GameData.ENEMY_TYPES` for real definitions
- **Game State**: MessageLog, Position, GameMap
- **Entity Interactions**: Movement, combat, vision, pathfinding

### ⚠️ MOCK ONLY WHEN NECESSARY:
- **Audio Systems**: SoundManager (external dependency)
- **File I/O**: Save/load operations that touch the filesystem
- **Complex UI**: Full console rendering, menu systems
- **External APIs**: Network calls, system-level operations

### ❌ AVOID MOCKING:
- Game entities (Player, Enemy, Position)
- Core game mechanics (movement, combat, exploits)
- Data structures (inventories, message logs, maps)

## Test Creation Patterns

### 1. Use Simple Fixtures for Real Objects

```python
# ✅ GOOD - Simple fixture that creates real objects
from tests.fixtures.simple_fixtures import player, enemy, test_map

def test_combat_scenario():
    attacker = player(x=10, y=10, cpu=100)
    target = enemy("scanner", 11, 10)  # Adjacent for combat
    game_map = test_map(20, 20)
    
    # Test real combat behavior
    result = combat_system.attack(attacker, target)
    assert result.success is True
```

### 2. Create Helper Functions for Complex Setups

```python
# ✅ GOOD - Helper function creates real game environment
def create_test_game_with_exploit_system():
    player = Player(10, 10)
    player.inventory_manager = InventoryManager(player)
    message_log = MessageLog()
    
    game = Mock()  # Only mock the game container
    game.player = player  # Real player object
    game.message_log = message_log  # Real message log
    game.sound_manager = Mock()  # Mock audio (external dependency)
    
    return game, ExploitSystem(game)
```

### 3. Use Real Game Data

```python
# ✅ GOOD - Use actual exploit definitions
from game_data import GameData

def test_exploit_heat_cost():
    game, exploit_system = create_test_game_with_exploit_system()
    
    # Use real exploit data
    shadow_step = GameData.EXPLOITS['shadow_step']
    cost = exploit_system._calculate_heat_cost(shadow_step)
    
    assert cost == shadow_step.heat  # Test actual behavior
```

### 4. Test Real API Responses

```python
# ✅ GOOD - Test actual MessageLog format
def test_message_logging():
    message_log = MessageLog()
    message_log.add_message("Test message")
    
    # Handle real message format: Message object with .text and .color attributes
    assert len(message_log.messages) > 0
    message_text = message_log.messages[-1].text
    assert "Test message" in message_text
```

## Common Anti-Patterns to Avoid

### ❌ BAD: Heavy Mock Usage for Core Logic

```python
# DON'T DO THIS - Mocking behavior we should be testing
def test_player_movement():
    mock_player = Mock()
    mock_player.x = 10
    mock_player.y = 10
    mock_player.move = Mock(return_value=True)
    
    result = mock_player.move(Direction.NORTH)
    assert result is True  # Tests mock, not real movement logic
```

### ✅ GOOD: Real Object Testing

```python
# DO THIS - Test actual movement behavior
def test_player_movement():
    player = Player(10, 10)
    game_map = test_map(20, 20)
    
    # Test real movement logic
    result = player.move(Direction.NORTH, game_map)
    assert player.y == 9  # Verify actual position change
    assert result.success is True
```

### ❌ BAD: Complex Builder Patterns

```python
# DON'T DO THIS - Overly complex test setup
def test_combat():
    builder = TestCombatScenarioBuilder()
    scenario = (builder
                .with_player_at(10, 10)
                .with_enemy_at(11, 10)
                .with_weapons(['laser', 'plasma'])
                .with_environment('dungeon')
                .build())
    # 15 lines of setup for simple test...
```

### ✅ GOOD: Simple Fixture Functions

```python
# DO THIS - Simple, clear test setup
def test_combat():
    attacker = player(10, 10, cpu=100)
    target = enemy("scanner", 11, 10)
    
    # Test happens immediately, no complex setup
    result = combat_system.attack(attacker, target)
    assert result.damage > 0
```

## Integration Test Guidelines

### Test Complete Workflows

Integration tests should test end-to-end scenarios using real objects:

```python
def test_player_detection_workflow():
    """Test complete workflow: player movement → enemy vision → alerting."""
    # Setup real scenario
    test_player = player(10, 10)
    scanner = enemy("scanner", 15, 10)  # Same row, 5 tiles away
    patrol = enemy("patrol", 20, 20)    # Far away
    game_map = test_map(30, 30)
    
    # Test real detection workflow
    enemies = [scanner, patrol]
    vision_results = process_enemy_vision(test_player, enemies, game_map)
    
    # Verify real game behavior
    assert scanner.state == EnemyState.ALERT  # Scanner should detect player
    assert patrol.state == EnemyState.UNAWARE  # Patrol too far away
```

## Test File Organization

### Structure by System, Not Implementation

```
tests/
├── fixtures/
│   ├── real_game_data.py      # Real object creation functions
│   └── simple_fixtures.py     # Simple test scenarios
├── unit/
│   ├── test_player_core.py    # Player mechanics
│   ├── test_enemy_ai.py       # Enemy behavior
│   ├── test_combat_system.py  # Combat mechanics
│   └── test_movement.py       # Movement system
└── integration/
    ├── test_player_enemy_interactions.py
    ├── test_combat_inventory_flow.py
    └── test_save_load_workflows.py
```

## Performance Testing Guidelines

### Prefer Real Objects for Performance Tests

```python
def test_enemy_ai_performance():
    """Test AI performance with realistic enemy counts."""
    # Create realistic test scenario
    player = player(15, 15)
    enemies = [enemy("scanner", x, y) for x in range(5, 25, 5) 
               for y in range(5, 25, 5)]  # 25 enemies
    
    start_time = time.time()
    for enemy in enemies:
        enemy.update_ai(player, game_map)
    execution_time = time.time() - start_time
    
    # Verify performance with real objects
    assert execution_time < 0.1  # Should process 25 enemies in <100ms
```

## Error Testing

### Test Real Error Conditions

```python
def test_exploit_insufficient_cpu():
    """Test exploit fails with insufficient CPU."""
    game, exploit_system = create_test_game_with_exploit_system()
    
    # Set up real low-CPU condition
    game.player.cpu = 5
    shadow_step = GameData.EXPLOITS['shadow_step']
    
    # Test real error handling
    result = exploit_system.use_exploit('shadow_step')
    
    assert result is False
    message_text = game.message_log.messages[-1].text
    assert "insufficient" in message_text.lower()
```

## Migration Strategy

### For Existing Mock-Heavy Tests:

1. **Identify core game logic tests** that use heavy mocking
2. **Create helper functions** like `create_test_game_with_exploit_system()`
3. **Replace mocks incrementally** with real objects
4. **Verify tests still pass** and catch real bugs
5. **Update assertions** to match real API behavior

### Example Migration:

```python
# BEFORE: Mock-heavy test
def test_old_way():
    mock_player = Mock()
    mock_player.cpu = 100
    mock_exploit = Mock()
    mock_exploit.heat = 20
    # ... lots of mock setup
    result = system.use_exploit(mock_exploit)
    mock_player.cpu.assert_called_with(80)

# AFTER: Real object test
def test_new_way():
    game, exploit_system = create_test_game_with_exploit_system()
    shadow_step = GameData.EXPLOITS['shadow_step']
    
    result = exploit_system.use_exploit('shadow_step')
    assert game.player.cpu == 100 - shadow_step.heat
```

## Summary

- **Real objects catch real bugs** - mocks only test mock behavior
- **Keep setup simple** - prefer fixtures over complex builders
- **Use real game data** - test with actual GameData definitions
- **Mock only external dependencies** - audio, file I/O, complex UI
- **Test actual API behavior** - learn real method signatures and responses
- **Focus on game logic** - movement, combat, AI, progression systems

Following these guidelines will create a test suite that:
- Catches real bugs before they reach players
- Documents actual game behavior 
- Remains maintainable as the codebase evolves
- Provides confidence in refactoring
- Tests the game players actually experience