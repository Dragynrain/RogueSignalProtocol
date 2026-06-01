#!/usr/bin/env python3
"""
Rogue Signal Protocol - A cyberspace stealth roguelike

Main entry point that imports modular components and initializes the game.
Sets up logging configuration for both console and file output.
"""

import atexit
import logging
import os
import sys

# Add src directory to path for rsp package imports
import sys as _sys
from pathlib import Path as _Path

import tcod

_src_dir = _Path(__file__).parent / "src"
_sys.path.insert(0, str(_src_dir))
del _sys, _Path, _src_dir


# CRITICAL: Set working directory to exe location when running as frozen executable
# This ensures the game can find assets regardless of where it's launched from
if getattr(sys, "frozen", False):
    # Running as compiled exe
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)

# CRITICAL: Initialize file paths BEFORE any logging or file operations
# This determines whether to use portable mode (./saves, ./logs) or AppData mode
from rsp.core.file_paths import (  # noqa: E402
    get_mode_description,
    initialize_data_directories,
    show_fatal_error_and_exit,
)

if not initialize_data_directories():
    show_fatal_error_and_exit(
        "Cannot create required directories for game data.\n\n"
        "The game tried:\n"
        "1. Portable mode (current directory)\n"
        "2. AppData mode (%LOCALAPPDATA%\\RogueSignalProtocol)\n\n"
        "Both failed. Please ensure you have write permissions,\n"
        "or move the game to a writable location (e.g., Desktop, Documents).",
        "Rogue Signal Protocol - Startup Error",
    )

# Import modular components for game loop and rendering
from rsp.core.loop import main  # noqa: E402

# Configure logging based on build type
# debug_mode.flag present: DEBUG logging with file output
# No flag: WARNING logging with minimal file output
DEBUG_MODE = os.path.exists("debug_mode.flag")

# Get log directory path (supports portable/AppData modes)
from rsp.core.file_paths import get_data_directory  # noqa: E402

log_dir = get_data_directory() / "logs"
log_dir.mkdir(exist_ok=True)

if DEBUG_MODE:
    # Debug mode - DEBUG level logging
    log_level = logging.DEBUG
    # Use unbuffered file handler so logs are written immediately (critical for crash debugging)
    # Open with buffering=1 for line buffering

    log_file = open(
        str(log_dir / "game_debug.log"), mode="w", buffering=1, encoding="utf-8", errors="replace"
    )  # Truncate mode for fresh logs each session
    atexit.register(log_file.close)  # Ensure file handle is closed on exit
    file_handler = logging.StreamHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Configure console handler with UTF-8 and error handling
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Keep console at INFO to reduce spam

    log_handlers = [console_handler, file_handler]
else:
    # Release build - minimal logging (default when no debug_mode.flag)
    log_level = logging.WARNING
    log_handlers = [logging.FileHandler(str(log_dir / "game_errors.log"), mode="w")]

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    handlers=log_handlers,
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,  # Force reconfiguration even if already configured
)

# Log startup info (now that logging is configured, replaces earlier print statements)
if DEBUG_MODE:
    logging.info("=" * 80)
    logging.info("[START] GAME SESSION START")
    logging.info("=" * 80)
    logging.info("Game started in DEBUG mode")
    logging.info(f"Working directory: {application_path}")
    logging.info(f"Data storage: {get_mode_description()}")
    logging.info(f"Log file: {log_dir / 'game_debug.log'}")
    logging.info(f"Python version: {__import__('sys').version}")
    logging.info(f"TCOD version: {tcod.__version__}")
    # Force flush to ensure it's written
    for handler in logging.root.handlers:
        handler.flush()
else:
    logging.warning(
        f"Game started in RELEASE mode (errors logged to {log_dir / 'game_errors.log'})"
    )


# All configuration constants are loaded from JSON files via:
# - GameConfig (game_config.py): Core game settings and balance values
# - ColorManager (game_entities.py): JSON-driven color management


if __name__ == "__main__":
    # Packaging smoke test (used by CI against the assembled binary + assets).
    # Reaching this point already proves the rsp package is bundled and the config
    # loaded at import time - the exact failure mode the source test suite cannot
    # catch (it imports rsp from src/, never from the frozen binary). We also load
    # game content explicitly, then exit 0 without opening a window.
    if "--self-test" in sys.argv:
        try:
            from rsp.core.config import GameBalance, GameConfig
            from rsp.core.data import GameData, GameUpgrades

            GameConfig.load_from_json()
            GameBalance.load_from_json()
            GameUpgrades._ensure_loaded()
            # Touch content that the game reads at runtime so missing/corrupt data fails here.
            assert GameData.ENEMY_TYPES, "No enemy types loaded"
            print("SELF-TEST OK")
            sys.exit(0)
        except Exception as e:
            logging.critical(f"SELF-TEST FAILED: {e}")
            print(f"SELF-TEST FAILED: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise
