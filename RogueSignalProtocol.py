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
from game_config import GameSettings, GameConfig, GameBalance, RoomGenerationConfig
from game_entities import (Position, EnemyState, EnemyMovement, TargetingMode,
                          ExploitDefinition, EnemyTypeDefinition, clamp, safe_divide,
                          validate_coordinates, calculate_manhattan_distance,
                          get_adjacent_positions, format_position_key, parse_position_key,
                          parse_coordinate_string, validate_position_bounds, ensure_color_tuple)
from game_data import GameData, GameUpgrades
from game_inventory import InventoryItem, CodeHack, ExploitItem, StoryFragment, InventoryManager
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
# GameConfig imported from game_config.py - no duplication needed


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
    UI_BG = (20, 20, 20)
    UI_TEXT = (200, 200, 200)
    LOG_BORDER = (100, 100, 100)
    LOG_BG = (10, 10, 10)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise