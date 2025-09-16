#!/usr/bin/env python3
"""
Core game entities and data structures.
Extracted from RogueSignalProtocol.py for better organization.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional


class Colors:
    """Modern cyberpunk neon color definitions for the game."""
    # Core neon palette
    WHITE = (255, 255, 255)
    BLACK = (5, 5, 15)  # Deep space blue-black
    RED = (220, 20, 60)  # Standardized to Crimson
    GREEN = (50, 255, 50)  # Standardized to Acid Green
    BLUE = (0, 191, 255)  # Standardized to Electric Blue
    YELLOW = (255, 215, 0)  # Standardized to Golden
    CYAN = (20, 255, 200)  # Standardized to Cyber Teal
    MAGENTA = (255, 20, 255)  # Standardized magenta
    ORANGE = (255, 120, 20)  # Neon orange
    
    # Extended neon palette
    ELECTRIC_PURPLE = (160, 20, 255)  # Electric purple
    NEON_PINK = (255, 20, 147)  # Hot pink
    ACID_GREEN = (50, 255, 50)  # Acid green
    DARK_GREEN = (20, 120, 20)  # Dark green for virus effect
    ELECTRIC_BLUE = (0, 191, 255)  # Electric blue
    CYBER_TEAL = (20, 255, 200)  # Cyber teal
    
    # Code colors (from config)
    CRIMSON = (220, 20, 60)
    AZURE = (30, 144, 255) 
    EMERALD = (50, 205, 50)
    GOLDEN = (255, 215, 0)
    VIOLET = (138, 43, 226)
    SILVER = (192, 192, 192)
    
    # Game-specific colors with neon theme
    FLOOR = (180, 180, 220)  # Bright light dots for empty spaces
    WALL = (120, 140, 180)  # Light blue-gray walls
    SHADOW = (3, 3, 8)  # Dark shadow areas
    PLAYER = (50, 255, 50)  # Standardized to Acid Green
    GATEWAY = (255, 215, 0)  # Standardized to Golden
    
    # Enemy colors matching vision overlay colors
    ENEMY_UNAWARE = (255, 255, 60)  # Yellow (matching vision color scheme)
    ENEMY_ALERT = (255, 165, 60)  # Orange (matching vision color scheme)
    ENEMY_HOSTILE = (255, 60, 60)  # Red (matching vision color scheme)
    
    # Vision overlays with neon glow
    VISION_UNAWARE = (80, 80, 10)  # Yellow glow (default state)
    VISION_ALERT = (80, 50, 10)  # Orange glow (getting suspicious)  
    VISION_HOSTILE = (80, 10, 10)  # Red glow (fully alert and tracking)
    
    # Modern UI colors
    UI_BG = (10, 15, 25)  # Dark blue-gray background
    UI_TEXT = (20, 255, 200)  # Standardized to Cyber Teal text
    UI_ACCENT = (160, 20, 255)  # Electric purple accents
    UI_HIGHLIGHT = (255, 20, 255)  # Standardized magenta highlights
    LOG_BG = (8, 12, 20)  # Darker blue background
    LOG_BORDER = (20, 255, 200)  # Cyber teal border
    LIGHT_GRAY = (160, 170, 190)  # Light cyberpunk gray

    @staticmethod
    def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Interpolate between two colors by the given factor (0.0 to 1.0)."""
        factor = max(0.0, min(1.0, factor))  # Clamp factor
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return (r, g, b)


class EnemyState(Enum):
    """Enemy awareness states."""
    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"


class EnemyMovement(Enum):
    """Enemy movement patterns."""
    STATIC = "static"
    LINEAR = "linear"
    RANDOM = "random"
    SEEK = "seek"
    TRACK = "track"


class TargetingMode(Enum):
    """Exploit targeting modes."""
    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"


@dataclass
class Position:
    """2D position with x, y coordinates."""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        if other is None:
            raise ValueError("Cannot calculate distance to None position")
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def is_valid(self, width: int, height: int) -> bool:
        """Check if position is within bounds."""
        if width <= 0 or height <= 0:
            return False
        return 0 <= self.x < width and 0 <= self.y < height
    
    def is_adjacent_to(self, other: 'Position') -> bool:
        """Check if this position is adjacent to another position."""
        if other is None:
            return False
        return abs(self.x - other.x) <= 1 and abs(self.y - other.y) <= 1
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"({self.x},{self.y})"
    
    def __hash__(self) -> int:
        """Make Position hashable for use as dictionary keys."""
        return hash((self.x, self.y))
    
    @staticmethod
    def create_safe(x: int, y: int, width: int, height: int) -> Optional['Position']:
        """Create a position only if coordinates are valid."""
        pos = Position(x, y)
        if pos.is_valid(width, height):
            return pos
        return None
    
    @staticmethod
    def from_tuple(coords: Tuple[int, int]) -> 'Position':
        """Create position from tuple coordinates."""
        return Position(coords[0], coords[1])
    
    def to_tuple(self) -> Tuple[int, int]:
        """Convert position to tuple for use as dictionary key."""
        return (self.x, self.y)
    
    def __eq__(self, other) -> bool:
        """Equality comparison for Position objects."""
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y


@dataclass
class EnemyTypeDefinition:
    """Definition of an enemy type with all its properties."""
    symbol: str
    cpu: int
    vision: int
    movement: str
    name: str
    damage: int


@dataclass
class ExploitDefinition:
    """Definition of an exploit with all its properties."""
    name: str
    ram: int
    heat: int
    range: int
    category: str
    damage: int
    targeting: str
    description: str = ""


@dataclass
class UpgradeDefinition:
    """Definition of an upgrade item."""
    name: str
    symbol: str
    color: Tuple[int, int, int]
    stat_type: str
    bonus_amount: int
    description: str = ""  # Add missing description field


# Utility functions for position handling
def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(value, max_val))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def validate_coordinates(x: int, y: int, width: int, height: int) -> bool:
    """Validate that coordinates are within bounds."""
    return 0 <= x < width and 0 <= y < height


def calculate_manhattan_distance(pos1: Position, pos2: Position) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)


def get_adjacent_positions(pos: Position, width: int, height: int) -> List[Position]:
    """Get all valid adjacent positions around a given position."""
    adjacent = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            new_x, new_y = pos.x + dx, pos.y + dy
            if validate_coordinates(new_x, new_y, width, height):
                adjacent.append(Position(new_x, new_y))
    return adjacent


def format_position_key(pos: Position) -> str:
    """Format position as string key for dictionaries."""
    return f"{pos.x},{pos.y}"


def parse_position_key(key: str) -> Optional[Position]:
    """Parse string key back to Position."""
    try:
        x, y = map(int, key.split(','))
        return Position(x, y)
    except (ValueError, AttributeError):
        return None


def parse_coordinate_string(coord_str: str) -> Optional[Position]:
    """Parse coordinate string like '10,20' to Position."""
    try:
        parts = coord_str.strip().split(',')
        if len(parts) == 2:
            x, y = int(parts[0].strip()), int(parts[1].strip())
            return Position(x, y)
    except (ValueError, AttributeError):
        pass
    return None


def validate_position_bounds(position: Position, width: int, height: int) -> bool:
    """Validate that a position is within the given bounds."""
    return position.is_valid(width, height)


def ensure_color_tuple(color) -> Tuple[int, int, int]:
    """Ensure color is a valid RGB tuple."""
    if isinstance(color, str):
        # Handle string color names - convert to Colors class attributes
        color_name = color.upper()
        if hasattr(Colors, color_name):
            return getattr(Colors, color_name)
        else:
            return Colors.WHITE
    elif isinstance(color, (list, tuple)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    else:
        return Colors.WHITE  # Default fallback