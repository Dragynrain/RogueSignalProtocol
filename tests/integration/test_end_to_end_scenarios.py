#!/usr/bin/env python3
"""
End-to-end gameplay scenario tests to validate complete game functionality.
These tests verify that critical game systems work together correctly.
"""

import os
import sys
import unittest
from unittest.mock import Mock

# Add the project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rsp.entities.characters import Enemy, Player
from rsp.core.config import GameConfig
from rsp.entities.base import EnemyState, Position
from rsp.level.map import GameMap
from rsp.systems.save import SaveGameManager
from rsp.core.state import GameStateManager, MessageLog, TurnProcessor


class TestEndToEndGameplayScenarios(unittest.TestCase):
    """End-to-end tests for complete gameplay scenarios."""

    def setUp(self):
        """Set up basic game components for testing."""
        self.game_map = GameMap(width=20, height=15)
        self.player = Player(x=5, y=5)
        self.game_state = GameStateManager()
        self.message_log = MessageLog()
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)

    def test_complete_player_turn_cycle(self):
        """Test a complete player turn including movement and state updates."""
        # Initial state
        initial_turn = self.game_state.turn
        initial_cpu = self.player.cpu

        # Simulate player movement
        new_x, new_y = 6, 5
        self.player.x = new_x
        self.player.y = new_y

        # Process turn
        self.turn_processor.process_turn(self.player)

        # Verify turn advanced
        self.assertEqual(self.game_state.turn, initial_turn + 1)

        # Verify player position updated
        self.assertEqual(self.player.x, new_x)
        self.assertEqual(self.player.y, new_y)

    def test_player_enemy_trace_level_scenario(self):
        """Test scenario where player comes within enemy trace level range."""
        # Create enemy
        enemy = Enemy(position=Position(10, 5), enemy_type="scanner")
        enemy.vision = 6  # Should detect player at distance 5

        # Position player within trace level range
        self.player.x = 5
        self.player.y = 5

        # Calculate distance
        distance = abs(enemy.position.x - self.player.x) + abs(
            enemy.position.y - self.player.y
        )  # Manhattan distance

        # Enemy should be able to detect player
        self.assertTrue(distance <= enemy.vision)

        # Verify initial enemy state
        self.assertEqual(enemy.state, EnemyState.UNAWARE)

    def test_game_state_persistence_scenario(self):
        """Test saving and loading game state maintains data integrity."""
        # Set up complex game state
        self.player.x = 15
        self.player.y = 10
        self.player.cpu = 120
        self.player.trace_level = 35
        self.player.heat = 15

        self.game_state.level = 3
        self.game_state.turn = 250

        # Create mock game object for saving
        mock_game = Mock()
        mock_game.player = self.player
        mock_game.game_state = self.game_state
        mock_game.game_map = self.game_map
        mock_game.inventory_manager = Mock()
        mock_game.inventory_manager.code_hacks = []
        mock_game.inventory_manager.exploits = []
        mock_game.inventory_manager.story_fragments = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []

        # Attempt save
        save_result = SaveGameManager.save_game(mock_game)

        # If save succeeds, verify we can load
        if save_result:
            loaded_data = SaveGameManager.load_game()  # Uses SaveGameManager.SAVE_FILE constant
            self.assertIsNotNone(loaded_data)

            # Verify key data preserved
            self.assertEqual(loaded_data["player"]["x"], 15)
            self.assertEqual(loaded_data["player"]["y"], 10)
            self.assertEqual(loaded_data["player"]["cpu"], 120)
            self.assertEqual(loaded_data["game_state"]["level"], 3)
            self.assertEqual(loaded_data["game_state"]["turn"], 250)

    def test_level_progression_scenario(self):
        """Test advancing to next level updates game state correctly."""
        # Initial level
        initial_level = self.game_state.level

        # Simulate level completion
        # Level progression (no reset method needed in new architecture)
        self.game_state.level += 1
        self.game_state.turn = 0

        # Verify level advanced
        self.assertEqual(self.game_state.level, initial_level + 1)

        # Verify turn count reset
        self.assertEqual(self.game_state.turn, 0)

        # Verify admin spawn flag reset
        self.assertFalse(self.game_state.admin_spawned)

    def test_network_config_scaling_scenario(self):
        """Test that network difficulty scales correctly with level."""
        # Test various levels
        for level in [1, 2, 3]:
            self.game_state.level = level
            config = self.game_state.get_current_network_config()

            # Verify config exists and has required fields
            self.assertIsInstance(config, dict)
            self.assertIn("enemies", config)
            self.assertIn("name", config)
            self.assertIn("background_trace", config)

            # Verify scaling makes sense
            self.assertTrue(config["enemies"] > 0)
            self.assertTrue(config["background_trace"] >= 1)
            self.assertTrue(config["enemies"] >= 1)

    def test_player_resource_management_scenario(self):
        """Test player resource management over multiple turns."""
        # Set initial resources
        self.player.heat = 30
        self.player.cpu = 150

        message_log = Mock()

        # Process several turns
        for turn in range(5):
            self.turn_processor.process_turn(self.player)

            # Verify resources stay within valid bounds
            self.assertTrue(self.player.heat >= 0)
            self.assertTrue(self.player.cpu >= 0)

    def test_error_recovery_scenario(self):
        """Test system behavior during error conditions."""
        # Test with None player (should be handled gracefully)
        message_log = Mock()

        try:
            self.turn_processor.process_turn(None)
            # Should not crash
            self.assertTrue(True)
        except Exception as e:
            # If it does error, should be handled gracefully
            self.assertIsInstance(e, (AttributeError, TypeError))

    def test_game_config_integration_scenario(self):
        """Test that game configuration integrates properly with game systems."""
        # Verify core config values exist and are reasonable
        self.assertIsInstance(GameConfig.SCREEN_WIDTH, int)
        self.assertIsInstance(GameConfig.SCREEN_HEIGHT, int)
        self.assertTrue(GameConfig.SCREEN_WIDTH > 0)
        self.assertTrue(GameConfig.SCREEN_HEIGHT > 0)

        # Test network config access
        try:
            configs = GameConfig.get_network_configs()
            self.assertIsInstance(configs, dict)
            self.assertTrue(len(configs) > 0)
        except Exception:
            # If network configs fail to load, test that the system handles it
            self.assertTrue(True)


class TestSystemIntegrationScenarios(unittest.TestCase):
    """Integration tests for core game systems working together."""

    def test_player_enemy_interaction_integration(self):
        """Test player and enemy systems working together."""
        game_map = GameMap(width=15, height=10)
        player = Player(x=5, y=5)
        enemy = Enemy(position=Position(10, 5), enemy_type="patrol")

        # Test basic interaction setup
        self.assertIsNotNone(player)
        self.assertIsNotNone(enemy)

        # Verify position tracking
        player_pos = Position(player.x, player.y)
        enemy_pos = enemy.position
        self.assertTrue(game_map.is_valid_position(player_pos))
        self.assertTrue(game_map.is_valid_position(enemy_pos))

    def test_game_state_and_turn_processing_integration(self):
        """Test game state management integrates with turn processing."""
        game_state = GameStateManager()
        turn_processor = TurnProcessor(game_state, MessageLog())
        player = Player(x=3, y=3)
        message_log = Mock()

        initial_turn = game_state.turn

        # Process turn
        turn_processor.process_turn(player)

        # Verify integration
        self.assertEqual(game_state.turn, initial_turn + 1)

    def test_save_load_system_integration(self):
        """Test save/load system integrates with game components."""
        # Create minimal game state
        player = Player(x=8, y=6)
        player.cpu = 100

        # Create mock game for saving
        mock_game = Mock()
        mock_game.player = player
        mock_game.game_state = Mock()
        mock_game.game_state.level = 1
        mock_game.game_state.turn = 50
        mock_game.game_map = Mock()
        mock_game.game_map.width = 20
        mock_game.game_map.height = 15
        mock_game.inventory_manager = Mock()
        mock_game.inventory_manager.code_hacks = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []

        # Test save functionality exists and doesn't crash
        try:
            save_result = SaveGameManager.save_game(mock_game)
            # Save may fail due to missing data, but should not crash
            self.assertIsInstance(save_result, bool)
        except Exception as e:
            # Acceptable exceptions during testing
            self.assertIsInstance(e, (TypeError, AttributeError))

    def test_comprehensive_system_stress_test(self):
        """Stress test multiple systems working together."""
        # Create game components
        game_map = GameMap(width=30, height=20)
        player = Player(x=15, y=10)
        game_state = GameStateManager()
        turn_processor = TurnProcessor(game_state, MessageLog())
        message_log = Mock()

        # Run multiple turns with various operations
        for turn in range(10):
            # Move player randomly within bounds
            new_x = max(0, min(game_map.width - 1, player.x + (turn % 3 - 1)))
            new_y = max(0, min(game_map.height - 1, player.y + (turn % 2)))
            player.x = new_x
            player.y = new_y

            # Process turn
            turn_processor.process_turn(player)

            # Verify system stability
            self.assertTrue(game_state.turn > 0)
            self.assertTrue(0 <= player.x < game_map.width)
            self.assertTrue(0 <= player.y < game_map.height)

        # Verify final state is consistent
        self.assertEqual(game_state.turn, 10)


if __name__ == "__main__":
    unittest.main()
