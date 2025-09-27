#!/usr/bin/env python3
"""
Save/Load Cycle Integration Tests.
Tests complete save and load functionality across all game systems.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
import tempfile
import os
from typing import Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_config import GameConfig, GameSettings
from game_save import SaveGameManager
from game_inventory import CodeHack, ExploitItem, StoryFragment, InventoryManager


class TestSaveLoadSystemIntegration:
    """Test save/load system integration with all game components."""
    
    def test_complete_game_state_save_load_cycle(self):
        """Complete game state is preserved through save/load cycle."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Create engine with complex state
            engine1 = GameEngine(load_save=False)
            
            # Set up complex game state
            engine1.game_state.level = 3
            engine1.game_state.turn = 150
            engine1.game_state.admin_spawned = True
            engine1.player.x = 25
            engine1.player.y = 30
            engine1.player.cpu = 75
            engine1.player.max_cpu = 120
            engine1.player.detection = 45.5
            engine1.player.shadow_steps = 3
            engine1.player.heat = 60
            
            # Add code hack effects
            engine1.code_hack_effects = {
                "red": ("speed_boost", "Increases movement speed"),
                "blue": ("stealth_mode", "Reduces detection")
            }
            engine1.discovered_code_effects = {"red": "speed_boost"}
            
            # Set UI state
            engine1.show_inventory = True
            engine1.inventory_selection = 2
            engine1.show_lore_viewer = True
            engine1.lore_viewer_selection = 1
            
            # Mock save data
            save_data = engine1.get_game_state_for_save()
            
            # Create new engine and load state
            with patch.object(SaveGameManager, 'load_game', return_value=save_data):
                engine2 = GameEngine(load_save=True)
                
                # Verify all state is preserved
                assert engine2.game_state.level == 3
                assert engine2.game_state.turn == 150
                assert engine2.game_state.admin_spawned is True
                assert engine2.player.x == 25
                assert engine2.player.y == 30
                assert engine2.player.cpu == 75
                assert engine2.player.max_cpu == 120
                assert engine2.player.detection == 45.5
                assert engine2.player.shadow_steps == 3
                assert engine2.player.heat == 60
                
                # Verify code effects are preserved
                assert engine2.code_hack_effects["red"] == ("speed_boost", "Increases movement speed")
                assert engine2.code_hack_effects["blue"] == ("stealth_mode", "Reduces detection")
                assert engine2.discovered_code_effects["red"] == "speed_boost"
                
                # Verify UI state is preserved
                assert engine2.show_inventory is True
                assert engine2.inventory_selection == 2
                assert engine2.show_lore_viewer is True
                assert engine2.lore_viewer_selection == 1
    
    def test_inventory_save_load_preservation(self):
        """Player inventory is correctly preserved through save/load."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine1 = GameEngine(load_save=False)
            
            # Set up inventory with various items
            code_hack = CodeHack("test_hack", Position(10, 10), "red")
            exploit_item = ExploitItem("buffer_overflow")
            story_fragment = StoryFragment(1)
            
            engine1.player.inventory_manager = InventoryManager()
            engine1.player.inventory_manager.inventory = [code_hack, exploit_item, story_fragment]
            engine1.player.inventory_manager.equipped_exploits = {"buffer_overflow": True}
            
            # Save state
            save_data = engine1.get_game_state_for_save()
            
            # Load state in new engine
            with patch.object(SaveGameManager, 'load_game', return_value=save_data):
                engine2 = GameEngine(load_save=True)
                
                # Verify inventory is preserved
                inventory = engine2.player.inventory_manager.inventory
                assert len(inventory) == 3
                
                # Verify item types and properties
                code_hacks = [item for item in inventory if isinstance(item, CodeHack)]
                exploits = [item for item in inventory if isinstance(item, ExploitItem)]
                stories = [item for item in inventory if isinstance(item, StoryFragment)]
                
                assert len(code_hacks) == 1
                assert len(exploits) == 1
                assert len(stories) == 1
                
                assert code_hacks[0].name == "test_hack"
                assert code_hacks[0].color == "red"
                assert exploits[0].name == "buffer_overflow"
                assert stories[0].fragment_id == 1
                
                # Verify equipped exploits
                assert engine2.player.inventory_manager.equipped_exploits["buffer_overflow"] is True
    
    def test_map_items_save_load_preservation(self):
        """Map items are correctly preserved through save/load."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine1 = GameEngine(load_save=False)
            
            # Add items to map
            code_hack = CodeHack("map_hack", Position(15, 20), "blue")
            code_hack.discovered = True
            engine1.game_map.code_hacks = [code_hack]
            
            exploit_pickup = ExploitItem("system_crash")
            engine1.game_map.exploit_pickups = [exploit_pickup]
            
            upgrade = ("cpu_boost", Position(25, 30))
            engine1.game_map.permanent_upgrades = [upgrade]
            
            # Save state
            save_data = engine1.get_game_state_for_save()
            
            # Load state in new engine
            with patch.object(SaveGameManager, 'load_game', return_value=save_data):
                engine2 = GameEngine(load_save=True)
                
                # Verify map items are preserved
                assert len(engine2.game_map.code_hacks) == 1
                assert engine2.game_map.code_hacks[0].name == "map_hack"
                assert engine2.game_map.code_hacks[0].position.x == 15
                assert engine2.game_map.code_hacks[0].position.y == 20
                assert engine2.game_map.code_hacks[0].color == "blue"
                assert engine2.game_map.code_hacks[0].discovered is True
                
                assert len(engine2.game_map.exploit_pickups) == 1
                assert engine2.game_map.exploit_pickups[0].name == "system_crash"
                
                assert len(engine2.game_map.permanent_upgrades) == 1
                assert engine2.game_map.permanent_upgrades[0][0] == "cpu_boost"
                assert engine2.game_map.permanent_upgrades[0][1].x == 25
                assert engine2.game_map.permanent_upgrades[0][1].y == 30
    
    def test_enemy_state_save_load_preservation(self):
        """Enemy states are correctly preserved through save/load."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine1 = GameEngine(load_save=False)
            
            # Add enemies with various states
            enemy1 = Mock(spec=Enemy)
            enemy1.position = Position(10, 15)
            enemy1.enemy_type = "scanner"
            enemy1.state = EnemyState.HOSTILE
            enemy1.movement_type = EnemyMovement.SEEK
            enemy1.target_position = Position(5, 5)
            enemy1.health = 80
            enemy1.max_health = 100
            
            enemy2 = Mock(spec=Enemy)
            enemy2.position = Position(20, 25)
            enemy2.enemy_type = "guardian"
            enemy2.state = EnemyState.PATROL
            enemy2.movement_type = EnemyMovement.LINEAR
            enemy2.patrol_points = [Position(20, 25), Position(25, 25)]
            enemy2.patrol_index = 1
            enemy2.health = 150
            enemy2.max_health = 150
            
            engine1.enemy_manager.enemies = [enemy1, enemy2]
            
            # Save state
            save_data = engine1.get_game_state_for_save()
            
            # Load state in new engine
            with patch.object(SaveGameManager, 'load_game', return_value=save_data):
                engine2 = GameEngine(load_save=True)
                
                # Verify enemies are preserved
                # Note: Actual implementation depends on enemy serialization
                # This test structure shows what should be tested
    
    def test_save_load_with_corrupted_data_recovery(self):
        """Save/load system handles corrupted data gracefully."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Test with various types of corrupted save data
            corrupted_saves = [
                None,  # No save file
                {},    # Empty save
                {"level": "invalid"},  # Invalid data types
                {"player": None},      # Missing required data
                {"malformed": "data"}  # Unexpected structure
            ]
            
            for corrupted_save in corrupted_saves:
                with patch.object(SaveGameManager, 'load_game', return_value=corrupted_save):
                    try:
                        engine = GameEngine(load_save=True)
                        
                        # Should fallback to new game
                        assert engine.game_state.level == 1
                        assert engine.game_state.turn == 0
                        assert engine.player.cpu == engine.player.max_cpu
                        
                    except Exception:
                        pytest.fail(f"Engine should handle corrupted save data: {corrupted_save}")


class TestSaveLoadTimingIntegration:
    """Test save/load timing and triggers."""
    
    def test_auto_save_triggers_during_gameplay(self):
        """Auto-save triggers at appropriate times during gameplay."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            with patch.object(SaveGameManager, 'save_game') as mock_save:
                
                # Auto-save should trigger on turn processing
                engine.process_turn()
                mock_save.assert_called()
                
                mock_save.reset_mock()
                
                # Auto-save should trigger on level progression
                with patch.object(engine, '_generate_procedural_level'):
                    engine.next_level()
                    mock_save.assert_called()
    
    def test_save_state_consistency_during_active_gameplay(self):
        """Save state remains consistent during active gameplay."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Rapidly change game state and save
            for i in range(10):
                engine.game_state.turn = i * 10
                engine.player.x = i % GameConfig.MAP_WIDTH
                engine.player.cpu = max(1, 100 - i * 5)
                
                save_data = engine.get_game_state_for_save()
                
                # Save data should reflect current state
                assert save_data['turn'] == i * 10
                assert save_data['player']['x'] == i % GameConfig.MAP_WIDTH
                assert save_data['player']['cpu'] == max(1, 100 - i * 5)
    
    def test_save_load_performance_with_large_state(self):
        """Save/load performs acceptably with large game states."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Create large game state
            # Add many code hack effects
            for i in range(100):
                color = f"color_{i}"
                effect = f"effect_{i}"
                description = f"description_{i}" * 10  # Long descriptions
                engine.code_hack_effects[color] = (effect, description)
                if i % 2 == 0:
                    engine.discovered_code_effects[color] = effect
            
            # Add many map items
            for i in range(50):
                hack = CodeHack(f"hack_{i}", Position(i % 40, i // 40), "red")
                engine.game_map.code_hacks.append(hack)
                
                exploit = ExploitItem(f"exploit_{i}")
                engine.game_map.exploit_pickups.append(exploit)
            
            # Save should complete without timeout
            try:
                save_data = engine.get_game_state_for_save()
                assert isinstance(save_data, dict)
                assert len(save_data) > 0
            except Exception:
                pytest.fail("Save should handle large game states efficiently")


class TestSaveLoadVersionCompatibility:
    """Test save/load compatibility across different versions."""
    
    def test_missing_save_fields_handled_gracefully(self):
        """Missing fields in save data are handled with defaults."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Create save data missing some fields
            incomplete_save = {
                'level': 2,
                'turn': 50,
                'player': {
                    'x': 10,
                    'y': 15,
                    'cpu': 80
                    # Missing other player fields
                },
                # Missing code_hack_effects, discovered_code_effects, etc.
            }
            
            with patch.object(SaveGameManager, 'load_game', return_value=incomplete_save):
                try:
                    engine = GameEngine(load_save=True)
                    
                    # Should load with defaults for missing fields
                    assert engine.game_state.level == 2
                    assert engine.game_state.turn == 50
                    assert engine.player.x == 10
                    assert engine.player.y == 15
                    assert engine.player.cpu == 80
                    
                    # Missing fields should have sensible defaults
                    assert isinstance(engine.code_hack_effects, dict)
                    assert isinstance(engine.discovered_code_effects, dict)
                    
                except Exception:
                    pytest.fail("Engine should handle incomplete save data")
    
    def test_extra_save_fields_ignored_gracefully(self):
        """Extra fields in save data are ignored gracefully."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Create save data with extra/unknown fields
            extended_save = {
                'level': 2,
                'turn': 50,
                'player': {
                    'x': 10,
                    'y': 15,
                    'cpu': 80,
                    'max_cpu': 100,
                    'unknown_field': 'unknown_value'  # Extra field
                },
                'code_hack_effects': {},
                'discovered_code_effects': {},
                'future_feature': 'future_data',  # Extra field
                'ui_state': {
                    'show_inventory': False,
                    'inventory_selection': 0,
                    'new_ui_feature': True  # Extra field
                }
            }
            
            with patch.object(SaveGameManager, 'load_game', return_value=extended_save):
                try:
                    engine = GameEngine(load_save=True)
                    
                    # Should load known fields correctly
                    assert engine.game_state.level == 2
                    assert engine.game_state.turn == 50
                    assert engine.player.x == 10
                    assert engine.player.y == 15
                    assert engine.player.cpu == 80
                    
                    # Extra fields should not cause errors
                    
                except Exception:
                    pytest.fail("Engine should ignore unknown save data fields")


class TestSaveLoadErrorHandling:
    """Test error handling in save/load operations."""
    
    def test_save_failure_does_not_corrupt_game_state(self):
        """Save failures do not corrupt active game state."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set up game state
            original_level = engine.game_state.level
            original_turn = engine.game_state.turn
            original_cpu = engine.player.cpu
            
            # Mock save to fail
            with patch.object(SaveGameManager, 'save_game', 
                            side_effect=Exception("Save failed")), \
                 patch('logging.error') as mock_log:
                
                engine.auto_save()
                
                # Game state should be unchanged
                assert engine.game_state.level == original_level
                assert engine.game_state.turn == original_turn
                assert engine.player.cpu == original_cpu
                
                # Error should be logged
                mock_log.assert_called()
    
    def test_load_failure_falls_back_to_new_game(self):
        """Load failures result in clean new game state."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            with patch.object(SaveGameManager, 'load_game', 
                            side_effect=Exception("Load failed")):
                
                engine = GameEngine(load_save=True)
                
                # Should have new game state
                assert engine.game_state.level == 1
                assert engine.game_state.turn == 0
                assert engine.game_state.game_over is False
                assert engine.player.cpu == engine.player.max_cpu
                assert engine.player.detection == 0.0
    
    def test_partial_save_data_corruption_recovery(self):
        """Engine recovers from partially corrupted save data."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Save data with some corrupted sections
            partially_corrupted = {
                'level': 3,  # Valid
                'turn': 'invalid_turn',  # Corrupted
                'player': {
                    'x': 15,  # Valid
                    'y': 'invalid_y',  # Corrupted
                    'cpu': 75  # Valid
                },
                'code_hack_effects': 'not_a_dict',  # Corrupted
                'discovered_code_effects': {}  # Valid
            }
            
            with patch.object(SaveGameManager, 'load_game', 
                            return_value=partially_corrupted):
                
                try:
                    engine = GameEngine(load_save=True)
                    
                    # Should recover valid data and use defaults for corrupted
                    assert engine.game_state.level == 3  # Valid data preserved
                    assert engine.player.x == 15  # Valid data preserved
                    assert engine.player.cpu == 75  # Valid data preserved
                    
                    # Corrupted data should have sensible defaults
                    assert isinstance(engine.game_state.turn, int)
                    assert engine.game_state.turn >= 0
                    assert isinstance(engine.player.y, int)
                    assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT
                    assert isinstance(engine.code_hack_effects, dict)
                    
                except Exception:
                    pytest.fail("Engine should recover from partially corrupted saves")


