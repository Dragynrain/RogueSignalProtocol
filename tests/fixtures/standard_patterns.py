"""
Standard Test Patterns

Reusable test scenario builders for common game situations.
These patterns use REAL game objects with minimal mocking.

Use these to quickly set up common test scenarios like:
- Combat situations
- Stealth infiltration
- Resource management
- Enemy AI behaviors
- Complete gameplay workflows
"""

from unittest.mock import Mock
from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_config import GameSettings
from tests.fixtures.simple_fixtures import player, create_test_map, create_real_player
from tests.fixtures.real_game_data import create_real_enemy


def create_basic_game_environment():
    """
    Create minimal game environment for testing.

    Returns a GameEngine with:
    - Real Player at (15, 15)
    - Real GameMap (30x30)
    - Mocked sound_manager (external dependency)
    - Enemies from level generation (clear manually if needed)

    Perfect for: Basic gameplay tests that need minimal setup
    """
    game_settings = GameSettings()
    game_settings.master_volume = 0.0
    game_settings.sfx_volume = 0.0
    game_settings.music_volume = 0.0
    game_settings.graphics_mode = "glyph"
    game_settings.dialogue_preferences = {}  # Clear all dialogue preferences for testing

    mock_sound_manager = Mock()

    engine = GameEngine(
        sound_manager=mock_sound_manager,
        settings=game_settings
    )

    # Position player in center (ensure not in wall)
    engine.player.position.x = 15
    engine.player.position.y = 15

    # If player ended up in a wall, find a nearby non-wall position
    if (engine.player.x, engine.player.y) in engine.game_map.walls:
        # Search nearby for a valid position
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                test_x, test_y = 15 + dx, 15 + dy
                if 0 <= test_x < engine.game_map.width and 0 <= test_y < engine.game_map.height:
                    if (test_x, test_y) not in engine.game_map.walls:
                        engine.player.position.x = test_x
                        engine.player.position.y = test_y
                        break
            if (engine.player.x, engine.player.y) not in engine.game_map.walls:
                break

    engine.player.cpu = 100
    engine.player.heat = 0

    # NOTE: Engine will have enemies from level generation.
    # For tests that need no enemies, manually clear: engine.enemies = []

    return engine


def create_combat_scenario(player_pos=(15, 15), enemy_type="scanner", enemy_pos=(17, 15)):
    """
    Create standard combat test scenario.

    Args:
        player_pos: (x, y) tuple for player position
        enemy_type: Type of enemy to create ("scanner", "bot", "hunter", etc.)
        enemy_pos: (x, y) tuple for enemy position

    Returns a GameEngine with:
    - Player at player_pos with full resources
    - One enemy at enemy_pos (UNAWARE state)
    - Clear line of sight between them

    Perfect for: Combat exploit tests, damage calculation, targeting validation
    """
    engine = create_basic_game_environment()

    # Position player
    engine.player.position.x = player_pos[0]
    engine.player.position.y = player_pos[1]
    engine.player.cpu = 100
    engine.player.heat = 0

    # Create enemy
    enemy = create_real_enemy(enemy_type, Position(enemy_pos[0], enemy_pos[1]))
    enemy.state = EnemyState.UNAWARE
    engine.enemies = [enemy]

    return engine


def create_stealth_scenario():
    """
    Create stealth testing scenario with shadows.

    Returns a GameEngine with:
    - Player in shadow zone (18, 20)
    - Shadow path from (15, 20) to (25, 20)
    - Enemy watching from light (20, 15)
    - Ghost node at (22, 22)

    Perfect for: Stealth mechanics, shadow detection, invisibility tests
    """
    engine = create_basic_game_environment()

    # Create blind spot path
    for x in range(15, 26):
        engine.game_map.blind_spots.add((x, 20))

    # Position player in shadows
    engine.player.position = Position(18, 20)

    # Create enemy watching from light
    scanner = create_real_enemy("scanner", Position(20, 15))
    scanner.state = EnemyState.UNAWARE
    engine.enemies = [scanner]

    # Add ghost node for advanced stealth
    engine.game_map.ghost_nodes.add((22, 22))

    return engine


def create_multi_enemy_scenario(enemy_count=3, enemy_types=None):
    """
    Create scenario with multiple enemies.

    Args:
        enemy_count: Number of enemies to create (default 3)
        enemy_types: List of enemy types, or None for mixed types

    Returns a GameEngine with:
    - Player at (15, 15) with full resources
    - Multiple enemies scattered around map
    - Mix of UNAWARE and patrolling enemies

    Perfect for: Enemy coordination, alert system, area exploits
    """
    engine = create_basic_game_environment()

    # Default enemy types mix
    if enemy_types is None:
        enemy_types = ["scanner", "bot", "patrol"]

    # Create enemies at different positions
    positions = [
        (10, 10),  # Northwest
        (20, 10),  # Northeast
        (10, 20),  # Southwest
        (20, 20),  # Southeast
        (15, 25),  # South
    ]

    enemies = []
    for i in range(min(enemy_count, len(positions))):
        enemy_type = enemy_types[i % len(enemy_types)]
        pos = positions[i]
        enemy = create_real_enemy(enemy_type, Position(pos[0], pos[1]))
        enemy.state = EnemyState.UNAWARE
        enemies.append(enemy)

    engine.enemies = enemies

    return engine


def create_surrounded_scenario():
    """
    Create scenario where player is surrounded by enemies.

    Returns a GameEngine with:
    - Player at (15, 15)
    - 4 enemies adjacent to player (cardinal directions)
    - All enemies HOSTILE
    - Player has high heat (emergency situation)

    Perfect for: Emergency exploits, EMP burst, escape mechanics
    """
    engine = create_basic_game_environment()

    # Position player
    engine.player.position.x = 15
    engine.player.position.y = 15
    engine.player.heat = 60  # High heat, dangerous situation
    engine.player.cpu = 80

    # Create enemies surrounding player
    adjacent_positions = [
        (14, 15),  # West
        (16, 15),  # East
        (15, 14),  # North
        (15, 16),  # South
    ]

    enemies = []
    for pos in adjacent_positions:
        enemy = create_real_enemy("bot", Position(pos[0], pos[1]))
        enemy.state = EnemyState.HOSTILE
        enemies.append(enemy)

    engine.enemies = enemies

    return engine


def create_resource_test_scenario():
    """
    Create scenario for testing resource management (heat, trace, CPU).

    Returns a GameEngine with:
    - Player with moderate resources
    - Cooling node at (10, 10)
    - CPU node at (20, 20)
    - Ghost node at (15, 25)
    - One patrolling enemy

    Perfect for: Resource collection, node effects, heat/trace management
    """
    engine = create_basic_game_environment()

    # Set player resources to moderate levels
    engine.player.cpu = 60
    engine.player.heat = 40
    engine.player.trace_level = 50.0

    # Add resource nodes
    engine.game_map.cooling_nodes.add((10, 10))
    engine.game_map.cpu_recovery_nodes.add((20, 20))
    engine.game_map.ghost_nodes.add((15, 25))

    # Add one enemy to make it interesting
    patrol = create_real_enemy("patrol", Position(25, 15))
    patrol.state = EnemyState.UNAWARE
    engine.enemies = [patrol]

    return engine


def create_level_completion_scenario():
    """
    Create scenario for testing level progression and completion.

    Returns a GameEngine with:
    - Player with moderate progression
    - Gateway at (30, 30)
    - Mix of collected and available items
    - Some defeated enemies

    Perfect for: Level completion, gateway mechanics, state persistence
    """
    engine = create_basic_game_environment()

    # Set player with some progression
    engine.player.cpu = 80
    engine.player.max_cpu = 120  # Upgraded
    engine.player.heat = 20
    engine.player.trace_level = 30.0

    # Player has collected some exploits
    engine.player.inventory_manager.equipped_exploits = ['buffer_overflow', 'threat_scan']

    # Place gateway
    gateway_pos = Position(30, 30)
    engine.game_map.gateway_position = gateway_pos

    # Add a few remaining enemies
    enemy1 = create_real_enemy("scanner", Position(25, 25))
    enemy2 = create_real_enemy("bot", Position(28, 28))
    engine.enemies = [enemy1, enemy2]

    return engine


