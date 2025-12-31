"""
Real game data fixtures for testing actual game behavior.
Use real GameData instead of mocks wherever possible.
"""

from rsp.entities.characters import Enemy
from rsp.entities.base import Position
from rsp.level.map import GameMap


def create_real_enemy(enemy_type: str = "scanner", position: Position = None) -> Enemy:
    """Create enemy using REAL GameData definitions."""
    if position is None:
        position = Position(10, 10)

    # Use actual GameData - no mocking!
    return Enemy(position, enemy_type)


def create_test_map_with_real_tiles(width: int = 80, height: int = 50) -> GameMap:
    """Create map using real tile definitions."""
    # Create a simple game map for testing - no level generation needed for basic tests
    return GameMap(width, height)