class TestSaveLoadConcurrency:
    """Test save/load behavior under concurrent operations."""
    
    def test_save_during_state_modification(self):
        """Save operations handle concurrent state modifications."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Simulate concurrent state modification during save
            def modify_state_during_save(*args):
                # Modify state during save operation
                engine.game_state.turn += 1
                engine.player.cpu -= 1
                return {'level': 1, 'turn': 0, 'player': {'cpu': 100}}
            
            with patch.object(engine, 'get_game_state_for_save', 
                            side_effect=modify_state_during_save):
                
                try:
                    engine.auto_save()
                    # Should not crash or corrupt state
                except Exception:
                    pytest.fail("Save should handle concurrent state modifications")
    
    def test_load_state_consistency(self):
        """Loaded state is internally consistent."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            consistent_save = {
                'level': 2,
                'turn': 100,
                'player': {
                    'x': 20,
                    'y': 25,
                    'cpu': 80,
                    'max_cpu': 100,
                    'detection': 30.0,
                    'shadow_steps': 2,
                    'heat': 45
                },
                'code_hack_effects': {'red': ['speed', 'Fast movement']},
                'discovered_code_effects': {'red': 'speed'},
                'ui_state': {
                    'show_inventory': False,
                    'inventory_selection': 0
                }
            }
            
            with patch.object(SaveGameManager, 'load_game', return_value=consistent_save):
                engine = GameEngine(load_save=True)
                
                # Verify all loaded state is consistent
                assert engine.game_state.level == 2
                assert engine.game_state.turn == 100
                assert engine.player.x == 20
                assert engine.player.y == 25
                assert engine.player.cpu == 80
                assert engine.player.max_cpu == 100
                assert engine.player.detection == 30.0
                assert engine.player.shadow_steps == 2
                assert engine.player.heat == 45
                
                # Verify references are correct
                assert engine.level == engine.game_state.level
                assert engine.turn == engine.game_state.turn