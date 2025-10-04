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
                          ExploitDefinition, EnemyTypeDefinition, clamp,
                          format_position_key, parse_position_key,
                          parse_coordinate_string, ensure_color_tuple)
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
from game_rendering import GameRenderer, UIRenderer, MapRenderer
from game_loop import main, initialize_tcod_context, WindowManager as LoopWindowManager

# Setup detailed logging for comprehensive debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    handlers=[
        logging.StreamHandler()
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================
# GameConfig imported from game_config.py - no duplication needed


# Colors are now handled by the JSON-driven ColorManager in game_entities.py


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise