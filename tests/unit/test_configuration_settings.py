#!/usr/bin/env python3
"""
Unit tests for Configuration and Settings functionality.
Tests game configuration loading, balance parameters, user preferences, and data loading systems.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock

from game_config import GameConfig, GameBalance, GameSettings
from data_loading import DataLoader, PersistentStorage


class TestGameSettings:
    """Test the GameSettings class for user preferences."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use a temporary settings file for testing
        self.temp_settings_file = "test_user_settings.json"
        self.original_file = GameSettings.SETTINGS_FILE
        GameSettings.SETTINGS_FILE = self.temp_settings_file
        
        # Clean up any existing test file
        if os.path.exists(self.temp_settings_file):
            os.remove(self.temp_settings_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original settings file
        GameSettings.SETTINGS_FILE = self.original_file
        
        # Clean up test file
        if os.path.exists(self.temp_settings_file):
            os.remove(self.temp_settings_file)
    
    def test_game_settings_initialization_defaults(self):
        """Test GameSettings initializes with correct defaults."""
        settings = GameSettings()
        
        assert settings.master_volume == 0.7
        assert settings.sfx_volume == 0.8
        assert settings.music_volume == 0.5
        assert settings.graphics_mode == "ascii"
    
    def test_load_settings_from_file(self):
        """Test loading settings from existing file."""
        # Create test settings file
        test_settings = {
            "master_volume": 0.9,
            "sfx_volume": 0.6,
            "music_volume": 0.3,
            "graphics_mode": "graphics"
        }
        with open(self.temp_settings_file, 'w') as f:
            json.dump(test_settings, f)
        
        settings = GameSettings()
        
        assert settings.master_volume == 0.9
        assert settings.sfx_volume == 0.6
        assert settings.music_volume == 0.3
        assert settings.graphics_mode == "graphics"
    
    def test_load_settings_empty_file_uses_defaults(self):
        """Test that empty settings file triggers default creation."""
        # Create empty file
        with open(self.temp_settings_file, 'w') as f:
            f.write("")
        
        with patch.object(GameSettings, '_create_default_settings_file') as mock_create:
            settings = GameSettings()
            mock_create.assert_called_once()
    
    def test_load_settings_corrupted_file_recreates_defaults(self):
        """Test that corrupted JSON triggers default file creation."""
        # Create corrupted JSON file
        with open(self.temp_settings_file, 'w') as f:
            f.write("{ invalid json")
        
        with patch.object(GameSettings, '_create_default_settings_file') as mock_create:
            settings = GameSettings()
            mock_create.assert_called_once()
    
    def test_load_settings_missing_keys_use_defaults(self):
        """Test that missing keys in settings file use default values."""
        # Create partial settings file
        partial_settings = {"master_volume": 0.5}
        with open(self.temp_settings_file, 'w') as f:
            json.dump(partial_settings, f)
        
        settings = GameSettings()
        
        assert settings.master_volume == 0.5  # From file
        assert settings.sfx_volume == 0.8     # Default
        assert settings.music_volume == 0.5   # Default
        assert settings.graphics_mode == "ascii"  # Default
    
    def test_save_settings_creates_file(self):
        """Test saving settings creates proper JSON file."""
        settings = GameSettings()
        settings.master_volume = 0.95
        settings.sfx_volume = 0.85
        settings.save_settings()
        
        # Verify file was created with correct content
        assert os.path.exists(self.temp_settings_file)
        with open(self.temp_settings_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["master_volume"] == 0.95
        assert saved_data["sfx_volume"] == 0.85
        assert saved_data["music_volume"] == 0.5
        assert saved_data["graphics_mode"] == "ascii"
    
    def test_volume_setting_methods(self):
        """Test volume setting methods with bounds checking."""
        settings = GameSettings()
        
        # Test setting valid volumes
        settings.set_master_volume(0.3)
        settings.set_sfx_volume(0.9)
        settings.set_music_volume(0.1)
        
        assert settings.master_volume == 0.3
        assert settings.sfx_volume == 0.9
        assert settings.music_volume == 0.1
    
    def test_volume_bounds_checking(self):
        """Test volume bounds are enforced (0.0 to 1.0)."""
        settings = GameSettings()
        
        # Test volume clamping
        settings.set_master_volume(-0.5)  # Below minimum
        assert settings.master_volume == 0.0
        
        settings.set_sfx_volume(1.5)  # Above maximum
        assert settings.sfx_volume == 1.0
        
        settings.set_music_volume(0.5)  # Valid range
        assert settings.music_volume == 0.5
    
    def test_graphics_mode_setting(self):
        """Test graphics mode setting with validation."""
        settings = GameSettings()
        
        # Test valid modes
        settings.set_graphics_mode("graphics")
        assert settings.graphics_mode == "graphics"
        
        settings.set_graphics_mode("ascii")
        assert settings.graphics_mode == "ascii"
        
        # Test invalid mode (should not change)
        original_mode = settings.graphics_mode
        settings.set_graphics_mode("invalid_mode")
        assert settings.graphics_mode == original_mode
    
    def test_volume_percentage_conversion(self):
        """Test volume percentage getter and setter methods."""
        settings = GameSettings()
        
        # Test percentage getter
        settings.master_volume = 0.75
        assert settings.get_volume_percent("master") == 75
        
        settings.sfx_volume = 0.0
        assert settings.get_volume_percent("sfx") == 0
        
        # Test percentage setter
        settings.set_volume_percent("music", 50)
        assert settings.music_volume == 0.5
        
        settings.set_volume_percent("master", 100)
        assert settings.master_volume == 1.0
    
    def test_create_default_settings_file(self):
        """Test default settings file creation."""
        settings = GameSettings()
        settings._create_default_settings_file()
        
        assert os.path.exists(self.temp_settings_file)
        with open(self.temp_settings_file, 'r') as f:
            default_data = json.load(f)
        
        assert default_data["master_volume"] == 0.7
        assert default_data["sfx_volume"] == 0.8
        assert default_data["music_volume"] == 0.5
        assert default_data["graphics_mode"] == "ascii"


class TestGameConfig:
    """Test the GameConfig class for game configuration constants."""
    
    def test_screen_dimensions(self):
        """Test screen dimension constants."""
        assert GameConfig.SCREEN_WIDTH == 80
        assert GameConfig.SCREEN_HEIGHT == 50
        assert GameConfig.MAP_WIDTH == 50
        assert GameConfig.MAP_HEIGHT == 50
    
    def test_ui_layout_constants(self):
        """Test UI layout constants."""
        assert GameConfig.UI_HEIGHT == 10
        assert GameConfig.SIDEBAR_WIDTH == 25
        assert GameConfig.LOG_WIDTH == 25
        assert GameConfig.PANEL_HEIGHT == 5
    
    def test_calculated_layout_properties(self):
        """Test calculated layout properties."""
        game_area_width = GameConfig.GAME_AREA_WIDTH()
        assert game_area_width == GameConfig.SCREEN_WIDTH - GameConfig.LOG_WIDTH
        
        panel_y = GameConfig.PANEL_Y()
        assert panel_y == GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT
    
    def test_game_parameter_constants(self):
        """Test core game parameter constants."""
        assert GameConfig.DEFAULT_PLAYER_RAM == 8
        assert GameConfig.DEFAULT_PLAYER_CPU == 100
        assert GameConfig.MAX_HEAT == 100
        assert GameConfig.MAX_DETECTION == 100
        assert GameConfig.DETECTION_REDUCTION_ON_LEVEL == 50
        assert isinstance(GameConfig.DUNGEON_SEED_RANGE, int)
        assert GameConfig.VIRUS_DAMAGE_PER_TURN == 3
    
    def test_load_from_json_file_exists(self):
        """Test loading configuration from JSON file."""
        mock_config = {
            "display": {
                "screen_width": 100,
                "screen_height": 60,
                "map_width": 70,
                "map_height": 70
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            with patch('os.path.exists', return_value=True):
                GameConfig.load_from_json()
                
                assert GameConfig.SCREEN_WIDTH == 100
                assert GameConfig.SCREEN_HEIGHT == 60
                assert GameConfig.MAP_WIDTH == 70
                assert GameConfig.MAP_HEIGHT == 70
    
    def test_load_from_json_file_not_found(self):
        """Test graceful handling when JSON file doesn't exist."""
        original_width = GameConfig.SCREEN_WIDTH
        
        with patch('builtins.open', side_effect=FileNotFoundError()):
            GameConfig.load_from_json()
            
            # Should maintain original values
            assert GameConfig.SCREEN_WIDTH == original_width
    
    def test_load_from_json_invalid_json(self):
        """Test graceful handling of invalid JSON."""
        original_width = GameConfig.SCREEN_WIDTH
        
        with patch('builtins.open', mock_open(read_data="{ invalid json")):
            with patch('os.path.exists', return_value=True):
                GameConfig.load_from_json()
                
                # Should maintain original values
                assert GameConfig.SCREEN_WIDTH == original_width
    
    def test_get_configuration_value(self):
        """Test getting configuration values by key."""
        mock_config = {
            "gameplay": {
                "difficulty": "hard",
                "auto_save": False
            },
            "graphics": {
                "effects": True
            }
        }
        
        GameConfig._config_data = mock_config
        
        # Test nested key access
        assert GameConfig.get("gameplay.difficulty") == "hard"
        assert GameConfig.get("gameplay.auto_save") is False
        assert GameConfig.get("graphics.effects") is True
        
        # Test default values
        assert GameConfig.get("nonexistent.key", "default") == "default"
        assert GameConfig.get("gameplay.missing", None) is None
    
    def test_network_configurations(self):
        """Test network configuration loading."""
        with patch.object(DataLoader, 'load_game_data') as mock_load:
            mock_load.return_value = {
                "network_configs": {
                    "1": {"name": "Test Network", "enemies": 10},
                    "2": {"name": "Hard Network", "enemies": 20}
                }
            }
            
            configs = GameConfig.get_network_configs()
            
            assert isinstance(configs, dict)
            assert 1 in configs
            assert 2 in configs
            assert configs[1]["name"] == "Test Network"
            assert configs[2]["enemies"] == 20


class TestGameBalance:
    """Test the GameBalance class for balance parameters."""
    
    def test_heat_management_constants(self):
        """Test heat management balance constants."""
        assert GameBalance.HEAT_REDUCTION_NORMAL == 2
        assert GameBalance.HEAT_REDUCTION_BOOSTED == 3
        assert isinstance(GameBalance.DETECTION_INCREASE_INTERVAL, int)
        assert isinstance(GameBalance.DETECTION_INCREASE_AMOUNT, int)
    
    def test_node_effect_constants(self):
        """Test special node effect constants."""
        assert GameBalance.COOLING_NODE_EFFECT == 20
        assert GameBalance.GHOST_NODE_DETECTION_REDUCTION_PERCENT == 20.0
        assert GameBalance.CPU_RECOVERY_AMOUNT == 20
    
    def test_combat_reward_constants(self):
        """Test combat reward balance constants."""
        assert GameBalance.ENEMY_ELIMINATION_CPU_REWARD == 5
    
    def test_code_patch_effect_constants(self):
        """Test code patch effect constants."""
        assert GameBalance.CPU_RESTORE_MIN == 30
        assert GameBalance.CPU_RESTORE_MAX == 40
        assert GameBalance.HEAT_REDUCTION_INSTANT == 40
        
        # Ensure min is less than max
        assert GameBalance.CPU_RESTORE_MIN < GameBalance.CPU_RESTORE_MAX
    
    def test_balance_parameter_bounds(self):
        """Test that balance parameters are within reasonable bounds."""
        # Heat values should be positive
        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.HEAT_REDUCTION_BOOSTED > 0
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0
        
        # Detection values should be reasonable
        assert 0 < GameBalance.DETECTION_INCREASE_INTERVAL <= 100
        assert 0 < GameBalance.DETECTION_INCREASE_AMOUNT <= 10
        
        # Node effects should be positive
        assert GameBalance.COOLING_NODE_EFFECT > 0
        assert GameBalance.CPU_RECOVERY_AMOUNT > 0
        
        # Percentage should be valid
        assert 0 <= GameBalance.GHOST_NODE_DETECTION_REDUCTION_PERCENT <= 100


class TestDataLoader:
    """Test the DataLoader class for JSON data loading."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear cached data for clean tests
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_load_story_fragments_success(self):
        """Test successful story fragment loading."""
        mock_data = {"fragments": ["Fragment 1", "Fragment 2", "Fragment 3"]}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
            fragments = DataLoader.load_story_fragments()
            
            assert fragments == ["Fragment 1", "Fragment 2", "Fragment 3"]
            assert DataLoader._story_fragments is not None
    
    def test_load_story_fragments_file_not_found(self):
        """Test story fragment loading with missing file."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            fragments = DataLoader.load_story_fragments()
            
            # Should return fallback fragments
            assert isinstance(fragments, list)
            assert len(fragments) >= 1
            assert "fallback" in fragments[0].lower()
    
    def test_load_story_fragments_invalid_json(self):
        """Test story fragment loading with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="{ invalid json")):
            fragments = DataLoader.load_story_fragments()
            
            # Should return fallback fragments
            assert isinstance(fragments, list)
            assert "fallback" in fragments[0].lower()
    
    def test_load_story_fragments_caching(self):
        """Test that story fragments are cached after first load."""
        mock_data = {"fragments": ["Cached Fragment"]}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))) as mock_file:
            # First call should read from file
            fragments1 = DataLoader.load_story_fragments()
            
            # Second call should use cache (no file access)
            fragments2 = DataLoader.load_story_fragments()
            
            assert fragments1 == fragments2
            assert mock_file.call_count == 1  # File only opened once
    
    def test_load_game_data_success(self):
        """Test successful game data loading."""
        mock_data = {
            "enemy_types": {"test_enemy": {"symbol": "T", "cpu": 50}},
            "exploits": {"test_exploit": {"name": "Test", "ram": 2}},
            "network_configs": {"1": {"name": "Test Network"}}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_data))):
            game_data = DataLoader.load_game_data()
            
            assert "enemy_types" in game_data
            assert "exploits" in game_data
            assert "network_configs" in game_data
            assert game_data["enemy_types"]["test_enemy"]["symbol"] == "T"
    
    def test_load_game_data_fallback(self):
        """Test game data loading with fallback data."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            game_data = DataLoader.load_game_data()
            
            # Should return fallback data with required keys
            assert "enemy_types" in game_data
            assert "exploits" in game_data
            assert "upgrades" in game_data
            assert "network_configs" in game_data
    
    def test_load_config_success(self):
        """Test successful configuration loading."""
        mock_config = {
            "gameplay": {"difficulty": "normal"},
            "graphics": {"ascii_mode": False},
            "audio": {"master_volume": 0.8}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
            config = DataLoader.load_config()
            
            assert config["gameplay"]["difficulty"] == "normal"
            assert config["graphics"]["ascii_mode"] is False
            assert config["audio"]["master_volume"] == 0.8
    
    def test_load_config_fallback(self):
        """Test configuration loading with fallback data."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            config = DataLoader.load_config()
            
            # Should return fallback config with required sections
            assert "gameplay" in config
            assert "graphics" in config
            assert "audio" in config
    
    def test_fallback_data_structure(self):
        """Test that fallback data has proper structure."""
        story_fallback = DataLoader._get_fallback_story_fragments()
        assert isinstance(story_fallback, list)
        assert len(story_fallback) > 0
        
        game_data_fallback = DataLoader._get_fallback_game_data()
        assert isinstance(game_data_fallback, dict)
        assert "enemy_types" in game_data_fallback
        
        config_fallback = DataLoader._get_fallback_config()
        assert isinstance(config_fallback, dict)
        assert "gameplay" in config_fallback


class TestPersistentStorage:
    """Test the PersistentStorage class for save/load operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = PersistentStorage(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistent_storage_initialization(self):
        """Test PersistentStorage creates directory."""
        assert os.path.exists(self.temp_dir)
        assert self.storage.base_dir == self.temp_dir
    
    def test_save_data_success(self):
        """Test successful data saving."""
        test_data = {"level": 5, "score": 1000, "player": {"name": "Test"}}
        
        result = self.storage.save_data("test_save.json", test_data)
        
        assert result is True
        filepath = os.path.join(self.temp_dir, "test_save.json")
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == test_data
    
    def test_save_data_failure(self):
        """Test data saving failure handling."""
        # Mock file operations to simulate failure
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = self.storage.save_data("test.json", {"data": "test"})
            assert result is False
    
    def test_load_data_success(self):
        """Test successful data loading."""
        test_data = {"loaded": True, "value": 42}
        
        # First save the data
        self.storage.save_data("test_load.json", test_data)
        
        # Then load it back
        loaded_data = self.storage.load_data("test_load.json")
        
        assert loaded_data == test_data
    
    def test_load_data_file_not_found(self):
        """Test loading non-existent file returns empty dict."""
        loaded_data = self.storage.load_data("nonexistent.json")
        assert loaded_data == {}
    
    def test_load_data_invalid_json(self):
        """Test loading invalid JSON returns empty dict."""
        # Create file with invalid JSON
        filepath = os.path.join(self.temp_dir, "invalid.json")
        with open(filepath, 'w') as f:
            f.write("{ invalid json content")
        
        loaded_data = self.storage.load_data("invalid.json")
        assert loaded_data == {}
    
    def test_directory_creation(self):
        """Test directory creation during initialization."""
        new_temp_dir = os.path.join(self.temp_dir, "nested", "test", "dir")
        
        # Directory shouldn't exist initially
        assert not os.path.exists(new_temp_dir)
        
        # Create storage - should create directory
        nested_storage = PersistentStorage(new_temp_dir)
        
        assert os.path.exists(new_temp_dir)


class TestConfigurationIntegration:
    """Test integration between configuration systems."""
    
    def test_settings_and_config_integration(self):
        """Test that GameSettings and GameConfig work together."""
        settings = GameSettings()
        
        # Settings should handle user preferences
        assert hasattr(settings, 'graphics_mode')
        assert hasattr(settings, 'master_volume')
        
        # Config should handle game constants
        assert hasattr(GameConfig, 'SCREEN_WIDTH')
        assert hasattr(GameConfig, 'MAX_HEAT')
    
    def test_data_loader_and_config_integration(self):
        """Test DataLoader provides data for GameConfig."""
        with patch.object(DataLoader, 'load_game_data') as mock_load:
            mock_load.return_value = {
                "network_configs": {"1": {"test": "data"}}
            }
            
            configs = GameConfig.get_network_configs()
            assert isinstance(configs, dict)
            mock_load.assert_called_once()
    
    def test_configuration_error_handling(self):
        """Test error handling across configuration systems."""
        # GameSettings should handle file errors gracefully
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            settings = GameSettings()
            # Should still initialize with defaults
            assert settings.master_volume == 0.7
        
        # DataLoader should handle JSON errors gracefully
        with patch('builtins.open', side_effect=json.JSONDecodeError("Invalid", "doc", 0)):
            data = DataLoader.load_game_data()
            # Should return fallback data
            assert isinstance(data, dict)
    
    def test_configuration_validation_rules(self):
        """Test validation rules across configuration systems."""
        settings = GameSettings()
        
        # Volume validation
        settings.set_master_volume(-1.0)  # Invalid
        assert settings.master_volume == 0.0  # Clamped to valid range
        
        settings.set_sfx_volume(2.0)  # Invalid
        assert settings.sfx_volume == 1.0  # Clamped to valid range
        
        # Graphics mode validation
        original_mode = settings.graphics_mode
        settings.set_graphics_mode("invalid_mode")
        assert settings.graphics_mode == original_mode  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])