"""
Color definitions for the Rogue Signal Protocol game.
"""

from typing import Tuple

# Type alias for RGB color tuples
Color = Tuple[int, int, int]


class Colors:
    """Central color definitions for consistent theming."""
    
    # UI Colors
    WHITE: Color = (255, 255, 255)
    BLACK: Color = (0, 0, 0)
    GRAY: Color = (128, 128, 128)
    LIGHT_GRAY: Color = (192, 192, 192)
    DARK_GRAY: Color = (64, 64, 64)
    
    # Cyberpunk Theme Colors
    NEON_BLUE: Color = (0, 255, 255)
    ELECTRIC_BLUE: Color = (0, 191, 255)
    CYBER_GREEN: Color = (0, 255, 0)
    NEON_PINK: Color = (255, 20, 147)
    PURPLE: Color = (160, 32, 240)
    
    # Game Element Colors
    PLAYER: Color = (100, 149, 237)  # Steel blue
    ENEMY: Color = (220, 20, 60)     # Crimson
    SHADOW: Color = (25, 25, 112)    # Midnight blue
    WALL: Color = (105, 105, 105)    # Dim gray
    FLOOR: Color = (47, 79, 79)      # Dark slate gray
    
    # Status Colors
    HEALTH: Color = (0, 128, 0)      # Green
    DANGER: Color = (255, 0, 0)      # Red
    WARNING: Color = (255, 165, 0)   # Orange
    SUCCESS: Color = (0, 255, 0)     # Bright green
    
    # UI Element Colors
    MENU_BACKGROUND: Color = (30, 30, 30)
    MENU_BORDER: Color = (100, 100, 100)
    MENU_TEXT: Color = (200, 200, 200)
    MENU_HIGHLIGHT: Color = (0, 255, 255)
    
    # Heat/Stealth Colors
    HEAT_LOW: Color = (0, 255, 0)    # Green
    HEAT_MEDIUM: Color = (255, 255, 0)  # Yellow
    HEAT_HIGH: Color = (255, 0, 0)   # Red
    STEALTH: Color = (138, 43, 226)  # Blue violet
    
    @classmethod
    def get_heat_color(cls, heat_level: float) -> Color:
        """Get color based on heat level (0.0 to 1.0)."""
        if heat_level <= 0.3:
            return cls.HEAT_LOW
        elif heat_level <= 0.7:
            return cls.HEAT_MEDIUM
        else:
            return cls.HEAT_HIGH
    
    @classmethod
    def interpolate_color(cls, color1: Color, color2: Color, factor: float) -> Color:
        """Interpolate between two colors. Factor should be 0.0 to 1.0."""
        factor = max(0.0, min(1.0, factor))  # Clamp to valid range
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return (r, g, b)