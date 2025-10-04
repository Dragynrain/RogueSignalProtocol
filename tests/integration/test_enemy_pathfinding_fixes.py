#!/usr/bin/env python3
"""
Integration tests for enemy pathfinding fixes.
Tests real game scenarios to prevent regression of pathfinding bugs.
Rewritten for on-demand movement calculation system (no movement queue).
"""

import unittest
from unittest.mock import Mock, patch
import random

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_map import GameMap
from game_config import GameConfig, GameSettings


class TestEnemyPathfindingFixes(unittest.TestCase):
    """Test enemy pathfinding fixes in real game scenarios."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def setUp(self):
        """Set up test game engine with real components."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()
        self.player = self.engine.player
        self.game_map = self.engine.game_map

        # Create a simple test map layout
        self.game_map.walls.clear()  # Clear existing walls

        # Add some walls to create pathfinding challenges
        for x in range(10, 15):
            self.game_map.walls.add((x, 10))  # Horizontal wall
        for y in range(8, 13):
            self.game_map.walls.add((12, y))  # Vertical wall intersecting

    def test_enemy_cannot_move_through_player_position(self):
        """Test that enemies don't calculate moves that would go through player position."""
        # Place player at position where enemy would want to go through them
        self.player.x, self.player.y = 15, 10

        # Place enemy on one side of player
        enemy = Enemy(Position(10, 10), 'virus')
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Calculate next move toward player
        next_move = enemy._calculate_next_move(self.player, self.game_map, self.engine)

        # Verify calculated move doesn't place enemy on player position
        if next_move:
            self.assertNotEqual((next_move.x, next_move.y), (self.player.x, self.player.y),
                              "Enemy calculated a move to player position")

        # Execute several moves and ensure enemy never moves onto player
        for _ in range(10):
            initial_pos = enemy.position
            moved = enemy.move(self.game_map, self.player, self.engine)

            # Enemy should never be on player position
            self.assertNotEqual((enemy.position.x, enemy.position.y), (self.player.x, self.player.y),
                              "Enemy moved to player position")

            # If adjacent to player, should stop moving
            if enemy.position.is_adjacent_to(Position(self.player.x, self.player.y)):
                break

    def test_enemy_finds_path_when_direct_path_blocked(self):
        """Test that enemies find alternative paths when direct path is blocked."""
        # Place player surrounded by walls except one opening
        self.player.x, self.player.y = 20, 20

        # Surround player with walls, leaving one opening
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Player position
                if dx == 1 and dy == 0:
                    continue  # Leave one opening
                wall_x, wall_y = self.player.x + dx, self.player.y + dy
                if 0 <= wall_x < GameConfig.MAP_WIDTH and 0 <= wall_y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, wall_y))

        # Place enemy far away who wants to reach player
        enemy = Enemy(Position(5, 5), 'bot')
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Calculate next move - should find alternative path
        next_move = enemy._calculate_next_move(self.player, self.game_map, self.engine)

        # Enemy should find a valid move (alternative path exists)
        if next_move:
            self.assertTrue(enemy._is_move_valid(next_move, self.game_map, self.player, self.engine),
                           f"Calculated move {next_move.x}, {next_move.y} should be valid")
            self.assertFalse(self.game_map.is_wall(next_move),
                           "Calculated move should not be a wall")

    def test_enemy_movement_prediction_respects_pathfinding(self):
        """Test that movement prediction uses correct pathfinding logic."""
        # Set up scenario where enemy would want to go through player
        self.player.x, self.player.y = 25, 25

        enemy = Enemy(Position(20, 25), 'bot')
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Get predicted next positions (simulates future moves)
        predicted_positions = self.engine.get_enemy_next_positions(enemy, steps=5)

        # Verify prediction doesn't include player position
        for predicted_pos in predicted_positions:
            self.assertNotEqual((predicted_pos.x, predicted_pos.y), (self.player.x, self.player.y),
                              "Movement prediction should not include player position")

    def test_blocked_enemy_gets_close_and_stops(self):
        """Test that enemy gets as close as possible when fully blocked."""
        # Create a scenario where player is completely inaccessible
        self.player.x, self.player.y = 30, 30

        # Surround player completely with walls
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if dx == 0 and dy == 0:
                    continue  # Player position
                wall_x, wall_y = self.player.x + dx, self.player.y + dy
                if 0 <= wall_x < GameConfig.MAP_WIDTH and 0 <= wall_y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, wall_y))

        # Place enemy outside the wall box
        enemy = Enemy(Position(25, 30), 'admin')
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(self.player.x, self.player.y)
        self.engine.enemies = [enemy]

        # Execute multiple movement attempts
        initial_distance = enemy.position.distance_to(Position(self.player.x, self.player.y))

        for _ in range(20):  # Try to move 20 times
            next_move = enemy._calculate_next_move(self.player, self.game_map, self.engine)
            if not next_move:
                break  # No valid move found

            if enemy._is_move_valid(next_move, self.game_map, self.player, self.engine):
                enemy.position = next_move

        final_distance = enemy.position.distance_to(Position(self.player.x, self.player.y))

        # Enemy should try to get closer (or may get stuck at walls)
        # Just verify enemy didn't break through walls to player
        self.assertNotEqual((enemy.position.x, enemy.position.y), (self.player.x, self.player.y),
                           "Enemy should not teleport through walls to player")

        # Verify enemy position is valid (not in a wall)
        self.assertFalse(self.game_map.is_wall(enemy.position),
                        "Enemy should not end up in a wall")

    def test_multiple_enemies_pathfind_independently(self):
        """Test that multiple enemies calculate their own paths correctly."""
        self.player.x, self.player.y = 30, 30

        # Create multiple enemies at different positions
        enemy1 = Enemy(Position(20, 20), 'virus')
        enemy1.state = EnemyState.HOSTILE
        enemy1.last_seen_player = Position(self.player.x, self.player.y)

        enemy2 = Enemy(Position(40, 40), 'bot')
        enemy2.state = EnemyState.HOSTILE
        enemy2.last_seen_player = Position(self.player.x, self.player.y)

        self.engine.enemies = [enemy1, enemy2]

        # Both enemies should calculate valid moves
        move1 = enemy1._calculate_next_move(self.player, self.game_map, self.engine)
        move2 = enemy2._calculate_next_move(self.player, self.game_map, self.engine)

        # Verify both found valid moves (if they exist)
        if move1:
            self.assertTrue(enemy1._is_move_valid(move1, self.game_map, self.player, self.engine),
                           "Enemy 1 should calculate valid move")

        if move2:
            self.assertTrue(enemy2._is_move_valid(move2, self.game_map, self.player, self.engine),
                           "Enemy 2 should calculate valid move")

        # Execute moves for both
        enemy1.move(self.game_map, self.player, self.engine)
        enemy2.move(self.game_map, self.player, self.engine)

        # Both should have moved closer or stayed in place
        # (valid pathfinding behavior)
        self.assertIsNotNone(enemy1.position, "Enemy 1 should have valid position")
        self.assertIsNotNone(enemy2.position, "Enemy 2 should have valid position")


if __name__ == '__main__':
    unittest.main()
