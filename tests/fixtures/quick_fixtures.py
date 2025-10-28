"""
Quick Test Fixtures - Fast, specialized fixtures for common testing needs.

These are optimized for speed and convenience, using minimal setup.
For complex scenarios, use standard_patterns.py instead.
"""

from unittest.mock import Mock
from game_engine import GameEngine
from game_config import GameSettings
from game_entities import Position, EnemyState
from tests.fixtures.real_game_data import create_real_enemy
from tests.fixtures.simple_fixtures import player


def mock_sound_manager():
    """Create a mocked sound manager for tests (external dependency)."""
    mock_sound = Mock()
    mock_sound.play_sfx = Mock()
    mock_sound.play_music = Mock()
    mock_sound.stop_music = Mock()
    mock_sound.set_volume = Mock()
    return mock_sound


def silent_settings():
    """Create GameSettings with all audio disabled."""
    settings = GameSettings()
    settings.master_volume = 0.0
    settings.sfx_volume = 0.0
    settings.music_volume = 0.0
    settings.graphics_mode = "glyph"
    return settings


def quick_engine(**kwargs):
    """Create GameEngine with sensible test defaults quickly.

    Args:
        load_save: Whether to load save (default: False)
        settings: GameSettings instance (default: silent_settings())
        **kwargs: Additional arguments passed to GameEngine

    Returns:
        GameEngine ready for testing

    Example:
        engine = quick_engine()
        engine.player.position.x = 20
        # ... test logic
    """
    defaults = {
        'settings': silent_settings(),
        'load_save': False,
    }
    defaults.update(kwargs)

    return GameEngine(**defaults)


def positioned_enemy(enemy_type, x, y, state=EnemyState.UNAWARE):
    """Create enemy at specific position with specific state.

    Args:
        enemy_type: Type of enemy ("scanner", "bot", etc.)
        x: X position
        y: Y position
        state: EnemyState (default: UNAWARE)

    Returns:
        Enemy instance positioned and configured
    """
    enemy = create_real_enemy(enemy_type, Position(x, y))
    enemy.state = state
    return enemy


def hostile_enemy(enemy_type, x, y, player_pos=None):
    """Create HOSTILE enemy tracking player.

    Args:
        enemy_type: Type of enemy
        x: X position
        y: Y position
        player_pos: Player position to track (optional)

    Returns:
        Enemy in HOSTILE state with last_seen_player set
    """
    enemy = positioned_enemy(enemy_type, x, y, state=EnemyState.HOSTILE)
    if player_pos:
        enemy.last_seen_player = player_pos
    return enemy


def wounded_player(x=10, y=10, cpu=30, heat=70):
    """Create player in critical condition (wounded, high heat).

    Args:
        x: X position (default: 10)
        y: Y position (default: 10)
        cpu: CPU level (default: 30 - wounded)
        heat: Heat level (default: 70 - high)

    Returns:
        Player in critical condition
    """
    test_player = player(x, y, cpu)
    test_player.heat = heat
    return test_player


def powered_player(x=10, y=10, cpu=150, exploits=None):
    """Create powered-up player with upgrades.

    Args:
        x: X position (default: 10)
        y: Y position (default: 10)
        cpu: CPU level (default: 150 - upgraded)
        exploits: List of exploit IDs to equip (default: None)

    Returns:
        Player with upgrades and exploits
    """
    test_player = player(x, y, cpu)
    test_player.max_cpu = cpu
    test_player.heat = 0

    if exploits:
        test_player.inventory_manager.equipped_exploits = exploits

    return test_player


def map_with_walls(width=30, height=30, wall_coords=None):
    """Create map with specified walls.

    Args:
        width: Map width (default: 30)
        height: Map height (default: 30)
        wall_coords: List of (x, y) tuples for walls (default: None)

    Returns:
        GameMap with walls placed

    Example:
        game_map = map_with_walls(wall_coords=[(5,5), (5,6), (5,7)])
    """
    from tests.fixtures.simple_fixtures import create_test_map

    game_map = create_test_map(width, height)

    if wall_coords:
        for x, y in wall_coords:
            game_map.walls.add((x, y))
        game_map.invalidate_transparency_cache()

    return game_map


def map_with_features(width=30, height=30, **features):
    """Create map with specified features.

    Args:
        width: Map width (default: 30)
        height: Map height (default: 30)
        **features: Keyword arguments for features:
            - walls: List of (x, y) tuples
            - shadows: List of (x, y) tuples
            - cooling_nodes: List of (x, y) tuples
            - cpu_nodes: List of (x, y) tuples
            - ghost_nodes: List of (x, y) tuples

    Returns:
        GameMap with all features placed

    Example:
        game_map = map_with_features(
            walls=[(5,5), (5,6)],
            shadows=[(10,10)],
            cooling_nodes=[(15,15)]
        )
    """
    from tests.fixtures.simple_fixtures import map_builder

    return map_builder(
        width=width,
        height=height,
        walls=features.get('walls'),
        shadows=features.get('shadows'),
        cooling_nodes=features.get('cooling_nodes'),
        cpu_nodes=features.get('cpu_nodes'),
        ghost_nodes=features.get('ghost_nodes')
    )
