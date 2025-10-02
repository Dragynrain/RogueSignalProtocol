#!/usr/bin/env python3
"""
Extended tests for game_core.py to improve coverage from 60% to 80%+.
Tests focus on uncovered methods and edge cases.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game_state import GameStateManager, TurnProcessor
from game_entities import Colors
from game_config import GameBalance


class TestGameStateManagerExtended(unittest.TestCase):
    """Extended tests for GameStateManager covering missing functionality."""
    
    def setUp(self):
        self.state_manager = GameStateManager()
        
    def test_admin_spawn_chance_calculation(self):
        """Test admin spawn chance calculation at different levels."""
        # Test level 1 (should have base chance)
        self.state_manager.current_level = 1
        config = self.state_manager.get_current_network_config()
        expected_chance = 0.1 + (1 - 1) * 0.05  # 0.1
        self.assertEqual(config['admin_chance'], expected_chance)
        
        # Test level 15 (should be capped at 0.8)
        self.state_manager.current_level = 15
        config = self.state_manager.get_current_network_config()
        expected_chance = min(0.8, 0.1 + (15 - 1) * 0.05)  # Should be capped at 0.8
        self.assertEqual(config['admin_chance'], 0.8)
        
    def test_patrol_density_scaling(self):
        """Test patrol density scaling with level."""
        # Test level 1
        self.state_manager.current_level = 1
        config = self.state_manager.get_current_network_config()
        expected_density = min(3, 1 + 1 // 3)  # 1
        self.assertEqual(config['patrol_density'], expected_density)
        
        # Test level 9 (should hit max)
        self.state_manager.current_level = 9
        config = self.state_manager.get_current_network_config()
        expected_density = min(3, 1 + 9 // 3)  # 3
        self.assertEqual(config['patrol_density'], 3)
        
    def test_security_level_scaling(self):
        """Test security level scaling with current level."""
        # Test level 1
        self.state_manager.current_level = 1
        config = self.state_manager.get_current_network_config()
        expected_security = min(5, 1 // 2 + 1)  # 1
        self.assertEqual(config['security_level'], expected_security)
        
        # Test level 10 (should be capped)
        self.state_manager.current_level = 10
        config = self.state_manager.get_current_network_config()
        expected_security = min(5, 10 // 2 + 1)  # Should be capped at 5
        self.assertEqual(config['security_level'], 5)
        
    def test_admin_spawn_after_spawning(self):
        """Test that admin won't spawn again after already spawning."""
        # Manually set admin as spawned
        self.state_manager.admin_spawned_this_level = True
        result = self.state_manager.should_spawn_admin()
        self.assertFalse(result)
        
    def test_admin_spawn_random_chance(self):
        """Test admin spawn with mocked random chance."""
        self.state_manager.current_level = 5
        
        # Mock random to return value that should trigger spawn
        with patch('random.random', return_value=0.1):  # Low value should trigger spawn
            result = self.state_manager.should_spawn_admin()
            self.assertTrue(result)
            self.assertTrue(self.state_manager.admin_spawned_this_level)
            
        # Reset for next test
        self.state_manager.admin_spawned_this_level = False
        
        # Mock random to return value that should NOT trigger spawn
        with patch('random.random', return_value=0.9):  # High value should not trigger spawn
            result = self.state_manager.should_spawn_admin()
            self.assertFalse(result)
            self.assertFalse(self.state_manager.admin_spawned_this_level)


class TestTurnProcessorExtended(unittest.TestCase):
    """Extended tests for TurnProcessor covering missing functionality."""
    
    def setUp(self):
        self.game_state = Mock()
        self.game_state.turn = 0
        self.message_log = Mock()
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)
        
    def test_heat_management_with_near_cooling_node(self):
        """Test heat management when player is near cooling node."""
        player = Mock()
        player.heat = 10
        player.near_cooling_node = True
        message_log = Mock()
        
        self.turn_processor._process_heat_management(player, message_log)
        
        expected_heat = max(0, 10 - GameBalance.HEAT_REDUCTION_BOOSTED)
        self.assertEqual(player.heat, expected_heat)
        message_log.add_message.assert_called_once()
        
        # Check that the message contains boosted reduction info
        call_args = message_log.add_message.call_args
        self.assertIn(str(GameBalance.HEAT_REDUCTION_BOOSTED), call_args[0][0])
        self.assertEqual(call_args[0][1], Colors.CYAN)
        
    def test_heat_management_normal_reduction(self):
        """Test heat management with normal reduction."""
        player = Mock()
        player.heat = 5
        player.near_cooling_node = False
        message_log = Mock()
        
        self.turn_processor._process_heat_management(player, message_log)
        
        expected_heat = max(0, 5 - GameBalance.HEAT_REDUCTION_NORMAL)
        self.assertEqual(player.heat, expected_heat)
        message_log.add_message.assert_called_once()
        
        # Check normal color
        call_args = message_log.add_message.call_args
        self.assertEqual(call_args[0][1], Colors.BLUE)
        
    def test_heat_management_no_change_when_zero(self):
        """Test heat management doesn't process when heat is already 0."""
        player = Mock()
        player.heat = 0
        message_log = Mock()
        
        self.turn_processor._process_heat_management(player, message_log)
        
        self.assertEqual(player.heat, 0)
        message_log.add_message.assert_not_called()
        
    def test_virus_duration_processing(self):
        """Test virus duration countdown and expiration."""
        player = Mock()
        player.virus_duration = 2
        # Mock temporary_effects to avoid iteration error
        player.temporary_effects = {}
        message_log = Mock()
        
        # First turn - should reduce but not expire
        self.turn_processor._process_temporary_effects(player, message_log)
        self.assertEqual(player.virus_duration, 1)
        message_log.add_message.assert_not_called()
        
        # Second turn - should expire
        self.turn_processor._process_temporary_effects(player, message_log)
        self.assertEqual(player.virus_duration, 0)
        message_log.add_message.assert_called_once_with("Virus effect has worn off", Colors.GREEN)
        
    def test_temporary_effects_processing(self):
        """Test temporary effects countdown and removal."""
        player = Mock()
        player.temporary_effects = {'stealth': 2, 'speed_boost': 1}
        player.virus_duration = 0  # Set to avoid virus processing
        message_log = Mock()
        
        # First turn - speed_boost should expire, stealth should reduce
        self.turn_processor._process_temporary_effects(player, message_log)
        
        self.assertEqual(player.temporary_effects, {'stealth': 1})
        message_log.add_message.assert_called_once_with("speed_boost effect has worn off", Colors.YELLOW)
        
    def test_temporary_effects_no_effects(self):
        """Test temporary effects processing when player has no effects."""
        player = Mock()
        player.virus_duration = 0  # Set to avoid virus processing
        # Player doesn't have temporary_effects attribute - create spec to avoid default Mock behavior
        player_spec = Mock(spec=[])  # Empty spec means no attributes
        player_spec.virus_duration = 0
        message_log = Mock()
        
        # Should not raise exception
        self.turn_processor._process_temporary_effects(player_spec, message_log)
        message_log.add_message.assert_not_called()
        
    def test_detection_increase_at_interval(self):
        """Test detection increases at proper intervals."""
        player = Mock()
        player.detection = 20
        message_log = Mock()
        
        # Set turn count to trigger detection increase
        self.game_state.turn = GameBalance.DETECTION_INCREASE_INTERVAL
        
        self.turn_processor._process_detection_increase(player, message_log)
        
        expected_detection = min(100, 20 + GameBalance.DETECTION_INCREASE_AMOUNT)
        self.assertEqual(player.detection, expected_detection)
        message_log.add_message.assert_called_once()
        
        call_args = message_log.add_message.call_args
        self.assertIn("Network security tightening", call_args[0][0])
        self.assertEqual(call_args[0][1], Colors.YELLOW)
        
    def test_detection_increase_not_at_interval(self):
        """Test detection doesn't increase when not at interval."""
        player = Mock()
        player.detection = 20
        message_log = Mock()
        
        # Set turn count to NOT trigger detection increase
        self.game_state.turn = GameBalance.DETECTION_INCREASE_INTERVAL - 1
        
        self.turn_processor._process_detection_increase(player, message_log)
        
        # Detection should remain unchanged
        self.assertEqual(player.detection, 20)
        message_log.add_message.assert_not_called()
        
    def test_detection_caps_at_100(self):
        """Test detection doesn't exceed 100."""
        player = Mock()
        # Start at 99, add 1, should cap at 100 and trigger message
        player.detection = 99  
        message_log = Mock()
        
        # Set turn count to trigger detection increase
        self.game_state.turn = GameBalance.DETECTION_INCREASE_INTERVAL
        
        self.turn_processor._process_detection_increase(player, message_log)
        
        # Should cap at 100
        self.assertEqual(player.detection, 100)
        message_log.add_message.assert_called_once()


class TestCoreIntegrationExtended(unittest.TestCase):
    """Extended integration tests for core systems."""
    
    def test_state_manager_and_turn_processor_integration(self):
        """Test that GameStateManager and TurnProcessor work together properly."""
        state_manager = GameStateManager()
        message_log = Mock()
        turn_processor = TurnProcessor(state_manager, message_log)
        
        # Create mock player and message log
        player = Mock()
        player.heat = 10
        player.detection = 30
        player.virus_duration = 1
        player.temporary_effects = {'haste': 2}
        player.near_cooling_node = False
        
        message_log = Mock()
        
        # Set turn count to trigger detection increase
        state_manager.turn = GameBalance.DETECTION_INCREASE_INTERVAL
        
        # Process turn
        turn_processor.process_turn(player, message_log)
        
        # Verify state manager was updated
        self.assertEqual(state_manager.turn, GameBalance.DETECTION_INCREASE_INTERVAL + 1)
        
        # Verify all effects were processed
        self.assertTrue(message_log.add_message.called)
        
    def test_network_config_caching(self):
        """Test that network configs are properly cached."""
        state_manager = GameStateManager()
        
        # Get config for level 1
        config1 = state_manager.get_current_network_config()
        config1_again = state_manager.get_current_network_config()
        
        # Should be the same object (cached)
        self.assertIs(config1, config1_again)
        
        # Change level and get new config
        state_manager.current_level = 2
        config2 = state_manager.get_current_network_config()
        
        # Should be different objects
        self.assertIsNot(config1, config2)
        
        # But level 1 should still be cached
        state_manager.current_level = 1
        config1_cached = state_manager.get_current_network_config()
        self.assertIs(config1, config1_cached)


if __name__ == '__main__':
    unittest.main()