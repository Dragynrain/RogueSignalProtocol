#!/usr/bin/env python3
"""
Unit tests for game_core.py - Core game logic and state management.
"""

import pytest
from unittest.mock import Mock, patch
import random

from game_core import GameStateManager, TurnProcessor
from game_entities import Colors


class TestGameStateManager:
    """Test the GameStateManager class."""
    
    def test_initialization(self):
        """Test GameStateManager initialization."""
        manager = GameStateManager()
        
        assert manager.current_level == 1
        assert manager.turn_count == 0
        assert manager.game_paused is False
        assert manager.admin_spawned_this_level is False
        assert manager.network_configs == {}
    
    def test_advance_turn(self):
        """Test turn advancement."""
        manager = GameStateManager()
        initial_turn = manager.turn_count
        
        manager.advance_turn()
        
        assert manager.turn_count == initial_turn + 1
    
    def test_reset_for_new_level(self):
        """Test level advancement and state reset."""
        manager = GameStateManager()
        manager.current_level = 3
        manager.turn_count = 50
        manager.admin_spawned_this_level = True
        
        manager.reset_for_new_level()
        
        assert manager.current_level == 4
        assert manager.turn_count == 0
        assert manager.admin_spawned_this_level is False
    
    def test_get_current_network_config_new_level(self):
        """Test network config generation for new level."""
        manager = GameStateManager()
        manager.current_level = 3
        
        config = manager.get_current_network_config()
        
        assert 'security_level' in config
        assert 'admin_chance' in config
        assert 'patrol_density' in config
        assert config['security_level'] == min(5, 3 // 2 + 1)  # 2 for level 3
        assert config['admin_chance'] == min(0.8, 0.1 + (3 - 1) * 0.05)  # 0.2
        assert config['patrol_density'] == min(3, 1 + 3 // 3)  # 2
    
    def test_get_current_network_config_cached(self):
        """Test that network config is cached correctly."""
        manager = GameStateManager()
        manager.current_level = 2
        
        # First call should generate config
        config1 = manager.get_current_network_config()
        
        # Second call should return cached config
        config2 = manager.get_current_network_config()
        
        assert config1 == config2
        assert 2 in manager.network_configs
    
    def test_get_current_network_config_scaling(self):
        """Test network config scaling with level progression."""
        manager = GameStateManager()
        
        # Test level 1
        manager.current_level = 1
        config1 = manager.get_current_network_config()
        assert config1['security_level'] == 1
        assert config1['admin_chance'] == 0.1
        assert config1['patrol_density'] == 1
        
        # Test level 10 (should hit caps)
        manager.current_level = 10
        config10 = manager.get_current_network_config()
        assert config10['security_level'] == 5  # Capped at 5
        assert config10['admin_chance'] == 0.55  # 0.1 + 9*0.05
        assert config10['patrol_density'] == 3  # Capped at 3
        
        # Test level 20 (should hit admin_chance cap)
        manager.current_level = 20
        config20 = manager.get_current_network_config()
        assert config20['admin_chance'] == 0.8  # Capped at 0.8
    
    @patch('random.random')
    def test_should_spawn_admin_success(self, mock_random):
        """Test admin spawning when conditions are met."""
        mock_random.return_value = 0.05  # Below chance threshold
        
        manager = GameStateManager()
        manager.current_level = 5  # admin_chance = 0.3
        
        result = manager.should_spawn_admin()
        
        assert result is True
        assert manager.admin_spawned_this_level is True
    
    @patch('random.random')
    def test_should_spawn_admin_failure(self, mock_random):
        """Test admin not spawning when chance fails."""
        mock_random.return_value = 0.95  # Above chance threshold
        
        manager = GameStateManager()
        manager.current_level = 5  # admin_chance = 0.3
        
        result = manager.should_spawn_admin()
        
        assert result is False
        assert manager.admin_spawned_this_level is False
    
    def test_should_spawn_admin_already_spawned(self):
        """Test admin not spawning when already spawned this level."""
        manager = GameStateManager()
        manager.admin_spawned_this_level = True
        
        result = manager.should_spawn_admin()
        
        assert result is False


class TestTurnProcessor:
    """Test the TurnProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameStateManager()
        self.turn_processor = TurnProcessor(self.game_state)
        
        # Create mock player and message log
        self.mock_player = Mock()
        self.mock_player.heat = 50
        self.mock_player.detection = 30
        self.mock_player.virus_duration = 0
        self.mock_player.temporary_effects = {}
        
        self.mock_message_log = Mock()
    
    def test_initialization(self):
        """Test TurnProcessor initialization."""
        assert self.turn_processor.game_state == self.game_state
    
    def test_process_turn_sequence(self):
        """Test that process_turn calls all sub-processes."""
        with patch.object(self.turn_processor, '_process_heat_management') as mock_heat, \
             patch.object(self.turn_processor, '_process_temporary_effects') as mock_effects, \
             patch.object(self.turn_processor, '_process_detection_increase') as mock_detection:
            
            initial_turn = self.game_state.turn_count
            
            self.turn_processor.process_turn(self.mock_player, self.mock_message_log)
            
            # Verify turn advanced
            assert self.game_state.turn_count == initial_turn + 1
            
            # Verify all processes called
            mock_heat.assert_called_once_with(self.mock_player, self.mock_message_log)
            mock_effects.assert_called_once_with(self.mock_player, self.mock_message_log)
            mock_detection.assert_called_once_with(self.mock_player, self.mock_message_log)
    
    def test_process_heat_management_normal_reduction(self):
        """Test normal heat reduction."""
        self.mock_player.heat = 50
        self.mock_player.near_cooling_node = False
        
        self.turn_processor._process_heat_management(self.mock_player, self.mock_message_log)
        
        # Heat should be reduced by normal amount (2)
        expected_heat = max(0, 50 - 2)  # GameBalance.HEAT_REDUCTION_NORMAL = 2
        assert self.mock_player.heat == expected_heat
        self.mock_message_log.add_message.assert_called()
    
    def test_process_heat_management_boosted_reduction(self):
        """Test boosted heat reduction near cooling node."""
        self.mock_player.heat = 50
        self.mock_player.near_cooling_node = True
        
        self.turn_processor._process_heat_management(self.mock_player, self.mock_message_log)
        
        # Heat should be reduced by boosted amount (3)
        expected_heat = max(0, 50 - 3)  # GameBalance.HEAT_REDUCTION_BOOSTED = 3
        assert self.mock_player.heat == expected_heat
        self.mock_message_log.add_message.assert_called()
    
    def test_process_heat_management_no_heat(self):
        """Test heat management when player has no heat."""
        self.mock_player.heat = 0
        
        self.turn_processor._process_heat_management(self.mock_player, self.mock_message_log)
        
        # Heat should remain 0, no message should be added
        assert self.mock_player.heat == 0
        self.mock_message_log.add_message.assert_not_called()
    
    def test_process_heat_management_minimum_zero(self):
        """Test that heat doesn't go below zero."""
        self.mock_player.heat = 1  # Less than normal reduction
        self.mock_player.near_cooling_node = False
        
        self.turn_processor._process_heat_management(self.mock_player, self.mock_message_log)
        
        assert self.mock_player.heat == 0
    
    def test_process_temporary_effects_virus_duration(self):
        """Test virus duration processing."""
        self.mock_player.virus_duration = 3
        
        self.turn_processor._process_temporary_effects(self.mock_player, self.mock_message_log)
        
        assert self.mock_player.virus_duration == 2
        # Should not add message when virus is still active
        
        # Test virus expiration
        self.mock_player.virus_duration = 1
        self.turn_processor._process_temporary_effects(self.mock_player, self.mock_message_log)
        
        assert self.mock_player.virus_duration == 0
        self.mock_message_log.add_message.assert_called_with("Virus effect has worn off", Colors.GREEN)
    
    def test_process_temporary_effects_custom_effects(self):
        """Test processing of custom temporary effects."""
        self.mock_player.temporary_effects = {
            'speed_boost': 2,
            'stealth_mode': 1,
            'damage_immunity': 3
        }
        
        self.turn_processor._process_temporary_effects(self.mock_player, self.mock_message_log)
        
        # Effects should be decremented
        assert self.mock_player.temporary_effects['speed_boost'] == 1
        assert self.mock_player.temporary_effects['damage_immunity'] == 2
        
        # stealth_mode should be removed and message added
        assert 'stealth_mode' not in self.mock_player.temporary_effects
        self.mock_message_log.add_message.assert_called()
    
    def test_process_detection_increase_interval(self):
        """Test detection increase at correct intervals."""
        # DETECTION_INCREASE_INTERVAL = 25 
        self.game_state.turn_count = 25  # Should trigger increase
        self.mock_player.detection = 50
        
        self.turn_processor._process_detection_increase(self.mock_player, self.mock_message_log)
        
        # Detection should increase by DETECTION_INCREASE_AMOUNT (1)
        expected_detection = min(100, 50 + 1)
        assert self.mock_player.detection == expected_detection
        self.mock_message_log.add_message.assert_called()
    
    def test_process_detection_increase_no_interval(self):
        """Test no detection increase when not at interval."""
        self.game_state.turn_count = 7  # Not at interval
        self.mock_player.detection = 50
        
        self.turn_processor._process_detection_increase(self.mock_player, self.mock_message_log)
        
        # Detection should remain unchanged
        assert self.mock_player.detection == 50
        self.mock_message_log.add_message.assert_not_called()
    
    def test_process_detection_increase_maximum(self):
        """Test detection increase caps at 100."""
        self.game_state.turn_count = 25  # At interval
        self.mock_player.detection = 99
        
        self.turn_processor._process_detection_increase(self.mock_player, self.mock_message_log)
        
        # Detection should cap at 100
        assert self.mock_player.detection == 100


class TestTurnProcessorIntegration:
    """Integration tests for TurnProcessor with actual game state."""
    
    def test_full_turn_processing(self):
        """Test complete turn processing with real state changes."""
        game_state = GameStateManager()
        turn_processor = TurnProcessor(game_state)
        
        # Create mock player with various states
        mock_player = Mock()
        mock_player.heat = 25
        mock_player.detection = 45
        mock_player.virus_duration = 2
        mock_player.temporary_effects = {'speed_boost': 1, 'stealth': 3}
        mock_player.near_cooling_node = False
        
        mock_message_log = Mock()
        
        initial_turn = game_state.turn_count
        
        turn_processor.process_turn(mock_player, mock_message_log)
        
        # Verify turn advanced
        assert game_state.turn_count == initial_turn + 1
        
        # Verify heat was processed
        assert mock_player.heat < 25  # Should be reduced
        
        # Verify effects were processed
        assert mock_player.virus_duration == 1
        assert 'speed_boost' not in mock_player.temporary_effects  # Should be removed
        assert mock_player.temporary_effects['stealth'] == 2  # Should be decremented