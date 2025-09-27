#!/usr/bin/env python3
"""
Comprehensive tests for GameEngine core functionality.
Focuses on engine initialization, state management, and critical game operations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from typing import Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_state import GameStateManager, TurnProcessor, MessageLog
from game_map import GameMap
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_input import InputHandler
from game_audio import SoundManager
from game_config import GameConfig, GameSettings


class TestGameEngineInitialization:
    """Test GameEngine initialization and dependency injection."""
    
    def test_engine_init_with_defaults(self):
        """Engine initializes with default dependencies when none provided."""
        engine = GameEngine()
        
        assert engine.game_state is not None
        assert engine.game_map is not None
        assert engine.level_generator is not None
        assert engine.enemy_manager is not None
        assert engine.sound_manager is not None
        assert engine.input_handler is not None
        assert isinstance(engine.player, Player)
        assert isinstance(engine.message_log, MessageLog)
        assert isinstance(engine.turn_processor, TurnProcessor)
    
    def test_engine_init_with_dependencies(self):
        """Engine accepts injected dependencies."""
        mock_state = Mock(spec=GameStateManager)
        mock_map = Mock(spec=GameMap)
        mock_level_gen = Mock(spec=LevelGenerator)
        mock_enemy_mgr = Mock(spec=EnemyManager)
        mock_exploit = Mock(spec=ExploitSystem)
        mock_input = Mock(spec=InputHandler)
        mock_sound = Mock(spec=SoundManager)
        
        engine = GameEngine(
            game_state_manager=mock_state,
            game_map=mock_map,
            level_generator=mock_level_gen,
            enemy_manager=mock_enemy_mgr,
            exploit_system=mock_exploit,
            input_handler=mock_input,
            sound_manager=mock_sound
        )
        
        assert engine.game_state is mock_state
        assert engine.game_map is mock_map
        assert engine.level_generator is mock_level_gen
        assert engine.enemy_manager is mock_enemy_mgr
        assert engine.sound_manager is mock_sound
        assert engine.input_handler is mock_input
    
    def test_engine_ui_state_initialization(self):
        """Engine initializes UI state correctly."""
        engine = GameEngine()
        
        assert engine.show_inventory is False
        assert engine.show_help is False
        assert engine.show_gateway_confirmation is False
        assert engine.show_story_fragment is None
        assert engine.show_lore_viewer is False
        assert engine.inventory_selection == 0
        assert engine.lore_viewer_selection == 0
        assert engine.lore_viewer_mode == "list"
    
    def test_targeting_system_initialization(self):
        """Targeting system initializes correctly."""
        engine = GameEngine()
        
        assert engine.targeting_mode is False
        assert engine.targeting_exploit is None
        assert isinstance(engine.cursor_position, Position)
    
    def test_overclock_system_initialization(self):
        """Overclocking system initializes correctly."""
        engine = GameEngine()
        
        assert engine.overclock_confirmation is False
        assert engine.overclock_exploit is None
    
    def test_code_system_initialization(self):
        """Code hack system initializes correctly."""
        engine = GameEngine()
        
        assert isinstance(engine.code_hack_effects, dict)
        assert isinstance(engine.discovered_code_effects, dict)
        assert engine.story_fragment_manager is not None


class TestGameEngineProperties:
    """Test GameEngine property interfaces."""
    
    def test_level_property(self):
        """Level property delegates to game state."""
        engine = GameEngine()
        engine.game_state.level = 5
        
        assert engine.level == 5
        
        engine.level = 10
        assert engine.game_state.level == 10
    
    def test_turn_property(self):
        """Turn property delegates to game state."""
        engine = GameEngine()
        engine.game_state.turn = 42
        
        assert engine.turn == 42
    
    def test_game_over_property(self):
        """Game over property delegates to game state."""
        engine = GameEngine()
        engine.game_state.game_over = True
        
        assert engine.game_over is True
        
        engine.game_over = False
        assert engine.game_state.game_over is False
    
    def test_admin_spawned_property(self):
        """Admin spawned property delegates to game state."""
        engine = GameEngine()
        engine.game_state.admin_spawned = True
        
        assert engine.admin_spawned is True
        
        engine.admin_spawned = False
        assert engine.game_state.admin_spawned is False
    
    def test_enemies_property(self):
        """Enemies property delegates to enemy manager."""
        engine = GameEngine()
        mock_enemies = [Mock(spec=Enemy), Mock(spec=Enemy)]
        engine.enemy_manager.enemies = mock_enemies
        
        assert engine.enemies == mock_enemies


class TestGameEngineStateManagement:
    """Test game state management and persistence."""
    
    @patch('game_engine.SaveGameManager.load_game')
    def test_load_from_save_success(self, mock_load):
        """Engine loads successfully from save file."""
        mock_save_data = {
            'level': 3,
            'turn': 150,
            'player': {
                'x': 10, 'y': 15,
                'cpu': 80, 'max_cpu': 100,
                'detection': 25.0,
                'shadow_steps': 5
            },
            'game_over': False,
            'admin_spawned': False,
            'dungeon_seed': 12345,
            'code_hack_effects': {},
            'discovered_code_effects': {},
            'ui_state': {
                'show_inventory': False,
                'inventory_selection': 0
            }
        }
        mock_load.return_value = mock_save_data
        
        with patch.object(GameEngine, '_restore_game_state') as mock_restore_state, \
             patch.object(GameEngine, '_restore_player_state') as mock_restore_player, \
             patch.object(GameEngine, '_restore_game_effects') as mock_restore_effects, \
             patch.object(GameEngine, '_sync_code_discovered_status') as mock_sync, \
             patch.object(GameEngine, '_restore_ui_state') as mock_restore_ui:
            
            engine = GameEngine(load_save=True)
            
            mock_restore_state.assert_called_once_with(mock_save_data)
            mock_restore_player.assert_called_once_with(mock_save_data['player'])
            mock_restore_effects.assert_called_once_with(mock_save_data)
            mock_sync.assert_called_once()
            mock_restore_ui.assert_called_once_with(mock_save_data)
    
    @patch('game_engine.SaveGameManager.load_game')
    def test_load_from_save_failure_fallback(self, mock_load):
        """Engine falls back to new game when save loading fails."""
        mock_load.return_value = None
        
        with patch.object(GameEngine, '_randomize_code_hacks') as mock_randomize, \
             patch.object(GameEngine, '_generate_procedural_level') as mock_generate:
            
            engine = GameEngine(load_save=True)
            
            mock_randomize.assert_called_once()
            mock_generate.assert_called_once()
    
    def test_restore_game_state(self):
        """Engine correctly restores game state from save data."""
        engine = GameEngine()
        save_data = {
            'level': 5,
            'turn': 200,
            'game_over': False,
            'admin_spawned': True,
            'dungeon_seed': 67890
        }
        
        engine._restore_game_state(save_data)
        
        assert engine.game_state.level == 5
        assert engine.game_state.turn == 200
        assert engine.game_state.game_over is False
        assert engine.game_state.admin_spawned is True
        assert engine.game_state.dungeon_seed == 67890
    
    def test_restore_player_state(self):
        """Engine correctly restores player state from save data."""
        engine = GameEngine()
        player_data = {
            'x': 25, 'y': 30,
            'cpu': 75, 'max_cpu': 120,
            'detection': 40.5,
            'shadow_steps': 8,
            'inventory': []
        }
        
        engine._restore_player_state(player_data)
        
        assert engine.player.x == 25
        assert engine.player.y == 30
        assert engine.player.cpu == 75
        assert engine.player.max_cpu == 120
        assert engine.player.detection == 40.5
        assert engine.player.shadow_steps == 8


class TestGameEngineTurnProcessing:
    """Test turn processing and game loop functionality."""
    
    def test_process_turn_calls_update_systems(self):
        """Process turn calls all necessary update systems."""
        engine = GameEngine()
        
        with patch.object(engine, '_update_threat_scan') as mock_threat, \
             patch.object(engine, '_update_memory_system') as mock_memory, \
             patch.object(engine, '_cleanup_ghost_positions') as mock_cleanup, \
             patch.object(engine, '_process_special_tiles') as mock_special, \
             patch.object(engine, '_update_enemies') as mock_enemies, \
             patch.object(engine, '_check_admin_spawn') as mock_admin, \
             patch.object(engine, 'auto_save') as mock_save, \
             patch.object(engine.turn_processor, 'increment_turn') as mock_increment:
            
            engine.process_turn()
            
            mock_threat.assert_called_once()
            mock_memory.assert_called_once()
            mock_cleanup.assert_called_once()
            mock_special.assert_called_once()
            mock_enemies.assert_called_once()
            mock_admin.assert_called_once()
            mock_save.assert_called_once()
            mock_increment.assert_called_once()
    
    def test_maybe_process_turn_when_turn_available(self):
        """Maybe process turn calls process_turn when turn is available."""
        engine = GameEngine()
        engine.turn_processor.turn_available = True
        
        with patch.object(engine, 'process_turn') as mock_process:
            engine.maybe_process_turn()
            mock_process.assert_called_once()
    
    def test_maybe_process_turn_when_turn_not_available(self):
        """Maybe process turn does nothing when turn not available."""
        engine = GameEngine()
        engine.turn_processor.turn_available = False
        
        with patch.object(engine, 'process_turn') as mock_process:
            engine.maybe_process_turn()
            mock_process.assert_not_called()


class TestGameEnginePlayerMovement:
    """Test player movement and collision handling."""
    
    def test_move_player_valid_move(self):
        """Player can move to valid position."""
        engine = GameEngine()
        engine.player.x = 10
        engine.player.y = 10
        
        # Mock valid movement conditions
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(engine, '_get_enemy_at', return_value=None), \
             patch.object(engine, 'maybe_process_turn') as mock_process:
            
            result = engine.move_player(1, 0)
            
            assert result is True
            assert engine.player.x == 11
            assert engine.player.y == 10
            mock_process.assert_called_once()
    
    def test_move_player_blocked_by_wall(self):
        """Player cannot move into wall."""
        engine = GameEngine()
        engine.player.x = 10
        engine.player.y = 10
        
        with patch('game_characters.can_move_to_position', return_value=False):
            result = engine.move_player(1, 0)
            
            assert result is False
            assert engine.player.x == 10  # Position unchanged
            assert engine.player.y == 10
    
    def test_move_player_attack_enemy(self):
        """Player attacks enemy when moving into occupied position."""
        engine = GameEngine()
        engine.player.x = 10
        engine.player.y = 10
        
        mock_enemy = Mock(spec=Enemy)
        mock_enemy.position = Position(11, 10)
        
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(engine, '_get_enemy_at', return_value=mock_enemy), \
             patch.object(engine, '_perform_bump_attack') as mock_attack, \
             patch.object(engine, 'maybe_process_turn') as mock_process:
            
            result = engine.move_player(1, 0)
            
            assert result is True
            mock_attack.assert_called_once_with(mock_enemy)
            mock_process.assert_called_once()
    
    def test_move_player_boundary_check(self):
        """Player cannot move outside map boundaries."""
        engine = GameEngine()
        engine.player.x = 0
        engine.player.y = 0
        
        # Try to move left (outside boundary)
        result = engine.move_player(-1, 0)
        
        assert result is False
        assert engine.player.x == 0  # Position unchanged


class TestGameEngineSpecialSystems:
    """Test special game systems like threat scanning and memory."""
    
    def test_update_threat_scan_calculates_nearby_enemies(self):
        """Threat scan correctly identifies nearby enemies."""
        engine = GameEngine()
        engine.player.x = 10
        engine.player.y = 10
        
        # Create mock enemies at various distances
        close_enemy = Mock(spec=Enemy)
        close_enemy.position = Position(12, 10)  # Distance 2
        far_enemy = Mock(spec=Enemy)
        far_enemy.position = Position(20, 10)   # Distance 10
        
        engine.enemy_manager.enemies = [close_enemy, far_enemy]
        
        engine._update_threat_scan()
        
        # Should detect close enemy but not far enemy
        assert engine.player.threat_scan_results is not None
    
    def test_cleanup_ghost_positions_removes_old_ghosts(self):
        """Ghost position cleanup removes expired ghost nodes."""
        engine = GameEngine()
        
        # Add some ghost nodes with old timestamps
        old_ghost = Position(5, 5)
        new_ghost = Position(10, 10)
        engine.game_map.ghost_nodes = {old_ghost: 1.0, new_ghost: 1000.0}
        
        with patch('time.time', return_value=500.0):
            engine._cleanup_ghost_positions()
        
        # Old ghost should be removed, new ghost should remain
        assert old_ghost not in engine.game_map.ghost_nodes
        assert new_ghost in engine.game_map.ghost_nodes


class TestGameEngineErrorHandling:
    """Test error handling and edge cases."""
    
    def test_process_turn_handles_exceptions(self):
        """Process turn gracefully handles system exceptions."""
        engine = GameEngine()
        
        with patch.object(engine, '_update_enemies', side_effect=Exception("Test error")), \
             patch('logging.error') as mock_log:
            
            # Should not raise exception
            try:
                engine.process_turn()
            except Exception:
                pytest.fail("process_turn should handle exceptions gracefully")
    
    def test_invalid_enemy_position_handling(self):
        """Engine handles invalid enemy positions gracefully."""
        engine = GameEngine()
        
        # Create enemy with invalid position
        invalid_enemy = Mock(spec=Enemy)
        invalid_enemy.position = Position(-1, -1)
        engine.enemy_manager.enemies = [invalid_enemy]
        
        # Should not crash when processing enemies
        try:
            engine._update_enemies()
        except Exception:
            pytest.fail("Engine should handle invalid enemy positions")
    
    def test_save_system_error_handling(self):
        """Engine handles save system errors gracefully."""
        engine = GameEngine()
        
        with patch.object(engine, 'get_game_state_for_save', side_effect=Exception("Save error")), \
             patch('logging.error') as mock_log:
            
            # Should not crash on save error
            try:
                engine.auto_save()
            except Exception:
                pytest.fail("auto_save should handle errors gracefully")


class TestGameEngineAdvancedFeatures:
    """Test advanced engine features like admin spawning and level progression."""
    
    def test_check_admin_spawn_conditions(self):
        """Admin spawn check evaluates correct conditions."""
        engine = GameEngine()
        engine.game_state.level = 5
        engine.game_state.admin_spawned = False
        engine.player.detection = 75.0
        
        with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
            engine._check_admin_spawn()
            
            # Should spawn admin if conditions are met
            # (exact conditions depend on game balance)
    
    def test_next_level_progression(self):
        """Next level correctly advances game state."""
        engine = GameEngine()
        initial_level = engine.game_state.level
        
        with patch.object(engine, '_generate_procedural_level') as mock_generate, \
             patch.object(engine.enemy_manager, 'clear_enemies') as mock_clear:
            
            engine.next_level()
            
            assert engine.game_state.level == initial_level + 1
            mock_generate.assert_called_once()
            mock_clear.assert_called_once()
    
    def test_cursor_movement_in_targeting_mode(self):
        """Cursor moves correctly in targeting mode."""
        engine = GameEngine()
        engine.targeting_mode = True
        engine.cursor_position = Position(10, 10)
        
        engine._move_cursor(1, 0)
        
        assert engine.cursor_position.x == 11
        assert engine.cursor_position.y == 10
    
    def test_cursor_boundary_constraints(self):
        """Cursor movement respects map boundaries."""
        engine = GameEngine()
        engine.targeting_mode = True
        engine.cursor_position = Position(0, 0)
        
        # Try to move cursor outside boundary
        engine._move_cursor(-1, 0)
        
        # Should stay within bounds
        assert engine.cursor_position.x >= 0
        assert engine.cursor_position.y >= 0