#!/usr/bin/env python3
"""
Auto-Walk System

Implements click-to-walk functionality using TCOD pathfinding.
Allows player to click distant tiles and automatically pathfind there,
with intelligent stop conditions for safety.
"""

import logging
from typing import TYPE_CHECKING

from game_entities import Position
from game_pathfinding import PathfindingHelper

if TYPE_CHECKING:
    from game_engine import GameEngine


class AutoWalk:
    """
    Automatic walking system for click-to-walk functionality.

    Features:
    - Uses TCOD A* pathfinding for intelligent routes
    - Stops on enemy detection (safety)
    - Stops on path blockage
    - Stops on player damage
    - Cancellable by user input

    The path is computed once when auto-walk starts, then executed
    step-by-step each turn with safety checks between steps.
    """

    def __init__(self):
        """Initialize auto-walk system in inactive state."""
        self.active = False
        self.path = []  # List of Position objects forming the route
        self.current_step = 0  # Index into path (0 = current position)
        self.destination = None  # Final target Position
        self.stop_reason = None  # Human-readable stop reason
        self._last_cpu = None  # Track damage detection

    def start(self, player_pos: Position, target_pos: Position, game_engine: "GameEngine") -> bool:
        """
        Start auto-walk from player position to target using TCOD pathfinding.

        Args:
            player_pos: Current player position
            target_pos: Destination position
            game_engine: GameEngine for map and pathfinding

        Returns:
            True if path found and auto-walk started, False if no path exists
        """
        # Can't walk to current position
        if player_pos == target_pos:
            return False

        # Can't walk to walls
        if game_engine.game_map.is_wall(target_pos):
            logging.debug(f"AutoWalk: Cannot walk to wall at {target_pos}")
            return False

        # Use PathfindingHelper for centralized pathfinding
        game_map = game_engine.game_map

        # Create cost map for pathfinding (no enemy collision for player autowalk)
        import numpy as np

        walkability = game_map.get_walkability_map()
        cost_map = np.where(walkability, 10, 0).astype(np.int32)

        # Calculate path using PathfindingHelper
        tcod_path = PathfindingHelper.calculate_simple_path(player_pos, target_pos, cost_map)

        # Validate path exists
        if tcod_path is None or len(tcod_path) < 2:  # Path includes start position
            logging.debug(f"AutoWalk: No path from {player_pos} to {target_pos}")
            return False

        # Convert TCOD path [(y,x), ...] to Position objects
        # Skip first entry (current position)
        self.path = [Position(p[1], p[0]) for p in tcod_path[1:]]
        self.current_step = 0
        self.destination = target_pos
        self.active = True
        self.stop_reason = None
        self._last_cpu = game_engine.player.cpu

        logging.info(
            f"AutoWalk: Started from {player_pos} to {target_pos}, path_length={len(self.path)}"
        )
        return True

    def get_next_move(self, game_engine: "GameEngine") -> tuple[int, int] | None:
        """
        Get next move in auto-walk path.

        Checks stop conditions BEFORE returning the move. If any stop
        condition is met, auto-walk is cancelled and None is returned.

        Args:
            game_engine: GameEngine for stop condition checks

        Returns:
            Tuple (dx, dy) for next move, or None if auto-walk stopped
        """
        if not self.active:
            return None

        # Check if we've exhausted the path
        if self.current_step >= len(self.path):
            self.stop("Destination reached")
            return None

        # Get next position in path
        next_pos = self.path[self.current_step]

        # Calculate movement delta
        dx = next_pos.x - game_engine.player.x
        dy = next_pos.y - game_engine.player.y

        # Sanity check: move should be adjacent (1 tile in any direction)
        if abs(dx) > 1 or abs(dy) > 1:
            logging.warning(f"AutoWalk: Non-adjacent move ({dx},{dy}), stopping")
            self.stop("Path error - non-adjacent move")
            return None

        return (dx, dy)

    def advance_step(self):
        """
        Advance to next step in path.

        Call this AFTER successfully executing a move.
        """
        if self.active:
            self.current_step += 1

    def check_stop_conditions(self, game_engine: "GameEngine") -> tuple[bool, str | None]:
        """
        Check all auto-walk stop conditions.

        Call this AFTER each move to decide if auto-walk should continue.

        Stop conditions:
        1. Enemy becomes visible (CRITICAL - safety)
        2. Player took damage
        3. Next tile is blocked (wall/enemy)
        4. Path exhausted (reached destination)

        Args:
            game_engine: GameEngine for game state checks

        Returns:
            Tuple (should_stop, reason_string)
        """
        if not self.active:
            return False, None

        # 1. CRITICAL: Enemy detection (stop immediately for safety)
        for enemy in game_engine.enemies:
            if game_engine.player.can_see_enemy(enemy, game_engine.game_map):
                return True, "Enemy spotted!"

        # 2. Player took damage (compare CPU to last known value)
        if self._last_cpu is not None and game_engine.player.cpu < self._last_cpu:
            return True, "Took damage!"
        self._last_cpu = game_engine.player.cpu

        # 3. Check if next tile is blocked (if we haven't reached destination)
        if self.current_step < len(self.path):
            next_pos = self.path[self.current_step]

            # Wall check
            if game_engine.game_map.is_wall(next_pos):
                return True, "Path blocked by wall"

            # Enemy blocking check
            for enemy in game_engine.enemies:
                if enemy.position == next_pos:
                    return True, "Path blocked by enemy"

        # 4. Reached destination
        if self.current_step >= len(self.path):
            return True, "Destination reached"

        # No stop conditions met - continue walking
        return False, None

    def stop(self, reason: str):
        """
        Stop auto-walk and log the reason.

        Args:
            reason: Human-readable reason for stopping
        """
        if self.active:
            logging.info(f"AutoWalk: Stopped - {reason}")
            self.stop_reason = reason

        self.active = False
        self.path = []
        self.current_step = 0
        self.destination = None
        self._last_cpu = None

    def cancel(self):
        """Cancel auto-walk (user-initiated)."""
        self.stop("Cancelled by user")

    def is_active(self) -> bool:
        """Check if auto-walk is currently active."""
        return self.active

    def get_remaining_path(self):
        """
        Get remaining path positions (for visual preview).

        Returns:
            List of Position objects representing remaining path
        """
        if not self.active:
            return []
        return self.path[self.current_step :]
