#!/usr/bin/env python3
"""
Rogue Signal Protocol - A cyberpunk stealth roguelike

Main entry point that imports modular components and initializes the game.
Sets up logging configuration for both console and file output.
"""

import sys
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

# CRITICAL: Set working directory to exe location when running as frozen executable
# This ensures the game can find assets regardless of where it's launched from
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    print(f"Running as frozen exe, changed working directory to: {application_path}")
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    print(f"Running as script, working directory: {application_path}")

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

# Configure logging based on build type
# Alpha builds: DEBUG logging with file output (for playtester bug reports)
# Release builds: WARNING logging with minimal file output
# Check for debug_mode.flag file created by build script
DEBUG_MODE = os.path.exists('debug_mode.flag')

if DEBUG_MODE:
    # Alpha/Debug build - INFO level logging (less spam, still useful)
    log_level = logging.INFO
    # Use unbuffered file handler so logs are written immediately (critical for crash debugging)
    # Open with buffering=1 for line buffering
    # Ensure logs directory exists
    import os
    os.makedirs('logs', exist_ok=True)

    log_file = open('logs/game_debug.log', mode='w', buffering=1)
    file_handler = logging.StreamHandler(log_file)
    file_handler.setLevel(logging.INFO)

    log_handlers = [
        logging.StreamHandler(),
        file_handler
    ]
    print("DEBUG MODE: Verbose logging enabled (Alpha build)")
else:
    # Release build - minimal logging
    log_level = logging.WARNING
    log_handlers = [
        logging.FileHandler('logs/game_errors.log', mode='w')
    ]
    print("RELEASE MODE: Minimal logging (Release build)")

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    handlers=log_handlers,
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # Force reconfiguration even if already configured
)

# Log the startup mode
if DEBUG_MODE:
    logging.info("="*80)
    logging.info("[START] GAME SESSION START")
    logging.info("="*80)
    logging.info("Game started in DEBUG mode (Alpha build for playtesters)")
    logging.info(f"Log file: logs/game_debug.log")
    logging.info(f"Python version: {__import__('sys').version}")
    logging.info(f"TCOD version: {tcod.__version__}")
    # Force flush to ensure it's written
    for handler in logging.root.handlers:
        handler.flush()
else:
    logging.warning("Game started in RELEASE mode (errors only logged to logs/game_errors.log)")


# All configuration constants are loaded from JSON files via:
# - GameConfig (game_config.py): Core game settings and balance values
# - ColorManager (game_entities.py): JSON-driven color management


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise