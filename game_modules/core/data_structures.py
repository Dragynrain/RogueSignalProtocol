"""
Core data structures and enums for the Rogue Signal Protocol game.
"""

import math
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple


class EnemyState(Enum):
    """Possible states for enemies in the game."""
    PATROL = "patrol"
    HUNT = "hunt"
    ALERT = "alert"
    DISABLED = "disabled"


class EnemyMovement(Enum):
    """Movement patterns for enemies."""
    STATIC = "static"
    PATROL = "patrol"
    RANDOM = "random"
    GUARD = "guard"


class TargetingMode(Enum):
    """Different targeting modes for exploits."""
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
    
    def get_neighbors(self) -> list['Position']:
        """Get all 8 adjacent positions."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbors.append(Position(self.x + dx, self.y + dy))
        return neighbors
    
    def manhattan_distance_to(self, other: 'Position') -> int:
        """Calculate Manhattan distance to another position."""
        if other is None:
            raise ValueError("Cannot calculate distance to None position")
        return abs(self.x - other.x) + abs(self.y - other.y)