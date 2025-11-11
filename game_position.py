#!/usr/bin/env python3
"""
Position class and coordinate utilities.

Defines the Position dataclass for 2D coordinates with:
- Distance calculations (Euclidean and grid/Chebyshev)
- Validation methods
- Conversion utilities
- Helper functions for coordinate parsing

Extracted from game_entities.py to improve modularity.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional


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

        NOTE: For gameplay purposes (exploits, effects), use grid_distance_to() instead!
        Euclidean distance treats diagonals as ~1.414, which doesn't match game grid logic.

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

    def grid_distance_to(self, other: 'Position') -> int:
        """
        Calculate Chebyshev (grid/chessboard) distance to another position.

        This is the CORRECT distance for gameplay mechanics (exploits, effects, etc).
        Treats diagonal movement as distance 1, matching 8-directional grid movement.

        Examples:
            - (0,0) to (1,0) = 1  (orthogonal)
            - (0,0) to (1,1) = 1  (diagonal - counts as 1 step!)
            - (0,0) to (2,1) = 2  (max of horizontal/vertical steps)

        IMPORTANT: For range-1 exploits like Buffer Overflow, ALL 8 adjacent tiles
        (including diagonals) should be valid targets. Use this method, not distance_to()!

        Args:
            other: Target position

        Returns:
            Integer grid distance (diagonals count as 1)

        Raises:
            ValueError: If other is None
        """
        if other is None:
            raise ValueError("Cannot calculate distance to None position")
        return max(abs(self.x - other.x), abs(self.y - other.y))

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

    def angle_to(self, other: 'Position') -> float:
        """
        Calculate angle in degrees from this position to another.

        Used for rotating sprites to point in the movement direction.
        0° = East (right), 90° = South (down), 180° = West (left), 270° = North (up)

        Args:
            other: Target position

        Returns:
            Angle in degrees (0-360, clockwise from east)
        """
        if other is None:
            return 0.0

        dx = other.x - self.x
        dy = other.y - self.y

        if dx == 0 and dy == 0:
            return 0.0  # Same position, default to east

        # atan2 returns angle in radians from east (0 = right)
        # Positive y is down in screen coordinates
        angle_rad = math.atan2(dy, dx)

        # Convert to degrees
        angle_deg = math.degrees(angle_rad)

        # Ensure positive range (0-360)
        if angle_deg < 0:
            angle_deg += 360

        return angle_deg

    def arrow_char_to(self, other: 'Position') -> str:
        """
        Get Unicode arrow character pointing from this position to another.

        Used for rendering directional indicators in glyph mode.
        Supports all 8 cardinal and diagonal directions.

        Args:
            other: Target position

        Returns:
            Unicode arrow character (→ ↑ ← ↓ ↗ ↖ ↙ ↘)
        """
        if other is None:
            return '→'  # Default to right

        dx = other.x - self.x
        dy = other.y - self.y

        if dx == 0 and dy == 0:
            return '·'  # Same position, use dot

        # Normalize to -1, 0, or 1
        dx_norm = 0 if dx == 0 else (1 if dx > 0 else -1)
        dy_norm = 0 if dy == 0 else (1 if dy > 0 else -1)

        # Map to arrow characters (all Unicode)
        arrow_map = {
            (1, 0): '→',   # East
            (1, -1): '↗',  # Northeast
            (0, -1): '↑',  # North
            (-1, -1): '↖', # Northwest
            (-1, 0): '←',  # West
            (-1, 1): '↙',  # Southwest
            (0, 1): '↓',   # South
            (1, 1): '↘',   # Southeast
        }

        return arrow_map.get((dx_norm, dy_norm), '→')

    def __eq__(self, other) -> bool:
        """Equality comparison for Position objects."""
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y


def parse_coordinate_string(coord_str: str) -> Optional[Position]:
    """
    Parse coordinate string from save file format.

    Supports format: "x,y" (e.g., "10,5")

    Args:
        coord_str: Coordinate string to parse

    Returns:
        Position if parse successful, None if malformed
    """
    try:
        parts = coord_str.split(',')
        if len(parts) == 2:
            x = int(parts[0])
            y = int(parts[1])
            return Position(x, y)
    except (ValueError, AttributeError):
        pass
    return None
