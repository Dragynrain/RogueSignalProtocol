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
        mock_player.trace_level = 0
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
        mock_game_state.revealed_special_nodes = {}  # Add missing attribute for save system
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