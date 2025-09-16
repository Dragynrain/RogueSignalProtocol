#!/usr/bin/env python3
"""
Game configuration and settings management.
Extracted from RogueSignalProtocol.py for better organization.
"""

import json
import logging
import os
from typing import Dict, Any


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(value, max_val))


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
            logging.warning(traceback.format_exc())
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
            logging.error(traceback.format_exc())
    
    def _set_volume_attribute(self, volume_type: str, volume: float):
        """Generic volume setter for any volume type."""
        clamped_volume = clamp_value(volume, 0.0, 1.0)
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
    
    # Screen dimensions  
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    
    # Map dimensions
    MAP_WIDTH = 80
    MAP_HEIGHT = 40
    
    # UI layout
    UI_HEIGHT = 10
    SIDEBAR_WIDTH = 25
    
    # Game parameters
    DEFAULT_PLAYER_RAM = 8
    DEFAULT_PLAYER_CPU = 100
    MAX_HEAT = 100
    
    _config_data = None
    
    @classmethod
    def load_from_json(cls):
        """Load configuration from JSON file."""
        try:
            with open('game_config.json', 'r', encoding='utf-8') as f:
                cls._config_data = json.load(f)
                
            # Update class attributes if values exist in JSON
            if 'display' in cls._config_data:
                display_config = cls._config_data['display']
                cls.SCREEN_WIDTH = display_config.get('screen_width', cls.SCREEN_WIDTH)
                cls.SCREEN_HEIGHT = display_config.get('screen_height', cls.SCREEN_HEIGHT)
                cls.MAP_WIDTH = display_config.get('map_width', cls.MAP_WIDTH)
                cls.MAP_HEIGHT = display_config.get('map_height', cls.MAP_HEIGHT)
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logging.warning(f"Could not load game config from JSON: {e}, using defaults")
    
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


class RoomGenerationConfig:
    """Configuration for room generation."""
    
    def __init__(self):
        self.min_room_size = 4
        self.max_room_size = 10
        self.max_rooms = 30
        self.room_attempts = 100


class GameBalance:
    """Game balance configuration."""
    
    @staticmethod
    def get_exploit_cpu_cost(exploit_name: str) -> int:
        """Get CPU cost for an exploit."""
        cpu_costs = {
            "shadow_step": 10,
            "buffer_overflow": 15,
            "code_injection": 20,
            "system_crash": 25,
            "threat_scan": 5,
            "log_wiper": 12,
            "antivirus": 18,
            "emp_burst": 30,
            "memory_leak": 8
        }
        return cpu_costs.get(exploit_name, 10)
    
    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies."""
        multipliers = {
            "easy": 0.8,
            "normal": 1.0,
            "hard": 1.3,
            "nightmare": 1.6
        }
        return multipliers.get(difficulty, 1.0)