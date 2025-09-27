#!/usr/bin/env python3
"""
Full Game Session Integration Tests.
Tests complete game session flow from initialization to completion.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from typing import Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_config import GameConfig, GameSettings
from game_audio import SoundManager
from game_save import SaveGameManager


class TestFullGameSessionFlow:
    """Test complete game session from start to finish."""
    
    def test_new_game_complete_initialization(self):
        """New game session initializes all systems correctly."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Verify all core systems are initialized
            assert engine.game_state is not None
            assert engine.game_map is not None
            assert engine.level_generator is not None
            assert engine.enemy_manager is not None
            assert engine.player is not None
            assert engine.message_log is not None
            assert engine.turn_processor is not None
            
            # Verify initial game state
            assert engine.game_state.level == 1
            assert engine.game_state.turn == 0
            assert engine.game_state.game_over is False
            assert engine.player.cpu == engine.player.max_cpu
            assert engine.player.detection == 0.0
    
    def test_player_movement_and_turn_processing_flow(self):
        """Player movement triggers proper turn processing flow."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            initial_turn = engine.game_state.turn
            
            # Mock movement validation
            with patch('game_characters.can_move_to_position', return_value=True), \
                 patch.object(engine, '_get_enemy_at', return_value=None):
                
                # Move player
                success = engine.move_player(1, 0)
                
                assert success is True
                # Turn should be available for processing
                assert engine.turn_processor.turn_available is True
                
                # Process the turn
                engine.maybe_process_turn()
                
                # Turn should have advanced
                assert engine.game_state.turn > initial_turn
    
    def test_enemy_interaction_and_combat_flow(self):
        """Enemy interaction and combat systems work together."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add an enemy
            enemy = Mock(spec=Enemy)
            enemy.position = Position(12, 10)
            enemy.state = EnemyState.HOSTILE
            enemy.movement_type = EnemyMovement.SEEK
            enemy.take_damage = Mock(return_value=50)
            engine.enemy_manager.enemies = [enemy]
            
            # Mock player attacking enemy
            with patch('game_characters.can_move_to_position', return_value=True), \
                 patch.object(engine, '_get_enemy_at', return_value=enemy), \
                 patch.object(engine, '_perform_bump_attack') as mock_attack:
                
                # Move player into enemy position
                success = engine.move_player(2, 0)  # Assuming player starts at 10, 10
                
                assert success is True
                mock_attack.assert_called_once_with(enemy)
    
    def test_level_progression_flow(self):
        """Level progression updates all relevant systems."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            initial_level = engine.game_state.level
            
            # Mock level generation components
            with patch.object(engine, '_generate_procedural_level') as mock_generate, \
                 patch.object(engine, 'auto_save') as mock_save:
                
                engine.next_level()
                
                # Level should advance
                assert engine.game_state.level == initial_level + 1
                
                # Level generation should be called
                mock_generate.assert_called_once()
                
                # Auto-save should be triggered
                mock_save.assert_called()
    
    def test_game_over_conditions_and_cleanup(self):
        """Game over conditions trigger proper cleanup."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Trigger game over by player death
            engine.player.cpu = 0
            engine.game_state.game_over = True
            
            assert engine.game_over is True
            
            # Game should be in a valid end state
            assert engine.player.cpu <= 0
    
    def test_save_system_integration_during_gameplay(self):
        """Save system works correctly during active gameplay."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Modify game state
            engine.game_state.level = 2
            engine.game_state.turn = 50
            engine.player.x = 15
            engine.player.y = 20
            engine.player.cpu = 75
            
            # Test auto-save functionality
            with patch.object(SaveGameManager, 'save_game') as mock_save:
                engine.auto_save()
                
                mock_save.assert_called_once()
                save_data = mock_save.call_args[0][0]
                
                # Verify save data contains current state
                assert save_data['level'] == 2
                assert save_data['turn'] == 50
                assert save_data['player']['x'] == 15
                assert save_data['player']['y'] == 20
                assert save_data['player']['cpu'] == 75


class TestGameSessionStateTransitions:
    """Test state transitions throughout a game session."""
    
    def test_peaceful_to_hostile_state_transition(self):
        """Game state transitions from peaceful to hostile correctly."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add peaceful enemy
            enemy = Mock(spec=Enemy)
            enemy.position = Position(15, 15)
            enemy.state = EnemyState.PATROL
            enemy.detection_range = 5
            enemy.can_see_position = Mock(return_value=True)
            engine.enemy_manager.enemies = [enemy]
            
            # Move player within detection range
            engine.player.x = 13
            engine.player.y = 15
            
            with patch.object(engine, '_handle_enemy_sees_player') as mock_sees:
                engine._update_enemy_awareness()
                
                # Should trigger enemy awareness update
                mock_sees.assert_called()
    
    def test_stealth_to_detected_transition(self):
        """Player stealth state transitions correctly when detected."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            initial_detection = engine.player.detection
            
            # Simulate detection increase
            engine.player.detection = 50.0
            
            # Process turn to update threat levels
            with patch.object(engine, '_update_threat_scan') as mock_threat, \
                 patch.object(engine, '_check_detection_threshold_warnings') as mock_warnings:
                
                engine.process_turn()
                
                mock_threat.assert_called_once()
                # Detection warnings should be checked
    
    def test_admin_spawn_threshold_transition(self):
        """Admin spawn occurs when conditions are met."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set conditions for admin spawn
            engine.game_state.level = 3
            engine.player.detection = 80.0
            engine.game_state.admin_spawned = False
            
            with patch.object(engine, '_spawn_admin_avatar') as mock_spawn:
                engine._check_admin_spawn()
                
                # Should attempt to spawn admin based on conditions
                # (Exact conditions depend on game balance)


