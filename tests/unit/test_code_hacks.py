#!/usr/bin/env python3
"""
Unit tests for code hack effects.
Tests all code hack types to ensure they function correctly.
"""

import unittest
from unittest.mock import MagicMock, patch
from game_inventory import CodeHack
from game_characters import Player


class TestCodeHackEffects(unittest.TestCase):
    """Test all code hack effect types."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(10, 10)
        self.mock_game = MagicMock()
        self.mock_game.message_log = MagicMock()
        self.mock_game.message_log.add_message = MagicMock()

        # Mock GameBalance values to avoid property issues
        self.game_balance_patcher = patch('game_inventory.GameBalance')
        self.mock_game_balance = self.game_balance_patcher.start()
        self.mock_game_balance.CPU_RESTORE_MIN = 30
        self.mock_game_balance.CPU_RESTORE_MAX = 40

    def tearDown(self):
        """Clean up patches."""
        self.game_balance_patcher.stop()

    def test_restore_cpu_effect(self):
        """Test that restore_cpu effect restores player CPU."""
        # Set player CPU below max
        self.player.cpu = 50
        self.player.max_cpu = 100

        code_hack = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU")
        result = code_hack._apply_effect('restore_cpu', self.player, self.mock_game)

        # Should restore CPU (amount varies due to random)
        self.assertTrue(result)
        self.assertGreater(self.player.cpu, 50)
        self.assertLessEqual(self.player.cpu, 100)
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
        """Test that reduce_heat effect reduces player heat."""
        # Set player heat
        self.player.heat = 75

        code_hack = CodeHack("blue", "reduce_heat", "Blue Code", "Reduces heat")
        result = code_hack._apply_effect('reduce_heat', self.player, self.mock_game)

        # Should reduce heat by 25
        self.assertTrue(result)
        self.assertEqual(self.player.heat, 50)
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

    def test_reduce_detection_effect(self):
        """Test that reduce_detection effect reduces player detection."""
        # Set player detection
        self.player.detection = 75

        code_hack = CodeHack("green", "reduce_detection", "Green Code", "Reduces detection")
        result = code_hack._apply_effect('reduce_detection', self.player, self.mock_game)

        # Should reduce detection by 25
        self.assertTrue(result)
        self.assertEqual(self.player.detection, 50)
        # Should log a message
        call_args = str(self.mock_game.message_log.add_message.call_args)
        self.assertIn("Detection", call_args)

    def test_reduce_detection_minimum_zero(self):
        """Test that reduce_detection doesn't go below zero."""
        # Set player detection low
        self.player.detection = 10

        code_hack = CodeHack("green", "reduce_detection", "Green Code", "Reduces detection")
        result = code_hack._apply_effect('reduce_detection', self.player, self.mock_game)

        # Should not go below 0
        self.assertTrue(result)
        self.assertEqual(self.player.detection, 0)

    def test_speed_boost_effect(self):
        """Test that speed_boost effect adds speed boost turns."""
        # Start with no speed boost
        self.player.temporary_effects['speed_boost_turns'] = 0

        code_hack = CodeHack("yellow", "speed_boost", "Yellow Code", "Speed boost")
        result = code_hack._apply_effect('speed_boost', self.player, self.mock_game)

        # Should add 3 turns of speed boost
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 3)
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
        """Test that enhanced_vision effect adds vision turns."""
        # Start with no enhanced vision
        self.player.temporary_effects['enhanced_vision_turns'] = 0

        code_hack = CodeHack("cyan", "enhanced_vision", "Cyan Code", "Enhanced vision")
        result = code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)

        # Should add 5 turns of enhanced vision
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 5)
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
        """Test that exploit_efficiency effect adds efficiency turns."""
        # Start with no exploit efficiency
        self.player.temporary_effects['exploit_efficiency_turns'] = 0

        code_hack = CodeHack("magenta", "exploit_efficiency", "Magenta Code", "Exploit efficiency")
        result = code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)

        # Should add 8 turns of exploit efficiency
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 8)
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