def create_exploit_testing_environment(exploit_id, target_required=True):
    """
    Create environment optimized for testing a specific exploit.

    Args:
        exploit_id: The exploit to test (e.g., "buffer_overflow")
        target_required: Whether exploit needs a target enemy

    Returns a GameEngine configured for testing the exploit:
    - Player with exploit equipped
    - Appropriate resources (CPU, heat)
    - Target enemy if needed
    - Proper positioning for exploit range

    Perfect for: Individual exploit tests, exploit validation
    """
    engine = create_basic_game_environment()

    # Equip the exploit
    engine.player.inventory_manager.equipped_exploits = [exploit_id]
    engine.player.cpu = 100
    engine.player.heat = 0

    # Create target enemy if needed
    if target_required:
        # Position based on common exploit ranges
        # Melee exploits: adjacent (1 tile)
        # Ranged exploits: medium distance (4 tiles)
        target_pos = Position(19, 15)  # 4 tiles from player at (15, 15)

        target = create_real_enemy("bot", target_pos)
        target.cpu = 50
        engine.enemies = [target]

    return engine


def create_ai_behavior_scenario():
    """
    Create scenario for testing enemy AI and pathfinding.

    Returns a GameEngine with:
    - Player visible to some enemies
    - Mix of enemy types with different movement patterns
    - Some enemies HOSTILE, some UNAWARE
    - Various obstacles (walls) to test pathfinding

    Perfect for: Enemy AI, pathfinding, alert system, state transitions
    """
    engine = create_basic_game_environment()

    # Position player
    engine.player.position.x = 15
    engine.player.position.y = 15

    # Create enemies with different states and positions
    scanner = create_real_enemy("scanner", Position(18, 15))  # Close, UNAWARE
    scanner.state = EnemyState.UNAWARE

    hunter = create_real_enemy("hunter", Position(20, 18))  # Medium distance, HOSTILE
    hunter.state = EnemyState.HOSTILE
    hunter.last_seen_player = engine.player.position

    patrol = create_real_enemy("patrol", Position(10, 10))  # Far, patrolling
    patrol.state = EnemyState.UNAWARE

    bot = create_real_enemy("bot", Position(25, 15))  # Far, ALERT
    bot.state = EnemyState.ALERT
    bot.last_seen_player = Position(20, 15)  # Knows approximate location

    engine.enemies = [scanner, hunter, patrol, bot]

    return engine


def create_full_gameplay_session():
    """
    Create comprehensive gameplay scenario for integration tests.

    Returns a GameEngine with:
    - Level 1 progression
    - Mix of enemies (some defeated)
    - Resources partially collected
    - Player with some upgrades
    - Items scattered on map
    - Active temporary effects

    Perfect for: Full gameplay integration tests, save/load tests
    """
    engine = create_basic_game_environment()

    # Set current level and progression
    engine.game_state.current_level = 1
    engine.game_state.enemies_defeated = 5

    # Player has progression
    engine.player.cpu = 75
    engine.player.max_cpu = 120
    engine.player.heat = 35
    engine.player.trace_level = 45.0
    engine.player.inventory_manager.equipped_exploits = ['code_injection', 'threat_scan', 'antivirus']

    # Active temporary effects
    engine.player.temporary_effects['exploit_efficiency_turns'] = 3

    # Mix of enemies in different states
    enemies = [
        create_real_enemy("scanner", Position(20, 20)),
        create_real_enemy("bot", Position(25, 15)),
        create_real_enemy("hunter", Position(30, 30)),
    ]
    enemies[0].state = EnemyState.UNAWARE
    enemies[1].state = EnemyState.ALERT
    enemies[2].state = EnemyState.HOSTILE

    engine.enemies = enemies

    # Add resources on map
    engine.game_map.cooling_nodes.add((12, 12))
    engine.game_map.cpu_recovery_nodes.add((18, 18))
    engine.game_map.ghost_nodes.add((22, 22))

    # Gateway for level completion
    engine.game_map.gateway_position = Position(35, 35)

    return engine
