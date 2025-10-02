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
        self.graphics_mode = "ascii"  # "ascii" or "graphics"
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
                    self.graphics_mode = settings_data.get("graphics_mode", "ascii")
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
                "graphics_mode": "ascii"
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
                "graphics_mode": self.graphics_mode
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
        clamped_volume = clamp(volume, 0.0, 1.0)
        setattr(self, f"{volume_type}_volume", clamped_volume)
        self.save_settings()
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self._set_volume_attribute("master", volume)
    
    def set_sfx_volume(self, volume: float):
        """Set SFX volume (0.0 to 1.0)"""
        self._set_volume_attribute("sfx", volume)
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self._set_volume_attribute("music", volume)
    
    def set_graphics_mode(self, mode: str):
        """Set graphics mode ('ascii' or 'graphics')"""
        if mode in ["ascii", "graphics"]:
            self.graphics_mode = mode
            self.save_settings()
    
    def get_volume_percent(self, volume_type: str) -> int:
        """Get volume as percentage (0-100)"""
        if volume_type == "master":
            return int(self.master_volume * 100)
        elif volume_type == "sfx":
            return int(self.sfx_volume * 100)
        elif volume_type == "music":
            return int(self.music_volume * 100)
        return 0
    
    def set_volume_percent(self, volume_type: str, percent: int):
        """Set volume from percentage (0-100)"""
        volume = percent / 100.0
        if volume_type == "master":
            self.set_master_volume(volume)
        elif volume_type == "sfx":
            self.set_sfx_volume(volume)
        elif volume_type == "music":
            self.set_music_volume(volume)


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
    MAX_DETECTION = 100
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
        """Load configuration from JSON file."""
        try:
            with open('game_config.json', 'r', encoding='utf-8') as f:
                cls._config_data = json.load(f)

            # Update class attributes for backward compatibility
            cls.SCREEN_WIDTH = cls.get('display.screen_width', cls.SCREEN_WIDTH)
            cls.SCREEN_HEIGHT = cls.get('display.screen_height', cls.SCREEN_HEIGHT)
            cls.MAP_WIDTH = cls.get('display.map_width', cls.MAP_WIDTH)
            cls.MAP_HEIGHT = cls.get('display.map_height', cls.MAP_HEIGHT)
            cls.UI_HEIGHT = cls.get('display.ui_height', cls.UI_HEIGHT)
            cls.SIDEBAR_WIDTH = cls.get('display.sidebar_width', cls.SIDEBAR_WIDTH)
            cls.LOG_WIDTH = cls.get('display.log_width', cls.LOG_WIDTH)
            cls.PANEL_HEIGHT = cls.get('display.panel_height', cls.PANEL_HEIGHT)
            cls.DEFAULT_PLAYER_RAM = cls.get('gameplay.default_player_ram', cls.DEFAULT_PLAYER_RAM)
            cls.DEFAULT_PLAYER_CPU = cls.get('gameplay.default_player_cpu', cls.DEFAULT_PLAYER_CPU)
            cls.MAX_HEAT = cls.get('gameplay.max_heat', cls.MAX_HEAT)
            cls.MAX_DETECTION = cls.get('gameplay.max_detection', cls.MAX_DETECTION)
            cls.DETECTION_REDUCTION_ON_LEVEL = cls.get('gameplay.detection_reduction_on_level', cls.DETECTION_REDUCTION_ON_LEVEL)
            cls.DUNGEON_SEED_RANGE = cls.get('gameplay.dungeon_seed_range', cls.DUNGEON_SEED_RANGE)
            cls.DEFAULT_VISION_RANGE = cls.get('gameplay.default_vision_range', cls.DEFAULT_VISION_RANGE)
            cls.MAX_SAVE_ATTEMPTS = cls.get('gameplay.max_save_attempts', cls.MAX_SAVE_ATTEMPTS)
            cls.NEARBY_ENEMY_ALERT_RADIUS = cls.get('gameplay.nearby_enemy_alert_radius', cls.NEARBY_ENEMY_ALERT_RADIUS)
            cls.VIRUS_DAMAGE_PER_TURN = cls.get('gameplay.virus_damage_per_turn', cls.VIRUS_DAMAGE_PER_TURN)
            cls.DEFAULT_FADE_TIME = cls.get('audio.default_fade_time', cls.DEFAULT_FADE_TIME)
            cls.MESSAGE_CENTER_OFFSET_LARGE = cls.get('ui.message_center_offset_large', cls.MESSAGE_CENTER_OFFSET_LARGE)
            cls.MESSAGE_CENTER_OFFSET_MEDIUM = cls.get('ui.message_center_offset_medium', cls.MESSAGE_CENTER_OFFSET_MEDIUM)
            cls.MESSAGE_CENTER_OFFSET_SMALL = cls.get('ui.message_center_offset_small', cls.MESSAGE_CENTER_OFFSET_SMALL)
            cls.MESSAGE_CENTER_OFFSET_TINY = cls.get('ui.message_center_offset_tiny', cls.MESSAGE_CENTER_OFFSET_TINY)
            cls.MESSAGE_LINE_SPACING = cls.get('ui.message_line_spacing', cls.MESSAGE_LINE_SPACING)
            cls.MESSAGE_BUTTON_SPACING = cls.get('ui.message_button_spacing', cls.MESSAGE_BUTTON_SPACING)

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logging.warning(f"Could not load game config from JSON: {e}, using defaults")
            # Keep existing values if JSON loading fails

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
    def get(cls, key: str, default=None):
        """Get configuration value by key."""
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
    DATA_PATCHES_PER_LEVEL = 4
    EXPLOIT_PICKUPS_PER_LEVEL = 3
    PERMANENT_UPGRADES_PER_LEVEL = 1

    @classmethod
    def load_from_json(cls):
        """Load room generation config from JSON."""
        cls.MIN_ROOMS_BASE = GameConfig.get('room_generation.min_rooms_base', 12)
        cls.ROOM_LEVEL_MULTIPLIER = GameConfig.get('room_generation.room_level_multiplier', 3)
        cls.MAX_ROOMS = GameConfig.get('room_generation.max_rooms', 20)
        cls.MAX_PLACEMENT_ATTEMPTS = GameConfig.get('room_generation.max_placement_attempts', 400)
        cls.MIN_ROOM_SIZE = GameConfig.get('room_generation.min_room_size', 3)
        cls.MAX_ROOM_SIZE = GameConfig.get('room_generation.max_room_size', 8)
        cls.ROOM_PADDING = GameConfig.get('room_generation.room_padding', 1)
        cls.COOLING_NODES_PER_LEVEL = GameConfig.get('room_generation.cooling_nodes_per_level', 3)
        cls.CPU_NODES_PER_LEVEL = GameConfig.get('room_generation.cpu_nodes_per_level', 2)
        cls.GHOST_NODES_PER_LEVEL = GameConfig.get('room_generation.ghost_nodes_per_level', 2)
        cls.DATA_PATCHES_PER_LEVEL = GameConfig.get('room_generation.data_patches_per_level', 4)
        cls.EXPLOIT_PICKUPS_PER_LEVEL = GameConfig.get('room_generation.exploit_pickups_per_level', 3)
        cls.PERMANENT_UPGRADES_PER_LEVEL = GameConfig.get('room_generation.permanent_upgrades_per_level', 1)

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
    DETECTION_INCREASE_INTERVAL = 25
    DETECTION_INCREASE_AMOUNT = 1
    COOLING_NODE_EFFECT = 20
    GHOST_NODE_DETECTION_REDUCTION_PERCENT = 20.0
    CPU_RECOVERY_AMOUNT = 20
    ENEMY_ELIMINATION_CPU_REWARD = 5
    CPU_RESTORE_MIN = 30
    CPU_RESTORE_MAX = 40
    HEAT_REDUCTION_INSTANT = 40
    ADJACENT_DISTANCE_THRESHOLD = 1.5
    PATROL_STUCK_THRESHOLD = 3
    MAX_MOVEMENT_QUEUE_SIZE = 3
    PATHFINDING_TIMEOUT_ATTEMPTS = 100
    ENHANCED_VISION_BONUS = 2
    SHADOW_VISION_REDUCTION_FACTOR = 3
    ENEMY_DETECTION_ALERT_TO_HOSTILE = 3
    ENEMY_DETECTION_CONTINUOUS_HOSTILE = 0.3
    ENEMY_MEMORY_TURNS = 20

    @classmethod
    def load_from_json(cls):
        """Load balance config from JSON."""
        cls.HEAT_REDUCTION_NORMAL = GameConfig.get('balance.heat_reduction_normal', 2)
        cls.HEAT_REDUCTION_BOOSTED = GameConfig.get('balance.heat_reduction_boosted', 3)
        cls.DETECTION_INCREASE_INTERVAL = GameConfig.get('balance.detection_increase_interval', 25)
        cls.DETECTION_INCREASE_AMOUNT = GameConfig.get('balance.detection_increase_amount', 1)
        cls.COOLING_NODE_EFFECT = GameConfig.get('balance.cooling_node_effect', 20)
        cls.GHOST_NODE_DETECTION_REDUCTION_PERCENT = GameConfig.get('balance.ghost_node_detection_reduction_percent', 20.0)
        cls.CPU_RECOVERY_AMOUNT = GameConfig.get('balance.cpu_recovery_amount', 20)
        cls.ENEMY_ELIMINATION_CPU_REWARD = GameConfig.get('balance.enemy_elimination_cpu_reward', 5)
        cls.CPU_RESTORE_MIN = GameConfig.get('balance.cpu_restore_min', 30)
        cls.CPU_RESTORE_MAX = GameConfig.get('balance.cpu_restore_max', 40)
        cls.HEAT_REDUCTION_INSTANT = GameConfig.get('balance.heat_reduction_instant', 40)
        cls.ADJACENT_DISTANCE_THRESHOLD = GameConfig.get('balance.adjacent_distance_threshold', 1.5)
        cls.PATROL_STUCK_THRESHOLD = GameConfig.get('balance.patrol_stuck_threshold', 3)
        cls.MAX_MOVEMENT_QUEUE_SIZE = GameConfig.get('balance.max_movement_queue_size', 3)
        cls.PATHFINDING_TIMEOUT_ATTEMPTS = GameConfig.get('balance.pathfinding_timeout_attempts', 100)
        cls.ENHANCED_VISION_BONUS = GameConfig.get('balance.enhanced_vision_bonus', 2)
        cls.SHADOW_VISION_REDUCTION_FACTOR = GameConfig.get('balance.shadow_vision_reduction_factor', 3)
        cls.ENEMY_DETECTION_ALERT_TO_HOSTILE = GameConfig.get('balance.enemy_detection_alert_to_hostile', 3)
        cls.ENEMY_DETECTION_CONTINUOUS_HOSTILE = GameConfig.get('balance.enemy_detection_continuous_hostile', 0.3)
        cls.ENEMY_MEMORY_TURNS = GameConfig.get('balance.enemy_memory_turns', 20)

    @staticmethod
    def get_exploit_cpu_cost(exploit_name: str) -> int:
        """Get CPU cost for an exploit."""
        from data_loading import DataLoader
        game_data = DataLoader.load_game_data()
        costs = game_data.get('exploit_cpu_costs', {})
        return costs.get(exploit_name, 10)

    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies."""
        from data_loading import DataLoader
        game_data = DataLoader.load_game_data()
        multipliers = game_data.get('difficulty_multipliers', {
            "easy": 0.8, "normal": 1.0, "hard": 1.3, "nightmare": 1.6
        })
        return multipliers.get(difficulty, 1.0)


# Load configurations when module is imported
GameConfig.load_from_json()
RoomGenerationConfig.load_from_json()
GameBalance.load_from_json()