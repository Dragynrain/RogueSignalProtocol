"""
Simple test fixtures that create real game objects quickly.
No complex builder patterns - just create what you need.
"""

import pytest
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
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


def create_test_map(width=20, height=20):
    """Create a simple test map."""
    return create_test_map_with_real_tiles(width, height)


def game_scenario():
    """Create a complete game scenario for testing."""
    return {
        'player': player(),
        'enemies': [enemy(), enemy("patrol", 15, 15)],
        'map': create_test_map()
    }


def combat_scenario():
    """Create a scenario for combat testing."""
    test_player = player(10, 10, 100)
    test_enemy = enemy("scanner", 11, 10)  # Adjacent for combat
    return {
        'player': test_player,
        'enemy': test_enemy,
        'map': create_test_map(30, 30)
    }


def vision_scenario():
    """Create a scenario for vision/trace level testing."""
    test_player = player(5, 5)
    scanner = enemy("scanner", 10, 5)  # Same row, different column
    patrol = enemy("patrol", 20, 20)   # Far away
    return {
        'player': test_player,
        'enemies': [scanner, patrol],
        'map': create_test_map(40, 40)
    }


def movement_scenario():
    """Create a scenario for movement testing."""
    test_player = player(15, 15)
    moving_enemy = enemy("bot", 10, 10)  # RANDOM movement
    patrolling_enemy = enemy("patrol", 5, 5)  # PATROL movement
    return {
        'player': test_player,
        'enemies': [moving_enemy, patrolling_enemy],
        'map': create_test_map(30, 30)
    }


def enemy_builder(enemy_type="scanner", pos=(10, 10), state=None,
                  last_seen=None, patrol_points=None, move_queue=None):
    """Flexible enemy builder with sensible defaults.

    Args:
        enemy_type: Type of enemy (scanner, bot, patrol, firewall, admin)
        pos: Tuple of (x, y) position
        state: EnemyState (defaults to type's natural state)
        last_seen: Tuple of (x, y) for last seen player position
        patrol_points: List of (x, y) tuples for patrol route
        move_queue: List of Position objects or tuples for movement queue

    Returns:
        Configured Enemy instance with real game data
    """
    e = create_real_enemy(enemy_type, Position(pos[0], pos[1]))

    if state is not None:
        e.state = state

    if last_seen:
        e.last_seen_player = Position(last_seen[0], last_seen[1])

    if patrol_points:
        e.patrol_points = [Position(p[0], p[1]) for p in patrol_points]

    if move_queue:
        e.move_queue = move_queue if isinstance(move_queue[0], Position) else \
                          [Position(p[0], p[1]) for p in move_queue]

    return e


def map_builder(width=30, height=30, walls=None, shadows=None,
                cooling_nodes=None, cpu_nodes=None, ghost_nodes=None):
    """Create test map with custom features.

    Args:
        width: Map width
        height: Map height
        walls: List of (x, y) tuples for wall positions
        shadows: List of (x, y) tuples for shadow positions
        cooling_nodes: List of (x, y) tuples for cooling nodes
        cpu_nodes: List of (x, y) tuples for CPU recovery nodes
        ghost_nodes: List of (x, y) tuples for ghost nodes

    Returns:
        GameMap instance with specified features
    """
    game_map = create_test_map_with_real_tiles(width, height)

    if walls:
        for x, y in walls:
            game_map.walls.add((x, y))
        game_map.invalidate_transparency_cache()

    if shadows:
        game_map.blind_spots.update(shadows)

    if cooling_nodes:
        game_map.cooling_nodes.update(cooling_nodes)

    if cpu_nodes:
        game_map.cpu_recovery_nodes.update(cpu_nodes)

    if ghost_nodes:
        game_map.ghost_nodes.update(ghost_nodes)

    return game_map