#!/usr/bin/env python3
"""
Unit tests for GameStateManager and core game logic.
Tests the actual core game state management and turn processing systems.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random

# Import actual core classes
from game_state import GameStateManager, MessageLog, TurnProcessor
# game_core module was removed - using only game_state implementations
from game_entities import Position, Colors
from game_characters import Player
from game_config import GameBalance


class TestMessageLog:
    """Test the MessageLog class functionality."""
    
    def test_message_log_initialization(self):
        """MessageLog initializes correctly."""
        log = MessageLog()
        assert log.messages == []
        assert log.max_messages == 100
        
        # Test with custom max messages
        custom_log = MessageLog(max_messages=50)
        assert custom_log.max_messages == 50
    
    def test_add_message_basic(self):
        """add_message adds messages correctly."""
        log = MessageLog()
        
        log.add_message("Test message")
        
        assert len(log.messages) == 1
        assert log.messages[0].text == "Test message"
        assert isinstance(log.messages[0].color, tuple)  # Color tuple
        assert len(log.messages[0].color) == 3  # RGB values
    
    def test_add_message_with_color(self):
        """add_message respects explicit color parameter."""
        log = MessageLog()
        test_color = (255, 128, 0)  # Orange
        
        log.add_message("Colored message", color=test_color)
        
        assert len(log.messages) == 1
        assert log.messages[0].color == test_color
    
    def test_add_message_with_type(self):
        """add_message handles message types correctly."""
        log = MessageLog()
        
        with patch.object(log, '_get_color_by_type', return_value=Colors.RED) as mock_get_color:
            log.add_message("Error message", msg_type="error")
            
            mock_get_color.assert_called_once_with("error")
            assert len(log.messages) == 1
    
    def test_add_empty_message(self):
        """add_message ignores empty or None messages."""
        log = MessageLog()
        
        log.add_message("")
        log.add_message(None)
        
        assert len(log.messages) == 0
    
    def test_message_log_max_capacity(self):
        """MessageLog respects max_messages capacity."""
        log = MessageLog(max_messages=3)
        
        # Add more messages than capacity
        for i in range(5):
            log.add_message(f"Message {i}")
        
        assert len(log.messages) == 3
        # Should keep the most recent messages
        assert log.messages[0].text == "Message 2"
        assert log.messages[1].text == "Message 3"
        assert log.messages[2].text == "Message 4"
    
    def test_get_recent_messages(self):
        """get_recent_messages returns correct number of messages."""
        log = MessageLog()
        
        for i in range(5):
            log.add_message(f"Message {i}")
        
        # Get last 3 messages
        recent = log.get_recent_messages(3)
        
        assert len(recent) == 3
        assert recent[0].text == "Message 2"
        assert recent[1].text == "Message 3"
        assert recent[2].text == "Message 4"
    
    def test_get_recent_messages_fewer_than_requested(self):
        """get_recent_messages handles requests for more messages than available."""
        log = MessageLog()
        
        log.add_message("Only message")
        
        recent = log.get_recent_messages(5)  # Request more than available
        
        assert len(recent) == 1
        assert recent[0].text == "Only message"
    
    def test_message_color_determination(self):
        """_determine_message_color chooses appropriate colors."""
        log = MessageLog()
        
        with patch('game_state.DataLoader') as mock_loader:
            # Mock config data
            mock_config = {
                "message_types": {
                    "patterns": {
                        "error": ["error", "failed", "crash"],
                        "success": ["success", "complete", "found"]
                    }
                },
                "colors": {
                    "message_log": {
                        "error": [255, 0, 0],
                        "success": [0, 255, 0],
                        "default": [255, 255, 255]
                    }
                }
            }
            mock_loader.load_config.return_value = mock_config
            
            # Test error message color
            error_color = log._determine_message_color("Operation failed")
            assert error_color == (255, 0, 0)  # Red
            
            # Test success message color
            success_color = log._determine_message_color("Task complete")
            assert success_color == (0, 255, 0)  # Green
            
            # Test default color
            default_color = log._determine_message_color("Generic message")
            assert default_color == (255, 255, 255)  # White


class TestGameStateManager:
    """Test the GameStateManager class functionality."""
    
    def test_game_state_manager_initialization(self):
        """GameStateManager initializes with correct defaults."""
        gsm = GameStateManager()
        
        assert gsm.level == 1
        assert gsm.turn == 0
        assert gsm.game_over is False
        assert gsm.admin_spawned is False
        assert isinstance(gsm.dungeon_seed, int)
        assert gsm.threat_scan_turns == 0
        assert gsm.noise_locations == []
        assert gsm.distraction_points == {}
    
    def test_advance_turn(self):
        """advance_turn increments turn counter."""
        gsm = GameStateManager()
        initial_turn = gsm.turn
        
        gsm.advance_turn()
        
        assert gsm.turn == initial_turn + 1
    
    def test_advance_turn_updates_effects(self):
        """advance_turn decreases threat scan duration."""
        gsm = GameStateManager()
        gsm.threat_scan_turns = 5
        
        gsm.advance_turn()
        
        assert gsm.threat_scan_turns == 4
    
    def test_multiple_turn_advances(self):
        """Multiple turn advances work correctly."""
        gsm = GameStateManager()
        
        for i in range(10):
            gsm.advance_turn()
        
        assert gsm.turn == 10
    
    def test_distraction_points_management(self):
        """Distraction points can be managed correctly."""
        gsm = GameStateManager()
        position = Position(10, 15)
        
        gsm.distraction_points[position] = 5
        
        assert gsm.distraction_points[position] == 5
        assert len(gsm.distraction_points) == 1
    
    def test_noise_locations_management(self):
        """Noise locations can be managed correctly."""
        gsm = GameStateManager()
        position1 = Position(5, 5)
        position2 = Position(10, 10)
        
        gsm.noise_locations.extend([position1, position2])
        
        assert len(gsm.noise_locations) == 2
        assert position1 in gsm.noise_locations
        assert position2 in gsm.noise_locations
    
    def test_revealed_special_nodes(self):
        """Revealed special nodes can be tracked."""
        gsm = GameStateManager()
        
        gsm.revealed_special_nodes[(15, 20)] = "cooling_node"
        gsm.revealed_special_nodes[(25, 30)] = "cpu_node"
        
        assert gsm.revealed_special_nodes[(15, 20)] == "cooling_node"
        assert gsm.revealed_special_nodes[(25, 30)] == "cpu_node"
        assert len(gsm.revealed_special_nodes) == 2


class TestTurnProcessor:
    """Test the TurnProcessor class functionality."""
    
    def test_turn_processor_initialization(self):
        """TurnProcessor initializes with GameStateManager and MessageLog."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        assert processor.game_state is gsm
        assert processor.message_log is message_log
    
    def test_process_turn_advances_game_state(self):
        """process_turn advances the game state."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        mock_player = Mock()
        # Configure mock with numeric values for logging
        mock_player.heat = 50
        mock_player.max_heat = 100
        mock_player.trace_level = 25.0
        mock_player.cpu = 70
        mock_player.max_cpu = 100

        initial_turn = gsm.turn

        with patch.object(processor, '_process_heat_management'), \
             patch.object(processor, '_process_temporary_effects'), \
             patch.object(processor, '_process_trace_increase'):

            processor.process_turn(mock_player)

            assert gsm.turn == initial_turn + 1
    
    def test_heat_management_processing(self):
        """_process_heat_management reduces player heat correctly."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.heat = 50
        mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        with patch('game_state.GameBalance') as mock_balance:
            mock_balance.HEAT_REDUCTION_NORMAL = 5
            mock_balance.HEAT_REDUCTION_BOOSTED = 10
            
            processor._process_heat_management(mock_player)
            
            assert mock_player.heat == 45
    
    def test_heat_management_with_cooling_boost(self):
        """_process_heat_management applies boost with exploit efficiency."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.heat = 60
        mock_player.temporary_effects = {'exploit_efficiency_turns': 3}  # Has efficiency boost
        
        with patch('game_state.GameBalance') as mock_balance:
            mock_balance.HEAT_REDUCTION_NORMAL = 5
            mock_balance.HEAT_REDUCTION_BOOSTED = 15
            
            processor._process_heat_management(mock_player)
            
            assert mock_player.heat == 45  # 60 - 15
    
    def test_heat_doesnt_go_negative(self):
        """Heat reduction doesn't make heat go below zero."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.heat = 3  # Low heat
        mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        with patch('game_state.GameBalance') as mock_balance:
            mock_balance.HEAT_REDUCTION_NORMAL = 5
            
            processor._process_heat_management(mock_player)
            
            assert mock_player.heat == 0  # Clamped to 0, not negative
    
    def test_temporary_effects_processing(self):
        """_process_temporary_effects decreases effect durations."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.temporary_effects = {
            'speed_boost_turns': 3,
            'data_mimic_turns': 1,
            'exploit_efficiency_turns': 5
        }
        
        processor._process_temporary_effects(mock_player)
        
        # Effects should decrease by 1
        assert mock_player.temporary_effects['speed_boost_turns'] == 2
        assert mock_player.temporary_effects['data_mimic_turns'] == 0  # Will be 0
        assert mock_player.temporary_effects['exploit_efficiency_turns'] == 4
    
    def test_trace_increase_processing(self):
        """_process_trace_increase increases trace level periodically."""
        gsm = GameStateManager()
        gsm.turn = 10  # Set to trigger trace level increase
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.trace_level = 20
        
        with patch('game_state.GameBalance') as mock_balance, \
             patch.object(gsm, 'get_current_network_config') as mock_config:
            mock_balance.TRACE_INCREASE_INTERVAL = 10
            mock_balance.TRACE_INCREASE_AMOUNT = 5
            mock_config.return_value = {'background_trace': 1}
            
            processor._process_trace_increase(mock_player)
            
            assert mock_player.trace_level == 25
    
    def test_trace_level_caps_at_100(self):
        """TraceLevel increase caps at 100%."""
        gsm = GameStateManager()
        gsm.turn = 10
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        
        mock_player = Mock()
        mock_player.trace_level = 98  # Near maximum
        
        with patch('game_state.GameBalance') as mock_balance, \
             patch.object(gsm, 'get_current_network_config') as mock_config:
            mock_balance.TRACE_INCREASE_INTERVAL = 10
            mock_balance.TRACE_INCREASE_AMOUNT = 5
            mock_config.return_value = {'background_trace': 1}
            
            processor._process_trace_increase(mock_player)
            
            assert mock_player.trace_level == 100  # Capped at 100


class TestGameLogicIntegration:
    """Test integration between core game logic components."""
    
    def test_message_log_and_state_manager_integration(self):
        """MessageLog and GameStateManager work together."""
        gsm = GameStateManager()
        message_log = MessageLog()
        
        # Simulate some game events
        gsm.advance_turn()
        message_log.add_message(f"Turn {gsm.turn}: Player moved")
        
        gsm.advance_turn()
        message_log.add_message(f"Turn {gsm.turn}: Enemy spotted")
        
        assert gsm.turn == 2
        assert len(message_log.messages) == 2
        assert "Turn 1" in message_log.messages[0].text
        assert "Turn 2" in message_log.messages[1].text
    
    def test_turn_processor_with_real_player(self):
        """TurnProcessor works with real Player object."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        player = Player(10, 10)
        player.heat = 30
        player.trace_level = 10
        
        # Process a few turns
        for _ in range(3):
            processor.process_turn(player)
        
        assert gsm.turn == 3
        # Player heat should have been processed (may or may not decrease depending on effects)
        assert player.heat <= 30
    
    def test_game_state_persistence_compatibility(self):
        """GameStateManager state can be serialized/deserialized."""
        gsm = GameStateManager()
        gsm.level = 5
        gsm.turn = 150
        gsm.admin_spawned = True
        
        # Test basic state serialization (simplified)
        state_dict = {
            'level': gsm.level,
            'turn': gsm.turn,
            'admin_spawned': gsm.admin_spawned,
            'threat_scan_turns': gsm.threat_scan_turns
        }
        
        # Create new state manager and restore
        new_gsm = GameStateManager()
        new_gsm.level = state_dict['level']
        new_gsm.turn = state_dict['turn']
        new_gsm.admin_spawned = state_dict['admin_spawned']
        new_gsm.threat_scan_turns = state_dict['threat_scan_turns']
        
        assert new_gsm.level == gsm.level
        assert new_gsm.turn == gsm.turn
        assert new_gsm.admin_spawned == gsm.admin_spawned
        assert new_gsm.threat_scan_turns == gsm.threat_scan_turns
    
    def test_effects_cleanup_over_time(self):
        """Temporary effects are cleaned up properly over multiple turns."""
        gsm = GameStateManager()
        message_log = MessageLog()
        processor = TurnProcessor(gsm, message_log)
        mock_player = Mock()
        mock_player.heat = 0  # Add heat attribute
        mock_player.trace_level = 50  # Add trace level attribute
        mock_player.cpu = 100  # Add cpu attribute for potential virus damage
        mock_player.take_damage = Mock(return_value=0)  # Mock take_damage method
        mock_player.temporary_effects = {
            'data_mimic_turns': 1,
            'speed_boost_turns': 3,
            'exploit_efficiency_turns': 5,
            'virus_turns': 0  # Add virus_turns for completeness
        }
        
        # Process several turns
        for _ in range(6):
            processor.process_turn(mock_player)
        
        # After 6 turns, all effects should be 0 or gone
        for effect in mock_player.temporary_effects.values():
            assert effect <= 0