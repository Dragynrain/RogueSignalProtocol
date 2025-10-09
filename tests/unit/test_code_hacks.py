#!/usr/bin/env python3
"""
Unit tests for code hack effects.
Tests all code hack types to ensure they function correctly.

IMPROVED: Uses real config values instead of mocking them.
"""

import unittest
from unittest.mock import MagicMock
from game_inventory import CodeHack
from game_characters import Player
from game_config import GameConfig, GameBalance


class TestCodeHackEffects(unittest.TestCase):
    """Test all code hack effect types."""

    @classmethod
    def setUpClass(cls):
        """Set up real config for all tests."""
        # Load real config once for all tests
        GameConfig._config_data = None
        GameConfig.load_from_json()
        GameBalance.load_from_json()

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(10, 10)
        self.mock_game = MagicMock()
        self.mock_game.message_log = MagicMock()
        self.mock_game.message_log.add_message = MagicMock()

    def test_restore_cpu_effect(self):
        """Test that restore_cpu effect restores player CPU using real config values."""
        # Set player CPU below max
        self.player.cpu = 50
        self.player.max_cpu = 100

        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")
        result = code_hack._apply_effect('restore_cpu', self.player, self.mock_game)

        # Should restore CPU using real balance values from JSON
        self.assertTrue(result)
        self.assertGreater(self.player.cpu, 50)
        self.assertLessEqual(self.player.cpu, 100)
        # Restored amount should be within real config range
        self.assertGreaterEqual(self.player.cpu, 50 + GameBalance.CPU_RESTORE_MIN)
        # Should log a message
        self.mock_game.message_log.add_message.assert_called()
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("CPU restored", call_args)

    def test_restore_cpu_at_max(self):
        """Test that restore_cpu doesn't exceed max CPU."""
        # Set player at max CPU
        self.player.cpu = 100
        self.player.max_cpu = 100

        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")
        result = code_hack._apply_effect('restore_cpu', self.player, self.mock_game)

        # Should not exceed max
        self.assertTrue(result)
        self.assertEqual(self.player.cpu, 100)

    def test_reduce_heat_effect(self):
        """Test that reduce_heat effect reduces player heat using real config values."""
        # Set player heat
        self.player.heat = 75

        code_hack = CodeHack("blue", "reduce_heat", "Blue Code", "Reduces heat")
        result = code_hack._apply_effect('reduce_heat', self.player, self.mock_game)

        # Should reduce heat by HEAT_REDUCTION_INSTANT from real config
        self.assertTrue(result)
        expected_heat = max(0, 75 - GameBalance.HEAT_REDUCTION_INSTANT)
        self.assertEqual(self.player.heat, expected_heat)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Heat reduced", call_args)

    def test_reduce_heat_minimum_zero(self):
        """Test that reduce_heat doesn't go below zero."""
        # Set player heat low
        self.player.heat = 10

        code_hack = CodeHack("blue", "reduce_heat", "Blue Code", "Reduces heat")
        result = code_hack._apply_effect('reduce_heat', self.player, self.mock_game)

        # Should not go below 0
        self.assertTrue(result)
        self.assertEqual(self.player.heat, 0)

    def test_reduce_trace_level_effect(self):
        """Test that reduce_trace level effect reduces player trace level."""
        # Set player trace level
        self.player.trace_level = 75

        code_hack = CodeHack("green", "reduce_trace level", "Green Code", "Reduces trace level")
        result = code_hack._apply_effect('reduce_trace_level', self.player, self.mock_game)

        # Should reduce trace level by 25
        self.assertTrue(result)
        self.assertEqual(self.player.trace_level, 50)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Trace Level", call_args)

    def test_reduce_trace_level_minimum_zero(self):
        """Test that reduce_trace level doesn't go below zero."""
        # Set player trace level low
        self.player.trace_level = 10

        code_hack = CodeHack("green", "reduce_trace level", "Green Code", "Reduces trace level")
        result = code_hack._apply_effect('reduce_trace_level', self.player, self.mock_game)

        # Should not go below 0
        self.assertTrue(result)
        self.assertEqual(self.player.trace_level, 0)

    def test_speed_boost_effect(self):
        """Test that speed_boost effect adds speed boost turns using real config."""
        # Start with no speed boost
        self.player.temporary_effects['speed_boost_turns'] = 0

        code_hack = CodeHack("yellow", "speed_boost", "Yellow Code", "Speed boost")
        result = code_hack._apply_effect('speed_boost', self.player, self.mock_game)

        # Should add turns based on real config (speed_boost_turns from game_config.json)
        self.assertTrue(result)
        # Get expected value from real config
        expected_turns = GameConfig.get('balance.speed_boost_turns', 3)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], expected_turns)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Speed boost active", call_args)

    def test_speed_boost_already_active(self):
        """Test that speed_boost doesn't stack when already active."""
        # Start with existing speed boost
        self.player.temporary_effects['speed_boost_turns'] = 2

        code_hack = CodeHack("yellow", "speed_boost", "Yellow Code", "Speed boost")
        result = code_hack._apply_effect('speed_boost', self.player, self.mock_game)

        # Should not add more turns
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 2)
        # Should log "already active" message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("already active", call_args)

    def test_speed_boost_cancels_slow(self):
        """Test that speed_boost cancels movement slow."""
        # Start with movement slow
        self.player.temporary_effects['movement_slowed_turns'] = 2
        self.player.temporary_effects['speed_boost_turns'] = 0

        code_hack = CodeHack("yellow", "speed_boost", "Yellow Code", "Speed boost")
        result = code_hack._apply_effect('speed_boost', self.player, self.mock_game)

        # Should cancel slow and add remaining speed boost
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['movement_slowed_turns'], 0)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 1)  # 3 - 2 = 1

    def test_enhanced_vision_effect(self):
        """Test that enhanced_vision effect adds vision turns using real config."""
        # Start with no enhanced vision
        self.player.temporary_effects['enhanced_vision_turns'] = 0

        code_hack = CodeHack("cyan", "enhanced_vision", "Cyan Code", "Enhanced vision")
        result = code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)

        # Should add turns based on real config
        self.assertTrue(result)
        expected_turns = GameConfig.get('balance.enhanced_vision_turns', 5)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], expected_turns)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Enhanced vision active", call_args)

    def test_enhanced_vision_extends(self):
        """Test that enhanced_vision extends when already active."""
        # Start with existing enhanced vision
        self.player.temporary_effects['enhanced_vision_turns'] = 3

        code_hack = CodeHack("cyan", "enhanced_vision", "Cyan Code", "Enhanced vision")
        result = code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)

        # Should extend to 8 turns (3 + 5)
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 8)
        # Should log "extended" message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("extended", call_args)

    def test_exploit_efficiency_effect(self):
        """Test that exploit_efficiency effect adds efficiency turns using real config."""
        # Start with no exploit efficiency
        self.player.temporary_effects['exploit_efficiency_turns'] = 0

        code_hack = CodeHack("magenta", "exploit_efficiency", "Magenta Code", "Exploit efficiency")
        result = code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)

        # Should add turns based on real config
        self.assertTrue(result)
        expected_turns = GameConfig.get('balance.exploit_efficiency_turns', 8)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], expected_turns)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Exploit efficiency active", call_args)

    def test_exploit_efficiency_extends(self):
        """Test that exploit_efficiency extends when already active."""
        # Start with existing exploit efficiency
        self.player.temporary_effects['exploit_efficiency_turns'] = 5

        code_hack = CodeHack("magenta", "exploit_efficiency", "Magenta Code", "Exploit efficiency")
        result = code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)

        # Should extend to 13 turns (5 + 8)
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 13)
        # Should log "extended" message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("extended", call_args)


if __name__ == '__main__':
    unittest.main()
