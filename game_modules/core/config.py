"""
Game configuration constants and settings.
"""

from typing import Dict, Any


class GameConfig:
    """Central game configuration constants."""
    
    # Screen and display
    SCREEN_WIDTH = 120
    SCREEN_HEIGHT = 40
    
    # Map dimensions
    MAP_WIDTH = 100
    MAP_HEIGHT = 35
    
    # Gameplay constants
    ADJACENT_VISIBILITY_THRESHOLD = 1.5
    ADJACENT_THRESHOLD = 1.5
    SHADOW_VISION_REDUCTION_FACTOR = 3
    
    # Player stat limits
    MAX_RAM_CAPACITY = 32
    MAX_CPU_CAPACITY = 300
    MAX_HEAT_CAPACITY = 200
    
    # File paths
    DEFAULT_TILESET = "dejavu10x10_gs_tc.png"
    SAVE_FILENAME = "rogue_signal_save.json"
    PROGRESS_FILENAME = "rogue_signal_progress.json"
    SETTINGS_FILENAME = "user_settings.json"
    
    # Game balance
    TURN_HEAT_REDUCTION = 2
    NODE_INTERACTION_HEAT_REDUCTION = 10
    EXPLOIT_BASE_HEAT_COST = 20
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """Get default configuration dictionary."""
        return {
            'screen_width': cls.SCREEN_WIDTH,
            'screen_height': cls.SCREEN_HEIGHT,
            'map_width': cls.MAP_WIDTH,
            'map_height': cls.MAP_HEIGHT,
            'tileset': cls.DEFAULT_TILESET,
            'audio_enabled': True,
            'graphics_mode': True,
            'debug_mode': False
        }