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
from typing import List, Dict, Any
from game_errors import GameErrorHandler


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
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data[key] if key else data
        except FileNotFoundError as e:
            GameErrorHandler.handle_config_error(f"{filename} not found", e)
        except json.JSONDecodeError as e:
            GameErrorHandler.handle_config_error(f"Invalid JSON in {filename}", e)
        except KeyError as e:
            GameErrorHandler.handle_config_error(f"Missing '{key}' key in {filename}", e)
    
    @classmethod
    def load_story_fragments(cls) -> List[str]:
        """Load story fragments from JSON file."""
        if cls._story_fragments is None:
            cls._story_fragments = cls._load_json_file('story_content.json', 'fragments')
        return cls._story_fragments
    
    @classmethod
    def load_game_data(cls) -> Dict[str, Any]:
        """Load game data from JSON file."""
        if cls._game_data is None:
            cls._game_data = cls._load_json_file('game_content.json')
        return cls._game_data
    
    @classmethod
    def _get_section(cls, section: str, data: Dict) -> Dict[str, Any]:
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
    def get_balance_config(cls) -> Dict[str, Any]:
        """Get balance configuration from game data."""
        return cls._get_section('balance', cls.load_game_data())

    @classmethod
    def get_item_effects(cls) -> Dict[str, Any]:
        """Get item effects configuration from game data."""
        return cls._get_section('item_effects', cls.load_game_data())

    @classmethod
    def get_ai_behavior_config(cls) -> Dict[str, Any]:
        """Get AI behavior configuration from game config."""
        config = cls.load_config()
        try:
            return config['balance']['ai_behavior']
        except KeyError as e:
            # Provide additional context for debugging
            if 'balance' in config:
                logging.error(f"Available balance keys: {list(config['balance'].keys())}")
            else:
                logging.error("No 'balance' section found")
                logging.error(f"Available sections: {list(config.keys())}")
            GameErrorHandler.handle_config_error("Missing AI behavior config in game_rules.json", e)
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
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
            try:
                with open('game_rules.json', 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
            except FileNotFoundError as e:
                error_msg = f"CRITICAL CONFIG ERROR: game_rules.json not found"
                logging.error(error_msg)
                logging.error(f"Exception: {str(e)}")
                raise FileNotFoundError(f"Required file game_rules.json is missing") from e
            except json.JSONDecodeError as e:
                error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in game_rules.json"
                logging.error(error_msg)
                logging.error(f"Exception: {str(e)}")
                raise json.JSONDecodeError(f"game_rules.json contains invalid JSON", e.doc, e.pos) from e
        return cls._config
    
    @classmethod
    def load_user_settings(cls) -> Dict[str, Any]:
        """Load user settings from JSON file."""
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Normal for first run - create default settings
            logging.debug("user_settings.json not found, using defaults (normal for first run)")
            return cls._get_default_user_settings()
        except json.JSONDecodeError as e:
            # Corrupted settings file - use defaults but warn user
            error_msg = f"WARNING: Invalid JSON in user_settings.json, using defaults"
            logging.warning(error_msg)
            logging.warning(f"JSON error: {str(e)}")
            return cls._get_default_user_settings()
    
    @classmethod
    def save_user_settings(cls, settings: Dict[str, Any]) -> bool:
        """Save user settings to JSON file."""
        try:
            with open('user_settings.json', 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Failed to save user settings: {e}")
            return False
    
    @classmethod
    def _get_default_user_settings(cls) -> Dict[str, Any]:
        """Default user settings if file doesn't exist - this is the only legitimate fallback."""
        return {
            "master_volume": 0.7,
            "sfx_volume": 1.0,
            "music_volume": 0.7,
            "graphics_mode": "terminal"
        }



class PersistentStorage:
    """Handles persistent storage and game saves."""
    
    def __init__(self, base_dir="saves"):
        self.base_dir = base_dir
        self.ensure_directory_exists()
    
    def ensure_directory_exists(self):
        """Create saves directory if it doesn't exist."""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
    
    def save_data(self, filename: str, data: Dict[str, Any]) -> bool:
        """Save data to JSON file."""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            from game_errors import GameErrorHandler
            GameErrorHandler.handle_error(e, f"PersistentStorage.save_data({filename})",
                                        "Failed to save game data")
            return False
    
    def load_data(self, filename: str) -> Dict[str, Any]:
        """Load data from JSON file."""
        filepath = os.path.join(self.base_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # This is normal for new games - return empty dict
            logging.debug(f"Save file not found: {filename} (normal for new games)")
            return {}
        except json.JSONDecodeError as e:
            # Handle corrupted save files
            logging.warning(f"Invalid JSON in save file {filename}: {e}")
            return {}
    
    def file_exists(self, filename: str) -> bool:
        """Check if save file exists."""
        filepath = os.path.join(self.base_dir, filename)
        return os.path.exists(filepath)
    
    def list_save_files(self) -> List[str]:
        """List all save files in the directory."""
        files = [f for f in os.listdir(self.base_dir) if f.endswith('.json')]
        return sorted(files)


def get_story_fragments() -> List[str]:
    """Get story fragments - convenience function."""
    return DataLoader.load_story_fragments()