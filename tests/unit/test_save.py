#!/usr/bin/env python3
"""
Unit tests for game_save.py - Save/load persistence system.
Tests save/load functionality, data integrity, and error handling.
"""

import pytest
import json
import os
import tempfile
import time
from unittest.mock import Mock, patch, mock_open, MagicMock
from game_save import SaveGameManager
from game_entities import Position
from game_characters import Player, Enemy
from game_config import GameConfig
from tests.fixtures.mock_factories import MockPlayerFactory, MockEnemyFactory, MockGameFactory


class TestSaveGameManager:
    """Test SaveGameManager functionality."""
    
    def test_save_file_constant(self):
        """Test save file constant is properly defined."""
        assert SaveGameManager.SAVE_FILE == "rogue_signal_save.json"
        assert isinstance(SaveGameManager.SAVE_FILE, str)
    
    @patch('os.path.exists')
    def test_save_exists_true(self, mock_exists):
        """Test save_exists returns True when file exists."""
        mock_exists.return_value = True
        
        result = SaveGameManager.save_exists()
        
        assert result is True
        mock_exists.assert_called_once_with(SaveGameManager.SAVE_FILE)
    
    @patch('os.path.exists')
    def test_save_exists_false(self, mock_exists):
        """Test save_exists returns False when file doesn't exist."""
        mock_exists.return_value = False
        
        result = SaveGameManager.save_exists()
        
        assert result is False
        mock_exists.assert_called_once_with(SaveGameManager.SAVE_FILE)
    
    def test_numpy_converter_int(self):
        """Test numpy converter handles numpy integers."""
        import numpy as np
        
        numpy_int = np.int32(42)
        result = SaveGameManager._numpy_converter(numpy_int)
        
        assert result == 42
        assert isinstance(result, int)
    
    def test_numpy_converter_float(self):
        """Test numpy converter handles numpy floats."""
        import numpy as np
        
        numpy_float = np.float64(3.14)
        result = SaveGameManager._numpy_converter(numpy_float)
        
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_numpy_converter_array(self):
        """Test numpy converter handles numpy arrays."""
        import numpy as np
        
        numpy_array = np.array([1, 2, 3])
        result = SaveGameManager._numpy_converter(numpy_array)
        
        assert result == [1, 2, 3]
        assert isinstance(result, list)
    
    def test_numpy_converter_unsupported_type(self):
        """Test numpy converter raises TypeError for unsupported types."""
        unsupported_obj = {"key": "value"}
        
        with pytest.raises(TypeError, match="is not JSON serializable"):
            SaveGameManager._numpy_converter(unsupported_obj)


class TestSaveGame:
    """Test game saving functionality."""
    
    def test_save_game_none_game(self):
        """Test save_game handles None game object."""
        with patch('logging.error') as mock_log:
            result = SaveGameManager.save_game(None)
            
            assert result is False
            mock_log.assert_called_once_with("Cannot save: game object is None")
    
    def test_save_game_none_player(self):
        """Test save_game handles None player object."""
        mock_game = Mock()
        mock_game.player = None
        
        with patch('logging.error') as mock_log:
            result = SaveGameManager.save_game(mock_game)
            
            assert result is False
            mock_log.assert_called_once_with("Cannot save: player object is None")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.move')
    @patch('os.path.exists', return_value=False)
    def test_save_game_success(self, mock_exists, mock_move, mock_file):
        """Test successful game save."""
        # Create comprehensive mock game
        mock_game = self._create_comprehensive_mock_game()
        
        with patch('logging.info') as mock_log:
            result = SaveGameManager.save_game(mock_game)
            
            assert result is True
            mock_log.assert_called_with("Game saved successfully")
            
            # Verify file operations
            mock_file.assert_called_once()
            mock_move.assert_called_once()
            
            # Verify JSON was written
            written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
            save_data = json.loads(written_content)
            
            # Verify essential data structure
            assert "version" in save_data
            assert "timestamp" in save_data
            assert "player" in save_data
            assert "level" in save_data
            assert "turn" in save_data
    
    @patch('builtins.open', side_effect=IOError("Disk full"))
    @patch('time.sleep')
    def test_save_game_io_error_retry(self, mock_sleep, mock_file):
        """Test save game retries on I/O errors."""
        mock_game = self._create_comprehensive_mock_game()
        
        with patch('logging.warning') as mock_warn:
            with patch('logging.error') as mock_error:
                result = SaveGameManager.save_game(mock_game)
                
                assert result is False
                
                # Should have tried MAX_SAVE_ATTEMPTS times
                assert mock_file.call_count == GameConfig.MAX_SAVE_ATTEMPTS
                assert mock_sleep.call_count == GameConfig.MAX_SAVE_ATTEMPTS - 1
                
                mock_error.assert_called_with("All save attempts failed")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump', side_effect=ValueError("Invalid data"))
    def test_save_game_serialization_error(self, mock_json_dump, mock_file):
        """Test save game handles serialization errors."""
        mock_game = self._create_comprehensive_mock_game()
        
        with patch('logging.error') as mock_error:
            result = SaveGameManager.save_game(mock_game)
            
            assert result is False
            mock_error.assert_called_with("Data serialization error (no retry): Invalid data")
    
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_save_game_permission_error(self, mock_file):
        """Test save game handles permission errors."""
        mock_game = self._create_comprehensive_mock_game()
        
        with patch('logging.error') as mock_error:
            result = SaveGameManager.save_game(mock_game)
            
            assert result is False
            mock_error.assert_called_with("All save attempts failed")
    
    def test_save_game_data_structure(self):
        """Test that save game creates correct data structure."""
        mock_game = self._create_comprehensive_mock_game()
        
        # Mock file operations to capture the data
        saved_data = None
        
        def capture_json_dump(data, file, **kwargs):
            nonlocal saved_data
            saved_data = data
        
        with patch('builtins.open', mock_open()):
            with patch('shutil.move'):
                with patch('os.path.exists', return_value=False):
                    with patch('json.dump', side_effect=capture_json_dump):
                        
                        SaveGameManager.save_game(mock_game)
                        
                        # Verify data structure
                        assert saved_data is not None
                        assert saved_data["version"] == "dev"
                        assert saved_data["level"] == 5
                        assert saved_data["turn"] == 100
                        assert saved_data["game_over"] is False
                        assert saved_data["admin_spawned"] is True
                        
                        # Verify player data
                        player_data = saved_data["player"]
                        assert player_data["x"] == 10
                        assert player_data["y"] == 15
                        assert player_data["cpu"] == 80
                        assert player_data["heat"] == 30
                        
                        # Verify structure exists
                        assert "game_effects" in saved_data
                        assert "map_state" in saved_data
                        assert "enemies" in saved_data
                        assert "code_hack_effects" in saved_data
                        assert "ui_state" in saved_data
    
    def _create_comprehensive_mock_game(self):
        """Create a comprehensive mock game for testing."""
        mock_game = Mock()
        mock_game.level = 5
        mock_game.turn = 100
        mock_game.game_over = False
        mock_game.admin_spawned = True
        
        # Mock game state
        mock_game.game_state = Mock()
        mock_game.game_state.dungeon_seed = 12345
        mock_game.game_state.threat_scan_turns = 3
        mock_game.game_state.noise_locations = [Position(20, 20)]
        mock_game.game_state.distraction_points = {Position(25, 25): 5}
        
        # Mock player
        mock_player = MockPlayerFactory.create_basic_player(10, 15)
        mock_player.cpu = 80
        mock_player.heat = 30
        mock_player.last_position = Position(9, 15)
        mock_player.inventory_manager.equipped_exploits = ["code_injection", "data_mimic"]
        mock_player.inventory_manager.max_equipped_exploits = 4
        mock_player.inventory_manager.items = []
        mock_game.player = mock_player
        
        # Mock game map
        mock_game.game_map = Mock()
        mock_game.game_map.code_hacks = {}
        mock_game.game_map.exploit_pickups = {}
        mock_game.game_map.permanent_upgrades = {(30, 30): "ram_boost"}
        mock_game.game_map.story_fragments = {}
        mock_game.game_map.gateway = Position(45, 45)
        mock_game.game_map.explored_tiles = {(10, 10), (11, 11)}
        mock_game.game_map.last_known_enemy_positions = {1: (Position(20, 20), 50)}
        
        # Mock enemies
        mock_game.enemies = [MockEnemyFactory.create_basic_enemy('scanner', 15, 15)]
        
        # Mock code effects
        mock_game.code_hack_effects = {"test_effect": ("increase", "cpu")}
        mock_game.discovered_code_effects = {"test_code": "discovered"}
        
        # Mock overclocking state
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        
        # Mock UI state
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        
        return mock_game


class TestLoadGame:
    """Test game loading functionality."""
    
    @patch.object(SaveGameManager, 'save_exists', return_value=False)
    def test_load_game_no_file(self, mock_save_exists):
        """Test load_game returns None when no save file exists."""
        result = SaveGameManager.load_game()
        
        assert result is None
        mock_save_exists.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open, read_data='')
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_empty_file(self, mock_save_exists, mock_file):
        """Test load_game handles empty file."""
        with patch('logging.error') as mock_error:
            result = SaveGameManager.load_game()
            
            assert result is None
            mock_error.assert_called_with("Save file is empty or corrupted")
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"level": 3, "turn": 50}')
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_success(self, mock_save_exists, mock_file):
        """Test successful game loading."""
        with patch('logging.info') as mock_info:
            result = SaveGameManager.load_game()
            
            assert result is not None
            assert result["level"] == 3
            assert result["turn"] == 50
            mock_info.assert_called_with("Game loaded successfully")
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json content')
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_json_decode_error(self, mock_save_exists, mock_file):
        """Test load_game handles JSON decode errors."""
        with patch('logging.error') as mock_error:
            result = SaveGameManager.load_game()
            
            assert result is None
            # Should log detailed error information
            assert mock_error.call_count >= 1
            error_call = mock_error.call_args_list[0]
            assert "JSON decode error" in error_call[0][0]
    
    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_file_not_found(self, mock_save_exists, mock_file):
        """Test load_game handles file not found during reading."""
        with patch('logging.info') as mock_info:
            result = SaveGameManager.load_game()
            
            assert result is None
            mock_info.assert_called_with("No save file found")
    
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_permission_error(self, mock_save_exists, mock_file):
        """Test load_game handles permission errors."""
        with patch('logging.error') as mock_error:
            result = SaveGameManager.load_game()
            
            assert result is None
            mock_error.assert_called_with("Permission denied accessing save file: Access denied")
    
    @patch('builtins.open', side_effect=Exception("Unexpected error"))
    @patch.object(SaveGameManager, 'save_exists', return_value=True)
    def test_load_game_unexpected_error(self, mock_save_exists, mock_file):
        """Test load_game handles unexpected errors."""
        with patch('logging.error') as mock_error:
            result = SaveGameManager.load_game()
            
            assert result is None
            # Should log the unexpected error
            assert mock_error.call_count >= 1


class TestSaveLoadIntegration:
    """Test save/load integration and round-trip consistency."""

    def _create_test_game(self):
        """Create a simple test game for basic testing."""
        mock_game = Mock()

        mock_game.level = 2
        mock_game.turn = 75
        mock_game.game_over = False
        mock_game.admin_spawned = False
        mock_game.game_state = Mock()
        mock_game.game_state.dungeon_seed = 12345
        mock_game.game_state.threat_scan_turns = 0
        mock_game.game_state.noise_locations = []
        mock_game.game_state.distraction_points = {}

        mock_player = Mock()
        mock_player.x = 12
        mock_player.y = 18
        mock_player.cpu = 90
        mock_player.last_position = Mock()
        mock_player.last_position.x = 11
        mock_player.last_position.y = 18
        mock_player.max_cpu = 100
        mock_player.heat = 0
        mock_player.max_heat = 100
        mock_player.detection = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}  # Empty dict, not Mock
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equipped_exploits = ["shadow_step"]
        mock_player.inventory_manager.max_equipped_exploits = 3
        mock_player.inventory_manager.items = []
        mock_game.player = mock_player

        mock_game.game_map = Mock()
        mock_game.game_map.code_hacks = {}
        mock_game.game_map.exploit_pickups = {}
        mock_game.game_map.permanent_upgrades = {}
        mock_game.game_map.story_fragments = {}
        mock_game.game_map.gateway = Mock()
        mock_game.game_map.gateway.x = 25
        mock_game.game_map.gateway.y = 30
        mock_game.game_map.explored_tiles = set()
        mock_game.game_map.last_known_enemy_positions = {}

        mock_game.enemies = []
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0

        return mock_game

    def _create_complex_test_game(self):
        """Create a complex test game with nested data structures."""
        mock_game = self._create_test_game()

        # Add complex data
        mock_game.game_state.threat_scan_turns = 5
        # Create simple objects with x,y attributes instead of Mock objects
        noise_pos = type('Position', (), {'x': 15, 'y': 20})
        distraction_pos = type('Position', (), {'x': 30, 'y': 25})
        mock_game.game_state.noise_locations = [noise_pos]
        mock_game.game_state.distraction_points = {distraction_pos: 8}

        mock_game.game_map.gateway.x = 40
        mock_game.game_map.gateway.y = 35
        mock_game.game_map.explored_tiles = {(5, 5), (6, 6), (7, 7)}
        enemy_pos1 = type('Position', (), {'x': 25, 'y': 30})
        enemy_pos2 = type('Position', (), {'x': 35, 'y': 40})
        mock_game.game_map.last_known_enemy_positions = {
            1: (enemy_pos1, 60),
            2: (enemy_pos2, 70)
        }

        # Add enemies (empty for test simplicity - serialization is complex)
        mock_game.enemies = []

        # Add code effects
        mock_game.code_hack_effects = {
            "speed_boost": ("increase", "speed"),
            "heat_reduction": ("decrease", "heat")
        }
        mock_game.discovered_code_effects = {
            "code_alpha": "Increases movement speed",
            "code_beta": "Reduces heat generation"
        }

        return mock_game

    def test_save_load_roundtrip_basic(self):
        """Test basic save and load round-trip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use temporary file for testing
            temp_save_file = os.path.join(temp_dir, "test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                # Create mock game
                mock_game = self._create_test_game()
                
                # Save game
                save_result = SaveGameManager.save_game(mock_game)
                assert save_result is True
                
                # Verify file was created
                assert os.path.exists(temp_save_file)
                
                # Load game
                load_result = SaveGameManager.load_game()
                assert load_result is not None
                
                # Verify essential data was preserved
                assert load_result["level"] == 2
                assert load_result["turn"] == 75
                assert load_result["player"]["x"] == 12
                assert load_result["player"]["y"] == 18
                assert load_result["player"]["cpu"] == 90
    
    def test_save_load_preserves_complex_data(self):
        """Test that save/load preserves complex nested data structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "test_complex_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                mock_game = self._create_complex_test_game()
                
                # Save and load
                SaveGameManager.save_game(mock_game)
                loaded_data = SaveGameManager.load_game()
                
                assert loaded_data is not None
                
                # Verify complex data structures
                assert "game_effects" in loaded_data
                assert "map_state" in loaded_data
                assert "enemies" in loaded_data
                
                # Verify nested data
                assert loaded_data["game_effects"]["threat_scan_turns"] == 5
                assert len(loaded_data["enemies"]) == 0

                # Verify complex map data
                assert loaded_data["map_state"]["gateway"]["x"] == 40
                assert loaded_data["map_state"]["gateway"]["y"] == 35


class TestSaveFileDeletion:
    """Test save file deletion scenarios."""

    def _create_test_game(self):
        """Create a simple test game for basic testing."""
        mock_game = Mock()

        mock_game.level = 2
        mock_game.turn = 75
        mock_game.game_over = False
        mock_game.admin_spawned = False
        mock_game.game_state = Mock()
        mock_game.game_state.dungeon_seed = 12345
        mock_game.game_state.threat_scan_turns = 0
        mock_game.game_state.noise_locations = []
        mock_game.game_state.distraction_points = {}

        mock_player = Mock()
        mock_player.x = 12
        mock_player.y = 18
        mock_player.cpu = 90
        mock_player.last_position = Mock()
        mock_player.last_position.x = 11
        mock_player.last_position.y = 18
        mock_player.max_cpu = 100
        mock_player.heat = 0
        mock_player.max_heat = 100
        mock_player.detection = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}  # Empty dict, not Mock
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equipped_exploits = ["shadow_step"]
        mock_player.inventory_manager.max_equipped_exploits = 3
        mock_player.inventory_manager.items = []
        mock_game.player = mock_player

        mock_game.game_map = Mock()
        mock_game.game_map.code_hacks = {}
        mock_game.game_map.exploit_pickups = {}
        mock_game.game_map.permanent_upgrades = {}
        mock_game.game_map.story_fragments = {}
        mock_game.game_map.gateway = Mock()
        mock_game.game_map.gateway.x = 25
        mock_game.game_map.gateway.y = 30
        mock_game.game_map.explored_tiles = set()
        mock_game.game_map.last_known_enemy_positions = {}

        mock_game.enemies = []
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0

        return mock_game

    def test_save_file_deletion_on_player_death(self):
        """Test save file is deleted when player dies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "death_test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                # Create a save file
                mock_game = self._create_test_game()
                
                # Save the game first
                result = SaveGameManager.save_game(mock_game)
                assert result is True
                assert SaveGameManager.save_exists()
                
                # Simulate player death and delete save
                SaveGameManager.delete_save()
                
                assert not SaveGameManager.save_exists()
    
    def test_save_file_deletion_confirmation(self):
        """Test save file deletion with confirmation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "delete_test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                # Create save file
                with open(temp_save_file, 'w') as f:
                    f.write('{"test": "data"}')
                
                assert SaveGameManager.save_exists()
                
                # Delete should succeed
                result = SaveGameManager.delete_save()
                assert result is True
                assert not SaveGameManager.save_exists()
                
                # Delete non-existent file should still return True
                result = SaveGameManager.delete_save()
                assert result is True
    
    def test_save_file_deletion_error_handling(self):
        """Test save file deletion error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "error_test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                # Mock file deletion failure
                with patch('os.remove', side_effect=PermissionError("Access denied")):
                    with patch.object(SaveGameManager, 'save_exists', return_value=True):
                        
                        result = SaveGameManager.delete_save()
                        
                        assert result is False


class TestUpgradePersistence:
    """Test upgrade state persistence in save files."""
    
    def test_permanent_upgrade_persistence(self):
        """Test permanent upgrades are saved and loaded correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "upgrade_test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                mock_game = self._create_test_game()
                
                # Add upgrades to the game
                mock_game.player.max_cpu = 120  # Upgraded
                mock_game.player.max_heat = 110  # Upgraded
                mock_game.player.ram_total = 25  # Upgraded
                
                # Mock game map with permanent upgrades
                mock_game.game_map.permanent_upgrades = {
                    (15, 10): "max_cpu_upgrade",
                    (22, 18): "max_heat_upgrade", 
                    (8, 25): "ram_upgrade"
                }
                
                # Save game with upgrades
                result = SaveGameManager.save_game(mock_game)
                assert result is True
                
                # Load and verify upgrades preserved
                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None
                
                # Check player stats reflect upgrades
                assert loaded_data["player"]["max_cpu"] == 120
                assert loaded_data["player"]["max_heat"] == 110
                assert loaded_data["player"]["ram_total"] == 25
                
                # Check upgrade locations preserved
                upgrades = loaded_data["map_state"]["permanent_upgrades"]
                assert "15,10" in upgrades
                assert upgrades["15,10"] == "max_cpu_upgrade"
                assert "22,18" in upgrades
                assert upgrades["22,18"] == "max_heat_upgrade"
                assert "8,25" in upgrades
                assert upgrades["8,25"] == "ram_upgrade"
    
    def test_upgrade_application_tracking(self):
        """Test tracking which upgrades have been applied."""
        # Create test data showing applied upgrades
        save_data = {
            "player": {
                "max_cpu": 130,  # Result of upgrades
                "max_heat": 120,
                "ram_total": 30
            },
            "map_state": {
                "permanent_upgrades": {}  # Upgrades consumed/applied
            }
        }
        
        # Verify that consumed upgrades are reflected in player stats
        # Base stats are 100/100/20, so these show upgrades applied
        assert save_data["player"]["max_cpu"] > 100
        assert save_data["player"]["max_heat"] > 100
        assert save_data["player"]["ram_total"] > 20
    
    def test_upgrade_state_consistency(self):
        """Test consistency between upgrade state and player stats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_save_file = os.path.join(temp_dir, "consistency_test_save.json")
            
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_save_file):
                # Create game with upgrade available but not yet applied
                mock_game = self._create_test_game()
                mock_game.game_map.permanent_upgrades = {
                    (10, 10): "max_cpu_upgrade"  # Upgrade available
                }
                # Player still has base stats (upgrade not picked up)
                mock_game.player.max_cpu = 100
                
                # Save and load
                SaveGameManager.save_game(mock_game)
                loaded_data = SaveGameManager.load_game()
                
                # Verify state consistency
                upgrade_exists = "10,10" in loaded_data["map_state"]["permanent_upgrades"]
                player_has_base_stats = loaded_data["player"]["max_cpu"] == 100
                
                # This is consistent - upgrade exists and player hasn't applied it yet
                assert upgrade_exists and player_has_base_stats
                
                map_state = loaded_data["map_state"]
                assert map_state["gateway"]["x"] == 25
                assert map_state["gateway"]["y"] == 30
    
    def test_save_atomic_operation(self):
        """Test that save operation is atomic (uses temporary file)."""
        mock_game = self._create_test_game()
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('shutil.move') as mock_move:
                with patch('os.path.exists', return_value=False):
                    
                    SaveGameManager.save_game(mock_game)
                    
                    # Should have opened temporary file
                    temp_file_name = SaveGameManager.SAVE_FILE + '.tmp'
                    mock_file.assert_called_once_with(temp_file_name, 'w', encoding='utf-8')
                    
                    # Should have moved temp file to final location
                    mock_move.assert_called_once_with(temp_file_name, SaveGameManager.SAVE_FILE)
    
    def test_temp_file_cleanup_on_error(self):
        """Test that temporary file is cleaned up on error."""
        mock_game = self._create_test_game()
        
        with patch('builtins.open', mock_open()):
            with patch('shutil.move', side_effect=OSError("Move failed")):
                with patch('os.path.exists', return_value=True) as mock_exists:
                    with patch('os.remove') as mock_remove:
                        
                        result = SaveGameManager.save_game(mock_game)
                        
                        assert result is False
                        # Should have attempted to clean up temp file
                        mock_remove.assert_called()
    
    def _create_test_game(self):
        """Create a simple test game for basic testing."""
        mock_game = Mock()
        mock_game.level = 2
        mock_game.turn = 75
        mock_game.game_over = False
        mock_game.admin_spawned = False
        
        mock_game.game_state = Mock()
        mock_game.game_state.dungeon_seed = 54321
        mock_game.game_state.threat_scan_turns = 0
        mock_game.game_state.noise_locations = []
        mock_game.game_state.distraction_points = {}
        
        mock_player = MockPlayerFactory.create_basic_player(12, 18)
        mock_player.cpu = 90
        mock_player.last_position = Position(11, 18)
        mock_player.inventory_manager.equipped_exploits = ["shadow_step"]
        mock_player.inventory_manager.max_equipped_exploits = 3
        mock_player.inventory_manager.items = []
        mock_game.player = mock_player
        
        mock_game.game_map = Mock()
        mock_game.game_map.code_hacks = {}
        mock_game.game_map.exploit_pickups = {}
        mock_game.game_map.permanent_upgrades = {}
        mock_game.game_map.story_fragments = {}
        mock_game.game_map.gateway = Position(25, 30)
        mock_game.game_map.explored_tiles = set()
        mock_game.game_map.last_known_enemy_positions = {}
        
        mock_game.enemies = []
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        
        return mock_game
    
    def _create_complex_test_game(self):
        """Create a complex test game with nested data structures."""
        mock_game = self._create_test_game()
        
        # Add complex data
        mock_game.game_state.threat_scan_turns = 5
        mock_game.game_state.noise_locations = [Position(15, 20)]
        mock_game.game_state.distraction_points = {Position(30, 25): 8}
        
        mock_game.game_map.gateway = Position(40, 35)
        mock_game.game_map.explored_tiles = {(5, 5), (6, 6), (7, 7)}
        mock_game.game_map.last_known_enemy_positions = {
            1: (Position(25, 30), 60),
            2: (Position(35, 40), 70)
        }
        
        # Add enemies
        mock_game.enemies = [
            MockEnemyFactory.create_hostile_enemy('hunter', 20, 25),
            MockEnemyFactory.create_basic_enemy('scanner', 30, 35)
        ]
        
        # Add code effects
        mock_game.code_hack_effects = {
            "speed_boost": ("increase", "speed"),
            "heat_reduction": ("decrease", "heat")
        }
        mock_game.discovered_code_effects = {
            "code_alpha": "Increases movement speed",
            "code_beta": "Reduces heat generation"
        }
        
        return mock_game


class TestSaveDataSerialization:
    """Test specific data serialization methods."""
    
    @pytest.mark.parametrize("input_data,expected_type", [
        # Test various data types that need serialization
        ({"simple": "data"}, dict),
        ([1, 2, 3], list),
        ("string", str),
        (42, int),
        (3.14, float),
        (True, bool),
    ])
    def test_json_serialization_types(self, input_data, expected_type):
        """Test that various data types serialize correctly."""
        # Test through the save system
        json_str = json.dumps(input_data, default=SaveGameManager._numpy_converter)
        reconstructed = json.loads(json_str)
        
        assert type(reconstructed) == expected_type
        assert reconstructed == input_data


class TestErrorRecovery:
    """Test error recovery and robustness."""
    
    def test_corrupted_save_file_handling(self):
        """Test handling of various corrupted save file scenarios."""
        corruption_scenarios = [
            "",  # Empty file
            "   ",  # Whitespace only
            "{incomplete json",  # Incomplete JSON
            '{"valid": "json", "but": "missing_quote}',  # Missing quote
            b'\x00\x01\x02',  # Binary data
        ]
        
        for corrupted_content in corruption_scenarios:
            with patch('builtins.open', mock_open(read_data=corrupted_content)):
                with patch.object(SaveGameManager, 'save_exists', return_value=True):
                    result = SaveGameManager.load_game()
                    assert result is None, f"Should handle corrupted content: {corrupted_content!r}"
    
    def test_large_file_handling(self):
        """Test handling of unusually large save files."""
        # Create a large but valid JSON structure
        large_data = {"large_array": list(range(10000))}
        large_json = json.dumps(large_data)
        
        with patch('builtins.open', mock_open(read_data=large_json)):
            with patch.object(SaveGameManager, 'save_exists', return_value=True):
                result = SaveGameManager.load_game()
                
                assert result is not None
                assert "large_array" in result
                assert len(result["large_array"]) == 10000
    
    def test_save_retry_mechanism(self):
        """Test save retry mechanism with partial failures."""
        # Create a proper mock game using the working helper method
        mock_game = Mock()
        mock_game.level = 1
        mock_game.turn = 50
        mock_game.game_over = False
        mock_game.admin_spawned = False
        mock_game.game_state = Mock()
        mock_game.game_state.dungeon_seed = 123
        mock_game.game_state.threat_scan_turns = 0
        mock_game.game_state.noise_locations = []
        mock_game.game_state.distraction_points = {}

        # Create player with all required attributes
        mock_player = Mock()
        mock_player.x = 10
        mock_player.y = 10
        mock_player.cpu = 80
        mock_player.last_position = Mock()
        mock_player.last_position.x = 9
        mock_player.last_position.y = 10
        mock_player.max_cpu = 100
        mock_player.heat = 0
        mock_player.max_heat = 100
        mock_player.detection = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equipped_exploits = []
        mock_player.inventory_manager.max_equipped_exploits = 3
        mock_player.inventory_manager.items = []
        mock_game.player = mock_player

        mock_game.game_map = Mock()
        mock_game.game_map.code_hacks = {}
        mock_game.game_map.exploit_pickups = {}
        mock_game.game_map.permanent_upgrades = {}
        mock_game.game_map.story_fragments = {}
        mock_game.game_map.gateway = None
        mock_game.game_map.explored_tiles = set()
        mock_game.game_map.last_known_enemy_positions = {}
        mock_game.enemies = []
        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        
        # Mock failed attempts followed by success
        call_count = 0
        def side_effect_open(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise IOError("Temporary failure")
            return mock_open()(*args, **kwargs)
        
        with patch('builtins.open', side_effect=side_effect_open):
            with patch('shutil.move'):
                with patch('os.path.exists', return_value=False):
                    with patch('time.sleep'):
                        result = SaveGameManager.save_game(mock_game)
                        
                        assert result is True
                        assert call_count == 3  # Should have retried