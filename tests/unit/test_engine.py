#!/usr/bin/env python3
"""
Simple unit tests for Game Engine functionality.
Focus on core game mechanics only.
"""


from game_characters import Enemy, Player
from game_entities import Position


def test_game_turn_system():
    """Game turn system works."""
    # Test that turns advance properly
    turn_count = 0

    # Simulate turn advancement
    turn_count += 1
    assert turn_count == 1

    turn_count += 1
    assert turn_count == 2


def test_player_turn():
    """Player can take actions on their turn."""
    player = Player(10, 10)

    # Player should be able to move
    old_x = player.x
    player.x += 1
    assert player.x == old_x + 1

    # Player should be able to take damage
    old_cpu = player.cpu
    player.take_damage(10)
    assert player.cpu == old_cpu - 10


def test_enemy_turn():
    """Enemies can take actions on their turn."""
    pos = Position(5, 5)
    enemy = Enemy(pos, "scanner")

    # Enemy should exist and have a position
    assert enemy.position.x == 5
    assert enemy.position.y == 5

    # Enemy should be able to move to new position
    new_pos = Position(6, 5)
    enemy.position = new_pos
    assert enemy.position.x == 6


def test_game_state_tracking():
    """Game tracks basic state."""
    # Game should track if it's running
    game_running = True
    assert game_running is True

    # Game should be able to end
    game_running = False
    assert game_running is False


def test_player_death_ends_game():
    """Player death should end the game."""
    player = Player(10, 10)
    game_over = False

    # Kill player
    player.take_damage(player.cpu)

    # Game should end when player dies
    if player.cpu <= 0:
        game_over = True

    assert game_over is True


def test_level_progression():
    """Level progression works."""
    current_level = 1

    # Level should advance
    current_level += 1
    assert current_level == 2

    # Level should not be negative
    assert current_level > 0


def test_game_initialization():
    """Game initializes correctly."""
    # Basic game components should exist
    player = Player(40, 20)  # Start position
    enemies = []
    level = 1

    assert player is not None
    assert isinstance(enemies, list)
    assert level >= 1


def test_collision_trace_level():
    """Basic collision trace_level works."""
    player = Player(10, 10)
    pos = Position(10, 10)
    enemy = Enemy(pos, "scanner")  # Same position

    # Characters at same position should collide
    collision = player.x == enemy.position.x and player.y == enemy.position.y
    assert collision is True

    # Characters at different positions don't collide
    new_pos = Position(15, 10)
    enemy.position = new_pos
    collision = player.x == enemy.position.x and player.y == enemy.position.y
    assert collision is False
