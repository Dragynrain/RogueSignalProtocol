#!/usr/bin/env python3
"""
Pathfinding utilities using TCOD A* and Dijkstra maps.

This module provides centralized pathfinding for all enemy movement:
- A* pathfinding with path length validation
- Dijkstra maps for advanced AI behaviors (flee, coordinate, ambush)
- Enemy collision avoidance
- Path validation and connectivity checks
"""

import logging

import numpy as np
import tcod

from rsp.entities.base import Position
from rsp.core.errors import GameErrorHandler


class PathfindingHelper:
    """
    Centralized pathfinding using TCOD A* and Dijkstra maps.

    Single source of truth for all enemy pathfinding operations.
    Used by the movement queue system to calculate paths to targets.

    This helper ensures consistent pathfinding behavior across all enemies
    and movement types (PATROL, SEEK, HOSTILE). Includes enemy collision
    avoidance and reasonable path length validation.

    NEW: Dijkstra map support for advanced AI behaviors:
    - Flee: Move away from dangerous positions
    - Coordinate: Position relative to other enemies
    - Ambush: Find optimal attack positions
    """

    # Pathfinding constants
    SHORT_DISTANCE_THRESHOLD = 5  # Distance considered "short" for pathfinding
    MIN_PATH_LENGTH = 15  # Minimum reasonable path length
    SHORT_DISTANCE_MULTIPLIER = 5  # Path length multiplier for short distances

    @staticmethod
    def calculate_path(
        start: Position,
        goal: Position,
        game_map,
        game_engine,
        moving_enemy,
        max_length_multiplier: float = 3.0,
    ) -> list[tuple[int, int]] | None:
        """
        Calculate path from start to goal.

        Args:
            start: Starting position
            goal: Goal position
            game_map: GameMap for walkability
            game_engine: GameEngine for enemy positions
            moving_enemy: Enemy doing pathfinding (exclude from collision)
            max_length_multiplier: Max path length as multiple of direct distance

        Returns:
            List of (y, x) tuples (TCOD format), or None if no reasonable path
        """
        # Calculate reasonable path length
        direct_distance = start.distance_to(goal)
        if direct_distance <= PathfindingHelper.SHORT_DISTANCE_THRESHOLD:
            max_length = max(
                PathfindingHelper.MIN_PATH_LENGTH,
                int(direct_distance * PathfindingHelper.SHORT_DISTANCE_MULTIPLIER),
            )
        else:
            max_length = max(
                PathfindingHelper.MIN_PATH_LENGTH, int(direct_distance * max_length_multiplier)
            )

        try:
            # Create cost map with enemy collision
            cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

            # TCOD pathfinding
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))

            # Validate path (TCOD returns numpy array)
            if len(path) > 1 and len(path) <= max_length:
                return path
            elif len(path) > max_length:
                logging.debug(
                    f"Pathfinding: ({start.x},{start.y}) -> ({goal.x},{goal.y}), path too long: {len(path)} > {max_length}"
                )
            else:
                logging.debug(
                    f"Pathfinding: ({start.x},{start.y}) -> ({goal.x},{goal.y}), no path found"
                )
            return None

        except Exception as e:
            GameErrorHandler.handle_error(e, "pathfinding", "Pathfinding failed", fatal=False)
            return None

    @staticmethod
    def create_dijkstra_map(
        goals: list[Position], game_map, game_engine, moving_enemy, max_distance: int = 100
    ) -> np.ndarray:
        """
        Create a Dijkstra map showing distance to nearest goal from any position.

        A Dijkstra map is a 2D array where each cell contains the cost to reach
        the nearest goal. This enables advanced AI behaviors:
        - Chase: Move to cells with LOWER values (closer to goals)
        - Flee: Move to cells with HIGHER values (further from goals)
        - Coordinate: Multiple enemies can use the same map

        Args:
            goals: List of goal positions (e.g., player position for chase,
                   enemy positions for flee)
            game_map: GameMap for walkability
            game_engine: GameEngine for enemy positions
            moving_enemy: Enemy using this map (for collision avoidance)
            max_distance: Maximum distance to compute (higher = more expensive)

        Returns:
            2D numpy array [y, x] with distance values (numpy.inf for unreachable)
        """
        # Create cost map with enemy collision
        cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

        # Create graph for pathfinding
        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        # Add all goals as roots
        for goal in goals:
            pathfinder.add_root((goal.y, goal.x))  # TCOD uses (y, x)

        # Return the distance map
        # pathfinder.distance is a 2D array with distances from roots
        return pathfinder.distance

    @staticmethod
    def get_flee_move(
        current_pos: Position, dijkstra_map: np.ndarray, game_map
    ) -> tuple[int, int] | None:
        """
        Get best move to FLEE from threats using Dijkstra map.

        Finds the adjacent cell with the HIGHEST distance value (furthest from threats).

        Args:
            current_pos: Current position of the fleeing enemy
            dijkstra_map: Dijkstra map with distances to threats
            game_map: GameMap for boundary checking

        Returns:
            Tuple (dx, dy) for the best flee direction, or None if no valid move
        """
        # Validate current position is within dijkstra_map bounds
        if dijkstra_map is None or dijkstra_map.size == 0:
            return None
        map_height, map_width = dijkstra_map.shape
        if not (0 <= current_pos.x < map_width and 0 <= current_pos.y < map_height):
            logging.debug(
                f"get_flee_move: current_pos ({current_pos.x},{current_pos.y}) "
                f"out of bounds for dijkstra_map ({map_width}x{map_height})"
            )
            return None

        best_move = None
        best_distance = dijkstra_map[current_pos.y, current_pos.x]  # [y, x] indexing

        # Check all 8 adjacent cells
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
            new_pos = Position(current_pos.x + dx, current_pos.y + dy)

            # Validate position
            if not new_pos.is_valid(game_map.width, game_map.height):
                continue
            if game_map.is_wall(new_pos):
                continue

            # Bounds check before array access (defensive - is_valid should catch this)
            if not (0 <= new_pos.x < map_width and 0 <= new_pos.y < map_height):
                continue

            # Get distance at this position
            distance = dijkstra_map[new_pos.y, new_pos.x]

            # We want HIGHER distance (flee) - skip unreachable cells
            if distance == np.inf:
                continue

            if distance > best_distance:
                best_distance = distance
                best_move = (dx, dy)

        return best_move

    @staticmethod
    def path_exists(start: Position, goal: Position, cost_map: np.ndarray) -> bool:
        """
        Check if a valid path exists between two points.

        Simpler than calculate_path - just returns boolean, doesn't validate length
        or apply enemy collision. Useful for connectivity validation.

        Args:
            start: Starting position
            goal: Goal position
            cost_map: Pre-computed cost map (0 = impassable, >0 = passable with cost)

        Returns:
            True if any path exists, False otherwise
        """

        def _check_path():
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))
            return len(path) >= 2  # Path includes start and goal

        return GameErrorHandler.handle_safe_operation(_check_path, "path_check", False)

    @staticmethod
    def calculate_simple_path(
        start: Position, goal: Position, cost_map: np.ndarray
    ) -> list[tuple[int, int]] | None:
        """
        Calculate path using a custom cost map without enemy collision.

        Used for special pathfinding cases like:
        - Level generation (ensuring spawn-to-gateway connectivity)
        - Autowalk (player pathfinding without enemy avoidance)
        - Patrol route generation

        Args:
            start: Starting position
            goal: Goal position
            cost_map: Pre-computed cost map (0 = impassable, >0 = passable with cost)

        Returns:
            List of (y, x) tuples (TCOD format), or None if no path exists
        """

        def _calculate_path():
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))

            if len(path) >= 2:
                return path
            return None

        return GameErrorHandler.handle_safe_operation(_calculate_path, "simple_path", None)

    @staticmethod
    def _create_cost_map(game_map, game_engine, moving_enemy):
        """Create cost map with enemy collision avoidance."""
        cost_map = game_map.get_walkability_map().copy()

        # Mark player as impassable (enemies path TO adjacent, not ONTO player)
        if hasattr(game_engine, "player") and game_engine.player is not None:
            try:
                player = game_engine.player
                # Validate coordinates are finite numbers BEFORE int conversion
                # (NaN/infinity would produce unpredictable int() results)
                if (
                    hasattr(player, "x")
                    and hasattr(player, "y")
                    and player.x is not None
                    and player.y is not None
                    and isinstance(player.x, (int, float))
                    and isinstance(player.y, (int, float))
                    and player.x == player.x  # NaN check (NaN != NaN)
                    and player.y == player.y
                ):
                    px, py = int(player.x), int(player.y)
                    if 0 <= px < game_map.width and 0 <= py < game_map.height:
                        cost_map[py, px] = 0  # TCOD uses [y, x] indexing
            except (AttributeError, TypeError, ValueError) as e:
                logging.debug(f"Failed to mark player as impassable in cost map: {e}")
                pass  # Skip player blocking if coordinates invalid (e.g., in tests)

        # Mark other enemies as impassable
        for enemy in game_engine.enemies:
            if enemy.id != moving_enemy.id:
                x, y = enemy.x, enemy.y
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    cost_map[y, x] = 0  # TCOD uses [y, x] indexing

        return cost_map
