"""
Simple test fixtures that create real game objects quickly.
No complex builder patterns - just create what you need.
"""

from game_characters import Player, Enemy
from game_entities import Position
from game_map import GameMap
from tests.fixtures.real_game_data import create_real_enemy, create_test_map_with_real_tiles


def player(x=10, y=10, cpu=100):
    """Create a simple test player."""
    p = Player(x, y)
    p.cpu = cpu
    p.max_cpu = cpu  # Set max_cpu to match
    return p


def create_real_player(x=10, y=10, cpu=100):
    """Create a real player for testing (alias for compatibility)."""
    return player(x, y, cpu)


def enemy(enemy_type="scanner", x=5, y=5):
    """Create a simple test enemy using real GameData."""
    return create_real_enemy(enemy_type, Position(x, y))


def test_map(width=20, height=20):
    """Create a simple test map."""
    return create_test_map_with_real_tiles(width, height)


def game_scenario():
    """Create a complete game scenario for testing."""
    return {
        'player': player(),
        'enemies': [enemy(), enemy("patrol", 15, 15)],
        'map': test_map()
    }


def combat_scenario():
    """Create a scenario for combat testing."""
    test_player = player(10, 10, 100)
    test_enemy = enemy("scanner", 11, 10)  # Adjacent for combat
    return {
        'player': test_player,
        'enemy': test_enemy,
        'map': test_map(30, 30)
    }


def vision_scenario():
    """Create a scenario for vision/detection testing."""
    test_player = player(5, 5)
    scanner = enemy("scanner", 10, 5)  # Same row, different column
    patrol = enemy("patrol", 20, 20)   # Far away
    return {
        'player': test_player,
        'enemies': [scanner, patrol],
        'map': test_map(40, 40)
    }


def movement_scenario():
    """Create a scenario for movement testing."""
    test_player = player(15, 15)
    moving_enemy = enemy("bot", 10, 10)  # RANDOM movement
    patrolling_enemy = enemy("patrol", 5, 5)  # PATROL movement
    return {
        'player': test_player,
        'enemies': [moving_enemy, patrolling_enemy],
        'map': test_map(30, 30)
    }