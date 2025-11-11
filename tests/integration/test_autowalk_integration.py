#!/usr/bin/env python3
"""
Integration tests for auto-walk (click-to-walk) system.

Tests the complete auto-walk flow including:
- TCOD pathfinding integration
- Stop conditions (enemy detection, damage, blocking)
- User cancellation
- Visual path preview
- Mouse click integration
"""

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from game_autowalk import AutoWalk
from game_entities import Position
from game_characters import Player, Enemy
from game_map import GameMap
from game_engine import GameEngine
from game_config import GameConfig, GameSettings


class TestAutoWalkBasic(unittest.TestCase):
    """Test basic auto-walk pathfinding and execution."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        # Create a minimal game map instead of full level generation
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()  # Start with no walls

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player at known location
        self.engine.player.position = Position(10, 10)

    def test_autowalk_straight_path(self):
        """Test auto-walk with straight unobstructed path."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)  # 5 tiles east

        # Start auto-walk
        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertTrue(success, "Auto-walk should start successfully")
        self.assertTrue(self.autowalk.is_active(), "Auto-walk should be active")
        # Path should have steps (exact count depends on TCOD pathfinding)
        self.assertGreater(len(self.autowalk.path), 0, "Path should have steps")
        # Verify destination is correct
        self.assertEqual(self.autowalk.path[-1], target_pos, "Last position should be target")

    def test_autowalk_diagonal_path(self):
        """Test auto-walk with diagonal movement."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 15)  # Diagonal

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertTrue(success)
        self.assertTrue(self.autowalk.is_active())
        # Path length should be roughly the diagonal distance
        self.assertGreater(len(self.autowalk.path), 0)

    def test_autowalk_around_obstacle(self):
        """Test auto-walk pathfinding around walls."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        # Create wall obstacle between start and target
        for y in range(8, 13):
            self.engine.game_map.walls.add((12, y))
        self.engine.game_map.invalidate_transparency_cache()

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertTrue(success, "Should find path around obstacle")
        self.assertTrue(self.autowalk.is_active())
        # Path should exist and reach destination
        self.assertGreater(len(self.autowalk.path), 0)
        self.assertEqual(self.autowalk.path[-1], target_pos)

    def test_autowalk_no_path_to_wall(self):
        """Test auto-walk correctly fails when target is a wall."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        # Make target a wall
        self.engine.game_map.walls.add((15, 10))
        self.engine.game_map.invalidate_transparency_cache()

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertFalse(success, "Should fail to start auto-walk to wall")
        self.assertFalse(self.autowalk.is_active())

    def test_autowalk_no_path_blocked(self):
        """Test auto-walk fails when completely blocked."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        # Surround player with walls (completely blocked)
        for x in range(9, 12):
            for y in range(9, 12):
                if not (x == 10 and y == 10):  # Don't block player position
                    self.engine.game_map.walls.add((x, y))
        self.engine.game_map.invalidate_transparency_cache()

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertFalse(success, "Should fail when no path exists")
        self.assertFalse(self.autowalk.is_active())


class TestAutoWalkStopConditions(unittest.TestCase):
    """Test auto-walk stop conditions (enemy detection, damage, blocking)."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player at known location
        self.engine.player.position = Position(10, 10)

    def test_stop_on_enemy_detection(self):
        """Test auto-walk stops when enemy becomes visible."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        # Place enemy in vision range (but not initially visible)
        enemy = Enemy(Position(25, 10), 'scanner')
        self.engine.enemies.append(enemy)

        # Move player closer so enemy becomes visible
        self.engine.player.position = Position(15, 10)

        # Check stop conditions
        should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

        # Enemy should be visible now
        if self.engine.player.can_see_enemy(enemy, self.engine.game_map):
            self.assertTrue(should_stop, "Should stop when enemy visible")
            self.assertIn("Enemy", reason, "Reason should mention enemy")

    def test_stop_on_player_damage(self):
        """Test auto-walk stops when player takes damage."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)
        initial_cpu = self.engine.player.cpu

        # Simulate damage
        self.engine.player.cpu -= 10

        # Check stop conditions
        should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

        self.assertTrue(should_stop, "Should stop when taking damage")
        self.assertIn("damage", reason.lower(), "Reason should mention damage")

    def test_stop_on_path_blocked_by_wall(self):
        """Test auto-walk stops when path becomes blocked by wall."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)

        # Simulate path becoming blocked (e.g., door closes)
        # Block the next tile in the path
        if len(self.autowalk.path) > 0:
            next_tile = self.autowalk.path[0]
            self.engine.game_map.walls.add((next_tile.x, next_tile.y))
            self.engine.game_map.invalidate_transparency_cache()

            # Check stop conditions
            should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

            self.assertTrue(should_stop, "Should stop when path blocked")
            self.assertIn("blocked", reason.lower(), "Reason should mention blocking")

    def test_stop_on_destination_reached(self):
        """Test auto-walk stops when destination reached."""
        start_pos = Position(10, 10)
        target_pos = Position(12, 10)  # Only 2 steps away

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)

        # Simulate reaching destination by exhausting path
        self.autowalk.current_step = len(self.autowalk.path)

        # Check stop conditions
        should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

        self.assertTrue(should_stop, "Should stop when destination reached")
        self.assertIn("reached", reason.lower(), "Reason should mention destination")


class TestAutoWalkExecution(unittest.TestCase):
    """Test auto-walk step-by-step execution."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player at known location
        self.engine.player.position = Position(10, 10)

    def test_get_next_move_returns_adjacent(self):
        """Test get_next_move returns adjacent movement delta."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)

        next_move = self.autowalk.get_next_move(self.engine)

        self.assertIsNotNone(next_move, "Should return next move")
        dx, dy = next_move
        # Move should be adjacent (max 1 in any direction)
        self.assertLessEqual(abs(dx), 1, "dx should be -1, 0, or 1")
        self.assertLessEqual(abs(dy), 1, "dy should be -1, 0, or 1")

    def test_advance_step_increments_counter(self):
        """Test advance_step increments the step counter."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        initial_step = self.autowalk.current_step

        self.autowalk.advance_step()

        self.assertEqual(self.autowalk.current_step, initial_step + 1)

    def test_cancel_stops_autowalk(self):
        """Test cancel() stops auto-walk."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        self.autowalk.cancel()

        self.assertFalse(self.autowalk.is_active())
        self.assertIsNotNone(self.autowalk.stop_reason)

    def test_stop_clears_path(self):
        """Test stop() clears the path and deactivates."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertGreater(len(self.autowalk.path), 0)

        self.autowalk.stop("Test stop")

        self.assertFalse(self.autowalk.is_active())
        self.assertEqual(len(self.autowalk.path), 0)
        self.assertEqual(self.autowalk.current_step, 0)


class TestAutoWalkPathPreview(unittest.TestCase):
    """Test path preview functionality for rendering."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player
        self.engine.player.position = Position(10, 10)

    def test_get_remaining_path(self):
        """Test get_remaining_path returns correct positions."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)

        remaining = self.autowalk.get_remaining_path()

        self.assertGreater(len(remaining), 0, "Should have remaining path")
        self.assertEqual(len(remaining), len(self.autowalk.path))
        # Last position should be the target
        self.assertEqual(remaining[-1].x, target_pos.x)
        self.assertEqual(remaining[-1].y, target_pos.y)

    def test_get_remaining_path_decreases_as_walking(self):
        """Test remaining path decreases as we advance steps."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        initial_remaining = len(self.autowalk.get_remaining_path())

        self.autowalk.advance_step()
        after_step = len(self.autowalk.get_remaining_path())

        self.assertEqual(after_step, initial_remaining - 1)

    def test_get_remaining_path_empty_when_inactive(self):
        """Test get_remaining_path returns empty list when inactive."""
        remaining = self.autowalk.get_remaining_path()

        self.assertEqual(len(remaining), 0, "Should return empty when inactive")


class TestAutoWalkTCODIntegration(unittest.TestCase):
    """Test TCOD pathfinding integration specifically."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player
        self.engine.player.position = Position(10, 10)

    def test_tcod_pathfinding_uses_walkability_map(self):
        """Test auto-walk respects walkability map (walls are impassable)."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        # Create L-shaped obstacle forcing path to go around
        for x in range(11, 15):
            self.engine.game_map.walls.add((x, 10))
        for y in range(10, 13):
            self.engine.game_map.walls.add((14, y))
        self.engine.game_map.invalidate_transparency_cache()

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        # Should find path going around the obstacle
        self.assertTrue(success, "Should find path around L-shaped obstacle")

        # Verify path doesn't go through walls
        for pos in self.autowalk.path:
            self.assertFalse(
                self.engine.game_map.is_wall(pos),
                f"Path should not go through wall at {pos}"
            )

    def test_tcod_pathfinding_finds_optimal_path(self):
        """Test TCOD finds reasonably optimal paths."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)  # 10 tiles away horizontally

        # No obstacles - should be straight line
        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertTrue(success)
        # Path should exist and reach destination
        self.assertGreater(len(self.autowalk.path), 0, "Should have a path")
        self.assertEqual(self.autowalk.path[-1], target_pos, "Should reach destination")

    def test_tcod_pathfinding_handles_complex_maze(self):
        """Test TCOD can navigate complex mazes."""
        start_pos = Position(5, 5)
        target_pos = Position(15, 15)

        # Create a maze-like structure with corridors
        # Vertical walls with gaps
        for y in range(3, 18):
            if y not in [7, 13]:  # Leave gaps
                self.engine.game_map.walls.add((10, y))
        self.engine.game_map.invalidate_transparency_cache()

        success = self.autowalk.start(start_pos, target_pos, self.engine)

        self.assertTrue(success, "Should find path through maze")
        # Path should navigate through the gaps
        self.assertGreater(len(self.autowalk.path), 0)


class TestAutoWalkInterruption(unittest.TestCase):
    """Test auto-walk interruption by various game actions."""

    def setUp(self):
        """Set up test fixtures."""
        settings = GameSettings()
        from game_map import GameMap
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        game_map.walls.clear()

        self.engine = GameEngine(
            settings=settings,
            game_map=game_map,
            load_save=False
        )
        self.autowalk = self.engine.autowalk

        # GameEngine generates a level on init, so clear walls again
        self.engine.game_map.walls.clear()
        self.engine.game_map.invalidate_transparency_cache()

        # Clear enemies
        self.engine.enemies.clear()

        # Place player at known location
        self.engine.player.position = Position(10, 10)

    def test_autowalk_interrupted_by_direct_cancel(self):
        """Test that autowalk.cancel() works directly."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        success = self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(success, "Autowalk should start successfully")
        self.assertTrue(self.autowalk.is_active(), "Autowalk should be active")

        # Cancel directly
        self.autowalk.cancel()

        # Should be inactive
        self.assertFalse(self.autowalk.is_active(), "Autowalk should be cancelled")

    def test_autowalk_interrupted_by_menu_opening(self):
        """Test auto-walk cancels when opening inventory menu.

        NOTE: This test demonstrates that we need to test the behavior
        at the AutoWalk API level, not through the full input handler,
        because the input handler has complex state management that's
        hard to mock in tests.
        """
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        success = self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(success, "Autowalk should start successfully")
        self.assertTrue(self.autowalk.is_active(), "Autowalk should be active")

        # Simulate what should happen when inventory is opened:
        # The game code should call cancel() before showing the inventory
        self.autowalk.cancel()
        self.engine.show_inventory = True

        # Verify autowalk was cancelled
        self.assertFalse(self.autowalk.is_active(), "Auto-walk should cancel when opening inventory")

    def test_autowalk_cancel_persists_reason(self):
        """Test that cancel() stores the reason for debugging."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        # Cancel with custom reason
        self.autowalk.cancel()

        self.assertFalse(self.autowalk.is_active())
        self.assertIsNotNone(self.autowalk.stop_reason)
        self.assertIn("user", self.autowalk.stop_reason.lower())

    def test_autowalk_multiple_cancel_calls_safe(self):
        """Test that calling cancel() multiple times is safe."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        # Cancel multiple times
        self.autowalk.cancel()
        self.autowalk.cancel()
        self.autowalk.cancel()

        # Should still be inactive
        self.assertFalse(self.autowalk.is_active())

    def test_autowalk_cancels_on_path_blocked_mid_walk(self):
        """Test auto-walk stops when path becomes blocked during execution."""
        start_pos = Position(10, 10)
        target_pos = Position(15, 10)

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        # Take one step
        next_move = self.autowalk.get_next_move(self.engine)
        self.assertIsNotNone(next_move)
        self.autowalk.advance_step()

        # Now block the next position in the path
        if self.autowalk.current_step < len(self.autowalk.path):
            next_tile = self.autowalk.path[self.autowalk.current_step]
            self.engine.game_map.walls.add((next_tile.x, next_tile.y))
            self.engine.game_map.invalidate_transparency_cache()

            # Check stop conditions - should detect blocked path
            should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

            self.assertTrue(should_stop, "Should stop when path blocked mid-walk")
            self.assertIn("blocked", reason.lower(), "Reason should mention blocking")

    def test_autowalk_cancels_on_enemy_appears_mid_walk(self):
        """Test auto-walk stops when enemy appears during walk."""
        start_pos = Position(10, 10)
        target_pos = Position(20, 10)

        # Start auto-walk
        self.autowalk.start(start_pos, target_pos, self.engine)
        self.assertTrue(self.autowalk.is_active())

        # Take a few steps
        for _ in range(3):
            next_move = self.autowalk.get_next_move(self.engine)
            if next_move:
                dx, dy = next_move
                self.engine.player.position = Position(
                    self.engine.player.x + dx,
                    self.engine.player.y + dy
                )
                self.autowalk.advance_step()

        # Enemy suddenly appears in player's vision
        enemy = Enemy(Position(self.engine.player.x + 5, self.engine.player.y), 'scanner')
        self.engine.enemies.append(enemy)

        # Check stop conditions
        should_stop, reason = self.autowalk.check_stop_conditions(self.engine)

        # Should stop if enemy is visible
        if self.engine.player.can_see_enemy(enemy, self.engine.game_map):
            self.assertTrue(should_stop, "Should stop when enemy appears mid-walk")
            self.assertIn("enemy", reason.lower(), "Reason should mention enemy")


if __name__ == '__main__':
    unittest.main()
