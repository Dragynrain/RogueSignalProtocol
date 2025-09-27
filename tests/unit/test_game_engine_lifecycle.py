#!/usr/bin/env python3
"""
Game Engine Lifecycle and State Management Tests.
Focuses on game initialization, state transitions, and save/load operations.
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


class TestGameEngineLifecycle:
    """Test complete game lifecycle from initialization to completion."""
    
    def test_new_game_initialization_sequence(self):
        """New game initializes in correct sequence."""
        with patch.object(GameEngine, '_randomize_code_hacks') as mock_randomize, \
             patch.object(GameEngine, '_generate_procedural_level') as mock_generate, \
             patch('game_audio.SoundManager') as mock_sound_mgr:
            
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Verify initialization sequence
            mock_randomize.assert_called_once()
            mock_generate.assert_called_once()
            assert engine.game_state.level == 1
            assert engine.game_state.turn == 0
            assert engine.game_state.game_over is False
    
    def test_randomize_code_hacks_creates_effects(self):
        """Code hack randomization creates proper effect mappings."""
        engine = GameEngine()
        
        # Clear existing effects
        engine.code_hack_effects.clear()
        engine.discovered_code_effects.clear()
        
        engine._randomize_code_hacks()
        
        # Should have created code hack effects
        assert len(engine.code_hack_effects) > 0
        # Discovered effects should initially be empty
        assert len(engine.discovered_code_effects) == 0
    
    def test_generate_procedural_level_sequence(self):
        """Procedural level generation follows correct sequence."""
        engine = GameEngine()
        
        with patch.object(engine, '_clear_map') as mock_clear, \
             patch.object(engine, '_create_border_walls') as mock_borders, \
             patch.object(engine.level_generator, 'generate_level') as mock_level_gen, \
             patch.object(engine, '_reset_player_state') as mock_reset_player, \
             patch.object(engine, '_place_code_hacks') as mock_place_hacks, \
             patch.object(engine, '_place_exploit_pickups') as mock_place_exploits, \
             patch.object(engine, '_place_story_fragment') as mock_place_story, \
             patch.object(engine, '_place_permanent_upgrades') as mock_place_upgrades, \
             patch.object(engine, '_place_enemies') as mock_place_enemies:
            
            engine._generate_procedural_level()
            
            # Verify generation sequence
            mock_clear.assert_called_once()
            mock_borders.assert_called_once()
            mock_level_gen.assert_called_once()
            mock_reset_player_state.assert_called_once()
            mock_place_hacks.assert_called_once()
            mock_place_exploits.assert_called_once()
            mock_place_story.assert_called_once()
            mock_place_upgrades.assert_called_once()
            mock_place_enemies.assert_called_once()
    
    def test_clear_map_resets_all_collections(self):
        """Map clearing resets all tile collections."""
        engine = GameEngine()
        
        # Add some items to collections
        engine.game_map.walls.add(Position(5, 5))
        engine.game_map.shadows.add(Position(6, 6))
        engine.game_map.cooling_nodes.add(Position(7, 7))
        engine.game_map.cpu_recovery_nodes.add(Position(8, 8))
        engine.game_map.ghost_nodes[Position(9, 9)] = 100.0
        engine.game_map.code_hacks.append(CodeHack("test", Position(10, 10), "red"))
        engine.game_map.exploit_pickups.append(ExploitItem("test_exploit"))
        engine.game_map.permanent_upgrades.append(("upgrade", Position(11, 11)))
        
        engine._clear_map()
        
        # All collections should be empty
        assert len(engine.game_map.walls) == 0
        assert len(engine.game_map.shadows) == 0
        assert len(engine.game_map.cooling_nodes) == 0
        assert len(engine.game_map.cpu_recovery_nodes) == 0
        assert len(engine.game_map.ghost_nodes) == 0
        assert len(engine.game_map.code_hacks) == 0
        assert len(engine.game_map.exploit_pickups) == 0
        assert len(engine.game_map.permanent_upgrades) == 0
    
    def test_create_border_walls_adds_perimeter(self):
        """Border wall creation adds walls around map perimeter."""
        engine = GameEngine()
        engine.game_map.walls.clear()
        
        engine._create_border_walls()
        
        # Should have walls on all borders
        assert len(engine.game_map.walls) > 0
        
        # Check specific border positions
        assert Position(0, 0) in engine.game_map.walls
        assert Position(GameConfig.MAP_WIDTH - 1, 0) in engine.game_map.walls
        assert Position(0, GameConfig.MAP_HEIGHT - 1) in engine.game_map.walls
        assert Position(GameConfig.MAP_WIDTH - 1, GameConfig.MAP_HEIGHT - 1) in engine.game_map.walls
    
    def test_find_valid_spawn_position_avoids_obstacles(self):
        """Spawn position finding avoids walls and obstacles."""
        engine = GameEngine()
        
        # Add walls to limit valid positions
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if x != 5 or y != 5:  # Leave one valid position
                    engine.game_map.walls.add(Position(x, y))
        
        position = engine._find_valid_spawn_position()
        
        assert position is not None
        assert position not in engine.game_map.walls
        assert 0 <= position.x < GameConfig.MAP_WIDTH
        assert 0 <= position.y < GameConfig.MAP_HEIGHT
    
    def test_reset_player_state_sets_correct_values(self):
        """Player state reset sets correct initial values."""
        engine = GameEngine()
        
        # Modify player state
        engine.player.cpu = 50
        engine.player.detection = 75.0
        engine.player.shadow_steps = 10
        
        engine._reset_player_state(20, 25)
        
        assert engine.player.x == 20
        assert engine.player.y == 25
        assert engine.player.cpu == engine.player.max_cpu
        assert engine.player.detection == 0.0
        assert engine.player.shadow_steps == 0


class TestGameEngineStateTransitions:
    """Test game state transitions and level progression."""
    
    def test_level_progression_updates_state(self):
        """Level progression correctly updates game state."""
        engine = GameEngine()
        initial_level = engine.game_state.level
        
        with patch.object(engine, '_generate_procedural_level') as mock_generate, \
             patch.object(engine.enemy_manager, 'clear_enemies') as mock_clear:
            
            engine.next_level()
            
            assert engine.game_state.level == initial_level + 1
            mock_generate.assert_called_once()
            mock_clear.assert_called_once()
    
    def test_game_over_state_transition(self):
        """Game over state transitions correctly."""
        engine = GameEngine()
        assert engine.game_state.game_over is False
        
        # Trigger game over
        engine.player.cpu = 0
        engine.game_state.game_over = True
        
        assert engine.game_over is True
    
    def test_admin_spawn_state_transition(self):
        """Admin spawn state transitions correctly."""
        engine = GameEngine()
        assert engine.game_state.admin_spawned is False
        
        with patch.object(engine, '_find_admin_spawn_position', return_value=Position(10, 10)), \
             patch.object(engine.enemy_manager, 'add_enemy') as mock_add:
            
            engine._spawn_admin_avatar()
            
            assert engine.game_state.admin_spawned is True
            mock_add.assert_called_once()
    
    def test_turn_advancement_increments_correctly(self):
        """Turn advancement increments turn counter."""
        engine = GameEngine()
        initial_turn = engine.game_state.turn
        
        engine.turn_processor.increment_turn()
        
        assert engine.game_state.turn == initial_turn + 1


class TestGameEngineSaveLoadSystem:
    """Test save and load system functionality."""
    
    def test_get_game_state_for_save_complete_data(self):
        """Game state for save includes all necessary data."""
        engine = GameEngine()
        
        # Set up some game state
        engine.game_state.level = 3
        engine.game_state.turn = 150
        engine.player.x = 20
        engine.player.y = 25
        engine.player.cpu = 80
        engine.code_hack_effects = {"red": ("effect1", "desc1")}
        engine.discovered_code_effects = {"red": "effect1"}
        
        save_data = engine.get_game_state_for_save()
        
        # Verify all critical data is included
        assert save_data['level'] == 3
        assert save_data['turn'] == 150
        assert save_data['player']['x'] == 20
        assert save_data['player']['y'] == 25
        assert save_data['player']['cpu'] == 80
        assert 'code_hack_effects' in save_data
        assert 'discovered_code_effects' in save_data
        assert 'ui_state' in save_data
    
    @patch('game_engine.SaveGameManager.save_game')
    def test_auto_save_calls_save_manager(self, mock_save):
        """Auto save calls save manager with correct data."""
        engine = GameEngine()
        
        with patch.object(engine, 'get_game_state_for_save', return_value={'test': 'data'}) as mock_get_state:
            engine.auto_save()
            
            mock_get_state.assert_called_once()
            mock_save.assert_called_once_with({'test': 'data'})
    
    def test_restore_game_effects_loads_code_systems(self):
        """Game effects restoration loads code hack systems."""
        engine = GameEngine()
        save_data = {
            'code_hack_effects': {
                'red': ['effect1', 'description1'],
                'blue': ['effect2', 'description2']
            },
            'discovered_code_effects': {
                'red': 'effect1'
            }
        }
        
        engine._restore_game_effects(save_data)
        
        assert engine.code_hack_effects['red'] == ('effect1', 'description1')
        assert engine.code_hack_effects['blue'] == ('effect2', 'description2')
        assert engine.discovered_code_effects['red'] == 'effect1'
    
    def test_restore_ui_state_loads_interface_state(self):
        """UI state restoration loads interface state."""
        engine = GameEngine()
        save_data = {
            'ui_state': {
                'show_inventory': True,
                'inventory_selection': 3,
                'show_lore_viewer': True,
                'lore_viewer_selection': 2
            }
        }
        
        engine._restore_ui_state(save_data)
        
        assert engine.show_inventory is True
        assert engine.inventory_selection == 3
        assert engine.show_lore_viewer is True
        assert engine.lore_viewer_selection == 2
    
    def test_deserialize_inventory_recreates_items(self):
        """Inventory deserialization recreates item objects correctly."""
        engine = GameEngine()
        items_data = [
            {'type': 'CodeHack', 'name': 'test_hack', 'color': 'red'},
            {'type': 'ExploitItem', 'name': 'test_exploit', 'data': 'exploit_data'},
            {'type': 'StoryFragment', 'fragment_id': 1, 'data': 'story_data'}
        ]
        
        items = engine._deserialize_inventory(items_data)
        
        assert len(items) == 3
        assert isinstance(items[0], CodeHack)
        assert isinstance(items[1], ExploitItem)
        assert isinstance(items[2], StoryFragment)
        assert items[0].name == 'test_hack'
        assert items[1].name == 'test_exploit'
    
    def test_restore_map_items_places_objects_correctly(self):
        """Map items restoration places objects in correct positions."""
        engine = GameEngine()
        map_data = {
            'code_hacks': [
                {'name': 'hack1', 'position': [10, 15], 'color': 'red', 'discovered': False}
            ],
            'exploit_pickups': [
                {'name': 'exploit1', 'data': 'test_data'}
            ],
            'permanent_upgrades': [
                ['upgrade1', [20, 25]]
            ]
        }
        
        engine._restore_map_items(map_data)
        
        assert len(engine.game_map.code_hacks) == 1
        assert engine.game_map.code_hacks[0].name == 'hack1'
        assert engine.game_map.code_hacks[0].position.x == 10
        assert engine.game_map.code_hacks[0].position.y == 15
        
        assert len(engine.game_map.exploit_pickups) == 1
        assert engine.game_map.exploit_pickups[0].name == 'exploit1'
        
        assert len(engine.game_map.permanent_upgrades) == 1
        assert engine.game_map.permanent_upgrades[0][0] == 'upgrade1'
        assert engine.game_map.permanent_upgrades[0][1].x == 20
        assert engine.game_map.permanent_upgrades[0][1].y == 25


class TestGameEngineErrorRecovery:
    """Test error recovery and graceful failure handling."""
    
    def test_invalid_save_data_fallback(self):
        """Engine handles invalid save data gracefully."""
        engine = GameEngine()
        
        # Test with malformed save data
        invalid_save_data = {'incomplete': 'data'}
        
        try:
            engine._restore_game_state(invalid_save_data)
            # Should not crash, should use defaults for missing data
        except KeyError:
            pytest.fail("Engine should handle missing save data keys gracefully")
    
    def test_corrupted_inventory_data_handling(self):
        """Engine handles corrupted inventory data gracefully."""
        engine = GameEngine()
        
        # Test with malformed inventory data
        corrupted_items = [
            {'type': 'InvalidType', 'data': 'bad_data'},
            {'type': 'CodeHack'},  # Missing required fields
            'not_a_dict'  # Wrong data type
        ]
        
        try:
            items = engine._deserialize_inventory(corrupted_items)
            # Should return empty list or skip invalid items
            assert isinstance(items, list)
        except Exception:
            pytest.fail("Engine should handle corrupted inventory data gracefully")
    
    def test_invalid_spawn_position_recovery(self):
        """Engine recovers from inability to find valid spawn positions."""
        engine = GameEngine()
        
        # Fill entire map with walls (no valid positions)
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                engine.game_map.walls.add(Position(x, y))
        
        # Should not crash, should return some fallback position
        position = engine._find_valid_spawn_position()
        
        # Even if all positions are "invalid", should return something
        assert position is not None
        assert isinstance(position, Position)
    
    def test_enemy_restoration_error_handling(self):
        """Engine handles enemy restoration errors gracefully."""
        engine = GameEngine()
        
        # Test with malformed enemy data
        corrupted_enemies = [
            {'type': 'InvalidEnemyType', 'position': [5, 5]},
            {'type': 'scanner'},  # Missing position
            'not_a_dict'  # Wrong data type
        ]
        
        try:
            engine._restore_enemies(corrupted_enemies)
            # Should not crash
        except Exception:
            pytest.fail("Engine should handle corrupted enemy data gracefully")
    
    @patch('logging.error')
    def test_save_system_error_logging(self, mock_log):
        """Save system errors are properly logged."""
        engine = GameEngine()
        
        with patch.object(engine, 'get_game_state_for_save', side_effect=Exception("Save error")):
            engine.auto_save()
            
            # Should log the error
            mock_log.assert_called()
    
    def test_level_generation_failure_recovery(self):
        """Engine recovers from level generation failures."""
        engine = GameEngine()
        
        with patch.object(engine.level_generator, 'generate_level', side_effect=Exception("Generation error")), \
             patch('logging.error') as mock_log:
            
            try:
                engine._generate_procedural_level()
                # Should not crash, should have some fallback behavior
            except Exception:
                pytest.fail("Engine should recover from level generation failures")


class TestGameEngineIntegration:
    """Test integration between different engine systems."""
    
    def test_player_movement_triggers_systems(self):
        """Player movement correctly triggers dependent systems."""
        engine = GameEngine()
        engine.player.x = 10
        engine.player.y = 10
        
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(engine, '_get_enemy_at', return_value=None), \
             patch.object(engine, '_update_threat_scan') as mock_threat, \
             patch.object(engine, '_process_special_tiles') as mock_special, \
             patch.object(engine.turn_processor, 'make_turn_available') as mock_turn:
            
            engine.move_player(1, 0)
            
            # Movement should trigger turn processing
            mock_turn.assert_called_once()
    
    def test_enemy_death_cleanup_integration(self):
        """Enemy death triggers proper cleanup across systems."""
        engine = GameEngine()
        
        # Create an enemy
        dead_enemy = Mock(spec=Enemy)
        dead_enemy.position = Position(10, 10)
        dead_enemy.state = EnemyState.DEAD
        
        engine.enemy_manager.enemies = [dead_enemy]
        
        with patch.object(engine.enemy_manager, 'remove_dead_enemies') as mock_remove, \
             patch.object(engine, '_cleanup_ghost_positions') as mock_cleanup:
            
            engine._update_enemies()
            
            # Death should trigger cleanup systems
            mock_remove.assert_called_once()
    
    def test_save_load_preserves_game_state_integrity(self):
        """Save and load preserves complete game state integrity."""
        engine = GameEngine()
        
        # Set up complex game state
        engine.game_state.level = 5
        engine.game_state.turn = 200
        engine.player.x = 25
        engine.player.y = 30
        engine.player.cpu = 75
        engine.code_hack_effects = {"red": ("test_effect", "test_desc")}
        engine.discovered_code_effects = {"red": "test_effect"}
        
        # Get save data
        save_data = engine.get_game_state_for_save()
        
        # Create new engine and restore
        new_engine = GameEngine()
        new_engine._restore_game_state(save_data)
        new_engine._restore_player_state(save_data['player'])
        new_engine._restore_game_effects(save_data)
        
        # Verify state preservation
        assert new_engine.game_state.level == 5
        assert new_engine.game_state.turn == 200
        assert new_engine.player.x == 25
        assert new_engine.player.y == 30
        assert new_engine.player.cpu == 75
        assert new_engine.code_hack_effects["red"] == ("test_effect", "test_desc")
        assert new_engine.discovered_code_effects["red"] == "test_effect"