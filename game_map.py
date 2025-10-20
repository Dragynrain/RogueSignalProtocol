"""
Game Map Module - Handles map data structure and spatial queries.

Manages all map-related data:
- Terrain (walls, shadows)
- Special nodes (cooling, CPU recovery, ghost)
- Items (code hacks, exploits, upgrades, story fragments)
- Gateway (level exit)
- Fog of war and enemy memory system
- Line of sight calculations using TCOD FOV
"""

import logging
import tcod
import tcod.constants
from functools import lru_cache
from typing import Set, Tuple, Dict, Optional
from game_entities import Position
from game_inventory import CodeHack, ExploitItem, StoryFragment


class GameMap:
    """
    Game world map with terrain and features.

    Stores map data as sets and dictionaries for fast lookups.
    Provides query methods for terrain, items, and visibility.
    Maintains explored tiles and last known enemy positions for fog of war.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Terrain sets
        self.walls: Set[Tuple[int, int]] = set()
        self.shadows: Set[Tuple[int, int]] = set()
        
        # Feature sets
        self.cooling_nodes: Set[Tuple[int, int]] = set()
        self.cpu_recovery_nodes: Set[Tuple[int, int]] = set()
        self.ghost_nodes: Set[Tuple[int, int]] = set()
        
        # Items
        self.code_hacks: Dict[Tuple[int, int], CodeHack] = {}
        self.exploit_pickups: Dict[Tuple[int, int], ExploitItem] = {}
        self.permanent_upgrades: Dict[Tuple[int, int], str] = {}  # position -> upgrade_key
        self.story_fragments: Dict[Tuple[int, int], StoryFragment] = {}  # position -> story_fragment
        
        # Special locations
        self.gateway: Optional[Position] = None
        
        # Memory system for hybrid fog of war
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.last_known_enemy_positions: Dict[int, Tuple[Position, int]] = {}  # enemy_id -> (position, turn_seen)

        # PHASE 5: Loot room clustering
        self.loot_room_positions: Set[Tuple[int, int]] = set()  # Floor positions in loot rooms
    
    def is_wall(self, position: Position) -> bool:
        """Check if position contains a wall."""
        if not position.is_valid(self.width, self.height):
            return True
        return (position.x, position.y) in self.walls
    
    def is_shadow(self, position: Position) -> bool:
        """
        Check if position is in shadow.

        Shadow zones provide stealth bonuses and enable Shadow Step teleportation.
        Ghost nodes also count as shadows in addition to their trace reduction effect.

        Args:
            position: Position to check

        Returns:
            True if position is in a shadow zone or is a ghost node
        """
        if not position.is_valid(self.width, self.height):
            return False
        # Ghost nodes function as shadows in addition to their special effect
        return ((position.x, position.y) in self.shadows or
                (position.x, position.y) in self.ghost_nodes)
    
    def is_cooling_node(self, position: Position) -> bool:
        """Check if position contains a cooling node."""
        return (position.x, position.y) in self.cooling_nodes
    
    def is_cpu_recovery_node(self, position: Position) -> bool:
        """Check if position contains a CPU recovery node."""
        return (position.x, position.y) in self.cpu_recovery_nodes
    
    def is_ghost_node(self, position: Position) -> bool:
        """Check if position contains a ghost node (trace level reduction)."""
        return (position.x, position.y) in self.ghost_nodes
    
    def get_code_hack(self, position: Position) -> Optional[CodeHack]:
        """Get code at position."""
        return self.code_hacks.get((position.x, position.y))
    
    def get_exploit_pickup(self, position: Position) -> Optional[ExploitItem]:
        """Get exploit pickup at position."""
        return self.exploit_pickups.get((position.x, position.y))
    
    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid for movement."""
        return (position.is_valid(self.width, self.height) and 
                not self.is_wall(position))
    
    def has_line_of_sight(self, start: Position, end: Position) -> bool:
        """
        Check line of sight between two positions.

        Uses TCOD's symmetric shadowcasting FOV algorithm for better corner visibility
        and consistency with the game's FOV rendering.

        Args:
            start: Starting position (viewer)
            end: Target position

        Returns:
            True if unobstructed line of sight exists
        """
        # Use the improved TCOD version for better corner visibility
        return self.has_line_of_sight_tcod(start, end)
    
    def has_line_of_sight_bresenham(self, start: Position, end: Position) -> bool:
        """Check line of sight between two positions using Bresenham's algorithm (legacy)."""
        if not (start.is_valid(self.width, self.height) and 
                end.is_valid(self.width, self.height)):
            return False
        
        # Calculate distance and direction for Bresenham's algorithm
        delta_x = abs(end.x - start.x)
        delta_y = abs(end.y - start.y)
        x_direction = 1 if start.x < end.x else -1
        y_direction = 1 if start.y < end.y else -1
        bresenham_error = delta_x - delta_y
        
        current_x, current_y = start.x, start.y
        max_steps = delta_x + delta_y + 1  # Safety counter to prevent infinite loops
        step_count = 0
        
        while step_count < max_steps:
            if current_x == end.x and current_y == end.y:
                return True
            if self.is_wall(Position(current_x, current_y)):
                return False
            
            # Bresenham's line algorithm step
            error_doubled = 2 * bresenham_error
            if error_doubled > -delta_y:
                bresenham_error -= delta_y
                current_x += x_direction
            if error_doubled < delta_x:
                bresenham_error += delta_x
                current_y += y_direction
            
            step_count += 1
        
        return False  # Safety fallback if max steps exceeded
    
    def has_line_of_sight_tcod(self, start: Position, end: Position) -> bool:
        """
        Check line of sight using TCOD's FOV system.

        Creates a transparency map and computes FOV from the start position.
        Uses symmetric shadowcasting for consistent visibility rules.

        Note: TCOD arrays use [y, x] indexing while functions use (x, y) parameters.

        Args:
            start: Starting position (viewer)
            end: Target position

        Returns:
            True if target is visible from start position
        """
        if not (start.is_valid(self.width, self.height) and 
                end.is_valid(self.width, self.height)):
            return False
        
        # Use TCOD's FOV for better corner visibility
        # Create a transparency map (True = transparent, False = opaque)
        transparency = self._get_transparency_map()
        
        # Calculate the maximum distance to check
        max_distance = max(abs(end.x - start.x), abs(end.y - start.y)) + 1
        
        # Compute FOV from start position (TCOD uses y,x coordinate order)
        fov = tcod.map.compute_fov(
            transparency=transparency,
            pov=(start.y, start.x),
            radius=max_distance,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST
        )
        
        # Check if end position is visible (TCOD array is indexed as [y, x])
        return fov[end.y, end.x]
    
    def _get_transparency_map(self):
        """Get transparency map for FOV calculations (cached for performance).

        Returns:
            Boolean numpy array with shape (height, width) where True = transparent.
            Uses (y, x) indexing consistent with TCOD conventions.
        """
        # Cache the transparency map to avoid recreating it every time
        if not hasattr(self, '_transparency_cache'):
            import numpy as np
            transparency = np.ones((self.height, self.width), dtype=bool)
            for y in range(self.height):
                for x in range(self.width):
                    # Walls are opaque (False), everything else is transparent (True)
                    transparency[y, x] = not self.is_wall(Position(x, y))
            self._transparency_cache = transparency
        return self._transparency_cache
    
    def invalidate_transparency_cache(self):
        """Invalidate transparency and walkability caches when map changes.

        Call this method whenever walls are added or removed from the map.
        """
        if hasattr(self, '_transparency_cache'):
            del self._transparency_cache
        if hasattr(self, '_walkability_cache'):
            del self._walkability_cache

    def get_walkability_map(self):
        """Get walkability map for pathfinding (cached for performance).

        Returns:
            Boolean numpy array with shape (height, width) where True = walkable.
            Uses (y, x) indexing consistent with TCOD conventions.
        """
        if not hasattr(self, '_walkability_cache'):
            import numpy as np
            walkability = np.zeros((self.height, self.width), dtype=bool)
            for y in range(self.height):
                for x in range(self.width):
                    pos = Position(x, y)
                    walkability[y, x] = self.is_valid_position(pos)
            self._walkability_cache = walkability
        return self._walkability_cache
    
    def can_see_position(self, start: Position, end: Position, vision_range: int) -> bool:
        """Check if start position can see end position using TCOD FOV within range (optimized with LRU caching)."""
        if not (start.is_valid(self.width, self.height) and
                end.is_valid(self.width, self.height)):
            return False

        # Check if within vision range first (faster early exit)
        distance = start.distance_to(end)
        if distance > vision_range:
            return False

        # Use internal cached FOV computation
        fov = self._compute_fov_cached(start.x, start.y, vision_range)

        # Check if end position is visible (TCOD array is indexed as [y, x])
        return fov[end.y, end.x]

    @lru_cache(maxsize=128)
    def _compute_fov_cached(self, start_x: int, start_y: int, vision_range: int):
        """Compute FOV with LRU caching for better performance.

        Args:
            start_x: Starting X position
            start_y: Starting Y position
            vision_range: Maximum vision radius

        Returns:
            Boolean numpy array of visible tiles
        """
        transparency = self._get_transparency_map()
        return tcod.map.compute_fov(
            transparency=transparency,
            pov=(start_y, start_x),
            radius=vision_range,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST
        )