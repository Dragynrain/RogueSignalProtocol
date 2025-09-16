"""
JSON data loading system with improved error handling and caching.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


class DataLoader:
    """
    Handles loading of JSON configuration and game data files.
    
    Uses caching to avoid repeated file I/O and provides robust
    error handling with fallback data.
    """
    
    _story_fragments: Optional[List[str]] = None
    _game_data: Optional[Dict[str, Any]] = None
    _config: Optional[Dict[str, Any]] = None
    
    @classmethod
    def load_story_fragments(cls, file_path: str = 'story_content.json') -> List[str]:
        """
        Load story fragments from JSON file.
        
        Args:
            file_path: Path to the story content JSON file
            
        Returns:
            List of story fragment strings
            
        Raises:
            DataLoadError: If loading fails and no fallback is available
        """
        if cls._story_fragments is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'fragments' not in data:
                        raise DataLoadError(f"Missing 'fragments' key in {file_path}")
                    cls._story_fragments = data['fragments']
                    logging.info(f"Loaded {len(cls._story_fragments)} story fragments")
                    
            except FileNotFoundError:
                logging.warning(f"Story content file not found: {file_path}")
                cls._story_fragments = cls._get_fallback_story_fragments()
                
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in {file_path}: {e}")
                cls._story_fragments = cls._get_fallback_story_fragments()
                
            except (KeyError, TypeError) as e:
                logging.error(f"Invalid story content format in {file_path}: {e}")
                cls._story_fragments = cls._get_fallback_story_fragments()
                
        return cls._story_fragments
    
    @classmethod
    def load_game_data(cls, file_path: str = 'game_data.json') -> Dict[str, Any]:
        """
        Load game data from JSON file.
        
        Args:
            file_path: Path to the game data JSON file
            
        Returns:
            Dictionary containing game data
        """
        if cls._game_data is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cls._game_data = json.load(f)
                    logging.info(f"Loaded game data from {file_path}")
                    
            except FileNotFoundError:
                logging.warning(f"Game data file not found: {file_path}")
                cls._game_data = cls._get_fallback_game_data()
                
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in {file_path}: {e}")
                cls._game_data = cls._get_fallback_game_data()
                
        return cls._game_data
    
    @classmethod
    def load_config(cls, file_path: str = 'game_config.json') -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            file_path: Path to the configuration JSON file
            
        Returns:
            Dictionary containing configuration data
        """
        if cls._config is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
                    logging.info(f"Loaded configuration from {file_path}")
                    
            except FileNotFoundError:
                logging.warning(f"Config file not found: {file_path}")
                cls._config = cls._get_fallback_config()
                
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in {file_path}: {e}")
                cls._config = cls._get_fallback_config()
                
        return cls._config
    
    @classmethod
    def reload_all(cls) -> None:
        """Force reload of all cached data."""
        cls._story_fragments = None
        cls._game_data = None
        cls._config = None
        logging.info("Cleared all cached data")
    
    @classmethod
    def _get_fallback_story_fragments(cls) -> List[str]:
        """Fallback story fragments if JSON loading fails."""
        return [
            "System malfunction detected. Initiating emergency protocols...",
            "Network connection established. Beginning infiltration sequence.",
            "WARNING: Hostile entities detected in the local network.",
            "Data extraction in progress. Maintain stealth protocols.",
            "Emergency fallback story fragment - JSON data could not be loaded."
        ]
    
    @classmethod
    def _get_fallback_game_data(cls) -> Dict[str, Any]:
        """Fallback game data if JSON loading fails."""
        return {
            "enemy_types": {
                "scanner": {
                    "symbol": "S", "cpu": 35, "vision": 5, 
                    "movement": "STATIC", "name": "Scanner", "damage": 0
                }
            },
            "exploits": {
                "shadow_step": {
                    "name": "Shadow Step", "ram": 3, "heat": 30, 
                    "range": 6, "category": "stealth", "damage": 0, 
                    "targeting": "SINGLE"
                }
            },
            "upgrades": {
                "ram_boost": {
                    "name": "Memory Expansion", "symbol": "[", 
                    "color": (100, 149, 237), "stat_type": "ram", 
                    "bonus_amount": 4
                }
            },
            "network_configs": {
                "1": {
                    "enemies": 15, "shadow_coverage": 0.15, 
                    "name": "Corporate Network", "background_detection": 1
                }
            }
        }
    
    @classmethod
    def _get_fallback_config(cls) -> Dict[str, Any]:
        """Fallback configuration if JSON loading fails."""
        return {
            "screen_width": 120,
            "screen_height": 40,
            "tileset": "dejavu10x10_gs_tc.png",
            "audio_enabled": True,
            "graphics_mode": True,
            "debug_mode": False
        }