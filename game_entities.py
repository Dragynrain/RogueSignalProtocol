#!/usr/bin/env python3
"""
Core game entities and data structures.

Defines foundational data classes:
- Position: 2D coordinates with utility methods
- ColorManager: JSON-driven color configuration (singleton)
- Enemy/Exploit/Upgrade definitions
- Enums for game states (EnemyState, EnemyMovement, TargetingMode)
- PositionValidator: Centralized position validation logic
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
from data_loading import DataLoader


class ColorManager:
    """
    JSON-driven color management for the game (singleton pattern).

    Loads all colors from game_config.json on first access and caches them.
    Ensures consistent color scheme across the entire game and fails fast
    if required colors are missing from configuration. No hardcoded fallbacks.

    The singleton pattern ensures only one instance loads the JSON once.
    """

    _instance = None
    _colors = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_colors()
        return cls._instance
    
    def _load_colors(self):
        """
        Load colors from JSON configuration with strict validation.

        Fails fast if any required color category or specific color is missing.
        This ensures configuration errors are caught immediately rather than
        causing subtle bugs during gameplay. No fallback values are used.

        Required categories: basic, game_elements, data_codes, message_log, enemies, ui
        """
        import logging

        try:
            config = DataLoader.load_config()
            self._colors = {}

            # Ensure colors section exists
            if 'colors' not in config:
                error_msg = "CRITICAL CONFIG ERROR: 'colors' section missing from game_config.json"
                logging.error(error_msg)
                logging.error(f"Available sections: {list(config.keys())}")
                raise KeyError("Required 'colors' section missing from game_config.json")

            color_config = config['colors']

            # Load all categories - FAIL if missing
            required_categories = ['basic', 'game_elements', 'data_codes', 'message_log', 'enemies', 'ui']
            for category in required_categories:
                if category not in color_config:
                    error_msg = f"CRITICAL CONFIG ERROR: 'colors.{category}' section missing from game_config.json"
                    logging.error(error_msg)
                    logging.error(f"Available color categories: {list(color_config.keys())}")
                    raise KeyError(f"Required color category missing: {category}")

            # Load basic, game_elements, data_codes, message_log categories
            for category in ['basic', 'game_elements', 'data_codes', 'message_log']:
                for name, rgb in color_config[category].items():
                    self._colors[name.upper()] = tuple(rgb)

            # Enemy colors - FAIL if missing
            enemies = color_config['enemies']
            required_enemy_colors = ['unaware', 'alert', 'hostile']
            for color_name in required_enemy_colors:
                if color_name not in enemies:
                    error_msg = f"CRITICAL CONFIG ERROR: 'colors.enemies.{color_name}' missing from game_config.json"
                    logging.error(error_msg)
                    logging.error(f"Available enemy colors: {list(enemies.keys())}")
                    raise KeyError(f"Required enemy color missing: {color_name}")

            self._colors['ENEMY_UNAWARE'] = tuple(enemies['unaware'])
            self._colors['ENEMY_ALERT'] = tuple(enemies['alert'])
            self._colors['ENEMY_HOSTILE'] = tuple(enemies['hostile'])

            # UI colors - FAIL if missing
            ui = color_config['ui']
            required_ui_colors = ['background', 'text', 'accent', 'highlight', 'electric_purple']
            for color_name in required_ui_colors:
                if color_name not in ui:
                    error_msg = f"CRITICAL CONFIG ERROR: 'colors.ui.{color_name}' missing from game_config.json"
                    logging.error(error_msg)
                    logging.error(f"Available UI colors: {list(ui.keys())}")
                    raise KeyError(f"Required UI color missing: {color_name}")

            self._colors['UI_BG'] = tuple(ui['background'])
            self._colors['UI_TEXT'] = tuple(ui['text'])
            self._colors['UI_ACCENT'] = tuple(ui['accent'])
            self._colors['UI_HIGHLIGHT'] = tuple(ui['highlight'])
            self._colors['ELECTRIC_PURPLE'] = tuple(ui['electric_purple'])

            # Derived colors
            self._colors['VISION_UNAWARE'] = self._darken_color(self._colors['ENEMY_UNAWARE'], 0.3)
            self._colors['VISION_ALERT'] = self._darken_color(self._colors['ENEMY_ALERT'], 0.3)
            self._colors['VISION_HOSTILE'] = self._darken_color(self._colors['ENEMY_HOSTILE'], 0.3)
            self._colors['LOG_BG'] = (8, 12, 20)
            self._colors['LOG_BORDER'] = self._colors['UI_TEXT']

            # LIGHT_GRAY should be in basic colors
            if 'LIGHT_GRAY' not in self._colors:
                error_msg = "CRITICAL CONFIG ERROR: 'light_gray' missing from colors.basic in game_config.json"
                logging.error(error_msg)
                raise KeyError("Required color missing: light_gray")

        except KeyError as e:
            # Re-raise KeyError to fail immediately
            raise
        except Exception as e:
            error_msg = f"CRITICAL CONFIG ERROR: Failed to load colors from game_config.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise RuntimeError(f"Failed to load colors: {e}") from e
    
    def _darken_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """
        Darken a color by multiplying each RGB component by the factor.

        Args:
            color: RGB tuple (0-255 for each component)
            factor: Darkening factor (0.0 = black, 1.0 = original color)

        Returns:
            Darkened RGB tuple
        """
        return tuple(int(c * factor) for c in color)

    def get_color(self, name: str) -> Tuple[int, int, int]:
        """
        Get color by name (case-insensitive).

        Args:
            name: Color name (e.g., 'white', 'ENEMY_HOSTILE')

        Returns:
            RGB tuple

        Raises:
            KeyError: If color name not found in configuration
        """
        name_upper = name.upper()
        if name_upper not in self._colors:
            import logging
            logging.error(f"CRITICAL CONFIG ERROR: Color '{name}' not found in game configuration")
            logging.error(f"Available colors: {sorted(self._colors.keys())}")
            raise KeyError(f"Color '{name}' not found in configuration. Check game_rules.json colors section.")
        return self._colors[name_upper]

    @staticmethod
    def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """
        Interpolate between two colors.

        Useful for creating smooth color transitions (e.g., heat meters, health bars).

        Args:
            color1: Starting RGB color
            color2: Ending RGB color
            factor: Interpolation factor (0.0 = color1, 1.0 = color2)

        Returns:
            Interpolated RGB tuple
        """
        factor = max(0.0, min(1.0, factor))
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return (r, g, b)


class Colors:
    """
    Backward-compatible color access wrapper for ColorManager.

    Provides attribute-style access to colors (e.g., Colors.WHITE, Colors.ENEMY_HOSTILE).
    Delegates to the singleton ColorManager instance under the hood.
    """
    
    _manager = None
    
    def __init__(self):
        if Colors._manager is None:
            Colors._manager = ColorManager()
    
    def __getattr__(self, name: str):
        if Colors._manager is None:
            Colors._manager = ColorManager()
        return Colors._manager.get_color(name)
    
    @classmethod
    def get_color(cls, name: str) -> Tuple[int, int, int]:
        """Get color by name."""
        if cls._manager is None:
            cls._manager = ColorManager()
        return cls._manager.get_color(name)
    
    @staticmethod
    def interpolate_color(color1: Tuple[int, int, int], color2: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Interpolate between two colors by the given factor (0.0 to 1.0)."""
        return ColorManager.interpolate_color(color1, color2, factor)


# Create a singleton instance for backward compatibility
Colors = Colors()


class EnemyState(Enum):
    """
    Enemy awareness states.

    UNAWARE: Enemy has not detected player (green)
    ALERT: Enemy suspects player presence, searching (yellow) - lasts 1 turn
    HOSTILE: Enemy actively pursuing player (red)
    """
    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"


class EnemyMovement(Enum):
    """
    Enemy movement patterns defining AI behavior.

    STATIC: Does not move unless alerted
    PATROL: Follows predefined patrol points in sequence
    RANDOM: Wanders randomly
    SEEK: Actively seeks player (used for hostile behavior)
    ADMIN: Perfect vision and constant seeking (boss-type enemy)
    TRACK: Legacy tracking behavior
    VIRUS: Randomly selects STATIC, PATROL, or RANDOM on spawn (unpredictable)
    """
    STATIC = "static"
    PATROL = "patrol"
    RANDOM = "random"
    SEEK = "seek"
    ADMIN = "admin"
    TRACK = "track"
    VIRUS = "virus"


class TargetingMode(Enum):
    """
    Exploit targeting modes.

    NONE: No targeting required (instant self-buff/debuff)
    SINGLE: Single target selection
    AREA: Area of effect around target point
    DIRECTION: Directional targeting (not currently used)
    """
    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"


@dataclass
class Position:
    """
    2D position with x, y coordinates and utility methods.

    Immutable-style dataclass representing a point on the game map.
    Provides distance calculations, validation, and conversion utilities.
    Hashable for use as dictionary keys.
    """
    x: int
    y: int

    def distance_to(self, other: 'Position') -> float:
        """
        Calculate Euclidean distance to another position.

        Args:
            other: Target position

        Returns:
            Float distance (uses sqrt, so diagonal = ~1.414)

        Raises:
            ValueError: If other is None
        """
        if other is None:
            raise ValueError("Cannot calculate distance to None position")
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def is_valid(self, width: int, height: int) -> bool:
        """
        Check if position is within rectangular bounds.

        Args:
            width: Map width
            height: Map height

        Returns:
            True if 0 <= x < width and 0 <= y < height
        """
        if width <= 0 or height <= 0:
            return False
        return 0 <= self.x < width and 0 <= self.y < height
    
    def is_adjacent_to(self, other: 'Position') -> bool:
        """
        Check if this position is adjacent to another (including diagonals).

        Args:
            other: Target position

        Returns:
            True if positions differ by at most 1 in both x and y
        """
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
    description: str = ""


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
    effect_duration: int = 0  # Duration in turns for effects (stun, invisibility, scan, etc.)
    effect_radius: int = 0  # Radius of effect for area exploits (0 for single-target/no effect)

    def get_detail_lines(self) -> list[str]:
        """
        Build formatted detail lines for this exploit.

        Returns a list of strings containing all exploit information,
        used by both the examine command and hover tooltips.

        Returns:
            List of formatted detail strings
        """
        lines = []
        lines.append(f"=== {self.name} ===")
        lines.append(f"Category: {self.category.title()}")
        lines.append(f"RAM Cost: {self.ram}")
        lines.append(f"Heat Cost: {self.heat}")

        if self.damage > 0:
            lines.append(f"Damage: {self.damage}")
        if self.range > 0:
            lines.append(f"Range: {self.range} tiles")

        lines.append(f"Targeting: {self.targeting.name}")
        lines.append(f"Effect: {self.description}")

        return lines


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
    """
    Clamp a value between min and max bounds.

    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Value constrained to [min_val, max_val]
    """
    return max(min_val, min(value, max_val))


def format_position_key(pos: Position) -> str:
    """
    Format position as string key for dictionaries.

    Args:
        pos: Position to format

    Returns:
        String in format "x,y"
    """
    return f"{pos.x},{pos.y}"

def parse_position_key(key: str) -> Optional[Position]:
    """
    Parse string key back to Position.

    Args:
        key: String in format "x,y"

    Returns:
        Position object, or None if parsing fails
    """
    try:
        x, y = map(int, key.split(','))
        return Position(x, y)
    except (ValueError, AttributeError):
        return None

def parse_coordinate_string(coord_str: str) -> Optional[Position]:
    """Parse coordinate string like '10,20' to Position."""
    try:
        parts = coord_str.strip().split(',')
        return Position(int(parts[0].strip()), int(parts[1].strip())) if len(parts) == 2 else None
    except (ValueError, AttributeError):
        return None

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


class PositionValidator:
    """
    Centralized position validation utilities to avoid code duplication.

    Provides static methods for common validation patterns:
    - Boundary checks
    - Wall collision detection
    - Item/enemy placement validation
    - Movement validation

    All methods are static as they don't maintain state.
    """

    @staticmethod
    def is_within_bounds(position: Position, width: int, height: int) -> bool:
        """Check if position is within map bounds."""
        return 0 <= position.x < width and 0 <= position.y < height

    @staticmethod
    def is_not_on_border(position: Position, width: int, height: int) -> bool:
        """Check if position is not on the map border."""
        return (position.x != 0 and position.x != width - 1 and
                position.y != 0 and position.y != height - 1)

    @staticmethod
    def is_basic_valid_position(position: Position, game_map) -> bool:
        """Basic position validation - within bounds and not a wall."""
        return (PositionValidator.is_within_bounds(position, game_map.width, game_map.height) and
                game_map.is_valid_position(position))

    @staticmethod
    def is_valid_for_placement(position: Position, game_map, min_distance_from_spawn: float = 5.0,
                              check_existing_items: bool = False) -> bool:
        """Check if position is valid for item/node placement.

        Ensures items don't spawn on gateway or other critical locations.
        """
        from game_config import GameConfig

        # Boundary and wall check
        if not (0 < position.x < GameConfig.MAP_WIDTH - 1 and 0 < position.y < GameConfig.MAP_HEIGHT - 1
                and game_map.is_valid_position(position)):
            return False

        # Gateway check - never place items on gateway
        if game_map.gateway and position.x == game_map.gateway.x and position.y == game_map.gateway.y:
            return False

        # Spawn distance check
        dx, dy = position.x - 5, position.y - 5
        if dx * dx + dy * dy <= min_distance_from_spawn * min_distance_from_spawn:
            return False

        # Check existing items
        if check_existing_items:
            pos_tuple = (position.x, position.y)
            if any(pos_tuple in items for items in [game_map.code_hacks, game_map.cooling_nodes,
                   game_map.cpu_recovery_nodes, game_map.ghost_nodes, game_map.exploit_pickups]):
                return False

        return True

    @staticmethod
    def is_valid_for_enemy_placement(position: Position, game_map, enemies_list, player_position: Position,
                                   check_existing_items: bool = True) -> bool:
        """Check if position is valid for enemy placement."""
        return (position.x != player_position.x or position.y != player_position.y) and \
               PositionValidator.is_valid_for_placement(position, game_map, 12.0, check_existing_items) and \
               (position.x, position.y) not in {(e.x, e.y) for e in enemies_list}

    @staticmethod
    def is_valid_for_enemy_movement(position: Position, game_map, enemies_list, player_position: Position, current_enemy) -> bool:
        """Check if position is valid for enemy movement."""
        # Basic position validation
        if not PositionValidator.is_basic_valid_position(position, game_map):
            return False

        # Can't move to player position
        if position.x == player_position.x and position.y == player_position.y:
            return False

        # Can't move to a position occupied by another enemy
        for other_enemy in enemies_list:
            if other_enemy != current_enemy and other_enemy.x == position.x and other_enemy.y == position.y:
                return False

        return True