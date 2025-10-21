#!/usr/bin/env python3
"""
Rogue Signal Protocol - A cyberpunk stealth roguelike

Main entry point that imports modular components and initializes the game.
Sets up logging configuration for both console and file output.
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
                          ExploitDefinition, EnemyTypeDefinition, clamp,
                          format_position_key, parse_position_key,
                          parse_coordinate_string, ensure_color_tuple)
from game_data import GameData, GameUpgrades
from game_inventory import InventoryItem, CodeHack, ExploitItem, StoryFragment, InventoryManager
from game_characters import Player, Enemy
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

# Import modular components for game loop and rendering
from game_state import MessageLog, GameStateManager, TurnProcessor
from game_rendering_core import GameRenderer
from game_rendering_ui import UIRenderer
from game_rendering_glyphs import GlyphsMapRenderer
from game_loop import main, initialize_tcod_context, WindowManager as LoopWindowManager

# Configure logging to capture debug info for both console and file output
# Overwrites game_debug.log each session to prevent log file bloat
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('game_debug.log', mode='w')
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)


# All configuration constants are loaded from JSON files via:
# - GameConfig (game_config.py): Core game settings and balance values
# - ColorManager (game_entities.py): JSON-driven color management


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise