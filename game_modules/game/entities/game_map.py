"""
Game map class managing terrain, features, and spatial queries.
"""

from typing import Dict, Set, Tuple, Optional, TYPE_CHECKING
import tcod
from tcod import libtcodpy

from ...core.data_structures import Position
from ...core.exceptions import InvalidPositionError

if TYPE_CHECKING:
    from ...inventory import DataPatch, ExploitItem, StoryFragment


class MapConfig:
    """Configuration constants for map functionality."""
    FOV_ALGORITHM = libtcodpy.FOV_BASIC
    FOV_LIGHT_WALLS = True
    FOV_RADIUS = 100  # Large radius for line of sight calculations


class GameMap:
    """
    Game world map with terrain, features, and spatial functionality.
    
    Manages walls, shadows, special nodes, items, and provides spatial
    queries like line of sight, pathfinding, and feature detection.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize game map with specified dimensions.
        
        Args:
            width: Map width in tiles
            height: Map height in tiles
            
        Raises:
            ValueError: If width or height are non-positive
        """
        if width <= 0 or height <= 0:
            raise ValueError("Map dimensions must be positive")
            
        self.width = width
        self.height = height
        
        # Terrain sets (using tuples for efficient set operations)
        self.walls: Set[Tuple[int, int]] = set()
        self.shadows: Set[Tuple[int, int]] = set()
        
        # Feature sets
        self.cooling_nodes: Set[Tuple[int, int]] = set()
        self.cpu_recovery_nodes: Set[Tuple[int, int]] = set()
        self.ghost_nodes: Set[Tuple[int, int]] = set()
        
        # Item collections
        self.data_patches: Dict[Tuple[int, int], 'DataPatch'] = {}
        self.exploit_pickups: Dict[Tuple[int, int], 'ExploitItem'] = {}
        self.permanent_upgrades: Dict[Tuple[int, int], str] = {}
        self.story_fragments: Dict[Tuple[int, int], 'StoryFragment'] = {}
        
        # Special locations
        self.gateway: Optional[Position] = None
        
        # Memory and fog of war system
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.last_known_enemy_positions: Dict[int, Tuple[Position, int]] = {}
        
        # TCOD FOV map for line of sight calculations
        self._fov_map: Optional[tcod.map.Map] = None
        self._initialize_fov_map()
    
    def _initialize_fov_map(self) -> None:
        """Initialize TCOD FOV map for line of sight calculations."""
        try:
            self._fov_map = tcod.map.Map(self.width, self.height)
            self._update_fov_map()
        except Exception:
            # Fallback if TCOD FOV unavailable
            self._fov_map = None
    
    def _update_fov_map(self) -> None:
        """Update TCOD FOV map with current wall configuration."""
        if not self._fov_map:
            return
            
        # Set all tiles as walkable and transparent by default
        for x in range(self.width):
            for y in range(self.height):
                is_wall = (x, y) in self.walls
                # Walls block movement and sight
                self._fov_map.transparent[x, y] = not is_wall
                self._fov_map.walkable[x, y] = not is_wall
    
    # ========== TERRAIN QUERIES ==========
    
    def is_wall(self, position: Position) -> bool:
        """
        Check if position contains a wall.
        
        Args:
            position: Position to check
            
        Returns:
            True if position is a wall or out of bounds
        """
        if not position.is_valid(self.width, self.height):
            return True
        return (position.x, position.y) in self.walls
    
    def is_shadow(self, position: Position) -> bool:
        """
        Check if position is in shadow (includes ghost nodes).
        
        Args:
            position: Position to check
            
        Returns:
            True if position provides shadow cover
        """
        if not position.is_valid(self.width, self.height):
            return False
        
        pos_tuple = (position.x, position.y)
        # Ghost nodes function as shadows in addition to their special effect
        return pos_tuple in self.shadows or pos_tuple in self.ghost_nodes
    
    def is_valid_position(self, position: Position) -> bool:
        """
        Check if position is valid for movement (not a wall, in bounds).
        
        Args:
            position: Position to check
            
        Returns:
            True if position is walkable
        """
        return (position.is_valid(self.width, self.height) and 
                not self.is_wall(position))
    
    # ========== FEATURE QUERIES ==========
    
    def is_cooling_node(self, position: Position) -> bool:
        """Check if position contains a cooling node."""
        return (position.x, position.y) in self.cooling_nodes
    
    def is_cpu_recovery_node(self, position: Position) -> bool:
        """Check if position contains a CPU recovery node."""
        return (position.x, position.y) in self.cpu_recovery_nodes
    
    def is_ghost_node(self, position: Position) -> bool:
        """Check if position contains a ghost node."""
        return (position.x, position.y) in self.ghost_nodes
    
    def is_gateway(self, position: Position) -> bool:
        """Check if position is the level gateway/exit."""
        return self.gateway is not None and position.x == self.gateway.x and position.y == self.gateway.y
    
    # ========== ITEM QUERIES ==========
    
    def has_data_patch(self, position: Position) -> bool:
        """Check if position contains a data patch."""
        return (position.x, position.y) in self.data_patches
    
    def get_data_patch(self, position: Position) -> Optional['DataPatch']:
        """Get data patch at position."""
        return self.data_patches.get((position.x, position.y))
    
    def has_exploit_pickup(self, position: Position) -> bool:
        """Check if position contains an exploit pickup."""
        return (position.x, position.y) in self.exploit_pickups
    
    def get_exploit_pickup(self, position: Position) -> Optional['ExploitItem']:
        """Get exploit pickup at position."""
        return self.exploit_pickups.get((position.x, position.y))
    
    def has_upgrade(self, position: Position) -> bool:
        """Check if position contains a permanent upgrade."""
        return (position.x, position.y) in self.permanent_upgrades
    
    def get_upgrade(self, position: Position) -> Optional[str]:
        """Get upgrade key at position."""
        return self.permanent_upgrades.get((position.x, position.y))
    
    def has_story_fragment(self, position: Position) -> bool:
        """Check if position contains a story fragment."""
        return (position.x, position.y) in self.story_fragments
    
    def get_story_fragment(self, position: Position) -> Optional['StoryFragment']:
        """Get story fragment at position."""
        return self.story_fragments.get((position.x, position.y))
    
    # ========== SPATIAL OPERATIONS ==========
    
    def can_see_position(self, from_pos: Position, to_pos: Position, 
                        max_range: int = None) -> bool:
        """
        Check if there's line of sight between two positions.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            max_range: Maximum sight range (None for unlimited)
            
        Returns:
            True if target is visible from starting position
        """
        # Check range if specified
        if max_range is not None:
            distance = from_pos.distance_to(to_pos)
            if distance > max_range:
                return False
        
        # Use TCOD FOV if available
        if self._fov_map:
            try:
                # Compute FOV from starting position
                tcod.map.compute_fov(
                    self._fov_map,
                    from_pos.x, from_pos.y,
                    radius=max_range or MapConfig.FOV_RADIUS,
                    algorithm=MapConfig.FOV_ALGORITHM,
                    light_walls=MapConfig.FOV_LIGHT_WALLS
                )
                return self._fov_map.fov[to_pos.x, to_pos.y]
            except (IndexError, AttributeError):
                # Fall back to simple line check
                pass
        
        # Fallback: simple line of sight check
        return self.has_line_of_sight(from_pos, to_pos)
    
    def has_line_of_sight(self, from_pos: Position, to_pos: Position) -> bool:
        """
        Simple line of sight check using Bresenham's line algorithm.
        
        Args:
            from_pos: Starting position
            to_pos: Target position
            
        Returns:
            True if there's a clear line between positions
        """
        # Use TCOD's line algorithm for accuracy
        try:
            line_points = list(tcod.los.bresenham(
                from_pos.x, from_pos.y, to_pos.x, to_pos.y
            ))
            
            # Check each point in the line (excluding start and end)
            for x, y in line_points[1:-1]:
                if (x, y) in self.walls:
                    return False
            return True
            
        except (ImportError, AttributeError):
            # Fallback: simple implementation
            return self._simple_line_of_sight(from_pos, to_pos)
    
    def _simple_line_of_sight(self, from_pos: Position, to_pos: Position) -> bool:
        """Simple line of sight implementation as fallback."""
        dx = abs(to_pos.x - from_pos.x)
        dy = abs(to_pos.y - from_pos.y)
        
        x, y = from_pos.x, from_pos.y
        
        x_inc = 1 if to_pos.x > from_pos.x else -1
        y_inc = 1 if to_pos.y > from_pos.y else -1
        
        error = dx - dy
        
        while x != to_pos.x or y != to_pos.y:
            # Check if current position (excluding start) blocks sight
            if x != from_pos.x or y != from_pos.y:
                if (x, y) in self.walls:
                    return False
            
            error2 = error * 2
            if error2 > -dy:
                error -= dy
                x += x_inc
            if error2 < dx:
                error += dx
                y += y_inc
        
        return True
    
    # ========== MODIFICATION METHODS ==========
    
    def add_wall(self, position: Position) -> None:
        """Add a wall at the specified position."""
        if position.is_valid(self.width, self.height):
            self.walls.add((position.x, position.y))
            self._update_fov_map()
    
    def remove_wall(self, position: Position) -> None:
        """Remove a wall at the specified position."""
        self.walls.discard((position.x, position.y))
        self._update_fov_map()
    
    def add_shadow(self, position: Position) -> None:
        """Add shadow coverage at the specified position."""
        if position.is_valid(self.width, self.height):
            self.shadows.add((position.x, position.y))
    
    def add_cooling_node(self, position: Position) -> None:
        """Add a cooling node at the specified position."""
        if position.is_valid(self.width, self.height):
            self.cooling_nodes.add((position.x, position.y))
    
    def add_cpu_recovery_node(self, position: Position) -> None:
        """Add a CPU recovery node at the specified position."""
        if position.is_valid(self.width, self.height):
            self.cpu_recovery_nodes.add((position.x, position.y))
    
    def add_ghost_node(self, position: Position) -> None:
        """Add a ghost node at the specified position."""
        if position.is_valid(self.width, self.height):
            self.ghost_nodes.add((position.x, position.y))
    
    def set_gateway(self, position: Position) -> None:
        """Set the level gateway/exit position."""
        if position.is_valid(self.width, self.height):
            self.gateway = Position(position.x, position.y)
    
    # ========== EXPLORATION SYSTEM ==========
    
    def mark_explored(self, position: Position) -> None:
        """Mark a position as explored by the player."""
        if position.is_valid(self.width, self.height):
            self.explored_tiles.add((position.x, position.y))
    
    def is_explored(self, position: Position) -> bool:
        """Check if a position has been explored."""
        return (position.x, position.y) in self.explored_tiles
    
    def remember_enemy_position(self, enemy_id: int, position: Position, turn: int) -> None:
        """Remember last known enemy position for fog of war."""
        self.last_known_enemy_positions[enemy_id] = (Position(position.x, position.y), turn)
    
    def get_last_known_enemy_position(self, enemy_id: int) -> Optional[Tuple[Position, int]]:
        """Get last known position of enemy."""
        return self.last_known_enemy_positions.get(enemy_id)
    
    # ========== UTILITY METHODS ==========
    
    def get_neighbors(self, position: Position, include_diagonals: bool = True) -> list[Position]:
        """
        Get valid neighboring positions.
        
        Args:
            position: Center position
            include_diagonals: Whether to include diagonal neighbors
            
        Returns:
            List of valid neighboring positions
        """
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        if include_diagonals:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        
        for dx, dy in directions:
            new_pos = Position(position.x + dx, position.y + dy)
            if new_pos.is_valid(self.width, self.height):
                neighbors.append(new_pos)
        
        return neighbors
    
    def get_walkable_neighbors(self, position: Position, include_diagonals: bool = True) -> list[Position]:
        """Get neighboring positions that are walkable (not walls)."""
        neighbors = self.get_neighbors(position, include_diagonals)
        return [pos for pos in neighbors if self.is_valid_position(pos)]
    
    def get_all_positions(self) -> list[Position]:
        """Get all valid positions on the map."""
        positions = []
        for x in range(self.width):
            for y in range(self.height):
                positions.append(Position(x, y))
        return positions
    
    def get_wall_count(self) -> int:
        """Get total number of walls on the map."""
        return len(self.walls)
    
    def get_shadow_count(self) -> int:
        """Get total number of shadow tiles on the map."""
        return len(self.shadows) + len(self.ghost_nodes)
    
    def clear_items(self) -> None:
        """Clear all items from the map."""
        self.data_patches.clear()
        self.exploit_pickups.clear()
        self.permanent_upgrades.clear()
        self.story_fragments.clear()
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"GameMap({self.width}x{self.height}, "
                f"walls={len(self.walls)}, shadows={len(self.shadows)})")
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"GameMap(width={self.width}, height={self.height}, "
                f"walls={len(self.walls)}, shadows={len(self.shadows)}, "
                f"features={len(self.cooling_nodes + self.cpu_recovery_nodes + self.ghost_nodes)})")