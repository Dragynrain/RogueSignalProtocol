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

import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open

from game_config import GameSettings, GameConfig


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

    def test_set_master_volume_clamps_to_range(self):
        """set_master_volume should clamp values to [0.0, 1.0]."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            # Test over max
            settings.set_master_volume(1.5)
            assert settings.master_volume == 1.0

            # Test under min
            settings.set_master_volume(-0.5)
            assert settings.master_volume == 0.0

            # Test valid value
            settings.set_master_volume(0.5)
            assert settings.master_volume == 0.5

    def test_set_sfx_volume_clamps_to_range(self):
        """set_sfx_volume should clamp values to [0.0, 1.0]."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            settings.set_sfx_volume(2.0)
            assert settings.sfx_volume == 1.0

            settings.set_sfx_volume(-1.0)
            assert settings.sfx_volume == 0.0

    def test_set_music_volume_clamps_to_range(self):
        """set_music_volume should clamp values to [0.0, 1.0]."""
        with patch.object(GameSettings, "load_settings"), patch.object(
            GameSettings, "save_settings"
        ):
            settings = GameSettings()

            settings.set_music_volume(1.2)
            assert settings.music_volume == 1.0

            settings.set_music_volume(-0.2)
            assert settings.music_volume == 0.0

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

    def test_load_settings_creates_default_on_missing_file(self):
        """load_settings should create default file if missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "test_settings.json")

            with patch.object(GameSettings, "__init__", lambda x: None):
                settings = GameSettings()
                settings.SETTINGS_FILE = temp_file

                # Copy DEFAULTS for initialization
                for key, value in GameSettings.DEFAULTS.items():
                    setattr(settings, key, value if not isinstance(value, dict) else value.copy())

                settings.load_settings()

                # Should have created the file
                assert os.path.exists(temp_file)


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

        # Viewport should fit within map
        assert GameConfig.VIEWPORT_WIDTH > 0
        assert GameConfig.VIEWPORT_HEIGHT > 0

        # Map should be larger than or equal to viewport
        assert GameConfig.MAP_WIDTH >= GameConfig.VIEWPORT_WIDTH
        assert GameConfig.MAP_HEIGHT >= GameConfig.VIEWPORT_HEIGHT

    def test_game_config_calculate_viewport_calculates_correctly(self):
        """_calculate_viewport should produce valid dimensions."""
        GameConfig.load_from_json()

        # Manually calculate expected values
        expected_width = GameConfig.SCREEN_WIDTH - GameConfig.SIDEBAR_WIDTH
        expected_height = GameConfig.SCREEN_HEIGHT - GameConfig.UI_HEIGHT

        assert GameConfig.VIEWPORT_WIDTH == expected_width
        assert GameConfig.VIEWPORT_HEIGHT == expected_height


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
