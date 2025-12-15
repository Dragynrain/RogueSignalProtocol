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

from game_config import GameSettings
from game_engine import GameEngine
from game_entities import EnemyState, Position
from game_map import RestoreNode
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

    engine = GameEngine(sound_manager=mock_sound_manager, settings=game_settings)

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
    engine.game_map.ghost_nodes[(22, 22)] = RestoreNode(node_type="ghost")

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