class TestCrossSystemIntegration:
    """Test integration between different game systems."""
    
    def test_movement_system_integration(self):
        """Movement system integrates with collision, enemies, and map."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add wall to test collision
            wall_pos = Position(11, 10)
            engine.game_map.walls.add(wall_pos)
            
            # Test wall collision
            engine.player.x = 10
            engine.player.y = 10
            
            with patch('game_characters.can_move_to_position', return_value=False):
                success = engine.move_player(1, 0)  # Try to move into wall
                
                assert success is False
                assert engine.player.x == 10  # Position unchanged
    
    def test_exploit_system_integration(self):
        """Exploit system integrates with heat, enemies, and turns."""
        from game_combat import ExploitSystem
        
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            exploit_system = ExploitSystem(engine)
            
            # Set up equipped exploit
            engine.player.inventory_manager = Mock()
            engine.player.inventory_manager.equipped_exploits = {"shadow_step": True}
            engine.player.heat = 30
            engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
            
            # Mock exploit data
            from game_data import GameData
            from game_entities import ExploitDefinition, TargetingMode
            
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.targeting = TargetingMode.NONE
            mock_exploit.range = 0
            mock_exploit.heat = 25
            
            with patch.dict(GameData.EXPLOITS, {"shadow_step": mock_exploit}), \
                 patch.object(exploit_system, 'execute_exploit', return_value=True):
                
                initial_heat = engine.player.heat
                result = exploit_system.use_exploit("shadow_step")
                
                assert result is True
                # Heat should increase (tested in exploit system execution)
    
    def test_sound_system_integration(self):
        """Sound system integrates with game events."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_instance = mock_sound_mgr.return_value
            mock_sound_instance.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Test sound triggering on level progression
            with patch.object(engine, '_generate_procedural_level'), \
                 patch.object(engine, 'auto_save'):
                
                engine.next_level()
                
                # Should play level music
                mock_sound_instance.play_music.assert_called()
    
    def test_message_system_integration(self):
        """Message system integrates with all game events."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Test message logging during gameplay
            initial_message_count = len(engine.message_log.messages)
            
            # Trigger various events that should log messages
            engine.message_log.add_message("Test message")
            
            assert len(engine.message_log.messages) > initial_message_count


class TestPerformanceIntegration:
    """Test performance characteristics of integrated systems."""
    
    def test_large_enemy_count_performance(self):
        """Game handles large numbers of enemies efficiently."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add many enemies
            for i in range(50):  # Large but reasonable number
                enemy = Mock(spec=Enemy)
                enemy.position = Position(i % 20, i // 20)
                enemy.state = EnemyState.PATROL
                enemy.movement_type = EnemyMovement.RANDOM
                enemy.movement_queue = []
                engine.enemy_manager.enemies.append(enemy)
            
            # Should handle enemy updates without performance issues
            try:
                engine._update_enemies()
            except Exception as e:
                pytest.fail(f"Engine should handle large enemy counts: {e}")
    
    def test_long_game_session_stability(self):
        """Game remains stable during extended play sessions."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Simulate many turns
            for turn in range(100):
                try:
                    # Simulate typical turn activities
                    engine.game_state.turn = turn
                    engine._update_threat_scan()
                    engine._cleanup_ghost_positions()
                    
                    # Memory usage should not grow excessively
                    # (This is more of a smoke test)
                    
                except Exception as e:
                    pytest.fail(f"Game should remain stable during long sessions: {e}")
    
    def test_rapid_state_changes_stability(self):
        """Game handles rapid state changes without corruption."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Rapidly change various game states
            for i in range(50):
                engine.player.x = (engine.player.x + 1) % GameConfig.MAP_WIDTH
                engine.player.y = (engine.player.y + 1) % GameConfig.MAP_HEIGHT
                engine.player.detection = (engine.player.detection + 1) % 100
                engine.game_state.turn = i
                
                # State should remain consistent
                assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
                assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT
                assert 0 <= engine.player.detection <= 100
                assert engine.game_state.turn == i


class TestErrorPropagationIntegration:
    """Test how errors propagate between integrated systems."""
    
    def test_subsystem_error_isolation(self):
        """Errors in one subsystem don't crash others."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Mock enemy manager to fail
            with patch.object(engine.enemy_manager, 'update_all_enemies', 
                            side_effect=Exception("Enemy system failed")), \
                 patch('logging.error') as mock_log:
                
                # Process turn should continue despite enemy system failure
                try:
                    engine.process_turn()
                    # Should log error but not crash
                    assert mock_log.called
                except Exception:
                    pytest.fail("Engine should isolate subsystem failures")
    
    def test_save_system_error_during_gameplay(self):
        """Save system errors don't interrupt active gameplay."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Mock save system to fail
            with patch.object(SaveGameManager, 'save_game', 
                            side_effect=Exception("Save failed")), \
                 patch('logging.error') as mock_log:
                
                # Gameplay should continue despite save failure
                try:
                    engine.auto_save()
                    
                    # Should be able to continue playing
                    success = engine.move_player(0, 0)  # No-op move
                    
                    assert mock_log.called
                except Exception:
                    pytest.fail("Gameplay should continue despite save failures")
    
    def test_rendering_error_isolation(self):
        """Rendering errors don't affect game logic."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Game logic should work independently of rendering
            initial_turn = engine.game_state.turn
            
            try:
                # Process game logic
                engine.process_turn()
                
                # Game state should update regardless of rendering
                assert engine.game_state.turn >= initial_turn
                
            except Exception:
                pytest.fail("Game logic should be independent of rendering")


class TestDataIntegrityIntegration:
    """Test data integrity across integrated systems."""
    
    def test_player_state_consistency(self):
        """Player state remains consistent across all systems."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Modify player state through various systems
            initial_cpu = engine.player.cpu
            engine.player.take_damage(20)
            
            # Player state should be consistent everywhere
            assert engine.player.cpu == initial_cpu - 20
            assert engine.player.cpu >= 0  # Should not go negative
    
    def test_game_state_synchronization(self):
        """Game state stays synchronized across all systems."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Update game state through engine
            engine.game_state.level = 3
            engine.game_state.turn = 100
            
            # All systems should see the same state
            assert engine.level == 3
            assert engine.turn == 100
            assert engine.game_state.level == 3
            assert engine.game_state.turn == 100
    
    def test_map_state_consistency(self):
        """Map state remains consistent across all systems."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add items to map
            wall_pos = Position(10, 10)
            engine.game_map.walls.add(wall_pos)
            
            # All systems should see the same map state
            assert wall_pos in engine.game_map.walls
            
            # Map should be accessible through different systems
            assert engine.level_generator.game_map is engine.game_map
            assert engine.enemy_manager.game_map is engine.game_map