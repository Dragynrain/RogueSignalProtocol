#!/usr/bin/env python3
"""
Data loading and configuration management.
Extracted from RogueSignalProtocol.py for better organization.
"""

import json
import logging
import os
from typing import List, Dict, Any


class DataLoader:
    """Handles loading of JSON configuration and game data files."""
    
    _story_fragments = None
    _game_data = None
    _config = None
    
    @classmethod
    def load_story_fragments(cls) -> List[str]:
        """Load story fragments from JSON file."""
        if cls._story_fragments is None:
            try:
                with open('story_content.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cls._story_fragments = data['fragments']
            except FileNotFoundError as e:
                error_msg = f"CRITICAL CONFIG ERROR: story_content.json not found"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise FileNotFoundError(f"Required file story_content.json is missing") from e
            except json.JSONDecodeError as e:
                error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in story_content.json"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise json.JSONDecodeError(f"story_content.json contains invalid JSON", e.doc, e.pos) from e
            except KeyError as e:
                error_msg = f"CRITICAL CONFIG ERROR: Missing 'fragments' key in story_content.json"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise KeyError(f"Required 'fragments' section missing from story_content.json") from e
        return cls._story_fragments
    
    @classmethod
    def load_game_data(cls) -> Dict[str, Any]:
        """Load game data from JSON file."""
        if cls._game_data is None:
            try:
                with open('game_data.json', 'r', encoding='utf-8') as f:
                    cls._game_data = json.load(f)
            except FileNotFoundError as e:
                error_msg = f"CRITICAL CONFIG ERROR: game_data.json not found"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise FileNotFoundError(f"Required file game_data.json is missing") from e
            except json.JSONDecodeError as e:
                error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in game_data.json"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise json.JSONDecodeError(f"game_data.json contains invalid JSON", e.doc, e.pos) from e
        return cls._game_data
    
    @classmethod
    def get_balance_config(cls) -> Dict[str, Any]:
        """Get balance configuration from game data."""
        game_data = cls.load_game_data()
        try:
            return game_data['balance']
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Missing 'balance' section in game_data.json"
            print(error_msg)
            logging.error(error_msg)
            print(f"Exception: {str(e)}")
            print(f"Available sections: {list(game_data.keys())}")
            raise KeyError(f"Required 'balance' section missing from game_data.json") from e

    @classmethod
    def get_item_effects(cls) -> Dict[str, Any]:
        """Get item effects configuration from game data."""
        game_data = cls.load_game_data()
        try:
            return game_data['item_effects']
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Missing 'item_effects' section in game_data.json"
            print(error_msg)
            logging.error(error_msg)
            print(f"Exception: {str(e)}")
            print(f"Available sections: {list(game_data.keys())}")
            raise KeyError(f"Required 'item_effects' section missing from game_data.json") from e

    @classmethod
    def get_ai_behavior_config(cls) -> Dict[str, Any]:
        """Get AI behavior configuration from game data."""
        game_data = cls.load_game_data()
        try:
            return game_data['balance']['ai_behavior']
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Missing AI behavior config in game_data.json"
            print(error_msg)
            logging.error(error_msg)
            print(f"Exception: {str(e)}")
            if 'balance' in game_data:
                print(f"Available balance keys: {list(game_data['balance'].keys())}")
            else:
                print("No 'balance' section found")
                print(f"Available sections: {list(game_data.keys())}")
            raise KeyError(f"Required 'balance.ai_behavior' section missing from game_data.json") from e
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if cls._config is None:
            try:
                with open('game_config.json', 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
            except FileNotFoundError as e:
                error_msg = f"CRITICAL CONFIG ERROR: game_config.json not found"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise FileNotFoundError(f"Required file game_config.json is missing") from e
            except json.JSONDecodeError as e:
                error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in game_config.json"
                print(error_msg)
                logging.error(error_msg)
                print(f"Exception: {str(e)}")
                raise json.JSONDecodeError(f"game_config.json contains invalid JSON", e.doc, e.pos) from e
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
            print(error_msg)
            logging.warning(error_msg)
            print(f"JSON error: {str(e)}")
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