#!/usr/bin/env python3
"""
Simple test fixtures for basic game testing.
Focus on core game mechanics only.
"""

from game_characters import Player, Enemy


def create_test_player(x=10, y=10, cpu=100):
    """Create a player for testing."""
    player = Player(x, y)
    player.cpu = cpu
    return player


def create_test_enemy(x=15, y=15, enemy_type="scanner", cpu=50):
    """Create an enemy for testing."""
    enemy = Enemy(x, y, enemy_type)
    if hasattr(enemy, 'cpu'):
        enemy.cpu = cpu
    return enemy


def create_test_level_data():
    """Create basic level data for testing."""
    return {
        "width": 80,
        "height": 40,
        "walls": [(0, 0), (0, 1), (1, 0)],  # Sample wall positions
        "floors": [(5, 5), (10, 10), (15, 15)]  # Sample floor positions
    }


def create_test_game_state():
    """Create basic game state for testing."""
    return {
        "player": create_test_player(),
        "enemies": [create_test_enemy()],
        "level": 1,
        "turn": 1,
        "game_over": False
    }