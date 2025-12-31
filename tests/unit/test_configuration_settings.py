#!/usr/bin/env python3
"""
Unit tests for Configuration and Settings - User Preferences Focus
Tests user settings (GameSettings) behavior with real objects.
File loading and validation tests moved to smoke tests (test_config_validation_smoke.py).
"""

import json
import os
import tempfile

import pytest

from rsp.core.config import GameBalance, GameConfig, GameSettings
from rsp.core.data_loading import PersistentStorage


class TestGameSettings:
    """Test the GameSettings class for user preferences with real objects."""

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
        assert settings.sfx_volume == 0.75
        assert settings.music_volume == 0.6
        assert settings.graphics_mode == "graphics"

    def test_load_settings_from_file(self):
        """Test loading settings from existing file."""
        # Create test settings file
        test_settings = {
            "master_volume": 0.9,
            "sfx_volume": 0.6,
            "music_volume": 0.3,
            "graphics_mode": "graphics",
        }
        with open(self.temp_settings_file, "w") as f:
            json.dump(test_settings, f)

        settings = GameSettings()

        assert settings.master_volume == 0.9
        assert settings.sfx_volume == 0.6
        assert settings.music_volume == 0.3
        assert settings.graphics_mode == "graphics"

    def test_load_settings_missing_keys_use_defaults(self):
        """Test that missing keys in settings file use default values."""
        # Create partial settings file
        partial_settings = {"master_volume": 0.5}
        with open(self.temp_settings_file, "w") as f:
            json.dump(partial_settings, f)

        settings = GameSettings()

        assert settings.master_volume == 0.5  # From file
        assert settings.sfx_volume == 0.75  # Default
        assert settings.music_volume == 0.6  # Default
        assert settings.graphics_mode == "graphics"  # Default

    def test_save_settings_creates_file(self):
        """Test saving settings creates proper JSON file."""
        settings = GameSettings()
        settings.master_volume = 0.95
        settings.sfx_volume = 0.85
        settings.save_settings()

        # Verify file was created with correct content
        assert os.path.exists(self.temp_settings_file)
        with open(self.temp_settings_file) as f:
            saved_data = json.load(f)

        assert saved_data["master_volume"] == 0.95
        assert saved_data["sfx_volume"] == 0.85
        assert saved_data["music_volume"] == 0.6  # Default (not modified in test)
        assert saved_data["graphics_mode"] == "graphics"

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
        assert settings.graphics_mode == "glyph"

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


class TestGameConfigConstants:
    """Test GameConfig layout calculations and relationships."""

    def test_calculated_layout_properties(self):
        """Test calculated layout properties work correctly."""
        # Test that calculated properties are internally consistent
        game_area_width = GameConfig.GAME_AREA_WIDTH()
        assert game_area_width == GameConfig.SCREEN_WIDTH - GameConfig.LOG_WIDTH
        assert game_area_width > 0

        panel_y = GameConfig.PANEL_Y()
        assert panel_y == GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT
        assert panel_y > 0

    def test_screen_layout_consistency(self):
        """Test that screen layout constants are internally consistent."""
        # UI elements should fit within screen
        assert GameConfig.SIDEBAR_WIDTH < GameConfig.SCREEN_WIDTH
        assert GameConfig.LOG_WIDTH < GameConfig.SCREEN_WIDTH
        assert GameConfig.UI_HEIGHT < GameConfig.SCREEN_HEIGHT
        assert GameConfig.PANEL_HEIGHT < GameConfig.SCREEN_HEIGHT

        # Map should fit within screen
        assert GameConfig.MAP_WIDTH <= GameConfig.SCREEN_WIDTH
        assert GameConfig.MAP_HEIGHT <= GameConfig.SCREEN_HEIGHT


class TestGameBalance:
    """Test GameBalance parameters have valid relationships."""

    def test_balance_parameter_relationships(self):
        """Test that balance parameters have sensible relationships."""
        # Heat reduction boosted should be better than normal
        assert GameBalance.HEAT_REDUCTION_BOOSTED > GameBalance.HEAT_REDUCTION_NORMAL

        # CPU restore range should be valid
        assert GameBalance.CPU_RESTORE_MIN < GameBalance.CPU_RESTORE_MAX
        assert GameBalance.CPU_RESTORE_MIN > 0

        # All numeric values should be positive
        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.HEAT_REDUCTION_BOOSTED > 0
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0
        assert GameBalance.COOLING_NODE_EFFECT > 0
        assert GameBalance.CPU_RECOVERY_AMOUNT > 0
        assert GameBalance.ENEMY_ELIMINATION_CPU_REWARD > 0

        # Percentages should be valid (0-100)
        assert 0 <= GameBalance.GHOST_NODE_DETECTION_REDUCTION_PERCENT <= 100

        # Trace level mechanics should be reasonable
        assert 0 < GameBalance.TRACE_INCREASE_INTERVAL <= 100
        assert 0 < GameBalance.TRACE_INCREASE_AMOUNT <= 20


class TestPersistentStorage:
    """Test the PersistentStorage class for save/load operations with real files."""

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
        with open(filepath) as f:
            saved_data = json.load(f)
        assert saved_data == test_data

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
        with open(filepath, "w") as f:
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
