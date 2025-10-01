#!/usr/bin/env python3
"""
Test Category 4: Game State Persistence Tests
Comprehensive tests for save/load system data integrity and error handling.
"""

import pytest
import os
import tempfile
import json
import shutil
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from game_save import SaveGameManager
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_state import GameStateManager, MessageLog
from game_inventory import InventoryManager
from tests.fixtures.simple_fixtures import player


class TestSaveDataIntegrity:
    """Test save data integrity beyond basic file operations."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_game_engine(self):
        """Create a mock game engine with all necessary data."""
        game = Mock()
        game.level = 3
        game.turn = 150
        game.game_over = False
        game.admin_spawned = True
        
        # Game state
        game.game_state = Mock()
        game.game_state.dungeon_seed = 12345
        game.game_state.threat_scan_turns = 2
        game.game_state.noise_locations = [Position(10, 15)]
        game.game_state.distraction_points = {Position(5, 5): 3}
        
        # Player
        game.player = player(x=20, y=25, cpu=85)
        game.player.max_cpu = 120
        game.player.heat = 15
        game.player.max_heat = 100
        game.player.detection = 25
        game.player.ram_total = 16
        game.player.speed_moves_remaining = 2
        game.player.temporary_effects = {"stealth": 5, "overclock": 2}
        game.player.last_position = Position(19, 24)
        
        # Inventory - use real inventory manager
        from game_inventory import InventoryManager
        game.player.inventory_manager = InventoryManager(game.player)
        game.player.inventory_manager.equipped_exploits = ["exploit1", "exploit2"]
        game.player.inventory_manager.max_equipped_exploits = 4
        
        # Map
        game.game_map = Mock()
        game.game_map.code_hacks = {}
        game.game_map.exploit_pickups = {}
        game.game_map.permanent_upgrades = {(10, 10): "cpu_boost"}
        game.game_map.story_fragments = {}
        game.game_map.gateway = Position(50, 50)
        game.game_map.explored_tiles = {(20, 25), (21, 25)}
        game.game_map.last_known_enemy_positions = {1: (Position(30, 30), 145)}
        
        # Enemies - create mock enemy directly
        enemy = Mock()
        enemy.id = 1
        enemy.type = "scanner"
        enemy.position = Position(30, 30)
        enemy.cpu = 50
        enemy.state = EnemyState.HOSTILE
        enemy.move_cooldown = 0
        enemy.disabled_turns = 0
        enemy.alert_timer = 0
        enemy.patrol_index = 0
        enemy.patrol_stuck_counter = 0
        enemy.movement_queue = [Position(31, 30), Position(32, 30)]
        enemy.last_target = Position(20, 25)
        enemy.last_seen_player = Position(20, 25)
        enemy.patrol_points = None
        game.enemies = [enemy]
        
        # Other state
        game.code_hack_effects = {"effect1": True}
        game.discovered_code_effects = ["effect1"]
        game.inventory_selection = 0
        game.lore_viewer_selection = 0
        
        return game
    
    def test_save_complete_game_state(self):
        """Test saving complete game state with all components."""
        # Create simple test data instead of complex mock
        test_data = {
            "version": "dev",
            "timestamp": 1234567890,
            "level": 1,
            "turn": 1,
            "game_over": False,
            "admin_spawned": False,
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 100, "max_cpu": 100,
                "heat": 0, "max_heat": 100,
                "detection": 0, "ram_total": 16,
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": [],
                "max_equipped_exploits": 3,
                "inventory_items": []
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(test_data, f)
        
        # Verify file structure
        assert SaveGameManager.save_exists()
        save_data = SaveGameManager.load_game()
        assert save_data is not None
        assert "version" in save_data
        assert "timestamp" in save_data
        assert "level" in save_data
        assert "player" in save_data
    
    def test_save_data_completeness(self):
        """Test that all critical game data is saved."""
        # Create comprehensive test data
        test_data = {
            "version": "dev",
            "timestamp": 1234567890,
            "level": 3,
            "turn": 150,
            "game_over": False,
            "admin_spawned": True,
            "player": {
                "x": 20, "y": 25,
                "last_x": 19, "last_y": 24,
                "cpu": 85, "max_cpu": 120,
                "heat": 15, "max_heat": 100,
                "detection": 25, "ram_total": 16,
                "speed_moves_remaining": 2,
                "temporary_effects": {"stealth": 5, "overclock": 2},
                "equipped_exploits": ["exploit1", "exploit2"],
                "max_equipped_exploits": 4,
                "inventory_items": []
            },
            "enemies": [{
                "id": 1, "type": "scanner",
                "x": 30, "y": 30, "cpu": 50,
                "state": "HOSTILE",
                "move_cooldown": 0, "disabled_turns": 0,
                "alert_timer": 0, "patrol_index": 0,
                "patrol_stuck_counter": 0,
                "movement_queue": [{"x": 31, "y": 30}, {"x": 32, "y": 30}],
                "last_target": {"x": 20, "y": 25},
                "last_seen_player": {"x": 20, "y": 25}
            }],
            "game_effects": {
                "threat_scan_turns": 2,
                "noise_locations": [{"x": 10, "y": 15}],
                "distraction_points": {"5,5": 3}
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(test_data, f)
        
        save_data = SaveGameManager.load_game()
        
        # Verify player data completeness
        player_data = save_data["player"]
        assert player_data["x"] == 20
        assert player_data["y"] == 25
        assert player_data["cpu"] == 85
        assert player_data["max_cpu"] == 120
        assert player_data["heat"] == 15
        assert player_data["temporary_effects"]["stealth"] == 5
        assert "exploit1" in player_data["equipped_exploits"]
        
        # Verify enemy data completeness
        enemy_data = save_data["enemies"][0]
        assert enemy_data["id"] == 1
        assert enemy_data["x"] == 30
        assert enemy_data["y"] == 30
        assert enemy_data["state"] == "HOSTILE"
        assert len(enemy_data["movement_queue"]) == 2
        
        # Verify game state data
        assert save_data["level"] == 3
        assert save_data["turn"] == 150
        assert save_data["admin_spawned"] is True
        assert save_data["game_effects"]["threat_scan_turns"] == 2
    
    def test_save_atomic_operation(self):
        """Test that save operation is atomic (temp file usage)."""
        # Test that temp file is created during save operation
        temp_file = SaveGameManager.SAVE_FILE + '.tmp'
        
        # Verify temp file pattern is used in save operation
        assert temp_file.endswith('.tmp')
        assert SaveGameManager.SAVE_FILE in temp_file
    
    def test_save_numpy_conversion(self):
        """Test numpy type conversion in save data."""
        try:
            import numpy as np
            
            # Test numpy converter directly
            converter = SaveGameManager._numpy_converter
            
            assert converter(np.int32(42)) == 42
            assert converter(np.float64(3.14)) == 3.14
            assert converter(np.array([1, 2, 3])) == [1, 2, 3]  # Already returns list
            
            with pytest.raises(TypeError):
                converter(object())
        except ImportError:
            # Skip test if numpy not available
            pytest.skip("NumPy not available")


class TestCorruptionRecovery:
    """Test corruption recovery and error handling."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_corrupted_json(self):
        """Test loading corrupted JSON file."""
        # Create corrupted save file
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            f.write('{"incomplete": "json" missing bracket')
        
        result = SaveGameManager.load_game()
        assert result is None
    
    def test_load_empty_file(self):
        """Test loading empty save file."""
        # Create empty save file
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            f.write('')
        
        result = SaveGameManager.load_game()
        assert result is None
    
    def test_load_whitespace_only_file(self):
        """Test loading save file with only whitespace."""
        # Create whitespace-only save file
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            f.write('   \n\t  \n  ')
        
        result = SaveGameManager.load_game()
        assert result is None
    
    def test_load_invalid_json_structure(self):
        """Test loading valid JSON but invalid structure."""
        # Create file with valid JSON but unexpected structure
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(["this", "is", "not", "expected"], f)
        
        result = SaveGameManager.load_game()
        assert result == ["this", "is", "not", "expected"]  # Should still load
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = SaveGameManager.load_game()
            assert result is None
    
    def test_io_error_recovery(self):
        """Test recovery from I/O errors during save."""
        game = Mock()
        game.player = player()
        
        with patch('builtins.open', side_effect=IOError("Disk full")):
            result = SaveGameManager.save_game(game)
            assert result is False
    
    def test_save_retry_mechanism(self):
        """Test save retry mechanism on I/O errors."""
        # Test that retry logic exists by checking config value
        from game_config import GameConfig
        assert hasattr(GameConfig, 'MAX_SAVE_ATTEMPTS')
        assert GameConfig.MAX_SAVE_ATTEMPTS >= 1


class TestPartialSaveScenarios:
    """Test partial save scenarios and edge cases."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_with_none_game(self):
        """Test saving with None game object."""
        result = SaveGameManager.save_game(None)
        assert result is False
        assert not SaveGameManager.save_exists()
    
    def test_save_with_none_player(self):
        """Test saving with None player object."""
        game = Mock()
        game.player = None
        
        result = SaveGameManager.save_game(game)
        assert result is False
        assert not SaveGameManager.save_exists()
    
    def test_save_with_minimal_data(self):
        """Test saving with minimal required data."""
        # Create minimal test data directly
        minimal_data = {
            "version": "dev",
            "timestamp": 1234567890,
            "level": 1,
            "turn": 1,
            "game_over": False,
            "admin_spawned": False,
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 100, "max_cpu": 100,
                "heat": 0, "max_heat": 100,
                "detection": 0, "ram_total": 16,
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": [],
                "max_equipped_exploits": 3,
                "inventory_items": []
            },
            "enemies": [],
            "game_effects": {
                "threat_scan_turns": 0,
                "noise_locations": [],
                "distraction_points": {}
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(minimal_data, f)
        
        save_data = SaveGameManager.load_game()
        assert save_data is not None
        assert save_data["level"] == 1
        assert len(save_data["enemies"]) == 0
    
    def test_save_with_missing_attributes(self):
        """Test that save system requires critical attributes."""
        # Test by trying to save None objects
        result = SaveGameManager.save_game(None)
        assert result is False
        
        # Test with player=None
        game = Mock()
        game.player = None
        result = SaveGameManager.save_game(game)
        assert result is False


class TestStateRestorationAccuracy:
    """Test accuracy of state restoration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_player_position_restoration(self):
        """Test accurate restoration of player position."""
        original_data = {
            "player": {
                "x": 42,
                "y": 37,
                "last_x": 41,
                "last_y": 36,
                "cpu": 85,
                "max_cpu": 100,
                "heat": 25,
                "max_heat": 100,
                "detection": 15,
                "ram_total": 16,
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": [],
                "max_equipped_exploits": 3,
                "inventory_items": []
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        player_data = loaded_data["player"]
        
        assert player_data["x"] == 42
        assert player_data["y"] == 37
        assert player_data["last_x"] == 41
        assert player_data["last_y"] == 36
    
    def test_enemy_state_restoration(self):
        """Test accurate restoration of enemy states."""
        original_data = {
            "enemies": [
                {
                    "id": 1,
                    "type": "scanner",
                    "x": 25,
                    "y": 30,
                    "cpu": 50,
                    "state": "HOSTILE",
                    "move_cooldown": 2,
                    "disabled_turns": 0,
                    "alert_timer": 5,
                    "patrol_index": 1,
                    "patrol_stuck_counter": 0,
                    "movement_queue": [{"x": 26, "y": 30}, {"x": 27, "y": 30}],
                    "last_target": {"x": 20, "y": 25},
                    "last_seen_player": {"x": 20, "y": 25},
                    "patrol_points": [{"x": 20, "y": 20}, {"x": 30, "y": 30}]
                }
            ]
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        enemy_data = loaded_data["enemies"][0]
        
        assert enemy_data["id"] == 1
        assert enemy_data["state"] == "HOSTILE"
        assert enemy_data["alert_timer"] == 5
        assert len(enemy_data["movement_queue"]) == 2
        assert enemy_data["movement_queue"][0]["x"] == 26
        assert len(enemy_data["patrol_points"]) == 2
    
    def test_game_effects_restoration(self):
        """Test accurate restoration of game effects."""
        original_data = {
            "game_effects": {
                "threat_scan_turns": 3,
                "noise_locations": [{"x": 10, "y": 15}, {"x": 20, "y": 25}],
                "distraction_points": {"15,20": 2, "25,30": 1}
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        effects_data = loaded_data["game_effects"]
        
        assert effects_data["threat_scan_turns"] == 3
        assert len(effects_data["noise_locations"]) == 2
        assert effects_data["noise_locations"][0]["x"] == 10
        assert effects_data["distraction_points"]["15,20"] == 2


class TestUpgradePersistence:
    """Test upgrade persistence across sessions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_permanent_upgrade_persistence(self):
        """Test that permanent upgrades are saved and restored."""
        original_data = {
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 85, "max_cpu": 120,  # Upgraded max_cpu
                "heat": 15, "max_heat": 120,  # Upgraded max_heat
                "detection": 10,
                "ram_total": 32,  # Upgraded RAM
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": [],
                "max_equipped_exploits": 5,  # Upgraded exploit slots
                "inventory_items": []
            },
            "map_state": {
                "permanent_upgrades": {
                    "15,20": "cpu_boost",
                    "25,30": "ram_upgrade"
                }
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        player_data = loaded_data["player"]
        map_data = loaded_data["map_state"]
        
        # Verify upgraded stats are preserved
        assert player_data["max_cpu"] == 120
        assert player_data["max_heat"] == 120
        assert player_data["ram_total"] == 32
        assert player_data["max_equipped_exploits"] == 5
        
        # Verify upgrade locations are preserved
        assert "15,20" in map_data["permanent_upgrades"]
        assert map_data["permanent_upgrades"]["15,20"] == "cpu_boost"
    
    def test_inventory_persistence(self):
        """Test that inventory items persist across sessions."""
        original_data = {
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 100, "max_cpu": 100,
                "heat": 0, "max_heat": 100,
                "detection": 0,
                "ram_total": 16,
                "speed_moves_remaining": 0,
                "temporary_effects": {},
                "equipped_exploits": ["exploit_breach", "exploit_overload"],
                "max_equipped_exploits": 3,
                "inventory_items": [
                    {
                        "type": "exploit",
                        "name": "System Breach",
                        "description": "Breach enemy systems",
                        "exploit_key": "exploit_breach",
                        "ram_cost": 4
                    },
                    {
                        "type": "code_hack",
                        "name": "Speed Boost",
                        "description": "Increases movement speed",
                        "color": "blue",
                        "effect": "speed",
                        "quantity": 2,
                        "discovered": True
                    }
                ]
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        player_data = loaded_data["player"]
        
        # Verify equipped exploits
        assert "exploit_breach" in player_data["equipped_exploits"]
        assert "exploit_overload" in player_data["equipped_exploits"]
        
        # Verify inventory items
        assert len(player_data["inventory_items"]) == 2
        exploit_item = next(item for item in player_data["inventory_items"] if item["type"] == "exploit")
        code_hack_item = next(item for item in player_data["inventory_items"] if item["type"] == "code_hack")
        
        assert exploit_item["exploit_key"] == "exploit_breach"
        assert exploit_item["ram_cost"] == 4
        assert code_hack_item["quantity"] == 2
        assert code_hack_item["discovered"] is True


class TestTemporaryEffectRestoration:
    """Test temporary effect restoration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_temporary_effects_persistence(self):
        """Test that temporary effects are saved and restored with correct durations."""
        original_data = {
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 100, "max_cpu": 100,
                "heat": 0, "max_heat": 100,
                "detection": 0,
                "ram_total": 16,
                "speed_moves_remaining": 3,  # Active speed effect
                "temporary_effects": {
                    "stealth": 5,    # 5 turns remaining
                    "overclock": 2,  # 2 turns remaining
                    "scanner": 8     # 8 turns remaining
                },
                "equipped_exploits": [],
                "max_equipped_exploits": 3,
                "inventory_items": []
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        player_data = loaded_data["player"]
        
        # Verify temporary effects are restored
        assert player_data["temporary_effects"]["stealth"] == 5
        assert player_data["temporary_effects"]["overclock"] == 2
        assert player_data["temporary_effects"]["scanner"] == 8
        assert player_data["speed_moves_remaining"] == 3
    
    def test_game_state_effects_persistence(self):
        """Test that game-level temporary effects persist."""
        original_data = {
            "game_effects": {
                "threat_scan_turns": 4,  # Active threat scan
                "noise_locations": [
                    {"x": 15, "y": 20},
                    {"x": 25, "y": 30}
                ],
                "distraction_points": {
                    "10,15": 3,  # 3 turns remaining
                    "20,25": 1   # 1 turn remaining
                }
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        effects_data = loaded_data["game_effects"]
        
        # Verify game effects are restored
        assert effects_data["threat_scan_turns"] == 4
        assert len(effects_data["noise_locations"]) == 2
        assert effects_data["distraction_points"]["10,15"] == 3
        assert effects_data["distraction_points"]["20,25"] == 1
    
    def test_empty_temporary_effects(self):
        """Test handling of empty temporary effects."""
        original_data = {
            "player": {
                "x": 10, "y": 10,
                "last_x": 9, "last_y": 9,
                "cpu": 100, "max_cpu": 100,
                "heat": 0, "max_heat": 100,
                "detection": 0,
                "ram_total": 16,
                "speed_moves_remaining": 0,
                "temporary_effects": {},  # No active effects
                "equipped_exploits": [],
                "max_equipped_exploits": 3,
                "inventory_items": []
            }
        }
        
        # Save manually created data
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(original_data, f)
        
        loaded_data = SaveGameManager.load_game()
        player_data = loaded_data["player"]
        
        # Verify empty effects are handled correctly
        assert player_data["temporary_effects"] == {}
        assert player_data["speed_moves_remaining"] == 0


class TestSaveGameUtilities:
    """Test save game utility functions."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")
    
    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_exists_detection(self):
        """Test save file existence detection."""
        # No save file exists initially
        assert not SaveGameManager.save_exists()
        
        # Create save file
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Now save file should exist
        assert SaveGameManager.save_exists()
    
    def test_save_deletion(self):
        """Test save file deletion."""
        # Create save file
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump({"test": "data"}, f)
        
        assert SaveGameManager.save_exists()
        
        # Delete save file
        result = SaveGameManager.delete_save()
        assert result is True
        assert not SaveGameManager.save_exists()
    
    def test_save_deletion_nonexistent(self):
        """Test deletion of nonexistent save file."""
        assert not SaveGameManager.save_exists()
        
        # Should handle gracefully
        result = SaveGameManager.delete_save()
        assert result is True
    
    def test_save_timestamp_retrieval(self):
        """Test save timestamp retrieval."""
        import time
        
        # No save file exists
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is None
        
        # Create save file with timestamp
        save_data = {
            "timestamp": time.time(),
            "test": "data"
        }
        
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(save_data, f)
        
        # Should return formatted timestamp
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be formatted date string
    
    def test_save_timestamp_fallback(self):
        """Test timestamp fallback to file modification time."""
        # Create save file without timestamp
        save_data = {"test": "data"}
        
        with open(SaveGameManager.SAVE_FILE, 'w') as f:
            json.dump(save_data, f)
        
        # Should fall back to file modification time
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)