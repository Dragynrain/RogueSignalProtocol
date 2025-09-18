#!/usr/bin/env python3
"""
Unit tests for game_config.py - Configuration and settings management.
Tests game configuration constants, settings persistence, and validation.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch, mock_open
from game_config import GameSettings, GameConfig, RoomGenerationConfig, GameBalance


class TestGameSettings:
    """Test GameSettings class for user settings management."""
    
    def test_default_settings_values(self):
        """Test that default settings have reasonable values."""
        settings = GameSettings()
        
        assert 0.0 <= settings.master_volume <= 1.0
        assert 0.0 <= settings.sfx_volume <= 1.0
        assert 0.0 <= settings.music_volume <= 1.0
        assert settings.graphics_mode in ["ascii", "graphics"]
    
    def test_volume_setting_validation(self):
        """Test volume setting with validation and clamping."""
        settings = GameSettings()
        
        # Test normal volume setting
        settings.set_master_volume(0.5)
        assert settings.master_volume == 0.5
        
        # Test volume clamping - above maximum
        settings.set_sfx_volume(1.5)
        assert settings.sfx_volume == 1.0
        
        # Test volume clamping - below minimum
        settings.set_music_volume(-0.2)
        assert settings.music_volume == 0.0
        
        # Test edge cases
        settings.set_master_volume(0.0)
        assert settings.master_volume == 0.0
        
        settings.set_master_volume(1.0)
        assert settings.master_volume == 1.0
    
    def test_graphics_mode_validation(self):
        """Test graphics mode setting with validation."""
        settings = GameSettings()
        
        # Test valid modes
        settings.set_graphics_mode("ascii")
        assert settings.graphics_mode == "ascii"
        
        settings.set_graphics_mode("graphics")
        assert settings.graphics_mode == "graphics"
        
        # Test invalid mode (should not change)
        original_mode = settings.graphics_mode
        settings.set_graphics_mode("invalid_mode")
        assert settings.graphics_mode == original_mode
    
    def test_volume_percentage_conversion(self):
        """Test conversion between volume (0.0-1.0) and percentage (0-100)."""
        settings = GameSettings()
        
        # Test getting percentage
        settings.master_volume = 0.75
        assert settings.get_volume_percent("master") == 75
        
        settings.sfx_volume = 0.0
        assert settings.get_volume_percent("sfx") == 0
        
        settings.music_volume = 1.0
        assert settings.get_volume_percent("music") == 100
        
        # Test setting from percentage
        settings.set_volume_percent("master", 50)
        assert settings.master_volume == 0.5
        
        settings.set_volume_percent("sfx", 80)
        assert settings.sfx_volume == 0.8
        
        settings.set_volume_percent("music", 0)
        assert settings.music_volume == 0.0
        
        # Test invalid volume type
        assert settings.get_volume_percent("invalid") == 0
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_settings_save_and_load(self, mock_exists, mock_file):
        """Test settings persistence to file."""
        # Setup mock for save operation
        mock_exists.return_value = False
        
        settings = GameSettings()
        settings.master_volume = 0.6
        settings.sfx_volume = 0.9
        settings.music_volume = 0.3
        settings.graphics_mode = "graphics"
        
        settings.save_settings()
        
        # Verify save was called with correct data
        mock_file.assert_called_with(GameSettings.SETTINGS_FILE, 'w')
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        
        # Parse the written JSON to verify correctness
        saved_data = json.loads(written_content)
        assert saved_data["master_volume"] == 0.6
        assert saved_data["sfx_volume"] == 0.9
        assert saved_data["music_volume"] == 0.3
        assert saved_data["graphics_mode"] == "graphics"
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"master_volume": 0.4, "sfx_volume": 0.7, "music_volume": 0.2, "graphics_mode": "ascii"}')
    @patch("os.path.exists", return_value=True)
    def test_settings_load_from_file(self, mock_exists, mock_file):
        """Test loading settings from existing file."""
        settings = GameSettings()
        
        assert settings.master_volume == 0.4
        assert settings.sfx_volume == 0.7
        assert settings.music_volume == 0.2
        assert settings.graphics_mode == "ascii"
    
    @patch("builtins.open", new_callable=mock_open, read_data='')
    @patch("os.path.exists", return_value=True)
    def test_empty_settings_file_handling(self, mock_exists, mock_file):
        """Test handling of empty settings file."""
        with patch.object(GameSettings, '_create_default_settings_file') as mock_create:
            settings = GameSettings()
            mock_create.assert_called_once()
    
    @patch("builtins.open", new_callable=mock_open, read_data='invalid json content')
    @patch("os.path.exists", return_value=True)
    def test_corrupted_settings_file_handling(self, mock_exists, mock_file):
        """Test handling of corrupted settings file."""
        with patch.object(GameSettings, '_create_default_settings_file') as mock_create:
            settings = GameSettings()
            mock_create.assert_called_once()
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"master_volume": 0.5}')
    @patch("os.path.exists", return_value=True)
    def test_partial_settings_file(self, mock_exists, mock_file):
        """Test loading settings file with only partial data."""
        settings = GameSettings()
        
        # Should load the existing value
        assert settings.master_volume == 0.5
        
        # Should use defaults for missing values
        assert settings.sfx_volume == 0.8  # Default value
        assert settings.music_volume == 0.5  # Default value
        assert settings.graphics_mode == "ascii"  # Default value


class TestGameConfig:
    """Test GameConfig class for game constants and configuration."""
    
    def test_screen_dimensions_are_positive(self):
        """Test that screen dimensions are positive integers."""
        assert GameConfig.SCREEN_WIDTH > 0
        assert GameConfig.SCREEN_HEIGHT > 0
        assert isinstance(GameConfig.SCREEN_WIDTH, int)
        assert isinstance(GameConfig.SCREEN_HEIGHT, int)
    
    def test_map_dimensions_are_positive(self):
        """Test that map dimensions are positive integers."""
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0
        assert isinstance(GameConfig.MAP_WIDTH, int)
        assert isinstance(GameConfig.MAP_HEIGHT, int)
    
    def test_ui_layout_constants(self):
        """Test UI layout constants are reasonable."""
        assert GameConfig.UI_HEIGHT > 0
        assert GameConfig.SIDEBAR_WIDTH > 0
        assert GameConfig.LOG_WIDTH > 0
        assert GameConfig.PANEL_HEIGHT > 0
        
        # UI should fit within screen
        assert GameConfig.UI_HEIGHT <= GameConfig.SCREEN_HEIGHT
        assert GameConfig.SIDEBAR_WIDTH <= GameConfig.SCREEN_WIDTH
        assert GameConfig.LOG_WIDTH <= GameConfig.SCREEN_WIDTH
        assert GameConfig.PANEL_HEIGHT <= GameConfig.SCREEN_HEIGHT
    
    def test_calculated_layout_properties(self):
        """Test calculated layout properties."""
        game_area_width = GameConfig.GAME_AREA_WIDTH()
        panel_y = GameConfig.PANEL_Y()
        
        assert game_area_width > 0
        assert game_area_width == GameConfig.SCREEN_WIDTH - GameConfig.LOG_WIDTH
        
        assert panel_y >= 0
        assert panel_y == GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT
        assert panel_y < GameConfig.SCREEN_HEIGHT
    
    def test_game_parameters_are_reasonable(self):
        """Test that game parameters have reasonable values."""
        assert GameConfig.DEFAULT_PLAYER_RAM > 0
        assert GameConfig.DEFAULT_PLAYER_CPU > 0
        assert GameConfig.MAX_HEAT > 0
        assert GameConfig.MAX_DETECTION > 0
        assert GameConfig.DETECTION_REDUCTION_ON_LEVEL >= 0
        assert GameConfig.DEFAULT_VISION_RANGE > 0
        assert GameConfig.MAX_SAVE_ATTEMPTS > 0
        
        # Capacity limits should be reasonable
        assert GameConfig.max_ram_capacity >= GameConfig.DEFAULT_PLAYER_RAM
        assert GameConfig.max_cpu_capacity >= GameConfig.DEFAULT_PLAYER_CPU
    
    def test_message_display_constants(self):
        """Test message display constants are non-negative."""
        message_constants = [
            GameConfig.MESSAGE_CENTER_OFFSET_LARGE,
            GameConfig.MESSAGE_CENTER_OFFSET_MEDIUM,
            GameConfig.MESSAGE_CENTER_OFFSET_SMALL,
            GameConfig.MESSAGE_CENTER_OFFSET_TINY,
            GameConfig.MESSAGE_LINE_SPACING,
            GameConfig.MESSAGE_BUTTON_SPACING
        ]
        
        for constant in message_constants:
            assert constant >= 0
            assert isinstance(constant, int)
    
    def test_vision_mechanics_constants(self):
        """Test vision mechanics constants are reasonable."""
        assert GameConfig.adjacent_visibility_threshold > 0
        assert GameConfig.shadow_vision_reduction_factor > 0
        assert GameConfig.adjacent_threshold > 0
        
        # Should be floats for precise calculations
        assert isinstance(GameConfig.adjacent_visibility_threshold, float)
        assert isinstance(GameConfig.shadow_vision_reduction_factor, (int, float))
        assert isinstance(GameConfig.adjacent_threshold, float)
    
    def test_virus_constants(self):
        """Test virus system constants."""
        assert GameConfig.virus_base_duration > 0
        assert GameConfig.virus_max_duration >= GameConfig.virus_base_duration
        assert GameConfig.VIRUS_DAMAGE_PER_TURN > 0
    
    def test_enemy_constants(self):
        """Test enemy-related constants."""
        assert GameConfig.NEARBY_ENEMY_ALERT_RADIUS > 0
        assert isinstance(GameConfig.NEARBY_ENEMY_ALERT_RADIUS, int)
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"display": {"screen_width": 100, "screen_height": 60, "map_width": 70, "map_height": 70}}')
    @patch("os.path.exists", return_value=True)
    def test_load_from_json(self, mock_exists, mock_file):
        """Test loading configuration from JSON file."""
        # Reset config data
        GameConfig._config_data = None
        
        GameConfig.load_from_json()
        
        assert GameConfig.SCREEN_WIDTH == 100
        assert GameConfig.SCREEN_HEIGHT == 60
        assert GameConfig.MAP_WIDTH == 70
        assert GameConfig.MAP_HEIGHT == 70
    
    def test_get_config_value(self):
        """Test getting configuration values by key."""
        # Mock config data
        GameConfig._config_data = {
            "display": {
                "screen_width": 90
            },
            "gameplay": {
                "difficulty": "normal"
            }
        }
        
        # Test existing nested key
        assert GameConfig.get("display.screen_width") == 90
        assert GameConfig.get("gameplay.difficulty") == "normal"
        
        # Test non-existing key with default
        assert GameConfig.get("non.existing.key", "default") == "default"
        
        # Test non-existing key without default
        assert GameConfig.get("non.existing.key") is None


class TestRoomGenerationConfig:
    """Test RoomGenerationConfig class for level generation settings."""
    
    def test_room_generation_constants(self):
        """Test that room generation constants are reasonable."""
        assert RoomGenerationConfig.MIN_ROOMS_BASE > 0
        assert RoomGenerationConfig.ROOM_LEVEL_MULTIPLIER >= 0
        assert RoomGenerationConfig.MAX_ROOMS >= RoomGenerationConfig.MIN_ROOMS_BASE
        assert RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS > 0
        
        assert RoomGenerationConfig.MIN_ROOM_SIZE > 0
        assert RoomGenerationConfig.MAX_ROOM_SIZE >= RoomGenerationConfig.MIN_ROOM_SIZE
        assert RoomGenerationConfig.ROOM_PADDING >= 0
    
    def test_special_tile_placement_constants(self):
        """Test special tile placement constants are non-negative."""
        tile_constants = [
            RoomGenerationConfig.COOLING_NODES_PER_LEVEL,
            RoomGenerationConfig.CPU_NODES_PER_LEVEL,
            RoomGenerationConfig.GHOST_NODES_PER_LEVEL,
            RoomGenerationConfig.DATA_PATCHES_PER_LEVEL,
            RoomGenerationConfig.EXPLOIT_PICKUPS_PER_LEVEL,
            RoomGenerationConfig.PERMANENT_UPGRADES_PER_LEVEL
        ]
        
        for constant in tile_constants:
            assert constant >= 0
            assert isinstance(constant, int)
    
    def test_room_generation_config_initialization(self):
        """Test RoomGenerationConfig initialization."""
        config = RoomGenerationConfig()
        
        assert config.min_room_size == RoomGenerationConfig.MIN_ROOM_SIZE
        assert config.max_room_size == RoomGenerationConfig.MAX_ROOM_SIZE
        assert config.max_rooms == RoomGenerationConfig.MAX_ROOMS
        assert config.room_attempts == RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS


class TestGameBalance:
    """Test GameBalance class for game balance constants."""
    
    def test_heat_management_constants(self):
        """Test heat management constants are reasonable."""
        assert GameBalance.HEAT_REDUCTION_NORMAL > 0
        assert GameBalance.HEAT_REDUCTION_BOOSTED >= GameBalance.HEAT_REDUCTION_NORMAL
        assert GameBalance.DETECTION_INCREASE_INTERVAL > 0
        assert GameBalance.DETECTION_INCREASE_AMOUNT > 0
    
    def test_node_effect_constants(self):
        """Test node effect constants are reasonable."""
        assert GameBalance.COOLING_NODE_EFFECT > 0
        assert 0.0 < GameBalance.GHOST_NODE_DETECTION_REDUCTION_PERCENT <= 100.0
        assert GameBalance.CPU_RECOVERY_AMOUNT > 0
    
    def test_combat_reward_constants(self):
        """Test combat reward constants are reasonable."""
        assert GameBalance.ENEMY_ELIMINATION_CPU_REWARD > 0
    
    def test_code_patch_effects(self):
        """Test code patch effect constants."""
        assert GameBalance.CPU_RESTORE_MIN > 0
        assert GameBalance.CPU_RESTORE_MAX >= GameBalance.CPU_RESTORE_MIN
        assert GameBalance.HEAT_REDUCTION_INSTANT > 0
    
    def test_enemy_detection_constants(self):
        """Test enemy detection constants."""
        assert GameBalance.ADMIN_DETECTION_INITIAL > 0
        assert GameBalance.ADMIN_DETECTION_CONTINUOUS > 0
        assert GameBalance.ENEMY_DETECTION_ALERT_TO_HOSTILE > 0
        assert GameBalance.ENEMY_DETECTION_CONTINUOUS_HOSTILE > 0
        assert GameBalance.ENEMY_MEMORY_TURNS > 0
    
    def test_exploit_cpu_costs(self):
        """Test exploit CPU cost calculations."""
        # Test known exploits
        known_exploits = [
            "shadow_step", "buffer_overflow", "code_injection", 
            "system_crash", "threat_scan", "log_wiper", 
            "antivirus", "emp_burst", "memory_leak"
        ]
        
        for exploit_name in known_exploits:
            cpu_cost = GameBalance.get_exploit_cpu_cost(exploit_name)
            assert 0 < cpu_cost <= 50, f"{exploit_name} CPU cost {cpu_cost} out of range"
        
        # Test unknown exploit returns default
        unknown_cost = GameBalance.get_exploit_cpu_cost("unknown_exploit")
        assert unknown_cost == 10
    
    def test_difficulty_multipliers(self):
        """Test enemy difficulty multipliers."""
        difficulties = ["easy", "normal", "hard", "nightmare"]
        
        for difficulty in difficulties:
            multiplier = GameBalance.get_enemy_difficulty_multiplier(difficulty)
            assert 0.5 <= multiplier <= 2.0, f"{difficulty} multiplier {multiplier} out of range"
        
        # Test multiplier ordering
        easy = GameBalance.get_enemy_difficulty_multiplier("easy")
        normal = GameBalance.get_enemy_difficulty_multiplier("normal")
        hard = GameBalance.get_enemy_difficulty_multiplier("hard")
        nightmare = GameBalance.get_enemy_difficulty_multiplier("nightmare")
        
        assert easy < normal < hard < nightmare
        
        # Test unknown difficulty
        unknown_mult = GameBalance.get_enemy_difficulty_multiplier("unknown")
        assert unknown_mult == 1.0


class TestConfigurationIntegrity:
    """Test overall configuration integrity and consistency."""
    
    def test_screen_and_map_size_relationship(self):
        """Test that map size is reasonable relative to screen size."""
        # Map should be reasonably sized relative to screen
        # Note: Map can be smaller than screen for smaller games
        assert GameConfig.MAP_WIDTH > 0
        assert GameConfig.MAP_HEIGHT > 0
        
        # But not excessively large compared to screen
        assert GameConfig.MAP_WIDTH <= GameConfig.SCREEN_WIDTH * 3
        assert GameConfig.MAP_HEIGHT <= GameConfig.SCREEN_HEIGHT * 3
    
    def test_ui_layout_fits_screen(self):
        """Test that UI layout components fit within screen bounds."""
        # Panel should fit at bottom of screen
        assert GameConfig.PANEL_Y() >= 0
        assert GameConfig.PANEL_Y() + GameConfig.PANEL_HEIGHT <= GameConfig.SCREEN_HEIGHT
        
        # Game area should fit within screen
        assert GameConfig.GAME_AREA_WIDTH() > 0
        assert GameConfig.GAME_AREA_WIDTH() <= GameConfig.SCREEN_WIDTH
    
    def test_player_defaults_within_limits(self):
        """Test that player defaults are within capacity limits."""
        assert GameConfig.DEFAULT_PLAYER_RAM <= GameConfig.max_ram_capacity
        assert GameConfig.DEFAULT_PLAYER_CPU <= GameConfig.max_cpu_capacity
    
    def test_room_generation_constraints(self):
        """Test that room generation constraints are consistent."""
        config = RoomGenerationConfig()
        
        # Room size constraints should be reasonable for map size
        max_room_area = config.max_room_size ** 2
        map_area = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
        
        assert max_room_area < map_area / 4, "Maximum room size too large for map"
        
        # Should be able to fit minimum number of rooms
        min_total_room_area = config.MIN_ROOMS_BASE * (config.min_room_size ** 2)
        assert min_total_room_area < map_area / 2, "Too many minimum rooms for map size"
    
    def test_balance_constants_consistency(self):
        """Test that balance constants are internally consistent."""
        # Heat reduction amounts should be reasonable
        assert GameBalance.HEAT_REDUCTION_NORMAL <= GameConfig.MAX_HEAT / 10
        assert GameBalance.HEAT_REDUCTION_INSTANT <= GameConfig.MAX_HEAT
        
        # Detection thresholds should exist and be reasonable
        assert 0 < GameConfig.DETECTION_REDUCTION_ON_LEVEL <= GameConfig.MAX_DETECTION
        
        # Virus duration should be reasonable (using GameConfig constants)
        assert GameConfig.virus_base_duration <= GameConfig.virus_max_duration
        assert GameConfig.virus_max_duration <= 20  # Not too long to be annoying
    
    def test_constant_types_are_appropriate(self):
        """Test that constants have appropriate types."""
        # Integer constants
        int_constants = [
            GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT,
            GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT,
            GameConfig.DEFAULT_PLAYER_RAM, GameConfig.DEFAULT_PLAYER_CPU,
            GameConfig.MAX_HEAT, GameConfig.MAX_DETECTION
        ]
        
        for constant in int_constants:
            assert isinstance(constant, int), f"Constant should be int: {constant}"
        
        # Float constants that need precision
        float_constants = [
            GameConfig.adjacent_visibility_threshold,
            GameConfig.adjacent_threshold,
            GameBalance.GHOST_NODE_DETECTION_REDUCTION_PERCENT
        ]
        
        for constant in float_constants:
            assert isinstance(constant, (int, float)), f"Constant should be numeric: {constant}"