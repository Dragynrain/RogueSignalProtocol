#!/usr/bin/env python3
"""
Tests for the main game loop and RogueSignalProtocol.py components.
Focus on improving coverage of the main game file.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))



class TestGameComponentIntegration(unittest.TestCase):
    """Test integration of major game components."""

    def test_game_settings_integration(self):
        """Test that GameSettings can be imported and initialized."""
        from game_config import GameSettings

        settings = GameSettings()
        self.assertIsInstance(settings, GameSettings)

        # Check default values are set
        self.assertIsInstance(settings.master_volume, float)
        self.assertIsInstance(settings.graphics_mode, str)
        self.assertIn(settings.graphics_mode, ["glyph", "graphics"])

    def test_player_integration(self):
        """Test that Player class can be imported and created."""
        from game_characters import Player

        # Create a player at a test position
        player = Player(x=5, y=5)
        self.assertIsInstance(player, Player)
        self.assertEqual(player.x, 5)
        self.assertEqual(player.y, 5)

    def test_enemy_manager_integration(self):
        """Test that EnemyManager can be imported."""
        from game_enemies import EnemyManager

        # Create mocks for required parameters
        game_map = Mock()
        game_map.width = 80
        game_map.height = 50
        message_log = Mock()

        enemy_manager = EnemyManager(game_map, message_log)
        self.assertIsInstance(enemy_manager, EnemyManager)

    def test_sound_manager_integration(self):
        """Test that SoundManager can be imported and initialized."""
        from game_audio import SoundManager

        with patch("pygame.mixer.init") as mock_mixer_init:
            mock_mixer_init.return_value = True
            sound_manager = SoundManager()
            self.assertIsInstance(sound_manager, SoundManager)


class TestGameConstantsAndConfiguration(unittest.TestCase):
    """Test game constants and configuration values."""

    def test_game_balance_constants(self):
        """Test that game balance constants are accessible."""
        from game_config import GameBalance

        # Test that critical constants exist and have reasonable values
        self.assertIsInstance(GameBalance.HEAT_REDUCTION_NORMAL, int)
        self.assertIsInstance(GameBalance.TRACE_INCREASE_INTERVAL, int)
        self.assertTrue(GameBalance.TRACE_INCREASE_INTERVAL > 0)
        self.assertTrue(GameBalance.HEAT_REDUCTION_NORMAL >= 0)

    def test_game_config_constants(self):
        """Test that game configuration constants are accessible."""
        from game_config import GameConfig

        # Test that essential config exists
        self.assertTrue(hasattr(GameConfig, "SCREEN_WIDTH"))
        self.assertTrue(hasattr(GameConfig, "SCREEN_HEIGHT"))
        self.assertIsInstance(GameConfig.SCREEN_WIDTH, int)
        self.assertIsInstance(GameConfig.SCREEN_HEIGHT, int)
        self.assertTrue(GameConfig.SCREEN_WIDTH > 0)
        self.assertTrue(GameConfig.SCREEN_HEIGHT > 0)

    def test_color_constants(self):
        """Test that color constants are available."""
        from game_entities import Colors

        # Test that basic colors are defined
        self.assertTrue(hasattr(Colors, "WHITE"))
        self.assertTrue(hasattr(Colors, "BLACK"))
        self.assertTrue(hasattr(Colors, "RED"))
        self.assertTrue(hasattr(Colors, "GREEN"))
        self.assertTrue(hasattr(Colors, "BLUE"))


class TestMainGameDataStructures(unittest.TestCase):
    """Test main game data structures and classes."""

    def test_position_class(self):
        """Test Position class functionality."""
        from game_entities import Position

        pos = Position(10, 20)
        self.assertEqual(pos.x, 10)
        self.assertEqual(pos.y, 20)

        # Test position operations
        self.assertTrue(hasattr(pos, "__eq__"))

    def test_enemy_state_enum(self):
        """Test EnemyState enum."""
        from game_entities import EnemyMovement, EnemyState

        # Test that expected states exist (EnemyState enum)
        self.assertTrue(hasattr(EnemyState, "UNAWARE"))
        self.assertTrue(hasattr(EnemyState, "HOSTILE"))

        # Test EnemyMovement enum has expected values
        self.assertTrue(hasattr(EnemyMovement, "SEEK"))
        self.assertTrue(hasattr(EnemyMovement, "RANDOM"))

    def test_exploit_definition_class(self):
        """Test ExploitDefinition class."""
        from game_entities import ExploitDefinition

        # Test creating an exploit definition with correct parameters
        exploit = ExploitDefinition(
            name="Test Exploit",
            ram=5,
            heat=10,
            range=5,
            category="test",
            damage=20,
            targeting="single",
            description="A test exploit",
        )

        self.assertEqual(exploit.name, "Test Exploit")
        self.assertEqual(exploit.heat, 10)
        self.assertEqual(exploit.range, 5)
        self.assertEqual(exploit.damage, 20)


if __name__ == "__main__":
    unittest.main()
