#!/usr/bin/env python3
"""
Rogue Signal Protocol - A cyberpunk stealth roguelike
Refactored main file - imports from modular components
"""

import tcod
from tcod import libtcodpy
import logging
import traceback
import random
import math
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

# Import refactored modules
from data_loading import DataLoader, PersistentStorage, get_story_fragments
from game_config import GameSettings, GameBalance, RoomGenerationConfig
from game_entities import (Position, EnemyState, EnemyMovement, TargetingMode,
                          ExploitDefinition, EnemyTypeDefinition, clamp, safe_divide,
                          validate_coordinates, calculate_manhattan_distance,
                          get_adjacent_positions, format_position_key, parse_position_key,
                          parse_coordinate_string, validate_position_bounds, ensure_color_tuple)
from game_data import GameData, GameUpgrades
from game_inventory import InventoryItem, DataPatch, ExploitItem, StoryFragment, InventoryManager
from game_characters import Player, Enemy, create_pathfinding_cost_map, pathfind_and_move, can_move_to_position
from game_audio import SoundManager
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_ui import render_char_safe, WindowManager, UniversalInputHandler
from game_menus import MenuBackground, MainMenu, LoreMenu, HelpMenu, SettingsMenu
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_map import GameMap
from game_input import InputHandler
from game_engine import GameEngine

# Import new modular components
from game_state import MessageLog, GameStateManager, TurnProcessor
from game_rendering import BaseRenderer, ASCIIRenderer, Renderer, UIRenderer, MapRenderer
from game_loop import main, initialize_tcod_context, WindowManager as LoopWindowManager

# Setup logging for error handling
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

class GameConfig:
    """Central configuration for game constants."""
    _config_data = None
    
    @classmethod
    def _get_config(cls):
        """Load config data if not already loaded."""
        if cls._config_data is None:
            cls._config_data = DataLoader.load_config()
        return cls._config_data
    
    # Static properties - load once and cache
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 50
    MAP_HEIGHT = 50
    LOG_WIDTH = 25
    PANEL_HEIGHT = 5
    DEFAULT_VISION_RANGE = 10
    MAX_HEAT = 100
    MAX_DETECTION = 100
    DETECTION_REDUCTION_ON_LEVEL = 50
    DUNGEON_SEED_RANGE = 1000000
    DEFAULT_FADE_TIME = 2000
    
    @classmethod
    def LOG_BORDER(cls):
        return cls._get_color_from_config("ui", "LOG_BORDER") or (100, 100, 100)
    
    @classmethod
    def LOG_BG(cls):
        return cls._get_color_from_config("ui", "LOG_BG") or (10, 10, 10)
    
    @classmethod
    def UI_BG(cls):
        return cls._get_color_from_config("ui", "UI_BG") or (20, 20, 20)
    
    @classmethod 
    def UI_TEXT(cls):
        return cls._get_color_from_config("ui", "UI_TEXT") or (200, 200, 200)
    
    @classmethod
    def GAME_AREA_WIDTH(cls):
        return cls.SCREEN_WIDTH - cls.LOG_WIDTH
    
    @classmethod
    def PANEL_Y(cls):
        return cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT
    
    @classmethod
    def VIRUS_DAMAGE_PER_TURN(cls):
        config = cls._get_config()
        return config.get("virus_damage_per_turn", 5)
    
    @classmethod
    def NETWORK_CONFIGS(cls):
        config = cls._get_config()
        return config.get("network_configs", {})
    
    @classmethod
    def _get_color_from_config(cls, category: str, color_name: str) -> Optional[Tuple[int, int, int]]:
        """Helper to extract and validate colors from config."""
        config = cls._get_config()
        colors = config.get("colors", {}).get(category, {})
        color_data = colors.get(color_name)
        
        if color_data and isinstance(color_data, list) and len(color_data) >= 3:
            try:
                return tuple(int(c) for c in color_data[:3])
            except (ValueError, TypeError):
                return None
        return None
    
    @classmethod
    def load_from_json(cls):
        """Load configuration from JSON files."""
        cls._config_data = DataLoader.load_config()


class Colors:
    """Color constants for the game."""
    
    # Basic colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    
    # Game-specific colors 
    PLAYER = (100, 149, 237)  # Cornflower blue
    WALL = (128, 128, 128)    # Gray
    FLOOR = (64, 64, 64)      # Dark gray
    ENEMY = (255, 69, 0)      # Red orange
    LIGHT_GRAY = (192, 192, 192)
    DARK_GREEN = (0, 100, 0)
    ORANGE = (255, 165, 0)
    
    # Vision overlays
    VISION_UNAWARE = (50, 50, 0)     # Dark yellow
    VISION_ALERT = (80, 40, 0)       # Orange-brown
    VISION_HOSTILE = (80, 0, 0)      # Dark red
    
    # Cyberpunk/neon colors
    ELECTRIC_BLUE = (0, 191, 255)
    ELECTRIC_PURPLE = (191, 0, 255)
    ACID_GREEN = (50, 205, 50)
    GATEWAY = (255, 215, 0)  # Gold
    
    # Data patch colors
    CRIMSON = (220, 20, 60)
    AZURE = (0, 127, 255) 
    EMERALD = (80, 200, 120)
    GOLDEN = (255, 215, 0)
    VIOLET = (138, 43, 226)
    SILVER = (192, 192, 192)
    
    # UI colors
    UI_BG = GameConfig.UI_BG()
    UI_TEXT = GameConfig.UI_TEXT()
    LOG_BORDER = GameConfig.LOG_BORDER()
    LOG_BG = GameConfig.LOG_BG()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise