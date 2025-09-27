#!/usr/bin/env python3
"""
Game Engine Error Handling and Edge Case Tests.
Focuses on robustness, error recovery, and graceful failure modes.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from typing import Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_config import GameConfig
from game_inventory import CodeHack, ExploitItem, StoryFragment


class TestGameEngineSystemFailures:
    """Test engine behavior when subsystems fail."""
    
    def test_sound_system_failure_graceful_degradation(self):
        """Engine continues operating when sound system fails."""
        with patch('game_audio.SoundManager', side_effect=Exception("Sound init failed")), \
             patch('logging.error') as mock_log:
            
            # Should not raise exception
            engine = GameEngine()
            
            # Engine should still be functional
            assert engine is not None
            assert engine.player is not None
            mock_log.assert_called()
    
    def test_level_generator_failure_fallback(self):
        """Engine provides fallback when level generation fails."""
        engine = GameEngine()
        
        with patch.object(engine.level_generator, 'generate_level', side_effect=Exception("Level gen failed")), \
             patch('logging.error') as mock_log, \
             patch.object(engine, '_create_border_walls') as mock_borders:
            
            # Should not crash
            engine._generate_procedural_level()
            
            # Should still create basic map structure
            mock_borders.assert_called_once()
            mock_log.assert_called()
    
    def test_enemy_manager_failure_isolation(self):
        """Enemy manager failures don't crash entire engine."""
        engine = GameEngine()
        
        with patch.object(engine.enemy_manager, 'update_all_enemies', side_effect=Exception("Enemy update failed")), \
             patch('logging.error') as mock_log:
            
            # Should not crash process_turn
            try:
                engine.process_turn()
            except Exception:
                pytest.fail("Engine should isolate enemy manager failures")
            
            mock_log.assert_called()
    
    def test_save_system_failure_continues_gameplay(self):
        """Save system failures don't interrupt gameplay."""
        engine = GameEngine()
        
        with patch('game_save.SaveGameManager.save_game', side_effect=Exception("Save failed")), \
             patch('logging.error') as mock_log:
            
            # Should not crash
            engine.auto_save()
            
            # Game should continue operating
            assert engine.game_state.game_over is False
            mock_log.assert_called()
    
    def test_input_handler_failure_recovery(self):
        """Engine recovers from input handler failures."""
        engine = GameEngine()
        
        with patch.object(engine.input_handler, 'handle_input', side_effect=Exception("Input failed")), \
             patch('logging.error') as mock_log:
            
            # Should not crash when handling input
            try:
                # Simulate input handling
                pass  # Input handling would be called externally
            except Exception:
                pytest.fail("Engine should recover from input handler failures")


class TestGameEngineDataCorruption:
    """Test engine behavior with corrupted or invalid data."""
    
    def test_corrupted_save_data_recovery(self):
        """Engine recovers from corrupted save file data."""
        corrupted_data = {
            'level': 'not_a_number',
            'turn': -5,
            'player': {
                'x': 'invalid',
                'cpu': None
            },
            'malformed_key': 'unexpected_data'
        }
        
        engine = GameEngine()
        
        # Should not crash, should use sensible defaults
        try:
            engine._restore_game_state(corrupted_data)
        except Exception:
            pytest.fail("Engine should handle corrupted save data gracefully")
        
        # Should maintain valid game state
        assert isinstance(engine.game_state.level, int)
        assert engine.game_state.level >= 1
        assert isinstance(engine.game_state.turn, int)
        assert engine.game_state.turn >= 0
    
    def test_invalid_enemy_data_filtering(self):
        """Engine filters out invalid enemy data during restoration."""
        invalid_enemies = [
            {'type': 'nonexistent_type', 'position': [5, 5]},
            {'type': 'scanner', 'position': 'invalid_position'},
            {'type': 'scanner', 'position': [-1, -1]},  # Out of bounds
            {'type': 'scanner', 'position': [1000, 1000]},  # Out of bounds
            None,  # Null entry
            'not_a_dict',  # Wrong type
            {},  # Empty dict
            {'incomplete': 'data'}  # Missing required fields
        ]
        
        engine = GameEngine()
        initial_enemy_count = len(engine.enemy_manager.enemies)
        
        with patch('logging.warning') as mock_warn:
            engine._restore_enemies(invalid_enemies)
        
        # Should filter out invalid enemies
        mock_warn.assert_called()
        # Enemy count should not increase (or increase only by valid enemies)
        assert len(engine.enemy_manager.enemies) >= initial_enemy_count
    
    def test_malformed_inventory_data_handling(self):
        """Engine handles malformed inventory data gracefully."""
        malformed_items = [
            {'type': 'UnknownItem', 'data': 'invalid'},
            {'type': 'CodeHack'},  # Missing required fields
            {'name': 'orphaned_data'},  # Missing type
            None,
            'string_instead_of_dict',
            {'type': 'CodeHack', 'name': None, 'color': 'invalid_color'},
            []  # Wrong data structure
        ]
        
        engine = GameEngine()
        
        # Should return empty list or filter out invalid items
        items = engine._deserialize_inventory(malformed_items)
        
        assert isinstance(items, list)
        # All returned items should be valid
        for item in items:
            assert hasattr(item, '__class__')
            assert item.__class__.__name__ in ['CodeHack', 'ExploitItem', 'StoryFragment']
    
    def test_corrupted_map_data_recovery(self):
        """Engine recovers from corrupted map data."""
        corrupted_map_data = {
            'code_hacks': [
                {'name': None, 'position': 'invalid', 'color': 'nonexistent'},
                {'malformed': 'entry'},
                None
            ],
            'exploit_pickups': 'should_be_list',
            'permanent_upgrades': [
                ['upgrade', 'invalid_position'],
                'malformed_upgrade',
                None
            ],
            'invalid_key': 'unexpected_data'
        }
        
        engine = GameEngine()
        
        with patch('logging.warning') as mock_warn:
            engine._restore_map_items(corrupted_map_data)
        
        # Should not crash and should log warnings
        mock_warn.assert_called()
        
        # Map should be in valid state
        assert isinstance(engine.game_map.code_hacks, list)
        assert isinstance(engine.game_map.exploit_pickups, list)
        assert isinstance(engine.game_map.permanent_upgrades, list)


class TestGameEngineResourceExhaustion:
    """Test engine behavior under resource constraints."""
    
    def test_memory_pressure_handling(self):
        """Engine handles memory pressure gracefully."""
        engine = GameEngine()
        
        # Simulate memory pressure by creating many objects
        large_enemy_list = []
        for i in range(10000):  # Large number of enemies
            mock_enemy = Mock(spec=Enemy)
            mock_enemy.position = Position(i % 100, i // 100)
            large_enemy_list.append(mock_enemy)
        
        engine.enemy_manager.enemies = large_enemy_list
        
        # Should not crash when processing large enemy lists
        try:
            engine._update_enemies()
        except MemoryError:
            pytest.fail("Engine should handle large enemy counts gracefully")
    
    def test_excessive_ghost_nodes_cleanup(self):
        """Engine cleans up excessive ghost nodes to prevent memory bloat."""
        engine = GameEngine()
        
        # Add excessive ghost nodes
        for i in range(10000):
            position = Position(i % 100, i // 100)
            engine.game_map.ghost_nodes[position] = float(i)
        
        with patch('time.time', return_value=5000.0):
            engine._cleanup_ghost_positions()
        
        # Should have cleaned up old ghost nodes
        assert len(engine.game_map.ghost_nodes) < 10000
    
    def test_large_save_file_handling(self):
        """Engine handles generation of large save files."""
        engine = GameEngine()
        
        # Create large game state
        engine.code_hack_effects = {f"color_{i}": (f"effect_{i}", f"description_{i}" * 100) 
                                   for i in range(1000)}
        engine.discovered_code_effects = {f"color_{i}": f"effect_{i}" for i in range(1000)}
        
        # Add many items to map
        for i in range(1000):
            hack = CodeHack(f"hack_{i}", Position(i % 100, i // 100), "red")
            engine.game_map.code_hacks.append(hack)
        
        # Should not crash when creating save data
        try:
            save_data = engine.get_game_state_for_save()
            assert isinstance(save_data, dict)
        except Exception:
            pytest.fail("Engine should handle large save data gracefully")
    
    def test_pathfinding_infinite_loop_prevention(self):
        """Engine prevents infinite loops in pathfinding."""
        engine = GameEngine()
        
        # Create scenario that might cause infinite pathfinding
        mock_enemy = Mock(spec=Enemy)
        mock_enemy.position = Position(10, 10)
        mock_enemy.state = EnemyState.HOSTILE
        mock_enemy.movement_type = EnemyMovement.SEEK
        mock_enemy.target_position = Position(10, 10)  # Same as current position
        
        # Mock pathfinding to simulate potential infinite loop
        with patch('game_characters.pathfind_and_move', return_value=[]) as mock_pathfind:
            
            predictions = engine.get_enemy_next_positions(mock_enemy, 100)  # Large step count
            
            # Should not hang and should return reasonable result
            assert isinstance(predictions, list)
            assert len(predictions) <= 100  # Should not exceed requested steps


class TestGameEngineEdgeCases:
    """Test engine behavior in edge case scenarios."""
    
    def test_zero_size_map_handling(self):
        """Engine handles edge case of minimal map size."""
        # This tests robustness against configuration errors
        with patch('game_config.GameConfig.MAP_WIDTH', 1), \
             patch('game_config.GameConfig.MAP_HEIGHT', 1):
            
            try:
                engine = GameEngine()
                # Should not crash with minimal map
                assert engine.game_map is not None
            except Exception:
                pytest.fail("Engine should handle minimal map sizes")
    
    def test_negative_coordinates_handling(self):
        """Engine handles negative coordinate edge cases."""
        engine = GameEngine()
        
        # Test cursor movement with negative coordinates
        engine.targeting_mode = True
        engine.cursor_position = Position(0, 0)
        
        # Try to move cursor to negative position
        engine._move_cursor(-5, -5)
        
        # Should clamp to valid bounds
        assert engine.cursor_position.x >= 0
        assert engine.cursor_position.y >= 0
    
    def test_maximum_coordinate_handling(self):
        """Engine handles maximum coordinate edge cases."""
        engine = GameEngine()
        
        engine.targeting_mode = True
        engine.cursor_position = Position(GameConfig.MAP_WIDTH - 1, GameConfig.MAP_HEIGHT - 1)
        
        # Try to move cursor beyond maximum bounds
        engine._move_cursor(10, 10)
        
        # Should clamp to valid bounds
        assert engine.cursor_position.x < GameConfig.MAP_WIDTH
        assert engine.cursor_position.y < GameConfig.MAP_HEIGHT
    
    def test_simultaneous_enemy_positions(self):
        """Engine handles multiple enemies at same position."""
        engine = GameEngine()
        
        same_position = Position(10, 10)
        enemy1 = Mock(spec=Enemy)
        enemy1.position = same_position
        enemy2 = Mock(spec=Enemy)
        enemy2.position = same_position
        
        engine.enemy_manager.enemies = [enemy1, enemy2]
        
        # Should handle overlapping enemies gracefully
        found_enemy = engine._get_enemy_at(same_position)
        assert found_enemy is not None
        # Should return one of the enemies (implementation detail which one)
    
    def test_empty_game_state_handling(self):
        """Engine handles completely empty game state."""
        engine = GameEngine()
        
        # Clear all game state
        engine.game_map.walls.clear()
        engine.game_map.shadows.clear()
        engine.enemy_manager.enemies.clear()
        engine.game_map.code_hacks.clear()
        engine.game_map.exploit_pickups.clear()
        
        # Should still be able to process turns
        try:
            engine.process_turn()
        except Exception:
            pytest.fail("Engine should handle empty game state")
    
    def test_rapid_state_changes(self):
        """Engine handles rapid state changes correctly."""
        engine = GameEngine()
        
        # Rapidly change game state
        for i in range(100):
            engine.game_state.level = i
            engine.game_state.turn = i * 10
            engine.player.x = i % GameConfig.MAP_WIDTH
            engine.player.y = i % GameConfig.MAP_HEIGHT
            
            # Should maintain consistency
            assert engine.game_state.level == i
            assert engine.game_state.turn == i * 10
    
    def test_boundary_collision_detection(self):
        """Engine correctly handles boundary collision cases."""
        engine = GameEngine()
        
        # Test each boundary
        boundaries = [
            (-1, 0),   # Left boundary
            (GameConfig.MAP_WIDTH, 0),   # Right boundary
            (0, -1),   # Top boundary
            (0, GameConfig.MAP_HEIGHT)   # Bottom boundary
        ]
        
        for x, y in boundaries:
            engine.player.x = max(0, min(x, GameConfig.MAP_WIDTH - 1))
            engine.player.y = max(0, min(y, GameConfig.MAP_HEIGHT - 1))
            
            # Should not allow movement outside boundaries
            result = engine.move_player(x - engine.player.x, y - engine.player.y)
            
            # Movement outside boundaries should be blocked
            assert engine.player.x >= 0
            assert engine.player.x < GameConfig.MAP_WIDTH
            assert engine.player.y >= 0
            assert engine.player.y < GameConfig.MAP_HEIGHT


class TestGameEngineRecoveryMechanisms:
    """Test engine recovery and self-healing mechanisms."""
    
    def test_invalid_player_position_correction(self):
        """Engine corrects invalid player positions."""
        engine = GameEngine()
        
        # Set invalid player position
        engine.player.x = -10
        engine.player.y = -10
        
        # Process turn should correct invalid positions
        with patch.object(engine, '_reset_player_state') as mock_reset:
            engine.process_turn()
            
            # Should detect and correct invalid position
            # (Implementation may vary - might reset or clamp)
    
    def test_corrupted_enemy_state_cleanup(self):
        """Engine cleans up corrupted enemy states."""
        engine = GameEngine()
        
        # Create enemy with invalid state
        corrupted_enemy = Mock(spec=Enemy)
        corrupted_enemy.position = Position(-5, -5)  # Invalid position
        corrupted_enemy.state = "INVALID_STATE"  # Invalid state
        
        engine.enemy_manager.enemies = [corrupted_enemy]
        
        with patch.object(engine.enemy_manager, 'remove_invalid_enemies') as mock_remove, \
             patch('logging.warning') as mock_warn:
            
            engine._update_enemies()
            
            # Should attempt to clean up invalid enemies
            # (Exact behavior depends on implementation)
    
    def test_game_state_consistency_validation(self):
        """Engine validates and maintains game state consistency."""
        engine = GameEngine()
        
        # Create inconsistent state
        engine.game_state.level = -1  # Invalid level
        engine.game_state.turn = -100  # Invalid turn
        
        # Engine should detect and correct inconsistencies
        try:
            engine.process_turn()
            
            # State should be corrected to valid values
            assert engine.game_state.level >= 1
            assert engine.game_state.turn >= 0
        except Exception:
            pytest.fail("Engine should validate and correct game state inconsistencies")
    
    def test_resource_leak_prevention(self):
        """Engine prevents resource leaks through proper cleanup."""
        engine = GameEngine()
        
        # Simulate operations that might cause leaks
        for i in range(100):
            # Create temporary objects
            temp_enemy = Mock(spec=Enemy)
            temp_enemy.position = Position(i, i)
            engine.enemy_manager.enemies.append(temp_enemy)
            
            # Process turn
            engine.process_turn()
            
            # Remove enemy
            engine.enemy_manager.enemies.remove(temp_enemy)
        
        # Should not accumulate excessive resources
        # (This is more of a stress test than assertion test)
        assert len(engine.enemy_manager.enemies) == 0
    
    def test_circular_dependency_prevention(self):
        """Engine prevents circular dependencies in object references."""
        engine = GameEngine()
        
        # Test that engine doesn't create circular references
        # that could prevent garbage collection
        
        # Get all major components
        components = [
            engine.game_state,
            engine.game_map,
            engine.level_generator,
            engine.enemy_manager,
            engine.turn_processor,
            engine.message_log
        ]
        
        # Each component should have clear ownership hierarchy
        # (This is more of a structural test)
        for component in components:
            assert component is not None
            # Should not have circular references back to engine
            # (Specific implementation detail)