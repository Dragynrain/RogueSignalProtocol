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
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Could not load story fragments from JSON: {e}")
                cls._story_fragments = cls._get_fallback_story_fragments()
        return cls._story_fragments
    
    @classmethod
    def load_game_data(cls) -> Dict[str, Any]:
        """Load game data from JSON file."""
        if cls._game_data is None:
            try:
                with open('game_data.json', 'r', encoding='utf-8') as f:
                    cls._game_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.warning(f"Could not load game data from JSON: {e}")
                cls._game_data = cls._get_fallback_game_data()
        return cls._game_data
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if cls._config is None:
            try:
                with open('game_config.json', 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.warning(f"Could not load config from JSON: {e}")
                cls._config = cls._get_fallback_config()
        return cls._config
    
    @classmethod
    def _get_fallback_story_fragments(cls) -> List[str]:
        """Fallback story fragments if JSON loading fails."""
        return [
            "Emergency fallback story fragment - JSON data could not be loaded.",
            "This is a backup narrative element to ensure the game remains playable."
        ]
    
    @classmethod
    def _get_fallback_game_data(cls) -> Dict[str, Any]:
        """Fallback game data if JSON loading fails."""
        return {
            "enemy_types": {"scanner": {"symbol": "S", "cpu": 35, "vision": 5, "movement": "STATIC", "name": "Scanner", "damage": 0}},
            "exploits": {"shadow_step": {"name": "Shadow Step", "ram": 3, "heat": 30, "range": 6, "category": "stealth", "damage": 0, "targeting": "SINGLE"}},
            "upgrades": {"ram_boost": {"name": "Memory Expansion", "symbol": "[", "color": (100, 149, 237), "stat_type": "ram", "bonus_amount": 4}},
            "network_configs": {"1": {"enemies": 15, "shadow_coverage": 0.15, "name": "Corporate Network", "background_detection": 1}}
        }
    
    @classmethod
    def _get_fallback_config(cls) -> Dict[str, Any]:
        """Fallback configuration if JSON loading fails."""
        return {
            "gameplay": {"difficulty": "normal", "auto_save": True},
            "graphics": {"ascii_mode": False, "colorblind_mode": False},
            "audio": {"master_volume": 0.7, "music_enabled": True, "sound_enabled": True}
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
            error_msg = f"Failed to save data to {filename}: {e}"
            print(error_msg)
            logging.error(error_msg)
            return False
    
    def load_data(self, filename: str) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            filepath = os.path.join(self.base_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            error_msg = f"Save file not found: {filename}"
            print(error_msg)
            logging.warning(error_msg)
            return {}
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in save file {filename}: {e}"
            print(error_msg)
            logging.error(error_msg)
            return {}
        except Exception as e:
            error_msg = f"Failed to load data from {filename}: {e}"
            print(error_msg)
            logging.error(error_msg)
            return {}
    
    def file_exists(self, filename: str) -> bool:
        """Check if save file exists."""
        filepath = os.path.join(self.base_dir, filename)
        return os.path.exists(filepath)
    
    def list_save_files(self) -> List[str]:
        """List all save files in the directory."""
        try:
            files = [f for f in os.listdir(self.base_dir) if f.endswith('.json')]
            return sorted(files)
        except Exception:
            return []


def get_story_fragments() -> List[str]:
    """Get story fragments - convenience function."""
    return DataLoader.load_story_fragments()