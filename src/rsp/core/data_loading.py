#!/usr/bin/env python3
"""
Data Loading and Configuration Management

Centralized JSON file loading with caching and strict error handling.
Provides static methods for loading:
- Game content (exploits, enemies, upgrades)
- Story fragments
- Configuration rules (balance, AI behavior)

Uses fail-fast approach - missing files or keys cause immediate errors
rather than using fallback values. This ensures configuration problems
are caught during development, not during gameplay.
"""

import json
import logging
import os
from typing import Any

from rsp.core.errors import GameErrorHandler
from rsp.core.file_paths import get_data_directory


class DataLoader:
    """
    Handles loading of JSON configuration and game data files.

    Uses class-level caching to avoid re-reading files on every access.
    All methods are class methods since there's no instance state.
    Delegates error handling to GameErrorHandler for consistent error reporting.
    """

    _story_fragments = None
    _game_data = None
    _config = None

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached data for testing isolation or runtime reloading.

        Resets all class-level cache variables to None, forcing fresh loads
        on next access.
        """
        cls._story_fragments = None
        cls._game_data = None
        cls._config = None

    @classmethod
    def _load_json_file(cls, filename: str, key: str = None) -> Any:
        """
        Load JSON file with standardized error handling.

        Args:
            filename: Path to JSON file
            key: Optional key to extract from root object

        Returns:
            Parsed JSON data (full or extracted by key)

        Raises:
            Exits game via GameErrorHandler if file not found or invalid
        """
        try:
            with open(filename, encoding="utf-8") as f:
                data = json.load(f)
                result = data[key] if key else data
                key_info = f", key='{key}'" if key else ""
                if isinstance(result, dict):
                    logging.debug(
                        f"Data Loading: Loaded {filename}{key_info} ({len(result)} entries)"
                    )
                elif isinstance(result, list):
                    logging.debug(
                        f"Data Loading: Loaded {filename}{key_info} ({len(result)} items)"
                    )
                else:
                    logging.debug(f"Data Loading: Loaded {filename}{key_info}")
                return result
        except FileNotFoundError as e:
            GameErrorHandler.handle_config_error(f"{filename} not found", e)
        except json.JSONDecodeError as e:
            GameErrorHandler.handle_config_error(f"Invalid JSON in {filename}", e)
        except KeyError as e:
            GameErrorHandler.handle_config_error(f"Missing '{key}' key in {filename}", e)

    @classmethod
    def load_story_fragments(cls) -> list[str]:
        """Load story fragments from JSON file."""
        if cls._story_fragments is None:
            logging.debug("Data Loading: Loading story fragments (cache miss)")
            cls._story_fragments = cls._load_json_file("narrative_content.json", "fragments")
        else:
            logging.debug("Data Loading: Using cached story fragments")
        return cls._story_fragments

    @classmethod
    def load_game_data(cls) -> dict[str, Any]:
        """Load game data from JSON file."""
        if cls._game_data is None:
            cls._game_data = cls._load_json_file("game_content.json")
        return cls._game_data

    @classmethod
    def _get_section(cls, section: str, data: dict) -> dict[str, Any]:
        """Get a section from data with error handling."""
        try:
            return data[section]
        except KeyError as e:
            msg = f"CRITICAL CONFIG ERROR: Missing '{section}' section in game_content.json"
            logging.error(msg)
            logging.error(f"Exception: {str(e)}")
            logging.error(f"Available sections: {list(data.keys())}")
            raise KeyError(f"Required '{section}' section missing from game_content.json") from e

    @classmethod
    def load_config(cls) -> dict[str, Any]:
        """
        Load configuration from game_rules.json with caching.

        Contains balance values, AI behavior, colors, and message patterns.
        Cached on first access to avoid repeated file I/O.

        Returns:
            Full configuration dictionary

        Raises:
            Exits game via GameErrorHandler if file missing or invalid
        """
        if cls._config is None:
            logging.debug("Data Loading: Loading game_rules.json (cache miss)")
            try:
                with open("game_rules.json", encoding="utf-8") as f:
                    cls._config = json.load(f)
                logging.debug(
                    f"Data Loading: Loaded game_rules.json ({len(cls._config)} top-level keys)"
                )
            except FileNotFoundError as e:
                error_msg = "CRITICAL CONFIG ERROR: game_rules.json not found"
                logging.error(error_msg)
                logging.error(f"Exception: {str(e)}")
                raise FileNotFoundError("Required file game_rules.json is missing") from e
            except json.JSONDecodeError as e:
                error_msg = "CRITICAL CONFIG ERROR: Invalid JSON in game_rules.json"
                logging.error(error_msg)
                logging.error(f"Exception: {str(e)}")
                raise json.JSONDecodeError(
                    "game_rules.json contains invalid JSON", e.doc, e.pos
                ) from e
        return cls._config


class PersistentStorage:
    """Handles persistent storage and game saves."""

    def __init__(self, base_dir=None):
        # Use data directory from game_file_paths if no explicit path provided
        if base_dir is None:
            self.base_dir = str(get_data_directory() / "saves")
        else:
            self.base_dir = base_dir
        self.ensure_directory_exists()

    def ensure_directory_exists(self) -> None:
        """Create saves directory if it doesn't exist."""
        os.makedirs(self.base_dir, exist_ok=True)

    def save_data(self, filename: str, data: dict[str, Any]) -> bool:
        """Save data to JSON file."""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            GameErrorHandler.handle_error(
                e, f"PersistentStorage.save_data({filename})", "Failed to save game data"
            )
            return False

    def load_data(self, filename: str) -> dict[str, Any]:
        """Load data from JSON file."""
        filepath = os.path.join(self.base_dir, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # This is normal for new games - return empty dict
            logging.debug(f"Save file not found: {filename} (normal for new games)")
            return {}
        except json.JSONDecodeError as e:
            # Handle corrupted save files - log as error for visibility
            # NOTE: Returns empty dict which treats corrupted save as new game.
            # This is intentional for permadeath roguelike design, but user
            # should ideally be notified their progress was lost.
            logging.error(f"CORRUPTED SAVE FILE {filename}: {e} - treating as new game")
            return {}


def get_story_fragments() -> list[str]:
    """Get story fragments - convenience function."""
    return DataLoader.load_story_fragments()


def get_environmental_messages() -> dict[str, list[str]]:
    """Get environmental messages for atmospheric flavor text."""
    return DataLoader._load_json_file("narrative_content.json", "environmental_messages")


def get_death_messages() -> list[str]:
    """Get death messages with story context."""
    return DataLoader._load_json_file("narrative_content.json", "death_messages")


def get_level_transition_messages() -> dict[str, str]:
    """Get level transition flavor text."""
    return DataLoader._load_json_file("narrative_content.json", "level_transition_messages")


def get_intro_messages() -> dict[str, dict[str, str]]:
    """Get tiered intro messages based on fragment discovery."""
    return DataLoader._load_json_file("narrative_content.json", "intro_messages")
