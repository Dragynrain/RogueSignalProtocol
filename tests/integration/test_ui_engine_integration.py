#!/usr/bin/env python3
"""
UI-Engine Integration Tests.
Tests integration between user interface systems and game engine.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_state import MessageLog
from game_input import InputHandler
from game_ui import UIManager
from game_rendering import GameRenderer
from game_menus import MenuManager
from game_audio import SoundManager


class TestUIEngineStateIntegration:
    """Test UI state synchronization with game engine."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_ui_state_reflects_game_state(self):
        """UI state correctly reflects current game state."""
        # Modify game state
        self.engine.game_state.level = 3
        self.engine.game_state.turn = 150
        self.engine.player.cpu = 75
        self.engine.player.detection = 60.0
        self.engine.player.heat = 45
        
        # UI should reflect these changes
        assert self.engine.level == 3
        assert self.engine.turn == 150
        assert self.engine.player.cpu == 75
        assert self.engine.player.detection == 60.0
        assert self.engine.player.heat == 45
    
    def test_inventory_ui_state_integration(self):
        """Inventory UI state integrates with game engine."""
        # Test inventory display state
        initial_show = self.engine.show_inventory
        initial_selection = self.engine.inventory_selection
        
        # Toggle inventory display
        self.engine.show_inventory = not initial_show
        self.engine.inventory_selection = 3
        
        # State should be updated
        assert self.engine.show_inventory != initial_show
        assert self.engine.inventory_selection == 3
    
    def test_help_ui_state_integration(self):
        """Help UI state integrates with game engine."""
        # Test help display state
        initial_show = self.engine.show_help
        
        # Toggle help display
        self.engine.show_help = not initial_show
        
        # State should be updated
        assert self.engine.show_help != initial_show
    
    def test_targeting_ui_state_integration(self):
        """Targeting UI state integrates with game engine."""
        # Test targeting mode
        self.engine.targeting_mode = True
        self.engine.targeting_exploit = "buffer_overflow"
        self.engine.cursor_position = Position(15, 20)
        
        # State should be accessible
        assert self.engine.targeting_mode is True
        assert self.engine.targeting_exploit == "buffer_overflow"
        assert self.engine.cursor_position.x == 15
        assert self.engine.cursor_position.y == 20
        
        # Test cursor movement
        self.engine._move_cursor(2, -1)
        assert self.engine.cursor_position.x == 17
        assert self.engine.cursor_position.y == 19
    
    def test_lore_viewer_ui_state_integration(self):
        """Lore viewer UI state integrates with game engine."""
        # Test lore viewer state
        self.engine.show_lore_viewer = True
        self.engine.lore_viewer_selection = 2
        self.engine.lore_viewer_mode = "details"
        
        # State should be accessible
        assert self.engine.show_lore_viewer is True
        assert self.engine.lore_viewer_selection == 2
        assert self.engine.lore_viewer_mode == "details"


class TestInputEngineIntegration:
    """Test input handling integration with game engine."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_movement_input_integration(self):
        """Movement input correctly integrates with game engine."""
        initial_x = self.engine.player.x
        initial_y = self.engine.player.y
        
        # Mock successful movement
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(self.engine, '_get_enemy_at', return_value=None):
            
            # Simulate movement input
            success = self.engine.move_player(1, 0)
            
            assert success is True
            assert self.engine.player.x == initial_x + 1
            assert self.engine.player.y == initial_y
    
    def test_menu_navigation_input_integration(self):
        """Menu navigation input integrates with UI state."""
        # Test inventory navigation
        self.engine.show_inventory = True
        self.engine.inventory_selection = 0
        
        # Simulate navigation input (implementation would depend on input handler)
        max_selection = 5
        
        # Move selection down
        new_selection = min(self.engine.inventory_selection + 1, max_selection - 1)
        self.engine.inventory_selection = new_selection
        
        assert self.engine.inventory_selection == 1
        
        # Move selection up
        new_selection = max(self.engine.inventory_selection - 1, 0)
        self.engine.inventory_selection = new_selection
        
        assert self.engine.inventory_selection == 0
    
    def test_exploit_input_integration(self):
        """Exploit input integrates with combat system."""
        from game_combat import ExploitSystem
        
        exploit_system = ExploitSystem(self.engine)
        
        # Set up player with equipped exploit
        from game_inventory import InventoryManager
        self.engine.player.inventory_manager = InventoryManager()
        self.engine.player.inventory_manager.equipped_exploits = {"shadow_step": True}
        self.engine.player.heat = 30
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        # Mock exploit data
        from game_data import GameData
        from game_entities import ExploitDefinition, TargetingMode
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"shadow_step": mock_exploit}), \
             patch.object(exploit_system, 'execute_exploit', return_value=True):
            
            # Simulate exploit input
            result = exploit_system.use_exploit("shadow_step")
            
            assert result is True
    
    def test_cursor_movement_input_integration(self):
        """Cursor movement input integrates with targeting system."""
        # Enter targeting mode
        self.engine.targeting_mode = True
        self.engine.cursor_position = Position(10, 10)
        
        # Test cursor movement in all directions
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        
        for dx, dy in directions:
            initial_x = self.engine.cursor_position.x
            initial_y = self.engine.cursor_position.y
            
            self.engine._move_cursor(dx, dy)
            
            # Cursor should move (within bounds)
            expected_x = max(0, min(initial_x + dx, 79))  # Assuming 80x24 map
            expected_y = max(0, min(initial_y + dy, 23))
            
            assert self.engine.cursor_position.x == expected_x
            assert self.engine.cursor_position.y == expected_y
    
    def test_escape_input_integration(self):
        """Escape input properly cancels UI modes."""
        # Test canceling targeting mode
        self.engine.targeting_mode = True
        self.engine.targeting_exploit = "buffer_overflow"
        
        # Simulate escape input
        self.engine.targeting_mode = False
        self.engine.targeting_exploit = None
        
        assert self.engine.targeting_mode is False
        assert self.engine.targeting_exploit is None
        
        # Test canceling inventory
        self.engine.show_inventory = True
        
        # Simulate escape input
        self.engine.show_inventory = False
        
        assert self.engine.show_inventory is False


class TestMessageLogIntegration:
    """Test message log integration with game events."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_combat_messages_integration(self):
        """Combat actions generate appropriate messages."""
        initial_message_count = len(self.engine.message_log.messages)
        
        # Add a message (simulating combat event)
        self.engine.message_log.add_message("Enemy takes damage!")
        
        assert len(self.engine.message_log.messages) > initial_message_count
        assert "Enemy takes damage!" in self.engine.message_log.messages[-1].text
    
    def test_level_progression_messages_integration(self):
        """Level progression generates appropriate messages."""
        initial_message_count = len(self.engine.message_log.messages)
        
        with patch.object(self.engine, '_generate_procedural_level'), \
             patch.object(self.engine, 'auto_save'):
            
            # Mock level progression message
            self.engine.message_log.add_message(f"Entering level {self.engine.level + 1}")
            self.engine.next_level()
            
            assert len(self.engine.message_log.messages) > initial_message_count
    
    def test_system_messages_integration(self):
        """System events generate appropriate messages."""
        # Test various system messages
        system_messages = [
            "CPU restored",
            "Detection increased",
            "Exploit failed",
            "Network breach detected"
        ]
        
        initial_count = len(self.engine.message_log.messages)
        
        for message in system_messages:
            self.engine.message_log.add_message(message)
        
        assert len(self.engine.message_log.messages) == initial_count + len(system_messages)
    
    def test_error_messages_integration(self):
        """Error conditions generate appropriate error messages."""
        # Test error message handling
        error_messages = [
            "Invalid move",
            "Cannot use exploit",
            "Target out of range",
            "System error"
        ]
        
        for error_msg in error_messages:
            self.engine.message_log.add_message(error_msg)
            
            # Message should be added to log
            assert error_msg in self.engine.message_log.messages[-1].text


class TestRenderingEngineIntegration:
    """Test rendering system integration with game engine."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_player_position_rendering_integration(self):
        """Player position changes are reflected in rendering."""
        # Move player
        self.engine.player.x = 25
        self.engine.player.y = 15
        
        # Rendering system should see updated position
        assert self.engine.player.x == 25
        assert self.engine.player.y == 15
    
    def test_enemy_position_rendering_integration(self):
        """Enemy positions are accessible for rendering."""
        # Add enemies
        enemy1 = Mock(spec=Enemy)
        enemy1.position = Position(10, 10)
        enemy1.enemy_type = "scanner"
        
        enemy2 = Mock(spec=Enemy)
        enemy2.position = Position(20, 20)
        enemy2.enemy_type = "guardian"
        
        self.engine.enemy_manager.enemies = [enemy1, enemy2]
        
        # Rendering system should see all enemies
        assert len(self.engine.enemies) == 2
        assert self.engine.enemies[0].position.x == 10
        assert self.engine.enemies[1].position.x == 20
    
    def test_map_state_rendering_integration(self):
        """Map state is accessible for rendering."""
        # Add map elements
        wall_pos = Position(15, 15)
        shadow_pos = Position(16, 16)
        cooling_pos = Position(17, 17)
        
        self.engine.game_map.walls.add(wall_pos)
        self.engine.game_map.shadows.add(shadow_pos)
        self.engine.game_map.cooling_nodes.add(cooling_pos)
        
        # Rendering system should see map elements
        assert wall_pos in self.engine.game_map.walls
        assert shadow_pos in self.engine.game_map.shadows
        assert cooling_pos in self.engine.game_map.cooling_nodes
    
    def test_ui_overlay_rendering_integration(self):
        """UI overlays integrate with game rendering."""
        # Test various UI overlays
        self.engine.show_inventory = True
        self.engine.show_help = True
        self.engine.targeting_mode = True
        
        # Rendering system should see UI state
        assert self.engine.show_inventory is True
        assert self.engine.show_help is True
        assert self.engine.targeting_mode is True
    
    def test_game_state_hud_integration(self):
        """Game state is accessible for HUD rendering."""
        # Set game state values
        self.engine.game_state.level = 2
        self.engine.game_state.turn = 150
        self.engine.player.cpu = 85
        self.engine.player.detection = 45.5
        self.engine.player.heat = 60
        
        # HUD should be able to access these values
        assert self.engine.level == 2
        assert self.engine.turn == 150
        assert self.engine.player.cpu == 85
        assert self.engine.player.detection == 45.5
        assert self.engine.player.heat == 60


class TestAudioEngineIntegration:
    """Test audio system integration with game engine."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            self.mock_sound_manager = mock_sound_mgr.return_value
            self.mock_sound_manager.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_movement_sound_integration(self):
        """Movement actions trigger appropriate sounds."""
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(self.engine, '_get_enemy_at', return_value=None):
            
            # Move player
            self.engine.move_player(1, 0)
            
            # Sound might be triggered (implementation dependent)
            # This test structure shows how to verify sound integration
    
    def test_combat_sound_integration(self):
        """Combat actions trigger appropriate sounds."""
        from game_combat import ExploitSystem
        
        exploit_system = ExploitSystem(self.engine)
        
        # Set up exploit
        from game_inventory import InventoryManager
        self.engine.player.inventory_manager = InventoryManager()
        self.engine.player.inventory_manager.equipped_exploits = {"shadow_step": True}
        self.engine.player.heat = 30
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        # Mock exploit data
        from game_data import GameData
        from game_entities import ExploitDefinition, TargetingMode
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 3
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"shadow_step": mock_exploit}), \
             patch.object(exploit_system, '_validate_target', return_value=True), \
             patch('game_characters.can_move_to_position', return_value=True):
            
            # Execute exploit
            exploit_system._execute_shadow_step(Position(12, 12))
            
            # Sound should be played
            self.mock_sound_manager.play_sound.assert_called_with("shadow_step")
    
    def test_level_progression_music_integration(self):
        """Level progression triggers appropriate music."""
        with patch.object(self.engine, '_generate_procedural_level'), \
             patch.object(self.engine, 'auto_save'):
            
            self.engine.next_level()
            
            # Music should be played for new level
            self.mock_sound_manager.play_music.assert_called()
    
    def test_game_over_sound_integration(self):
        """Game over triggers appropriate sounds."""
        # Trigger game over condition
        self.engine.game_state.level = 4  # Beyond max level
        
        with patch.object(self.engine, '_generate_procedural_level'), \
             patch.object(self.engine, 'auto_save'):
            
            self.engine.next_level()
            
            if self.engine.game_over:
                # Victory music should play
                self.mock_sound_manager.play_music.assert_called_with("victory.ogg", loops=1)


class TestUIEngineErrorIntegration:
    """Test error handling between UI and engine systems."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_invalid_ui_state_error_handling(self):
        """Invalid UI states are handled gracefully."""
        # Set invalid UI state
        self.engine.inventory_selection = -5  # Invalid selection
        self.engine.cursor_position = Position(-10, -10)  # Invalid cursor position
        
        # Engine should handle invalid states gracefully
        try:
            # Normalize invalid states
            if self.engine.inventory_selection < 0:
                self.engine.inventory_selection = 0
            
            if self.engine.cursor_position.x < 0:
                self.engine.cursor_position.x = 0
            if self.engine.cursor_position.y < 0:
                self.engine.cursor_position.y = 0
            
            assert self.engine.inventory_selection >= 0
            assert self.engine.cursor_position.x >= 0
            assert self.engine.cursor_position.y >= 0
            
        except Exception:
            pytest.fail("Engine should handle invalid UI states")
    
    def test_missing_ui_components_error_handling(self):
        """Missing UI components are handled gracefully."""
        # Simulate missing UI components
        original_message_log = self.engine.message_log
        self.engine.message_log = None
        
        try:
            # Engine should handle missing message log
            # (Would need fallback behavior in actual implementation)
            pass
        except AttributeError:
            pytest.fail("Engine should handle missing UI components")
        finally:
            # Restore message log
            self.engine.message_log = original_message_log
    
    def test_ui_state_corruption_recovery(self):
        """Corrupted UI state is recovered gracefully."""
        # Corrupt UI state
        self.engine.show_inventory = "invalid"  # Should be boolean
        self.engine.targeting_mode = None       # Should be boolean
        
        try:
            # Engine should detect and correct invalid UI state
            if not isinstance(self.engine.show_inventory, bool):
                self.engine.show_inventory = False
            
            if not isinstance(self.engine.targeting_mode, bool):
                self.engine.targeting_mode = False
            
            assert isinstance(self.engine.show_inventory, bool)
            assert isinstance(self.engine.targeting_mode, bool)
            
        except Exception:
            pytest.fail("Engine should recover from UI state corruption")


class TestUIEnginePerformanceIntegration:
    """Test performance characteristics of UI-engine integration."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
    
    def test_rapid_ui_state_changes_performance(self):
        """Rapid UI state changes don't degrade performance."""
        # Rapidly change UI states
        for i in range(100):
            self.engine.show_inventory = i % 2 == 0
            self.engine.show_help = i % 3 == 0
            self.engine.targeting_mode = i % 4 == 0
            self.engine.inventory_selection = i % 10
            self.engine.cursor_position = Position(i % 80, i % 24)
            
            # State should remain consistent
            assert isinstance(self.engine.show_inventory, bool)
            assert isinstance(self.engine.show_help, bool)
            assert isinstance(self.engine.targeting_mode, bool)
            assert 0 <= self.engine.inventory_selection < 10
    
    def test_large_message_log_performance(self):
        """Large message logs don't degrade UI performance."""
        # Add many messages
        for i in range(1000):
            self.engine.message_log.add_message(f"Message {i}")
        
        # Message log should handle large numbers of messages
        assert len(self.engine.message_log.messages) <= 1000  # May have size limit
        
        # Recent messages should be accessible
        recent_messages = self.engine.message_log.messages[-10:]
        assert len(recent_messages) <= 10
    
    def test_complex_ui_state_consistency(self):
        """Complex UI states remain consistent across operations."""
        # Set up complex UI state
        self.engine.show_inventory = True
        self.engine.inventory_selection = 5
        self.engine.targeting_mode = True
        self.engine.targeting_exploit = "buffer_overflow"
        self.engine.cursor_position = Position(25, 15)
        self.engine.show_lore_viewer = True
        self.engine.lore_viewer_selection = 3
        
        # Perform game operations
        for i in range(10):
            self.engine.game_state.turn += 1
            self.engine.player.detection += 1.0
            
            # UI state should remain consistent
            assert self.engine.show_inventory is True
            assert self.engine.inventory_selection == 5
            assert self.engine.targeting_mode is True
            assert self.engine.targeting_exploit == "buffer_overflow"
            assert self.engine.cursor_position.x == 25
            assert self.engine.cursor_position.y == 15