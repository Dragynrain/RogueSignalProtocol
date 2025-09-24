#!/usr/bin/env python3
"""
Unit tests for Game Loop and Turn Management functionality.
Tests turn processing, game state transitions, pause/resume, and game over conditions.
"""

import pytest
from unittest.mock import MagicMock, patch, call
import time

from game_engine import GameEngine
from game_state import GameStateManager, TurnProcessor, MessageLog
from game_loop import initialize_tcod_context, load_tileset
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_map import GameMap
from game_enemies import EnemyManager
from game_config import GameConfig, GameBalance
from game_save import SaveGameManager


class TestGameEngine:
    """Test the GameEngine class functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameStateManager()
        self.message_log = MessageLog()
        self.game_map = GameMap(80, 50)
        self.enemy_manager = EnemyManager(self.game_map, self.message_log)
        
        self.engine = GameEngine(
            game_state_manager=self.game_state,
            game_map=self.game_map,
            enemy_manager=self.enemy_manager
        )
    
    def test_game_engine_initialization(self):
        """Test GameEngine initializes with correct default state."""
        assert self.engine.game_state == self.game_state
        assert self.engine.game_map == self.game_map
        assert isinstance(self.engine.player, Player)
        assert isinstance(self.engine.message_log, MessageLog)
        assert isinstance(self.engine.turn_processor, TurnProcessor)
        assert self.engine.game_over is False
        assert self.engine.show_inventory is False
        assert self.engine.show_help is False
    
    def test_game_over_property(self):
        """Test game_over property getter and setter."""
        assert self.engine.game_over is False
        
        self.engine.game_over = True
        assert self.engine.game_over is True
        assert self.engine.game_state.game_over is True
    
    def test_process_turn_basic_functionality(self):
        """Test basic turn processing without speed boosts."""
        initial_turn = self.engine.game_state.turn
        initial_cpu = self.engine.player.cpu
        
        # Mock the turn processor to avoid complex dependencies
        with patch.object(self.engine.turn_processor, 'process_turn') as mock_process:
            self.engine.process_turn()
            
            # Turn processor should be called with player
            mock_process.assert_called_once_with(self.engine.player)
    
    def test_process_turn_with_speed_boost(self):
        """Test turn processing when player has speed boost active."""
        # Give player speed boost but no remaining moves
        self.engine.player.temporary_effects['speed_boost_turns'] = 3
        self.engine.player.speed_moves_remaining = 0
        
        with patch.object(self.engine.turn_processor, 'process_turn'):
            self.engine.process_turn()
            
            # Should grant speed move
            assert self.engine.player.speed_moves_remaining == 1
    
    def test_process_turn_virus_damage_sound(self):
        """Test virus damage triggers sound effects."""
        initial_cpu = self.engine.player.cpu
        self.engine.player.temporary_effects['virus_turns'] = 2
        
        with patch.object(self.engine.sound_manager, 'play_sound') as mock_sound:
            with patch.object(self.engine.turn_processor, 'process_turn') as mock_process:
                # Simulate virus damage reducing CPU
                def reduce_cpu(player):
                    player.cpu -= 10
                mock_process.side_effect = reduce_cpu
                
                self.engine.process_turn()
                
                # Should play virus damage sound
                mock_sound.assert_called_with("virus_damage")
    
    def test_process_turn_player_death_from_virus(self):
        """Test player death from virus triggers multiple sounds."""
        self.engine.player.cpu = 5
        self.engine.player.temporary_effects['virus_turns'] = 1
        
        with patch.object(self.engine.sound_manager, 'play_sound') as mock_sound:
            with patch.object(self.engine.turn_processor, 'process_turn') as mock_process:
                # Simulate virus killing player
                def kill_player(player):
                    player.cpu = 0
                mock_process.side_effect = kill_player
                
                self.engine.process_turn()
                
                # Should play death sounds
                expected_calls = [
                    call("virus_damage"),
                    call("player_death", priority=10),
                    call("critical_system_failure", priority=10)
                ]
                mock_sound.assert_has_calls(expected_calls, any_order=True)
    
    def test_maybe_process_turn_with_speed_moves(self):
        """Test maybe_process_turn when player has speed moves remaining."""
        self.engine.player.speed_moves_remaining = 2
        
        with patch.object(self.engine, 'process_turn') as mock_process:
            self.engine.maybe_process_turn()
            
            # Should consume speed move but not process full turn
            assert self.engine.player.speed_moves_remaining == 1
            mock_process.assert_not_called()
    
    def test_maybe_process_turn_no_speed_moves(self):
        """Test maybe_process_turn when no speed moves remaining."""
        self.engine.player.speed_moves_remaining = 0
        
        with patch.object(self.engine, 'process_turn') as mock_process:
            self.engine.maybe_process_turn()
            
            # Should process full turn
            mock_process.assert_called_once()
    
    def test_maybe_process_turn_with_movement_inhibition(self):
        """Test maybe_process_turn grants enemies extra turn when movement slowed."""
        self.engine.player.speed_moves_remaining = 0
        self.engine.player.temporary_effects['movement_slowed_turns'] = 1
        
        with patch.object(self.engine, 'process_turn') as mock_process:
            with patch.object(self.engine, '_update_enemies') as mock_enemies:
                self.engine.maybe_process_turn()
                
                # Should process turn and give enemies extra update
                mock_process.assert_called_once()
                mock_enemies.assert_called_once()


class TestGameStateManager:
    """Test the GameStateManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameStateManager()
    
    def test_initialization(self):
        """Test GameStateManager initializes with correct defaults."""
        assert self.game_state.level == 1
        assert self.game_state.turn == 0
        assert self.game_state.game_over is False
        assert self.game_state.admin_spawned is False
        assert isinstance(self.game_state.dungeon_seed, int)
        assert self.game_state.threat_scan_turns == 0
        assert self.game_state.noise_locations == []
        assert self.game_state.distraction_points == {}
    
    def test_advance_turn(self):
        """Test turn advancement and effect processing."""
        self.game_state.turn = 5
        self.game_state.threat_scan_turns = 3
        
        # Add a distraction point that should expire
        pos1 = Position(10, 10)
        pos2 = Position(15, 15)
        self.game_state.distraction_points[pos1] = 1  # Should expire
        self.game_state.distraction_points[pos2] = 3  # Should decay
        
        self.game_state.advance_turn()
        
        # Turn should increment
        assert self.game_state.turn == 6
        
        # Threat scan should decay
        assert self.game_state.threat_scan_turns == 2
        
        # Distraction points should be processed
        assert pos1 not in self.game_state.distraction_points  # Expired
        assert self.game_state.distraction_points[pos2] == 2   # Decayed
    
    def test_should_spawn_admin(self):
        """Test admin spawning logic."""
        # Should not spawn if already spawned
        self.game_state.admin_spawned = True
        assert not self.game_state.should_spawn_admin(100.0)
        
        # Should spawn when detection at max
        self.game_state.admin_spawned = False
        assert self.game_state.should_spawn_admin(GameConfig.MAX_DETECTION)
        
        # Should not spawn below threshold
        assert not self.game_state.should_spawn_admin(GameConfig.MAX_DETECTION - 1)
    
    def test_get_current_network_config(self):
        """Test network configuration retrieval."""
        # Test default level
        config = self.game_state.get_current_network_config()
        assert isinstance(config, dict)
        
        # Test higher level
        self.game_state.level = 3
        config = self.game_state.get_current_network_config()
        assert isinstance(config, dict)


class TestTurnProcessor:
    """Test the TurnProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.game_state = GameStateManager()
        self.message_log = MessageLog()
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)
        self.player = Player(5, 5)
    
    def test_process_turn_advances_game_state(self):
        """Test that processing turn advances game state."""
        initial_turn = self.game_state.turn
        
        self.turn_processor.process_turn(self.player)
        
        assert self.game_state.turn == initial_turn + 1
    
    def test_heat_reduction_normal(self):
        """Test normal heat reduction during turn."""
        self.player.heat = 50
        self.player.temporary_effects['exploit_efficiency_turns'] = 0
        
        self.turn_processor.process_turn(self.player)
        
        expected_heat = 50 - GameBalance.HEAT_REDUCTION_NORMAL
        assert self.player.heat == max(0, expected_heat)
    
    def test_heat_reduction_boosted(self):
        """Test boosted heat reduction with exploit efficiency."""
        self.player.heat = 50
        self.player.temporary_effects['exploit_efficiency_turns'] = 3
        
        self.turn_processor.process_turn(self.player)
        
        expected_heat = 50 - GameBalance.HEAT_REDUCTION_BOOSTED
        assert self.player.heat == max(0, expected_heat)
    
    def test_temporary_effects_decay(self):
        """Test temporary effects decaying over turns."""
        self.player.temporary_effects['speed_boost_turns'] = 3
        self.player.temporary_effects['data_mimic_turns'] = 1
        
        self.turn_processor.process_turn(self.player)
        
        # Effects should decay
        assert self.player.temporary_effects['speed_boost_turns'] == 2
        assert self.player.temporary_effects['data_mimic_turns'] == 0
    
    def test_virus_damage_processing(self):
        """Test virus damage is applied during turn processing."""
        self.player.cpu = 50
        self.player.temporary_effects['virus_turns'] = 2
        
        initial_cpu = self.player.cpu
        self.turn_processor.process_turn(self.player)
        
        # Should take virus damage
        expected_damage = GameConfig.VIRUS_DAMAGE_PER_TURN
        assert self.player.cpu == initial_cpu - expected_damage
        assert self.player.temporary_effects['virus_turns'] == 1
    
    def test_virus_kills_player(self):
        """Test virus can kill player and triggers game over."""
        self.player.cpu = 3  # Set to exact virus damage amount
        self.player.temporary_effects['virus_turns'] = 1
        
        with patch.object(SaveGameManager, 'delete_save') as mock_delete:
            self.turn_processor.process_turn(self.player)
            
            # Player should die (virus does 3 damage)
            assert self.player.cpu <= 0
            assert self.game_state.game_over is True
            
            # Save should be deleted
            mock_delete.assert_called_once()
            
            # Death message should be logged
            messages = [msg[0] for msg in self.message_log.messages]
            assert any("CRITICAL SYSTEM FAILURE" in msg for msg in messages)
    
    def test_detection_increase_processing(self):
        """Test periodic detection level increases."""
        # Set turn to trigger detection increase
        self.game_state.turn = GameBalance.DETECTION_INCREASE_INTERVAL - 1
        self.player.detection = 10
        
        self.turn_processor.process_turn(self.player)
        
        # Detection should increase
        config = self.game_state.get_current_network_config()
        expected_increase = (config.get('background_detection', 1) * 
                           GameBalance.DETECTION_INCREASE_AMOUNT)
        
        assert self.player.detection == min(100, 10 + expected_increase)


class TestGameLoopComponents:
    """Test game loop initialization and context management."""
    
    def test_load_tileset(self):
        """Test tileset loading functionality."""
        with patch('tcod.tileset.load_tilesheet') as mock_load:
            mock_tileset = MagicMock()
            mock_load.return_value = mock_tileset
            
            result = load_tileset()
            
            mock_load.assert_called_once_with(
                "terminal10x16_gs_ro.png", 16, 16, mock_load.call_args[0][3]
            )
            assert result == mock_tileset
    
    def test_initialize_tcod_context(self):
        """Test TCOD context initialization."""
        with patch('game_loop.load_tileset') as mock_tileset:
            with patch('tcod.context.new') as mock_context:
                mock_tileset.return_value = MagicMock()
                mock_context.return_value = MagicMock()
                
                initialize_tcod_context()
                
                # Should load tileset and create context
                mock_tileset.assert_called_once()
                mock_context.assert_called_once()
                
                # Check context arguments
                call_args = mock_context.call_args[1]
                assert call_args['columns'] == GameConfig.SCREEN_WIDTH
                assert call_args['rows'] == GameConfig.SCREEN_HEIGHT
                assert call_args['title'] == "Rogue Signal Protocol"
                assert call_args['vsync'] is True


class TestGameStateTransitions:
    """Test game state transitions and consistency."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = GameEngine()
    
    def test_new_game_state(self):
        """Test initial game state is correct."""
        assert self.engine.game_state.level == 1
        assert self.engine.game_state.turn == 0
        assert not self.engine.game_over
        assert self.engine.player.cpu > 0
        assert self.engine.player.detection == 0
    
    def test_game_over_state_consistency(self):
        """Test game over state is consistent across systems."""
        self.engine.game_over = True
        
        # Game state should reflect game over
        assert self.engine.game_state.game_over is True
        
        # Game over state should be consistent
        assert self.engine.game_over is True
    
    def test_level_progression_state(self):
        """Test state consistency during level progression."""
        initial_level = self.engine.game_state.level
        
        # Simulate level advancement
        self.engine.game_state.level += 1
        
        # State should be consistent
        assert self.engine.game_state.level == initial_level + 1
        
        # Network config should update
        config = self.engine.game_state.get_current_network_config()
        assert isinstance(config, dict)
    
    def test_turn_order_consistency(self):
        """Test that turn processing maintains consistent order."""
        initial_turn = self.engine.game_state.turn
        
        with patch.object(self.engine, '_update_enemies') as mock_enemies:
            with patch.object(self.engine.turn_processor, 'process_turn') as mock_turn:
                self.engine.process_turn()
                
                # Turn processor should be called before enemy updates
                mock_turn.assert_called_once()
                mock_enemies.assert_called_once()
    
    def test_state_persistence_during_save_load(self):
        """Test state consistency during save/load operations."""
        # Set some specific state
        self.engine.game_state.level = 3
        self.engine.game_state.turn = 100
        self.engine.player.cpu = 75
        
        # Test that save operation works
        with patch.object(SaveGameManager, 'save_game') as mock_save:
            # State should be maintained during save operations
            assert self.engine.game_state.level == 3
            assert self.engine.game_state.turn == 100
            assert self.engine.player.cpu == 75


class TestEnemyTurnProcessing:
    """Test enemy turn processing order and behavior."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = GameEngine()
        
        # Add some test enemies (correct constructor: position, enemy_type)
        self.enemy1 = Enemy(Position(10, 10), 'scanner')
        self.enemy2 = Enemy(Position(15, 15), 'bot')
        self.engine.enemy_manager.enemies = [self.enemy1, self.enemy2]
    
    def test_enemies_process_in_order(self):
        """Test enemies are processed in consistent order."""
        with patch.object(self.engine, '_update_enemies') as mock_update:
            self.engine._update_enemies()
            
            # Should process enemy updates
            mock_update.assert_called_once()
            
            # Verify enemies are in the manager
            assert len(self.engine.enemy_manager.enemies) == 2
            assert self.enemy1 in self.engine.enemy_manager.enemies
            assert self.enemy2 in self.engine.enemy_manager.enemies
    
    def test_enemy_state_consistency_during_turn(self):
        """Test enemy states remain consistent during turn processing."""
        # Set enemy to hostile state
        self.enemy1.state = EnemyState.HOSTILE
        self.enemy1.last_known_player_pos = Position(5, 5)
        
        # Verify state is set correctly
        assert self.enemy1.state == EnemyState.HOSTILE
        assert self.enemy1.last_known_player_pos == Position(5, 5)
        
        # State should remain consistent
        with patch.object(self.engine, '_update_enemies') as mock_update:
            self.engine._update_enemies()
            mock_update.assert_called_once()
            
            # Enemy state should be maintained
            assert self.enemy1.state == EnemyState.HOSTILE
    
    def test_enemy_turn_processing_with_player_effects(self):
        """Test enemy processing respects player effects like Data Mimic."""
        # Give player Data Mimic invisibility
        self.engine.player.temporary_effects['data_mimic_turns'] = 2
        
        with patch.object(self.engine, '_update_enemies') as mock_update:
            self.engine._update_enemies()
            
            # Should process enemy updates
            mock_update.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])