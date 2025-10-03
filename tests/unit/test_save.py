#!/usr/bin/env python3
"""
Unit tests for Save/Load functionality testing real save system.
Tests the actual SaveGameManager class and game state persistence.
"""

import pytest
import os
import tempfile
import json
import time
from unittest.mock import Mock, patch, MagicMock

from game_save import SaveGameManager
from game_characters import Player, Enemy
from game_entities import Position


class TestSaveGameManager:
    """Test the SaveGameManager class functionality."""
    
    def test_save_exists_when_file_present(self):
        """save_exists returns True when save file exists."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = SaveGameManager.save_exists()
            
            assert result is True
            mock_exists.assert_called_once_with(SaveGameManager.SAVE_FILE)
    
    def test_save_exists_when_file_missing(self):
        """save_exists returns False when save file doesn't exist."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = SaveGameManager.save_exists()
            
            assert result is False
            mock_exists.assert_called_once_with(SaveGameManager.SAVE_FILE)
    
    def test_numpy_converter_integer(self):
        """_numpy_converter handles numpy integers."""
        import numpy as np
        
        numpy_int = np.int32(42)
        result = SaveGameManager._numpy_converter(numpy_int)
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_numpy_converter_float(self):
        """_numpy_converter handles numpy floats."""
        import numpy as np
        
        numpy_float = np.float64(3.14)
        result = SaveGameManager._numpy_converter(numpy_float)
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_numpy_converter_array(self):
        """_numpy_converter handles numpy arrays."""
        import numpy as np
        
        numpy_array = np.array([1, 2, 3])
        result = SaveGameManager._numpy_converter(numpy_array)
        
        assert result == [1, 2, 3]
        assert isinstance(result, list)
    
    def test_numpy_converter_unsupported_type(self):
        """_numpy_converter raises TypeError for unsupported types."""
        with pytest.raises(TypeError, match="is not JSON serializable"):
            SaveGameManager._numpy_converter({"unsupported": "dict"})
    
    def test_save_game_none_game_object(self):
        """save_game returns False when game object is None."""
        with patch('logging.error') as mock_log:
            result = SaveGameManager.save_game(None)
            
            assert result is False
            mock_log.assert_called_with("Cannot save: game object is None")
    
    def test_save_game_none_player_object(self):
        """save_game returns False when player object is None."""
        mock_game = Mock()
        mock_game.player = None
        
        with patch('logging.error') as mock_log:
            result = SaveGameManager.save_game(mock_game)
            
            assert result is False
            mock_log.assert_called_with("Cannot save: player object is None")
    
    def test_save_game_success(self):
        """save_game successfully saves complete game state."""
        # Create comprehensive mock game object
        mock_game = Mock()
        mock_game.level = 5
        mock_game.turn = 100
        mock_game.game_over = False
        mock_game.admin_spawned = True
        
        # Mock player
        mock_player = Mock()
        mock_player.x = 10
        mock_player.y = 15
        mock_player.last_position = Position(8, 12)
        mock_player.cpu = 75
        mock_player.max_cpu = 100
        mock_player.heat = 25
        mock_player.max_heat = 100
        mock_player.detection = 5
        mock_player.ram_total = 16
        mock_player.speed_moves_remaining = 2
        mock_player.temporary_effects = {'data_mimic_turns': 3}
        
        # Mock inventory manager
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {'buffer_overflow': True}
        mock_inventory.max_equipped_exploits = 8
        mock_inventory.items = []
        mock_player.inventory_manager = mock_inventory
        
        mock_game.player = mock_player
        
        # Mock game state and map
        mock_game_state = Mock()
        mock_game_state.dungeon_seed = 12345
        mock_game_state.threat_scan_turns = 0
        mock_game_state.noise_locations = []
        mock_game_state.distraction_points = {}
        mock_game.game_state = mock_game_state
        
        mock_map = Mock()
        mock_map.code_hacks = {}
        mock_map.exploit_pickups = {}
        mock_map.permanent_upgrades = {}
        mock_map.story_fragments = {}
        mock_map.gateway = Position(50, 50)
        mock_map.explored_tiles = {(5, 5), (6, 6)}
        mock_map.last_known_enemy_positions = {}
        mock_game.game_map = mock_map
        
        # Mock enemies (save method expects game.enemies directly)
        mock_game.enemies = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []
        
        # Mock additional attributes that save might access
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        
        # Mock UI state attributes that save expects
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        
        # Mock overclocking state attributes
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        
        with patch('builtins.open', create=True) as mock_open, \
             patch('shutil.move') as mock_move, \
             patch('os.path.exists') as mock_exists:
            
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_exists.return_value = False  # No temp file cleanup needed
            
            result = SaveGameManager.save_game(mock_game)
            
            assert result is True
            # Should open temp file first, then move to final location
            temp_file_name = SaveGameManager.SAVE_FILE + '.tmp'
            mock_open.assert_called_once_with(temp_file_name, 'w', encoding='utf-8')
            # json.dump() calls write() many times, just check it was called
            assert mock_file.write.call_count > 0
            mock_move.assert_called_once_with(temp_file_name, SaveGameManager.SAVE_FILE)
    
    def test_load_game_missing_file(self):
        """load_game returns None when save file doesn't exist."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = SaveGameManager.load_game()
            
            assert result is None
    
    def test_load_game_corrupted_file(self):
        """load_game handles corrupted JSON files."""
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_exists.return_value = True
            mock_file = Mock()
            mock_file.read.return_value = "invalid json content {"
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('logging.error') as mock_log:
                result = SaveGameManager.load_game()
                
                assert result is None
                mock_log.assert_called()
    
    def test_load_game_success(self):
        """load_game successfully loads valid save data."""
        test_save_data = {
            "version": "0.8.0 Alpha",
            "timestamp": time.time(),
            "level": 3,
            "turn": 50,
            "player": {
                "x": 20,
                "y": 25,
                "cpu": 80
            }
        }
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_exists.return_value = True
            mock_file = Mock()
            mock_file.read.return_value = json.dumps(test_save_data)
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = SaveGameManager.load_game()
            
            assert result is not None
            assert result["level"] == 3
            assert result["turn"] == 50
            assert result["player"]["x"] == 20
    
    def test_delete_save_success(self):
        """delete_save successfully removes save file."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            
            mock_exists.return_value = True
            
            result = SaveGameManager.delete_save()
            
            assert result is True
            mock_remove.assert_called_once_with(SaveGameManager.SAVE_FILE)
    
    def test_delete_save_file_not_found(self):
        """delete_save handles missing save file gracefully."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = SaveGameManager.delete_save()
            
            assert result is True  # Returns True even if file doesn't exist (no-op success)
    
    def test_delete_save_permission_error(self):
        """delete_save handles permission errors."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.remove') as mock_remove:
            
            mock_exists.return_value = True
            mock_remove.side_effect = PermissionError("Access denied")
            
            with patch('logging.error') as mock_log:
                result = SaveGameManager.delete_save()
                
                assert result is False
                mock_log.assert_called()
    
    def test_get_save_timestamp_exists(self):
        """get_save_timestamp returns formatted timestamp when file exists."""
        test_timestamp = time.time()
        test_save_data = {
            "timestamp": test_timestamp,
            "player": {"x": 10, "y": 10}
        }
        
        with patch('os.path.exists') as mock_exists, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_exists.return_value = True
            mock_file = Mock()
            mock_file.read.return_value = json.dumps(test_save_data)
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = SaveGameManager.get_save_timestamp()
            
            assert result is not None
            assert isinstance(result, str)
            # Should contain formatted date/time
            assert len(result) > 0
    
    def test_get_save_timestamp_missing_file(self):
        """get_save_timestamp returns None when save file doesn't exist."""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = SaveGameManager.get_save_timestamp()
            
            assert result is None


class TestSaveDataSerialization:
    """Test serialization of various game data types."""
    
    def test_serialize_inventory_empty(self):
        """_serialize_inventory handles empty inventory."""
        result = SaveGameManager._serialize_inventory([])
        
        assert result == []
    
    def test_serialize_code_hacks_empty(self):
        """_serialize_code_hacks handles empty code hacks."""
        result = SaveGameManager._serialize_code_hacks({})
        
        assert result == {}
    
    def test_serialize_exploit_pickups_empty(self):
        """_serialize_exploit_pickups handles empty exploit pickups."""
        result = SaveGameManager._serialize_exploit_pickups({})
        
        assert result == {}
    
    def test_serialize_enemies_empty(self):
        """_serialize_enemies handles empty enemy list."""
        result = SaveGameManager._serialize_enemies([])
        
        assert result == []
    
    def test_serialize_enemies_with_data(self):
        """_serialize_enemies correctly serializes enemy data."""
        with patch('game_data.GameData') as mock_game_data:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 50
            mock_game_data.ENEMY_TYPES = {'scanner': mock_enemy_type}
            
            enemy = Enemy(Position(10, 15), "scanner")
            from game_entities import EnemyState
            enemy.state = EnemyState.UNAWARE
            enemy.alert_timer = 0
            
            result = SaveGameManager._serialize_enemies([enemy])
            
            assert len(result) == 1
            assert result[0]["type"] == "scanner"
            assert result[0]["x"] == 10
            assert result[0]["y"] == 15


class TestSaveGameIntegration:
    """Test save/load integration with actual file operations."""
    
    def test_save_load_cycle_basic_data(self):
        """Basic save/load cycle preserves essential data."""
        # Mock minimal game state
        mock_game = self._create_minimal_mock_game()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Override the save file path
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                # Save the game
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True
                
                # Load the game
                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None
                
                # Verify key data is preserved
                assert loaded_data["level"] == mock_game.level
                assert loaded_data["player"]["x"] == mock_game.player.x
                assert loaded_data["player"]["cpu"] == mock_game.player.cpu
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _create_minimal_mock_game(self):
        """Create a minimal mock game object for testing."""
        mock_game = Mock()
        mock_game.level = 1
        mock_game.turn = 10
        mock_game.game_over = False
        mock_game.admin_spawned = False
        
        # Mock player
        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 8
        mock_player.last_position = Position(5, 8)
        mock_player.cpu = 90
        mock_player.max_cpu = 100
        mock_player.heat = 15
        mock_player.max_heat = 100
        mock_player.detection = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        # Ensure temporary_effects is a real dict, not Mock
        mock_player.temporary_effects = dict()
        
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {}
        mock_inventory.max_equipped_exploits = 8
        mock_inventory.items = []
        mock_player.inventory_manager = mock_inventory
        
        mock_game.player = mock_player
        
        # Mock game state
        mock_game_state = Mock()
        mock_game_state.dungeon_seed = 54321
        mock_game_state.threat_scan_turns = 0
        mock_game_state.noise_locations = []
        mock_game_state.distraction_points = {}
        mock_game.game_state = mock_game_state
        
        # Mock map
        mock_map = Mock()
        mock_map.code_hacks = {}
        mock_map.exploit_pickups = {}
        mock_map.permanent_upgrades = {}
        mock_map.story_fragments = {}
        mock_map.gateway = None
        mock_map.explored_tiles = set()
        mock_map.last_known_enemy_positions = {}
        mock_game.game_map = mock_map
        
        # Mock enemies (save method expects game.enemies directly)
        mock_game.enemies = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []
        
        # Mock additional attributes that save might access
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        
        # Mock UI state attributes that save expects
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        
        # Mock overclocking state attributes
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        
        # Debug: Ensure distraction_points dict is properly formatted
        mock_game_state.distraction_points = {}
        # Debug: Ensure noise_locations is a proper list
        mock_game_state.noise_locations = []
        
        return mock_game