#!/usr/bin/env python3
"""
Additional unit tests for game_state.py - covering missing areas.
Tests specifically target uncovered lines in MessageLog, GameStateManager, and TurnProcessor.
"""

import pytest
from unittest.mock import Mock, patch
import random

from game_state import MessageLog, GameStateManager, TurnProcessor
from game_entities import Position, Colors
from game_config import GameConfig


class TestMessageLogMissingCoverage:
    """Test MessageLog functionality - covering missing areas."""
    
    def test_add_message_empty_text(self):
        """Test adding empty message (line 26)."""
        message_log = MessageLog()
        initial_count = len(message_log.messages)
        
        # Empty text should be rejected
        message_log.add_message("")
        message_log.add_message(None)
        
        assert len(message_log.messages) == initial_count
    
    def test_add_message_with_none_color_and_type(self):
        """Test add_message with None color and msg_type (line 37)."""
        message_log = MessageLog()
        
        with patch.object(message_log, '_determine_message_color') as mock_determine:
            mock_determine.return_value = (100, 150, 200)
            
            message_log.add_message("Test message", color=None, msg_type=None)
            
            mock_determine.assert_called_once_with("Test message")
            assert message_log.messages[-1] == ("Test message", (100, 150, 200))
    
    def test_get_recent_messages_exact_count(self):
        """Test get_recent_messages when count equals message count (line 75)."""
        message_log = MessageLog()
        
        # Add exactly 3 messages
        message_log.add_message("Message 1")
        message_log.add_message("Message 2") 
        message_log.add_message("Message 3")
        
        # Request exactly 3 messages
        recent = message_log.get_recent_messages(3)
        
        assert len(recent) == 3
        assert recent == message_log.messages  # Should return all messages
    
    @patch('data_loading.DataLoader.load_config')
    def test_determine_message_color_no_pattern_match(self, mock_load_config):
        """Test _determine_message_color when no patterns match (line 70)."""
        mock_load_config.return_value = {
            "message_types": {
                "patterns": {
                    "combat": ["attack", "damage"],
                    "system": ["cpu", "restored"]
                }
            },
            "colors": {
                "message_log": {
                    "combat": [255, 0, 0],
                    "system": [0, 255, 0],
                    "default": [144, 238, 144]
                }
            }
        }
        
        message_log = MessageLog()
        color = message_log._determine_message_color("Random unmatched message")
        
        # Should return default color
        assert color == (144, 238, 144)


class TestGameStateManagerMissingCoverage:
    """Test GameStateManager functionality - covering missing areas."""
    
    def test_advance_turn_threat_scan_processing(self):
        """Test advance_turn with threat_scan_turns processing (line 100)."""
        manager = GameStateManager()
        manager.threat_scan_turns = 3
        
        manager.advance_turn()
        
        assert manager.threat_scan_turns == 2
        assert manager.turn == 1
    
    def test_advance_turn_distraction_points_decay(self):
        """Test advance_turn with distraction points decay (lines 105-111)."""
        manager = GameStateManager()
        
        # Set up distraction points with different durations
        pos1 = Position(5, 5)
        pos2 = Position(10, 10)
        pos3 = Position(15, 15)
        
        manager.distraction_points = {
            pos1: 1,  # Should expire
            pos2: 3,  # Should decrement
            pos3: 1   # Should also expire
        }
        
        manager.advance_turn()
        
        # pos1 and pos3 should be removed, pos2 should be decremented
        assert pos1 not in manager.distraction_points
        assert pos3 not in manager.distraction_points
        assert manager.distraction_points[pos2] == 2
    
    def test_should_spawn_admin_already_spawned(self):
        """Test should_spawn_admin when admin already spawned (lines 120-123)."""
        manager = GameStateManager()
        manager.admin_spawned = True
        
        result = manager.should_spawn_admin(95.0)  # High detection
        
        assert result is False


class TestTurnProcessorMissingCoverage:
    """Test TurnProcessor functionality - covering missing areas."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameStateManager()
        self.message_log = MessageLog()
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)
        
        # Create mock player
        self.mock_player = Mock()
        self.mock_player.heat = 0
        self.mock_player.detection = 30
        self.mock_player.temporary_effects = {
            'exploit_efficiency_turns': 0,
            'virus_turns': 0
        }
        self.mock_player.cpu = 100
        self.mock_player.take_damage = Mock(return_value=10)
    
    def test_process_heat_management_with_exploit_efficiency(self):
        """Test heat management with exploit efficiency boost (lines 149-154)."""
        self.mock_player.heat = 20
        self.mock_player.temporary_effects['exploit_efficiency_turns'] = 3
        
        self.turn_processor._process_heat_management(self.mock_player)
        
        # Should use boosted reduction (GameBalance.HEAT_REDUCTION_BOOSTED = 3)
        expected_heat = max(0, 20 - 3)
        assert self.mock_player.heat == expected_heat
    
    def test_process_temporary_effects_virus_damage(self):
        """Test virus damage processing (lines 165-176)."""
        self.mock_player.temporary_effects['virus_turns'] = 2
        self.mock_player.cpu = 50
        
        self.turn_processor._process_temporary_effects(self.mock_player)
        
        # Virus should cause damage
        self.mock_player.take_damage.assert_called()
        # Effect should be decremented
        assert self.mock_player.temporary_effects['virus_turns'] == 1
    
    def test_process_temporary_effects_virus_death(self):
        """Test virus causing player death (lines 170-176)."""
        self.mock_player.temporary_effects['virus_turns'] = 1
        self.mock_player.cpu = 0  # Player dies from virus
        
        with patch('game_save.SaveGameManager.delete_save') as mock_delete:
            self.turn_processor._process_temporary_effects(self.mock_player)
            
            mock_delete.assert_called_once()
            assert self.game_state.game_over is True
    
    def test_process_temporary_effects_effect_expiration_messages(self):
        """Test effect expiration messages (lines 182-191)."""
        self.mock_player.temporary_effects = {
            'exploit_efficiency_turns': 1,
            'data_mimic_turns': 1,
            'speed_boost_turns': 1,
            'movement_slowed_turns': 1,
            'virus_turns': 1
        }
        self.mock_player.cpu = 100  # Ensure no death
        
        # Process turn to expire all effects
        self.turn_processor._process_temporary_effects(self.mock_player)
        
        # All effects should now be 0
        for effect_name, turns in self.mock_player.temporary_effects.items():
            assert turns == 0
        
        # Check that appropriate messages were added for each effect type
        messages = [msg[0] for msg in self.message_log.messages]
        
        expected_messages = [
            "Exploit efficiency boost expired",
            "Data Mimic invisibility expired", 
            "Speed boost expired",
            "Movement returns to normal",
            "Virus purged from system"
        ]
        
        for expected_msg in expected_messages:
            assert any(expected_msg in msg for msg in messages)
    
    def test_process_detection_increase_silent(self):
        """Test detection increase happens silently (lines 196-200)."""
        self.game_state.turn = 25  # At interval
        initial_messages = len(self.message_log.messages)
        
        self.turn_processor._process_detection_increase(self.mock_player)
        
        # Detection should increase but no message should be added
        assert self.mock_player.detection > 30
        assert len(self.message_log.messages) == initial_messages
    
    def test_process_detection_increase_with_network_config(self):
        """Test detection increase using network config (lines 196-200)."""
        self.game_state.turn = 25  # At interval
        self.game_state.level = 3  # Specific level for config
        self.mock_player.detection = 40
        
        # Mock the get_current_network_config to return specific values
        with patch.object(self.game_state, 'get_current_network_config') as mock_config:
            mock_config.return_value = {'background_detection': 2}
            
            self.turn_processor._process_detection_increase(self.mock_player)
            
            # Detection should increase by background_detection * DETECTION_INCREASE_AMOUNT
            # 2 * 1 = 2 points increase
            expected_detection = min(100, 40 + 2)
            assert self.mock_player.detection == expected_detection


class TestMessageLogAdvancedCoverage:
    """Additional MessageLog tests for edge cases."""
    
    @patch('data_loading.DataLoader.load_config')
    def test_get_color_by_type_fallback_to_default(self, mock_load_config):
        """Test _get_color_by_type fallback when specific type not found."""
        mock_load_config.return_value = {
            "colors": {
                "message_log": {
                    "combat": [255, 0, 0],
                    "default": [144, 238, 144]
                }
            }
        }
        
        message_log = MessageLog()
        color = message_log._get_color_by_type("nonexistent_type")
        
        # Should return default color
        assert color == (144, 238, 144)
    
    @patch('data_loading.DataLoader.load_config')
    def test_get_color_by_type_missing_default(self, mock_load_config):
        """Test _get_color_by_type when default is also missing."""
        mock_load_config.return_value = {
            "colors": {
                "message_log": {
                    "combat": [255, 0, 0]
                    # No default
                }
            }
        }
        
        message_log = MessageLog()
        color = message_log._get_color_by_type("nonexistent_type")
        
        # Should return fallback default
        assert color == (144, 238, 144)
    
    def test_message_log_max_messages_boundary(self):
        """Test message log at max capacity boundary."""
        message_log = MessageLog(max_messages=3)
        
        # Add messages up to capacity
        message_log.add_message("Message 1")
        message_log.add_message("Message 2")
        message_log.add_message("Message 3")
        
        assert len(message_log.messages) == 3
        
        # Add one more to trigger truncation
        message_log.add_message("Message 4")
        
        assert len(message_log.messages) == 3
        # First message should be removed
        messages_text = [msg[0] for msg in message_log.messages]
        assert "Message 1" not in messages_text
        assert "Message 4" in messages_text