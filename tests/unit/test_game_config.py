#!/usr/bin/env python3
"""
Unit tests for game_config.py - Configuration and settings management.

Tests cover:
- GameSettings initialization and defaults
- Settings persistence (save/load)
- Volume setters with clamping
- Graphics mode validation
- GameConfig loading from JSON
- Error handling for missing/corrupt config

Does NOT test:
- UI color RGB conversion (integration with ColorManager)
- Dialogue preferences (covered by dialogue system tests)
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from game_config import GameConfig, GameSettings


class TestGameSettingsInitialization:
    """Test GameSettings initialization and defaults."""

    def test_game_settings_initializes_with_defaults(self):
        """GameSettings should initialize with default values."""
        with patch.object(GameSettings, "load_settings"):
            # Skip loading to test pure initialization
            settings = GameSettings.__new__(GameSettings)
            settings.master_volume = GameSettings.DEFAULTS["master_volume"]
            settings.sfx_volume = GameSettings.DEFAULTS["sfx_volume"]
            settings.music_volume = GameSettings.DEFAULTS["music_volume"]
            settings.graphics_mode = GameSettings.DEFAULTS["graphics_mode"]
            settings.show_achievement_popups = GameSettings.DEFAULTS["show_achievement_popups"]
            settings.show_particle_effects = GameSettings.DEFAULTS["show_particle_effects"]
            settings.ui_color = GameSettings.DEFAULTS["ui_color"]

            assert settings.master_volume == 0.7
            assert settings.sfx_volume == 0.75
            assert settings.music_volume == 0.6
            assert settings.graphics_mode == "graphics"
            assert settings.show_achievement_popups is True
            assert settings.show_particle_effects is True
            assert settings.ui_color == "cyan"

    def test_defaults_has_all_required_keys(self):
        """DEFAULTS should contain all required setting keys."""
        required_keys = [
            "master_volume",
            "sfx_volume",
            "music_volume",
            "graphics_mode",
            "show_achievement_popups",
            "show_particle_effects",
            "ui_color",
            "dialogue_preferences",
            "custom_keyboard_bindings",
            "custom_gamepad_bindings",
            "gamepad_deadzone",
            "gamepad_enabled",
        ]

        for key in required_keys:
            assert key in GameSettings.DEFAULTS, f"Missing required default: {key}"

    def test_defaults_volume_values_are_valid(self):
        """Default volume values should be between 0.0 and 1.0."""
        assert 0.0 <= GameSettings.DEFAULTS["master_volume"] <= 1.0
        assert 0.0 <= GameSettings.DEFAULTS["sfx_volume"] <= 1.0
        assert 0.0 <= GameSettings.DEFAULTS["music_volume"] <= 1.0

    def test_defaults_graphics_mode_is_valid(self):
        """Default graphics mode should be 'glyph' or 'graphics'."""
        assert GameSettings.DEFAULTS["graphics_mode"] in ["glyph", "graphics"]


class TestGameSettingsVolume:
    """Test volume setting methods."""

    @pytest.mark.parametrize("volume_type,setter_method,attr_name", [
        ("master", "set_master_volume", "master_volume"),
        ("sfx", "set_sfx_volume", "sfx_volume"),
        ("music", "set_music_volume", "music_volume"),
    ])
    def test_set_volume_clamps_to_range(self, volume_type, setter_method, attr_name):
        """Volume setters should clamp values to [0.0, 1.0]."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            # Test over max
            getattr(settings, setter_method)(1.5)
            assert getattr(settings, attr_name) == 1.0

            # Test under min
            getattr(settings, setter_method)(-0.5)
            assert getattr(settings, attr_name) == 0.0

            # Test valid value
            getattr(settings, setter_method)(0.5)
            assert getattr(settings, attr_name) == 0.5

    def test_get_volume_percent_converts_correctly(self):
        """get_volume_percent should convert float to percentage."""
        with patch.object(GameSettings, "load_settings"):
            settings = GameSettings()
            settings.master_volume = 0.75
            settings.sfx_volume = 0.5
            settings.music_volume = 1.0

            assert settings.get_volume_percent("master") == 75
            assert settings.get_volume_percent("sfx") == 50
            assert settings.get_volume_percent("music") == 100

    def test_set_volume_percent_converts_correctly(self):
        """set_volume_percent should convert percentage to float."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            settings.set_volume_percent("master", 50)
            assert settings.master_volume == 0.5

            settings.set_volume_percent("sfx", 100)
            assert settings.sfx_volume == 1.0

            settings.set_volume_percent("music", 0)
            assert settings.music_volume == 0.0


class TestGameSettingsProperties:
    """Test GameSettings computed properties."""

    def test_audio_enabled_property(self):
        """audio_enabled should be True when master volume > 0."""
        with patch.object(GameSettings, "load_settings"):
            settings = GameSettings()

            settings.master_volume = 0.5
            assert settings.audio_enabled is True

            settings.master_volume = 0.0
            assert settings.audio_enabled is False

    def test_music_enabled_property(self):
        """music_enabled should require both master and music volume > 0."""
        with patch.object(GameSettings, "load_settings"):
            settings = GameSettings()

            # Both > 0
            settings.master_volume = 0.5
            settings.music_volume = 0.5
            assert settings.music_enabled is True

            # Master = 0
            settings.master_volume = 0.0
            settings.music_volume = 0.5
            assert settings.music_enabled is False

            # Music = 0
            settings.master_volume = 0.5
            settings.music_volume = 0.0
            assert settings.music_enabled is False

            # Both = 0
            settings.master_volume = 0.0
            settings.music_volume = 0.0
            assert settings.music_enabled is False


class TestGameSettingsGraphicsMode:
    """Test graphics mode setting."""

    def test_set_graphics_mode_accepts_valid_modes(self):
        """set_graphics_mode should accept 'glyph' and 'graphics'."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            settings.set_graphics_mode("glyph")
            assert settings.graphics_mode == "glyph"

            settings.set_graphics_mode("graphics")
            assert settings.graphics_mode == "graphics"

    def test_set_graphics_mode_accepts_ascii_for_backwards_compat(self):
        """set_graphics_mode should accept 'ascii' for backwards compatibility."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            settings.set_graphics_mode("ascii")
            # Should be migrated to 'glyph'
            assert settings.graphics_mode == "glyph"


class TestGameSettingsPersistence:
    """Test settings file save/load."""

    def test_create_default_settings_file_creates_valid_json(self):
        """_create_default_settings_file should create valid JSON."""
        with patch.object(GameSettings, "load_settings"):
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
                temp_file = f.name

            try:
                settings = GameSettings()
                settings.SETTINGS_FILE = temp_file
                settings._create_default_settings_file()

                # Verify file exists and contains valid JSON
                assert os.path.exists(temp_file)

                with open(temp_file) as f:
                    data = json.load(f)

                # Check it matches DEFAULTS
                assert data["master_volume"] == GameSettings.DEFAULTS["master_volume"]
                assert data["graphics_mode"] == GameSettings.DEFAULTS["graphics_mode"]

            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def test_load_settings_uses_defaults_when_file_missing(self):
        """load_settings should use in-memory defaults when file doesn't exist (no file creation)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "test_settings.json")

            with patch.object(GameSettings, "__init__", lambda x: None):
                settings = GameSettings()
                settings.SETTINGS_FILE = temp_file

                # Copy DEFAULTS for initialization
                for key, value in GameSettings.DEFAULTS.items():
                    setattr(settings, key, value if not isinstance(value, dict) else value.copy())

                settings.load_settings()

                # Should NOT have created the file (lazy file creation)
                assert not os.path.exists(temp_file)

                # Should still have default values in memory
                assert settings.master_volume == GameSettings.DEFAULTS["master_volume"]
                assert settings.graphics_mode == GameSettings.DEFAULTS["graphics_mode"]


class TestGameConfigLoading:
    """Test GameConfig JSON loading."""

    def test_game_config_has_default_constants(self):
        """GameConfig should have default constant values."""
        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0

    def test_game_config_loaded_has_required_values(self):
        """GameConfig loaded from JSON should have required values."""
        # This assumes game_rules.json exists and is valid
        GameConfig.load_from_json()

        # Check critical values are loaded
        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0
        assert GameConfig.DEFAULT_PLAYER_RAM > 0
        assert GameConfig.DEFAULT_PLAYER_CPU > 0
        assert GameConfig.MAX_HEAT > 0

    def test_game_config_viewport_dimensions_are_valid(self):
        """GameConfig viewport dimensions should be valid."""
        GameConfig.load_from_json()

        # Viewport should be positive (using default glyph mode)
        viewport_width = GameConfig.VIEWPORT_WIDTH()
        viewport_height = GameConfig.VIEWPORT_HEIGHT()

        assert viewport_width > 0
        assert viewport_height > 0

        # Both map and viewport should be positive and reasonable
        # Note: viewport CAN be larger than map (map gets centered in viewport)
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0

    def test_game_config_calculate_viewport_calculates_correctly(self):
        """VIEWPORT_WIDTH/HEIGHT should return valid dimensions in glyph mode."""
        GameConfig.load_from_json()

        # Calculate viewport using default glyph mode
        viewport_width = GameConfig.VIEWPORT_WIDTH()
        viewport_height = GameConfig.VIEWPORT_HEIGHT()

        # In glyph mode:
        # - viewport_width = SCREEN_WIDTH - SIDEBAR_WIDTH (game area width)
        # - viewport_height = SCREEN_HEIGHT - PANEL_HEIGHT - 1 (status bar at top)
        expected_width = GameConfig.GAME_AREA_WIDTH()
        expected_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1

        assert viewport_width == expected_width
        assert viewport_height == expected_height


class TestGameConfigErrorHandling:
    """Test GameConfig error handling."""

    def test_get_required_raises_on_missing_key(self):
        """_get_required should raise KeyError for missing config keys."""
        GameConfig._config_data = {"test": {"key": "value"}}

        with pytest.raises(KeyError):
            GameConfig._get_required("nonexistent.key")

    def test_get_required_returns_value_for_valid_key(self):
        """_get_required should return value for valid keys."""
        GameConfig._config_data = {"test": {"key": 42}}

        value = GameConfig._get_required("test.key")
        assert value == 42

    def test_get_required_handles_nested_keys(self):
        """_get_required should handle nested dictionary keys."""
        GameConfig._config_data = {"level1": {"level2": {"level3": "deep_value"}}}

        value = GameConfig._get_required("level1.level2.level3")
        assert value == "deep_value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
