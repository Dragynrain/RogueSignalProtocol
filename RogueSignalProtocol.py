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

import tcod

# CRITICAL: Set working directory to exe location when running as frozen executable
# This ensures the game can find assets regardless of where it's launched from
if getattr(sys, "frozen", False):
    # Running as compiled exe
    application_path = os.path.dirname(sys.executable)
    os.chdir(application_path)
    print(f"Running as frozen exe, changed working directory to: {application_path}")
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    print(f"Running as script, working directory: {application_path}")

# CRITICAL: Initialize file paths BEFORE any logging or file operations
# This determines whether to use portable mode (./saves, ./logs) or AppData mode
from game_file_paths import (  # noqa: E402
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

print(f"Data storage mode: {get_mode_description()}")

# Import refactored modules

# Import modular components for game loop and rendering
from game_loop import main  # noqa: E402

# Configure logging based on build type
# Alpha builds: DEBUG logging with file output (for playtester bug reports)
# Release builds: WARNING logging with minimal file output
# Check for debug_mode.flag file created by build script
DEBUG_MODE = os.path.exists("debug_mode.flag")

# Get log directory path (supports portable/AppData modes)
from game_file_paths import get_data_directory  # noqa: E402

log_dir = get_data_directory() / "logs"
log_dir.mkdir(exist_ok=True)

if DEBUG_MODE:
    # Alpha/Debug build - DEBUG level logging (for playtester bug reports)
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
    print("DEBUG MODE: Verbose logging enabled (Alpha build)")
else:
    # Release build - minimal logging
    log_level = logging.WARNING
    log_handlers = [logging.FileHandler(str(log_dir / "game_errors.log"), mode="w")]
    print("RELEASE MODE: Minimal logging (Release build)")

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    handlers=log_handlers,
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,  # Force reconfiguration even if already configured
)

# Log the startup mode
if DEBUG_MODE:
    logging.info("=" * 80)
    logging.info("[START] GAME SESSION START")
    logging.info("=" * 80)
    logging.info("Game started in DEBUG mode (Alpha build for playtesters)")
    logging.info(f"Log file: {log_dir / 'game_debug.log'}")
    logging.info(f"Data directory: {get_mode_description()}")
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
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise
