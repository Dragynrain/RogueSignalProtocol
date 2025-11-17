"""
Quick Test Fixtures - Fast, specialized fixtures for common testing needs.

These are optimized for speed and convenience, using minimal setup.
For complex scenarios, use standard_patterns.py instead.
"""

from unittest.mock import Mock

from game_config import GameSettings
from game_engine import GameEngine
from game_entities import EnemyState, Position
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
        "settings": silent_settings(),
        "load_save": False,
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
