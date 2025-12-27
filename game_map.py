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

from dataclasses import dataclass
from functools import lru_cache

import tcod
import tcod.constants

from game_entities import Position
from game_inventory import CodeHack, ExploitItem, StoryFragment


@dataclass
class RestoreNode:
    """
    Tracks per-node state for A13+ capacity system.

    Position is NOT stored in RestoreNode - it's the dict key.
    This avoids redundancy and potential key/value mismatch bugs.
    """

    node_type: str  # "cooling", "cpu", "ghost"
    total_capacity: int = -1  # -1 = unlimited (pre-A13), >0 = max capacity
    used_capacity: int = 0  # How much has been consumed

    def use(self, amount_needed: int) -> int:
        """
        Consume capacity and return actual restoration amount.

        Only consumes capacity equal to actual benefit provided.
        Returns actual amount restored (may be less than requested if depleted).

        Args:
            amount_needed: Amount of restoration requested

        Returns:
            Actual amount restored (may be less if capacity is limited)
        """
        if self.total_capacity == -1:
            return amount_needed  # Unlimited

        remaining = self.total_capacity - self.used_capacity
        actual = min(amount_needed, remaining)
        self.used_capacity += actual
        return actual

    @property
    def depleted(self) -> bool:
        """Check if node is fully depleted."""
        return self.total_capacity != -1 and self.used_capacity >= self.total_capacity

    @property
    def unlimited(self) -> bool:
        """Check if node has unlimited capacity."""
        return self.total_capacity == -1


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
        self.walls: set[tuple[int, int]] = set()
        self.blind_spots: set[tuple[int, int]] = set()
        self.used_blind_spots: set[tuple[int, int]] = set()  # A20: consumed blind spots

        # Node dicts - dict[position, RestoreNode] for A13+ capacity system
        # Membership check: `pos in cooling_nodes` works same as with sets
        # Iteration: `for pos in cooling_nodes` iterates over positions
        self.cooling_nodes: dict[tuple[int, int], RestoreNode] = {}
        self.cpu_recovery_nodes: dict[tuple[int, int], RestoreNode] = {}
        self.ghost_nodes: dict[tuple[int, int], RestoreNode] = {}

        # Items
        self.code_hacks: dict[tuple[int, int], CodeHack] = {}
        self.exploit_pickups: dict[tuple[int, int], ExploitItem] = {}
        self.permanent_upgrades: dict[tuple[int, int], str] = {}  # position -> upgrade_key
        self.story_fragments: dict[tuple[int, int], StoryFragment] = (
            {}
        )  # position -> story_fragment

        # Special locations
        self.gateway: Position | None = None

        # Memory system for hybrid fog of war
        self.explored_tiles: set[tuple[int, int]] = set()
        self.last_known_enemy_positions: dict[int, tuple[Position, int]] = (
            {}
        )  # enemy_id -> (position, turn_seen)

        # PHASE 5: Loot room clustering
        self.loot_room_positions: set[tuple[int, int]] = set()  # Floor positions in loot rooms

    def is_wall(self, position: Position) -> bool:
        """Check if position contains a wall."""
        if not position.is_valid(self.width, self.height):
            return True
        return (position.x, position.y) in self.walls

    def is_blind_spot(self, position: Position) -> bool:
        """
        Check if position is in a blind spot.

        Blind spots provide stealth bonuses and enable System Hop pivoting.
        Ghost nodes also count as blind spots in addition to their trace reduction effect.

        Args:
            position: Position to check

        Returns:
            True if position is in a blind spot zone or is a ghost node
        """
        if not position.is_valid(self.width, self.height):
            return False
        # Ghost nodes function as blind spots in addition to their special effect
        return (position.x, position.y) in self.blind_spots or (
            position.x,
            position.y,
        ) in self.ghost_nodes

    def consume_blind_spot(self, position: Position) -> bool:
        """
        Consume a blind spot (A20+: one-time-use blind spots).

        Moves the blind spot from active to used. Ghost nodes are NOT consumed
        as they are special nodes, not regular blind spots.

        Args:
            position: Position of blind spot to consume

        Returns:
            True if blind spot was consumed, False if not a consumable blind spot
        """
        pos = (position.x, position.y)
        if pos in self.blind_spots:
            self.blind_spots.remove(pos)
            self.used_blind_spots.add(pos)
            return True
        return False

    def is_cooling_node(self, position: Position) -> bool:
        """Check if position contains an active (non-depleted) cooling node."""
        pos = (position.x, position.y)
        node = self.cooling_nodes.get(pos)
        return node is not None and not node.depleted

    def is_cpu_recovery_node(self, position: Position) -> bool:
        """Check if position contains an active (non-depleted) CPU recovery node."""
        pos = (position.x, position.y)
        node = self.cpu_recovery_nodes.get(pos)
        return node is not None and not node.depleted

    def is_ghost_node(self, position: Position) -> bool:
        """Check if position contains an active (non-depleted) ghost node."""
        pos = (position.x, position.y)
        node = self.ghost_nodes.get(pos)
        return node is not None and not node.depleted

    def get_special_node_type(self, position: Position) -> str | None:
        """
        Get the type of special node at position, if any.

        Consolidates the repeated OR-chain pattern found in rendering and turn
        processing code into a single helper method.

        Args:
            position: Position to check

        Returns:
            'cooling', 'cpu', 'ghost', or None if no special node
        """
        pos_tuple = (position.x, position.y)
        if pos_tuple in self.cooling_nodes:
            return "cooling"
        if pos_tuple in self.cpu_recovery_nodes:
            return "cpu"
        if pos_tuple in self.ghost_nodes:
            return "ghost"
        return None

    def is_special_node(self, position: Position) -> bool:
        """
        Check if position has any special node.

        Consolidates the repeated pattern:
            is_cooling_node(pos) or is_cpu_recovery_node(pos) or is_ghost_node(pos)

        Args:
            position: Position to check

        Returns:
            True if any special node exists at position
        """
        return self.get_special_node_type(position) is not None

    def get_code_hack(self, position: Position) -> CodeHack | None:
        """Get code at position."""
        return self.code_hacks.get((position.x, position.y))

    def get_exploit_pickup(self, position: Position) -> ExploitItem | None:
        """Get exploit pickup at position."""
        return self.exploit_pickups.get((position.x, position.y))

    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid for movement."""
        return position.is_valid(self.width, self.height) and not self.is_wall(position)

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
        if not (start.is_valid(self.width, self.height) and end.is_valid(self.width, self.height)):
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
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
        )

        # Check if end position is visible (TCOD array is indexed as [y, x])
        return fov[end.y, end.x]

    def has_line_of_sight_bresenham(self, start: Position, end: Position) -> bool:
        """
        Check line of sight using Bresenham's line algorithm.

        More permissive than FOV-based LOS - simply checks if any wall blocks
        the straight line between two points. Better for targeting where you
        want intuitive "can I see that tile" behavior.

        Args:
            start: Starting position (viewer)
            end: Target position

        Returns:
            True if no wall blocks the line between start and end
        """
        if not (start.is_valid(self.width, self.height) and end.is_valid(self.width, self.height)):
            return False

        # Same position is always visible
        if start == end:
            return True

        # Bresenham's line algorithm
        x0, y0 = start.x, start.y
        x1, y1 = end.x, end.y

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        x, y = x0, y0
        while True:
            # Skip start position, check all others including endpoint
            if (x, y) != (x0, y0):
                # If we hit a wall before reaching the end, no LOS
                if self.is_wall(Position(x, y)):
                    return False

            # Reached the end
            if x == x1 and y == y1:
                return True

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _get_transparency_map(self):
        """Get transparency map for FOV calculations (cached for performance).

        Returns:
            Boolean numpy array with shape (height, width) where True = transparent.
            Uses (y, x) indexing consistent with TCOD conventions.
        """
        # Cache the transparency map to avoid recreating it every time
        if not hasattr(self, "_transparency_cache"):
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
        if hasattr(self, "_transparency_cache"):
            del self._transparency_cache
        if hasattr(self, "_walkability_cache"):
            del self._walkability_cache
        # Clear LRU cache for FOV computations
        self._compute_fov_cached.cache_clear()

    def get_walkability_map(self):
        """Get walkability map for pathfinding (cached for performance).

        Returns:
            Boolean numpy array with shape (height, width) where True = walkable.
            Uses (y, x) indexing consistent with TCOD conventions.
        """
        if not hasattr(self, "_walkability_cache"):
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
        if not (start.is_valid(self.width, self.height) and end.is_valid(self.width, self.height)):
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
        # Only log when actually computing (not from cache)
        # This is the first call for this set of parameters
        transparency = self._get_transparency_map()
        result = tcod.map.compute_fov(
            transparency=transparency,
            pov=(start_y, start_x),
            radius=vision_range,
            algorithm=tcod.constants.FOV_SYMMETRIC_SHADOWCAST,
        )
        # Note: Can't reliably detect cache hits/misses here, so minimal logging
        return result

    def reveal_area_around(self, center: Position | tuple[int, int], radius: int = 1) -> None:
        """
        Reveal a square area around a position by adding tiles to explored_tiles.

        Used for revealing context around enemies, nodes, and other points of interest.
        Validates positions are within map bounds before adding.

        Args:
            center: Center position (Position or (x, y) tuple)
            radius: Half-size of area to reveal (1 = 3x3, 2 = 5x5, etc.)
        """
        # Handle both Position objects and tuples
        if isinstance(center, Position):
            cx, cy = center.x, center.y
        else:
            cx, cy = center

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = cx + dx, cy + dy
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.explored_tiles.add((x, y))
