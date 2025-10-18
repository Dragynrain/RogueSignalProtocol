#!/usr/bin/env python3
"""
Game configuration and settings management.
Extracted from RogueSignalProtocol.py for better organization.
"""

import json
import logging
import os
from typing import Dict, Any
from data_loading import DataLoader




class GameSettings:
    """Manages game settings with persistent storage."""
    
    SETTINGS_FILE = "user_settings.json"
    
    def __init__(self):
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.music_volume = 0.5
        self.graphics_mode = "glyph"  # "glyph" (CP437 characters) or "graphics" (PNG sprites)
        self.dialogue_preferences = {}  # Stores user preferences for dialogue visibility
        self.load_settings()
    
    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                # Read file content first to check for corruption
                with open(self.SETTINGS_FILE, 'r') as f:
                    content = f.read().strip()
                
                # Check if file is empty or contains only whitespace
                if not content:
                    logging.warning("Settings file is empty, using defaults")
                    self._create_default_settings_file()
                    return
                
                # Try to parse JSON
                try:
                    settings_data = json.loads(content)
                    self.master_volume = settings_data.get("master_volume", 0.7)
                    self.sfx_volume = settings_data.get("sfx_volume", 0.8)
                    self.music_volume = settings_data.get("music_volume", 0.5)
                    self.graphics_mode = settings_data.get("graphics_mode", "glyph")

                    # Migrate old "ascii" setting to "glyph"
                    if self.graphics_mode == "ascii":
                        self.graphics_mode = "glyph"
                        # Save immediately to persist the migration
                        self.save_settings()
                        logging.info("Migrated graphics_mode from 'ascii' to 'glyph'")

                    # Load dialogue preferences with default empty dict
                    self.dialogue_preferences = settings_data.get("dialogue_preferences", {})
                except json.JSONDecodeError as e:
                    logging.warning(f"Settings file corrupted (JSON decode error: {e}), recreating with defaults")
                    self._create_default_settings_file()
        except Exception as e:
            import traceback
            logging.warning(f"Failed to load settings: {e}")
            logging.debug(traceback.format_exc())
            self._create_default_settings_file()
    
    def _create_default_settings_file(self) -> None:
        """Create a default settings file."""
        try:
            default_settings = {
                "master_volume": 0.7,
                "sfx_volume": 0.8,
                "music_volume": 0.5,
                "graphics_mode": "glyph",
                "dialogue_preferences": {}
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(default_settings, f, indent=2)
            logging.info("Created default settings file")
        except Exception as e:
            logging.error(f"Failed to create default settings file: {e}")
    
    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = {
                "master_volume": self.master_volume,
                "sfx_volume": self.sfx_volume,
                "music_volume": self.music_volume,
                "graphics_mode": self.graphics_mode,
                "dialogue_preferences": self.dialogue_preferences
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            import traceback
            logging.error(f"Failed to save settings: {e}")
            logging.debug(traceback.format_exc())
    
    def _set_volume_attribute(self, volume_type: str, volume: float):
        """Generic volume setter for any volume type."""
        from game_entities import clamp
        setattr(self, f"{volume_type}_volume", clamp(volume, 0.0, 1.0))
        self.save_settings()

    def set_master_volume(self, volume: float):
        self._set_volume_attribute("master", volume)

    def set_sfx_volume(self, volume: float):
        self._set_volume_attribute("sfx", volume)

    def set_music_volume(self, volume: float):
        self._set_volume_attribute("music", volume)
    
    def set_graphics_mode(self, mode: str):
        """Set graphics mode ('glyph' for CP437 characters or 'graphics' for PNG sprites)"""
        if mode in ["glyph", "graphics", "ascii"]:  # Accept "ascii" for backwards compatibility
            # Migrate "ascii" to "glyph" if provided
            if mode == "ascii":
                mode = "glyph"
                logging.info("Migrated graphics_mode from 'ascii' to 'glyph'")
            self.graphics_mode = mode
            self.save_settings()
    
    def get_volume_percent(self, volume_type: str) -> int:
        """Get volume as percentage (0-100)"""
        volume_map = {"master": self.master_volume, "sfx": self.sfx_volume, "music": self.music_volume}
        return int(volume_map.get(volume_type, 0) * 100)

    def set_volume_percent(self, volume_type: str, percent: int):
        """Set volume from percentage (0-100)"""
        setter_map = {"master": self.set_master_volume, "sfx": self.set_sfx_volume, "music": self.set_music_volume}
        if volume_type in setter_map:
            setter_map[volume_type](percent / 100.0)


class GameConfig:
    """Game configuration constants and settings."""

    _config_data = None

    # Initialize class attributes with defaults first
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 50
    MAP_HEIGHT = 50
    UI_HEIGHT = 10
    SIDEBAR_WIDTH = 25
    LOG_WIDTH = 25
    PANEL_HEIGHT = 5
    DEFAULT_PLAYER_RAM = 8
    DEFAULT_PLAYER_CPU = 100
    MAX_HEAT = 100
    MAX_TRACE_LEVEL = 100
    DETECTION_REDUCTION_ON_LEVEL = 50
    DUNGEON_SEED_RANGE = 1000000
    DEFAULT_VISION_RANGE = 10
    MAX_SAVE_ATTEMPTS = 3
    NEARBY_ENEMY_ALERT_RADIUS = 8
    VIRUS_DAMAGE_PER_TURN = 3
    DEFAULT_FADE_TIME = 2000
    MESSAGE_CENTER_OFFSET_LARGE = 15
    MESSAGE_CENTER_OFFSET_MEDIUM = 12
    MESSAGE_CENTER_OFFSET_SMALL = 8
    MESSAGE_CENTER_OFFSET_TINY = 10
    MESSAGE_LINE_SPACING = 1
    MESSAGE_BUTTON_SPACING = 3

    @classmethod
    def load_from_json(cls):
        """Load configuration from JSON file - FAILS if required values missing."""
        try:
            with open('game_rules.json', 'r', encoding='utf-8') as f:
                cls._config_data = json.load(f)

            # Update class attributes - NO FALLBACKS, fail if missing
            cls.SCREEN_WIDTH = cls._get_required('display.screen_width')
            cls.SCREEN_HEIGHT = cls._get_required('display.screen_height')
            cls.MAP_WIDTH = cls._get_required('display.map_width')
            cls.MAP_HEIGHT = cls._get_required('display.map_height')
            cls.UI_HEIGHT = cls._get_required('display.ui_height')
            cls.SIDEBAR_WIDTH = cls._get_required('display.sidebar_width')
            cls.LOG_WIDTH = cls._get_required('display.log_width')
            cls.PANEL_HEIGHT = cls._get_required('display.panel_height')
            cls.DEFAULT_PLAYER_RAM = cls._get_required('gameplay.default_player_ram')
            cls.DEFAULT_PLAYER_CPU = cls._get_required('gameplay.default_player_cpu')
            cls.MAX_HEAT = cls._get_required('gameplay.max_heat')
            cls.MAX_TRACE_LEVEL = cls._get_required('gameplay.max_trace_level')
            cls.DETECTION_REDUCTION_ON_LEVEL = cls._get_required('gameplay.trace_reduction_on_level')
            cls.DUNGEON_SEED_RANGE = cls._get_required('gameplay.dungeon_seed_range')
            cls.DEFAULT_VISION_RANGE = cls._get_required('gameplay.default_vision_range')
            cls.MAX_SAVE_ATTEMPTS = cls._get_required('gameplay.max_save_attempts')
            cls.NEARBY_ENEMY_ALERT_RADIUS = cls._get_required('gameplay.nearby_enemy_alert_radius')
            cls.VIRUS_DAMAGE_PER_TURN = cls._get_required('gameplay.virus_damage_per_turn')
            cls.DEFAULT_FADE_TIME = cls._get_required('audio.default_fade_time')
            cls.MESSAGE_CENTER_OFFSET_LARGE = cls._get_required('ui.message_center_offset_large')
            cls.MESSAGE_CENTER_OFFSET_MEDIUM = cls._get_required('ui.message_center_offset_medium')
            cls.MESSAGE_CENTER_OFFSET_SMALL = cls._get_required('ui.message_center_offset_small')
            cls.MESSAGE_CENTER_OFFSET_TINY = cls._get_required('ui.message_center_offset_tiny')
            cls.MESSAGE_LINE_SPACING = cls._get_required('ui.message_line_spacing')
            cls.MESSAGE_BUTTON_SPACING = cls._get_required('ui.message_button_spacing')

        except FileNotFoundError as e:
            error_msg = f"CRITICAL CONFIG ERROR: game_rules.json not found"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise FileNotFoundError(f"Required file game_rules.json is missing") from e
        except json.JSONDecodeError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in game_rules.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise json.JSONDecodeError(f"game_rules.json contains invalid JSON", e.doc, e.pos) from e
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Missing required config value in game_rules.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            if cls._config_data:
                logging.error(f"Available top-level sections: {list(cls._config_data.keys())}")
            raise KeyError(f"Required configuration value missing from game_rules.json: {e}") from e

    @classmethod
    def _ensure_loaded(cls):
        """Ensure config data is loaded."""
        if cls._config_data is None:
            cls.load_from_json()

    # Calculated layout properties
    @classmethod
    def GAME_AREA_WIDTH(cls):
        """Calculate game area width (screen width minus log width)."""
        cls._ensure_loaded()
        return cls.SCREEN_WIDTH - cls.LOG_WIDTH

    @classmethod
    def PANEL_Y(cls):
        """Calculate panel Y position (screen height minus panel height)."""
        cls._ensure_loaded()
        return cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT

    @classmethod
    def VIEWPORT_WIDTH(cls, graphics_mode: str = "glyph"):
        """
        Calculate viewport width (visible tiles) based on rendering mode.

        In graphics mode, viewport is smaller to make sprites appear larger.
        In glyph mode, viewport fills the full game area.

        Args:
            graphics_mode: "graphics" or "glyph"

        Returns:
            Number of tiles visible horizontally
        """
        cls._ensure_loaded()
        game_area_width = cls.SCREEN_WIDTH - cls.LOG_WIDTH

        if graphics_mode == "graphics":
            # Half size viewport for graphics mode (larger sprites)
            return game_area_width // 2
        else:
            # Full viewport for glyph mode
            return game_area_width

    @classmethod
    def VIEWPORT_HEIGHT(cls, graphics_mode: str = "glyph"):
        """
        Calculate viewport height (visible tiles) based on rendering mode.

        In graphics mode, viewport is smaller to make sprites appear larger.
        In glyph mode, viewport fills the full game area.

        Args:
            graphics_mode: "graphics" or "glyph"

        Returns:
            Number of tiles visible vertically (excluding top status bar)
        """
        cls._ensure_loaded()
        viewable_height = cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT - 1

        if graphics_mode == "graphics":
            # Half size viewport for graphics mode (larger sprites)
            return viewable_height // 2
        else:
            # Full viewport for glyph mode
            return viewable_height
    
    @classmethod
    def _get_required(cls, key: str):
        """Get required configuration value - raises KeyError if missing."""
        if cls._config_data is None:
            raise RuntimeError("Config data not loaded - call load_from_json first")

        keys = key.split('.')
        value = cls._config_data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError) as e:
            error_msg = f"CRITICAL CONFIG ERROR: Required key '{key}' not found in game_rules.json"
            logging.error(error_msg)

            # Provide helpful debug info
            partial_keys = []
            partial_value = cls._config_data
            for k in keys:
                partial_keys.append(k)
                try:
                    partial_value = partial_value[k]
                except (KeyError, TypeError):
                    break

            if partial_keys:
                path_str = '.'.join(partial_keys[:-1]) if len(partial_keys) > 1 else "root"
                if isinstance(partial_value, dict):
                    logging.error(f"Available keys at '{path_str}': {list(partial_value.keys())}")
                else:
                    logging.error(f"Value at '{path_str}' is {type(partial_value).__name__}, not a dict")

            raise KeyError(f"Required config key missing: {key}") from e

    @classmethod
    def get(cls, key: str, default=None):
        """Get configuration value by key with optional default (use sparingly)."""
        if cls._config_data is None:
            cls.load_from_json()

        if cls._config_data:
            keys = key.split('.')
            value = cls._config_data
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass

        return default
    
    @classmethod
    def get_network_configs(cls) -> Dict[int, Dict[str, Any]]:
        """Get network configurations from game data."""
        game_data = DataLoader.load_game_data()
        configs = game_data["network_configs"]
        return {int(k): v for k, v in configs.items()}
    
    @classmethod
    def NETWORK_CONFIGS(cls) -> Dict[int, Dict[str, Any]]:
        """Get network configurations from game data."""
        return cls.get_network_configs()


class RoomGenerationConfig:
    """Configuration for procedural room generation."""

    # Set class attributes with defaults
    MIN_ROOMS_BASE = 12
    ROOM_LEVEL_MULTIPLIER = 3
    MAX_ROOMS = 20
    MAX_PLACEMENT_ATTEMPTS = 400
    MIN_ROOM_SIZE = 3
    MAX_ROOM_SIZE = 8
    ROOM_PADDING = 1
    COOLING_NODES_PER_LEVEL = 3
    CPU_NODES_PER_LEVEL = 2
    GHOST_NODES_PER_LEVEL = 2
    CODE_HACKS_PER_LEVEL = 4
    EXPLOIT_PICKUPS_PER_LEVEL = 3
    PERMANENT_UPGRADES_PER_LEVEL = 1

    @classmethod
    def load_from_json(cls):
        """Load room generation config from JSON - NO FALLBACKS."""
        cls.MIN_ROOMS_BASE = GameConfig._get_required('room_generation.min_rooms_base')
        cls.ROOM_LEVEL_MULTIPLIER = GameConfig._get_required('room_generation.room_level_multiplier')
        cls.MAX_ROOMS = GameConfig._get_required('room_generation.max_rooms')
        cls.MAX_PLACEMENT_ATTEMPTS = GameConfig._get_required('room_generation.max_placement_attempts')
        cls.MIN_ROOM_SIZE = GameConfig._get_required('room_generation.min_room_size')
        cls.MAX_ROOM_SIZE = GameConfig._get_required('room_generation.max_room_size')
        cls.ROOM_PADDING = GameConfig._get_required('room_generation.room_padding')
        cls.COOLING_NODES_PER_LEVEL = GameConfig._get_required('room_generation.cooling_nodes_per_level')
        cls.CPU_NODES_PER_LEVEL = GameConfig._get_required('room_generation.cpu_nodes_per_level')
        cls.GHOST_NODES_PER_LEVEL = GameConfig._get_required('room_generation.ghost_nodes_per_level')
        cls.CODE_HACKS_PER_LEVEL = GameConfig._get_required('room_generation.code_hacks_per_level')
        cls.EXPLOIT_PICKUPS_PER_LEVEL = GameConfig._get_required('room_generation.exploit_pickups_per_level')
        cls.PERMANENT_UPGRADES_PER_LEVEL = GameConfig._get_required('room_generation.permanent_upgrades_per_level')

    def __init__(self):
        self.min_room_size = self.MIN_ROOM_SIZE
        self.max_room_size = self.MAX_ROOM_SIZE
        self.max_rooms = self.MAX_ROOMS
        self.room_attempts = self.MAX_PLACEMENT_ATTEMPTS


class GameBalance:
    """Game balance configuration."""

    # Set class attributes with defaults
    HEAT_REDUCTION_NORMAL = 2
    HEAT_REDUCTION_BOOSTED = 3
    TRACE_INCREASE_INTERVAL = 25
    TRACE_INCREASE_AMOUNT = 1
    COOLING_NODE_EFFECT = 20
    GHOST_NODE_DETECTION_REDUCTION_PERCENT = 20.0
    CPU_RECOVERY_AMOUNT = 20
    ENEMY_ELIMINATION_CPU_REWARD = 5
    CPU_RESTORE_MIN = 30
    CPU_RESTORE_MAX = 40
    HEAT_REDUCTION_INSTANT = 40
    ADJACENT_DISTANCE_THRESHOLD = 1.5
    PATROL_STUCK_THRESHOLD = 3
    PATHFINDING_TIMEOUT_ATTEMPTS = 100
    ENHANCED_VISION_BONUS = 2
    SHADOW_VISION_REDUCTION_FACTOR = 3
    ENEMY_TRACE_ALERT_TO_HOSTILE = 3
    ENEMY_TRACE_CONTINUOUS_HOSTILE = 0.3
    ENEMY_MEMORY_TURNS = 20

    @classmethod
    def load_from_json(cls):
        """Load balance config from JSON - NO FALLBACKS."""
        cls.HEAT_REDUCTION_NORMAL = GameConfig._get_required('balance.heat_reduction_normal')
        cls.HEAT_REDUCTION_BOOSTED = GameConfig._get_required('balance.heat_reduction_boosted')
        cls.TRACE_INCREASE_INTERVAL = GameConfig._get_required('balance.trace_increase_interval')
        cls.TRACE_INCREASE_AMOUNT = GameConfig._get_required('balance.trace_increase_amount')
        cls.COOLING_NODE_EFFECT = GameConfig._get_required('balance.cooling_node_effect')
        cls.GHOST_NODE_DETECTION_REDUCTION_PERCENT = GameConfig._get_required('balance.ghost_node_trace_reduction_percent')
        cls.CPU_RECOVERY_AMOUNT = GameConfig._get_required('balance.cpu_recovery_amount')
        cls.ENEMY_ELIMINATION_CPU_REWARD = GameConfig._get_required('balance.enemy_elimination_cpu_reward')
        cls.CPU_RESTORE_MIN = GameConfig._get_required('balance.cpu_restore_min')
        cls.CPU_RESTORE_MAX = GameConfig._get_required('balance.cpu_restore_max')
        cls.HEAT_REDUCTION_INSTANT = GameConfig._get_required('balance.heat_reduction_instant')
        cls.ADJACENT_DISTANCE_THRESHOLD = GameConfig._get_required('balance.adjacent_distance_threshold')
        cls.PATROL_STUCK_THRESHOLD = GameConfig._get_required('balance.patrol_stuck_threshold')
        cls.PATHFINDING_TIMEOUT_ATTEMPTS = GameConfig._get_required('balance.pathfinding_timeout_attempts')
        cls.ENHANCED_VISION_BONUS = GameConfig._get_required('balance.enhanced_vision_bonus')
        cls.SHADOW_VISION_REDUCTION_FACTOR = GameConfig._get_required('balance.shadow_vision_reduction_factor')
        cls.ENEMY_TRACE_ALERT_TO_HOSTILE = GameConfig._get_required('balance.ai_behavior.enemy_trace_alert_to_hostile')
        cls.ENEMY_TRACE_CONTINUOUS_HOSTILE = GameConfig._get_required('balance.ai_behavior.enemy_trace_continuous_hostile')
        cls.ENEMY_MEMORY_TURNS = GameConfig._get_required('balance.enemy_memory_turns')

    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies - FAILS if not found."""
        from data_loading import DataLoader
        game_data = DataLoader.load_game_data()
        try:
            multipliers = game_data['difficulty_multipliers']
            return multipliers[difficulty]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Difficulty '{difficulty}' not found in game_content.json difficulty_multipliers"
            logging.error(error_msg)
            if 'difficulty_multipliers' in game_data:
                logging.error(f"Available difficulties: {list(game_data['difficulty_multipliers'].keys())}")
            else:
                logging.error(f"'difficulty_multipliers' section missing from game_content.json")
                logging.error(f"Available sections: {list(game_data.keys())}")
            raise KeyError(f"Difficulty multiplier not found for: {difficulty}") from e


# Load configurations when module is imported
GameConfig.load_from_json()
RoomGenerationConfig.load_from_json()
GameBalance.load_from_json()